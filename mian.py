import speech_recognition as sr
import subprocess
import psutil
import signal
import tkinter as tk
import tkinter.filedialog as fd
import tkinter.font as fonts
import tkinter.messagebox as msg
import color_palette as cp
import threading
import os

SAVE_FILE_NAME = "Save.txt"
OPEN_COMMAND_NAME = 'Open'
CLOSE_COMMAND_NAME = 'Close'

LISTENING_STATE = 0
NO_LISTENING_STATE = 1

folders_with_keywords = dict()
files_with_keywords = dict()
commands_with_keywords = dict()
commands_with_functions = dict()
opened_apps = dict()

# listen background task
listen_thread = None


def get_voice_string() -> str:
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
        try:
            text = r.recognize_google(audio, language="pl")
            return text
        except:
            return ""


def create_path_widget(parent, path, kw="") -> tuple:
    row_container = tk.Frame(parent)
    path_title_frame = tk.Frame(row_container, bg=cp.misty_rose)
    path_title_frame.pack()
    path_title = tk.Label(path_title_frame, text="path :", bg=cp.misty_rose, anchor='w', width=25)
    path_title.pack(fill="x", side="left")

    def del_button_behaviour():
        if path in files_with_keywords:
            del files_with_keywords[path]
        else:
            del folders_with_keywords[path]
        row_container.destroy()

    del_button = tk.Button(path_title_frame, text="del", fg="white", bg="red", command=del_button_behaviour)
    del_button.pack(side="right")
    path_label = tk.Entry(row_container, bg=cp.champagne_pink)
    path_label.insert(0, path)
    path_label.pack(fill="x")
    kw_title = tk.Label(row_container, text="keywords : ", bg=cp.misty_rose, anchor='w')
    kw_title.pack(fill="x")
    keywords_entry = tk.Entry(row_container, bg=cp.champagne_pink)
    keywords_entry.insert(0, kw)
    keywords_entry.pack(fill="x")
    return row_container, keywords_entry


def create_command_widget(parent, command_name, command_function) -> tk.Frame:
    row_container = tk.Frame(parent)
    command_title = tk.Label(row_container, bg=cp.misty_rose, text=f'{command_name} command keywords:', anchor='w',
                             width=31)
    command_title.pack(fill='x')
    command_entry = tk.Entry(row_container, bg=cp.champagne_pink)
    command_entry.pack(fill='x')
    commands_with_keywords[command_name] = command_entry
    commands_with_functions[command_name] = command_function
    return row_container


def add_path_row(canvas: tk.Canvas, parent: tk.Frame, file_type: str):
    # for child in parent.winfo_children():
    #   child.destroy()

    path = None
    target_dict = None
    if file_type == "folder":
        path = fd.askdirectory(initialdir='/')
        target_dict = folders_with_keywords
    elif file_type == "file":
        title = "Select file"
        filetypes = [("all files", "*.*")]
        path = fd.askopenfilename(initialdir='/', title=title, filetypes=filetypes)
        target_dict = files_with_keywords
    else:
        raise ValueError('Incorrect file type, valid file types are "file" or "folder"')

    if path == "":
        return

    if path in target_dict:
        msg.showerror("Cannot insert", "This file/folder is already on the list.")
    else:
        widget_with_keywords = create_path_widget(parent, path)
        target_dict[path] = widget_with_keywords[1]
        widget_with_keywords[0].pack(fill="x", expand=False, padx=5, pady=5)
        canvas.configure(scrollregion=canvas.bbox('all'))
        print(target_dict)


def recreate_path_row(parent: tk.Frame, path: str, kw: str):
    if os.path.exists(path):
        if os.path.isdir(path):
            target_dict = folders_with_keywords
        else:
            target_dict = files_with_keywords
        widget_with_keywords = create_path_widget(parent, path, kw)
        target_dict[path] = widget_with_keywords[1]
        widget_with_keywords[0].pack(fill="x", expand=False, padx=5, pady=5)


def save_app_data_to_file(filename: str):
    print(folders_with_keywords)
    print(files_with_keywords)
    with open(filename, 'w') as f:
        folders_count = len(folders_with_keywords)
        files_count = len(files_with_keywords)
        f.write(f"{str(folders_count)}\n")
        for path in folders_with_keywords:
            f.write(f"{path};{folders_with_keywords[path].get().strip()}\n")
        f.write(f"{str(files_count)}\n")
        for path in files_with_keywords:
            f.write(f"{path};{files_with_keywords[path].get().strip()}\n")
        # zapisaywanie slow kluczonwych komendy otwarcia
        f.write(f"{commands_with_keywords[OPEN_COMMAND_NAME].get().strip()}\n")


