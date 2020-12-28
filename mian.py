import speech_recognition as sr
import tkinter as tk
import tkinter.filedialog as fd
import tkinter.font as fonts
import color_palette as cp
import threading
import os

LISTENING_STATE = 0
NO_LISTENING_STATE = 1
folder_paths = []
file_paths = []

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


def create_path_widget(parent, path) -> tk.Frame:
    row_contener = tk.Frame(parent, width=100)
    path_title_frame = tk.Frame(row_contener, bg=cp.misty_rose)
    path_title_frame.pack()
    path_title = tk.Label(path_title_frame, text="path :", bg=cp.misty_rose, anchor='w', width=25)
    path_title.pack(fill="x", side="left")
    del_button = tk.Button(path_title_frame, text="del", fg="white", bg="red", command=lambda: row_contener.destroy())
    del_button.pack(side="right")
    path_label = tk.Entry(row_contener, bg=cp.champagne_pink)
    path_label.insert(0, path)
    path_label.pack(fill="x")
    kw_title = tk.Label(row_contener, text="keywords : ", bg=cp.misty_rose, anchor='w')
    kw_title.pack(fill="x")
    keywords_entry = tk.Entry(row_contener, bg=cp.champagne_pink)
    keywords_entry.pack(fill="x")
    return row_contener


def add_path_row(canvas: tk.Canvas, parent: tk.Frame, file_type: str):
    # for child in parent.winfo_children():
    #   child.destroy()

    path = None
    target_array = None
    if file_type == "folder":
        path = fd.askdirectory(initialdir='/')
        target_array = folder_paths
    elif file_type == "file":
        title = "Select file"
        filetypes = [("all files", "*.*")]
        path = fd.askopenfilename(initialdir='/', title=title, filetypes=filetypes)
        target_array = file_paths
    else:
        raise ValueError('Incorrect file type, valid file types are "file" or "folder"')

    if path == "":
        return

    row_contener = create_path_widget(parent, path)
    target_array.append(path)
    row_contener.pack(fill="x", expand=False, padx=5, pady=5)
    canvas.configure(scrollregion=canvas.bbox('all'))


window = tk.Tk()
window.configure(background=cp.dark_purple)
window.wm_minsize(800, 600)
window.wm_maxsize(800, 600)

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

window.mainloop()
