import speech_recognition as sr
import tkinter as tk
import tkinter.font as fonts
import color_palette as cp
import threading

LISTENING_STATE = 0
NO_LISTENING_STATE = 1

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


window = tk.Tk()
window.configure(background=cp.dark_purple)
window.wm_minsize(800, 600)
window.wm_maxsize(800, 600)

# Fonts
header_font = fonts.Font(family='Courier New', size=36, weight='bold')
smaller_header_font = fonts.Font(family='Courier New', size=20, weight='bold')

# Header ( in root )

header_text = tk.Label(window, font=header_font, text='Windows Voice Navigator', fg=cp.champagne_pink)
header_text.configure(background=cp.dark_purple)
header_text.pack()

# Center Panel ( in root )

center_panel = tk.Frame(width=750, height=400, bg=cp.misty_rose)
center_panel.pack()

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

def active_listen() :
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
