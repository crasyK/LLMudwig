import tkinter as tk
import tkinter.ttk as ttk
from tkinter import simpledialog, messagebox
import threading
import queue
from typing import Literal
from pydantic import BaseModel
from ollama import chat
from PIL import ImageGrab
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

class ImageDescription(BaseModel):
    emotion: Literal["Happy", "Excited", "Sad", "Angry", "Surprised", "Neutral", "CUTE"]
    catchphrase: str


# --- GUI Application ---
class StreamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LLMudwig")
        self.root.geometry("300x200")

        self.emoticons = {
            "Happy": "( •̀ ω •́ )✧", "Excited": "q(≧▽≦q)", "Sad": "(╯︵╰,)",
            "Angry": "(╯°□°）╯︵ ┻━┻", "Surprised": "Σ(⊙▽⊙'')", "Neutral": "(￣_￣)",
            "CUTE": "(｡♥‿♥｡)"
        }
        self.create_menu()
        
        self.status_label = tk.Label(root, text="")
        self.status_label.pack(pady=5)

        self.rec_button = tk.Button(
            root, 
            text="◉", 
            command=self.start_analysis, 
            font=("Arial", 32),
            height=2,                
            width=4
        )
        self.rec_button.pack(pady=10)

        self.emoticon_label = tk.Label(root, text="", font=("Arial", 24))
        self.emoticon_label.pack(pady=10)

        self.catchphrase_label = tk.Label(root, text="", wraplength=380)
        self.catchphrase_label.pack(pady=5)
        
        # --- Settings ---
        self.llm_model = tk.StringVar(value="gemma3:4b")

        self.q = queue.Queue()
        self.loading_chars = "|/-\\"
        self.loading_index = 0
        self.is_loading = False
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Configure...", command=self.open_settings_window)
        
    def open_settings_window(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Settings")
        settings_win.geometry("300x150")
        settings_win.transient(self.root) 
        settings_win.grab_set() 

        ttk.Label(settings_win, text="Ollama Code:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        model_entry = ttk.Entry(settings_win, textvariable=self.llm_model, width=30)
        model_entry.grid(row=0, column=1, padx=10, pady=10)

        button_frame = ttk.Frame(settings_win)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Save", command=settings_win.destroy).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=settings_win.destroy).pack(side="left", padx=5)

    def start_analysis(self):
        self.status_label.pack(pady=5)
        self.rec_button.pack_forget()
        self.emoticon_label.config(text="")
        self.catchphrase_label.config(text="")
        self.is_loading = True
        self.update_loading_animation()
        threading.Thread(target=self.run_ai_analysis, daemon=True).start()
        self.root.after(100, self.check_queue)

    def run_ai_analysis(self):
        try:
                path_addr = "screenshot.png"
                screenshot = ImageGrab.grab()
                screenshot.save(path_addr)
                path = Path(path_addr)
                response = chat(
                    model='gemma3:4b',
                    format=ImageDescription.model_json_schema(),
                    messages=[
                        {
                        'role': 'user',
                        'content': 'You are a streamer doing reactions! Analyze this image and return a detailed JSON including: what reaction in form of an emotion would fit best and a short comedic phrase that relates to the image and fits the emotion. Also not everything is a surprise, something might be boring pr just make you happy like code and feel cute like cats!.',
                        'images': [path],
                        },
                    ],
                    options={'temperature': 0.2},
                )
                image_analysis = ImageDescription.model_validate_json(response.message.content)
                
                self.q.put(image_analysis)
        except Exception as e:
            self.q.put(e)

    def update_loading_animation(self):
        if self.is_loading:
            char = self.loading_chars[self.loading_index]
            self.status_label.config(text=f"{char}", font=("Arial", 24))
            self.loading_index = (self.loading_index + 1) % len(self.loading_chars)
            self.root.after(100, self.update_loading_animation)

    def check_queue(self):
        try:
            result = self.q.get_nowait()
            self.is_loading = False
            self.status_label.config(text="")
            self.root.after(500, lambda: self.status_label.config(text=""))
            if isinstance(result, Exception):
                self.catchphrase_label.config(text=f"Error: {result}")
                self.rec_button.config(state=tk.NORMAL)
            else:
                self.emoticon_label.config(text=self.emoticons.get(result.emotion, ""))
                words = result.catchphrase.split()
                self.display_catchphrase_word_by_word(words)
        except queue.Empty:
            self.root.after(100, self.check_queue)

    def display_catchphrase_word_by_word(self, words):
        if words:
            current_text = self.catchphrase_label.cget("text")
            next_word = words.pop(0)
            self.catchphrase_label.config(text=f"{current_text} {next_word}".strip())
            self.root.after(200, lambda: self.display_catchphrase_word_by_word(words))
        else:
            self.rec_button.pack(pady=10)
            self.rec_button.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = StreamerApp(root)
    root.mainloop()