def load_app_data_from_file(filename: str):
    if os.path.exists(SAVE_FILE_NAME):
        with open(filename, 'r') as f:
            folder_count = int(f.readline())
            for i in range(folder_count):
                split_line = f.readline().split(';')
                recreate_path_row(folder_frame, split_line[0], split_line[1])
            file_count = int(f.readline())
            for i in range(file_count):
                split_line = f.readline().split(';')
                recreate_path_row(files_frame, split_line[0], split_line[1])
            commands_with_keywords[OPEN_COMMAND_NAME].insert(0, f.readline())


def on_window_close(window_to_close: tk.Tk):
    save_app_data_to_file(SAVE_FILE_NAME)
    window_to_close.destroy()


def run_file(path):
    real_path = os.path.realpath(path)
    os.startfile(real_path)


def close_file(path):
    print("Im in closed")
    if path in opened_apps:
        print('child pid')
        print(opened_apps[path])
        os.kill(opened_apps[path], signal.SIGTERM)
        del opened_apps[path]


def react_to_voice_string(voice_string):
    folder_names = []
    file_names = []
    command_name = None
    for folder_path in folders_with_keywords:
        for kw in map(lambda x: x.strip().lower(), folders_with_keywords[folder_path].get().split(',')):
            if kw in voice_string.lower() and len(kw) != 0:
                folder_names.append(folder_path)
                break
    for file_path in files_with_keywords:
        for kw in map(lambda x: x.strip().lower(), files_with_keywords[file_path].get().split(',')):
            if kw in voice_string.lower() and len(kw) != 0:
                file_names.append(file_path)
                break
    for command in commands_with_keywords:
        match_found = False
        for kw in map(lambda x: x.strip().lower(), commands_with_keywords[command].get().split(',')):
            if kw in voice_string.lower() and len(kw) != 0:
                command_name = command
                match_found = True
                break
        if match_found:
            break

    print(voice_string)
    print(folder_names)
    print(file_names)
    print(command_name)

    if command_name is None:
        # nic nie rób bo nie wybrano komendy
        return

    if not (len(folder_names) == 0 or len(file_names) == 0):
        # znaleziono obie ścieżki
        # TODO - Zmienić przy ulepszaniu funkcjonalności
        for name in folder_names:
            commands_with_functions[command_name](name)
        for name in file_names:
            commands_with_functions[command_name](name)

    elif not len(folder_names) == 0:
        for name in folder_names:
            commands_with_functions[command_name](name)
    elif not len(file_names) == 0:
        for name in file_names:
            commands_with_functions[command_name](name)

window = tk.Tk()
window.configure(background=cp.dark_purple)
window.wm_minsize(800, 600)
window.wm_maxsize(800, 600)
window.protocol("WM_DELETE_WINDOW", lambda: on_window_close(window))

# Fonts
header_font = fonts.Font(family='Courier New', size=36, weight='bold')
smaller_header_font = fonts.Font(family='Courier New', size=20, weight='bold')
small_courier = fonts.Font(family='Courier New', size=12, weight='bold')

# Header ( in root )

header_text = tk.Label(window, font=header_font, text='Windows Voice Navigator', fg=cp.champagne_pink)
header_text.configure(background=cp.dark_purple)
header_text.pack()

# Center Panel ( in root )

center_panel = tk.Frame(bg=cp.misty_rose, width=750, height=400)
center_panel.pack()

# Folders Panel ( in Center Panel )

folders_panel = tk.Frame(center_panel, bg=cp.excel_blue)
folders_panel.place(relwidth=0.32, relheight=0.96, relx=0.01, rely=0.02)

folders_panel_header = tk.Label(folders_panel, font=smaller_header_font, text='Folders', bg=cp.excel_blue)
folders_panel_header.pack()
add_folder_button = tk.Button(folders_panel, text="Add", font=small_courier)
add_folder_button.pack(pady=10, side='bottom')

## Folder paths Panel

folder_wrapper = tk.LabelFrame(folders_panel)

folder_canvas = tk.Canvas(folder_wrapper, width=220)
folder_canvas.pack(side="left", fill="y", expand=True)

folder_scrollbar = tk.Scrollbar(folder_wrapper, orient="vertical", command=folder_canvas.yview)
folder_scrollbar.pack(side="right", fill="y")

folder_canvas.configure(yscrollcommand=folder_scrollbar.set)
folder_canvas.bind("<Configure>", lambda e: folder_canvas.configure(scrollregion=folder_canvas.bbox('all')))

folder_frame = tk.Frame(folder_canvas, bg=cp.excel_blue)
folder_canvas.create_window((0, 0), window=folder_frame, anchor="nw")

folder_wrapper.pack(fill="both", expand=True)

add_folder_button.configure(command=lambda: add_path_row(folder_canvas, folder_frame, "folder"))

# Files Panel

files_panel = tk.Frame(center_panel, bg=cp.excel_blue)
files_panel.place(relwidth=0.32, relheight=0.96, relx=0.34, rely=0.02)
files_panel_header = tk.Label(files_panel, font=smaller_header_font, text='Files', bg=cp.excel_blue)
files_panel_header.pack()
add_file_button = tk.Button(files_panel, text="Add", font=small_courier)
add_file_button.pack(pady=10, side='bottom')

## Files paths Panel

files_wrapper = tk.LabelFrame(files_panel)

files_canvas = tk.Canvas(files_wrapper, width=220)
files_canvas.pack(side="left", fill="y", expand=True)

files_scrollbar = tk.Scrollbar(files_wrapper, orient="vertical", command=files_canvas.yview)
files_scrollbar.pack(side="right", fill="y")

files_canvas.configure(yscrollcommand=files_scrollbar.set)
files_canvas.bind("<Configure>", lambda e: files_canvas.configure(scrollregion=files_canvas.bbox('all')))

files_frame = tk.Frame(files_canvas, bg=cp.excel_blue)
files_canvas.create_window((0, 0), window=files_frame, anchor="nw")

files_wrapper.pack(fill="both", expand=True)

add_file_button.configure(command=lambda: add_path_row(files_canvas, files_frame, "file"))

# Commands Panel

commands_panel = tk.Frame(center_panel, bg=cp.excel_blue)
commands_panel.place(relwidth=0.32, relheight=0.96, relx=0.67, rely=0.02)
commands_panel_header = tk.Label(commands_panel, font=smaller_header_font, text='Commands', bg=cp.excel_blue)
commands_panel_header.pack()

commands_wrapper = tk.LabelFrame(commands_panel)

commands_canvas = tk.Canvas(commands_wrapper, width=220)
commands_canvas.pack(side="left", fill="y", expand=True)

commands_scrollbar = tk.Scrollbar(commands_wrapper, orient="vertical", command=commands_canvas.yview)
commands_scrollbar.pack(side="right", fill="y")

commands_canvas.configure(yscrollcommand=commands_scrollbar.set)
commands_canvas.bind("<Configure>", lambda e: commands_canvas.configure(scrollregion=commands_canvas.bbox('all')))

commands_frame = tk.Frame(commands_canvas, bg=cp.excel_blue)
commands_canvas.create_window((0, 0), window=commands_frame, anchor="nw")

commands_wrapper.pack(fill="both", expand=True)

create_command_widget(commands_frame, OPEN_COMMAND_NAME, run_file).pack()

# Listen Panel ( in root )

listen_panel = tk.Frame(width=750, height=100, bg=cp.champagne_pink)
listen_panel.pack(pady=20)

# Audio Text Box ( in Listen Panel )

listen_box = tk.Text(listen_panel, wrap="word")
listen_box.insert(tk.INSERT, "Your words here...")
listen_box.configure(state="disabled")
listen_box.place(relheight="0.8", relwidth="0.5", relx="0.48", rely="0.1")

# Listen Button ( in Listen Panel )

# if listening, state = 1, 0 otherwise
BUTTON_STATE = NO_LISTENING_STATE

listen_button = tk.Button(listen_panel, text="Listen", font=smaller_header_font, bg=cp.excel_green)


def active_listen():
    global listen_box
    while BUTTON_STATE == LISTENING_STATE:
        voice_string = get_voice_string()
        if len(voice_string) != 0:
            listen_box.configure(state="normal")
            listen_box.delete("1.0", "end")
            listen_box.insert(tk.INSERT, voice_string)
            listen_box.configure(state="disabled")
            react_to_voice_string(voice_string)


def listen_button_behaviour():
    global BUTTON_STATE
    global listen_thread
    if BUTTON_STATE == NO_LISTENING_STATE:
        BUTTON_STATE = LISTENING_STATE
        listen_button.configure(text="I'm\nlistening...", bg=cp.excel_blue)
        listen_thread = threading.Thread(target=active_listen)
        listen_thread.start()
    else:
        BUTTON_STATE = NO_LISTENING_STATE
        listen_button.configure(text="Listen", bg=cp.excel_green)


listen_button.configure(command=listen_button_behaviour)
listen_button.place(relheight="0.8", relwidth="0.3", relx="0.02", rely="0.1")

load_app_data_from_file(SAVE_FILE_NAME)

window.mainloop()
