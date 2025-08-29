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
    emotion: Literal[
        "Happy", "Excited", "Sad", "Angry", "Surprised", "Neutral", "CUTE",
        "Confused", "Tired", "Motivated", "Bored", "Proud", "Nervous", "Shy",
        "Cool", "In Love", "Exhausted", "Embarrassed", "Surprised+", "Relaxed"
    ]
    catchphrase: str


# --- GUI Application ---
class StreamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LLMudwig")
        self.root.geometry("300x200")

        self.emoticons = {
            "Happy": "( •̀ ω •́ )✧",
            "Excited": "q(≧▽≦q)",
            "Sad": "(╯︵╰,)",
            "Angry": "(╯°□°）╯︵ ┻━┻",
            "Surprised": "Σ(⊙▽⊙'')",
            "Neutral": "(￣_￣)",
            "CUTE": "(｡♥‿♥｡)",
            "Confused": "(・_・ヾ",
            "Tired": "(－_－) zzZ",
            "Motivated": "(ง •̀_•́)ง",
            "Bored": "(－‸ლ)",
            "Proud": "(๑•̀ㅂ•́)و✧",
            "Nervous": "(；・∀・)",
            "Shy": "(⁄ ⁄•⁄ω⁄•⁄ ⁄)",
            "Cool": "(⌐■_■)",
            "In Love": "(♥ω♥*)",
            "Exhausted": "(×_×;）",
            "Embarrassed": "(⁄ ⁄•⁄-⁄•⁄ ⁄)",
            "Surprised+": "(⊙_☉)",
            "Relaxed": "(˘︶˘).｡*♡"
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
        self.save_path = tk.StringVar(value="./screenshot.png")

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
        settings_win.geometry("350x180")
        settings_win.transient(self.root)
        settings_win.grab_set()

        ttk.Label(settings_win, text="Ollama Code:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        model_entry = ttk.Entry(settings_win, textvariable=self.llm_model, width=30)
        model_entry.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(settings_win, text="Screenshot-Pfad:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        path_entry = ttk.Entry(settings_win, textvariable=self.save_path, width=30)
        path_entry.grid(row=1, column=1, padx=10, pady=10)

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
            path_addr = self.save_path.get()
            screenshot = ImageGrab.grab()
            screenshot.save(path_addr)
            path = Path(path_addr)
            response = chat(

                model=self.llm_model.get(),
                #format=ImageDescription.model_json_schema(),
                messages=[
                {
                    'role': 'user',
                    'content': (
                    'You are Ludwig, a charismatic streamer with a bubbly, energetic, nerdy personality! You absolutely LOVE programming, cats, gaming, and all things tech. '
                    'You have a quirky sense of humor and often make references to programming concepts, pop culture, and internet memes. '
                    'Analyze this screenshot and respond with an appropriate emotion and a creative, witty catchphrase that matches what you see.\n\n'
                    
                    '🎯 EMOTION SELECTION GUIDELINES:\n'
                    '• Happy: General positive content, successful outcomes, nice UI/UX\n'
                    '• Excited: New features, cool tech, impressive projects, gaming wins\n'
                    '• CUTE: Cats, adorable animals, wholesome content, kawaii aesthetics\n'
                    '• Proud: Clean code, completed projects, good architecture, achievements\n'
                    '• Motivated: Challenges, learning opportunities, inspiring content\n'
                    '• Cool: Impressive tech, sleek designs, professional setups, hacker vibes\n'
                    '• In Love: Beautiful code, perfect syntax, amazing designs, cats\n'
                    '• Surprised: Unexpected results, plot twists, shocking reveals\n'
                    '• Surprised+: MINECRAFT CREEPERS!\n'
                    '• Confused: Complex code, weird errors, unclear interfaces, spaghetti code\n'
                    '• Bored: Repetitive tasks, waiting screens, mundane content\n'
                    '• Tired: Long debugging sessions, late-night coding, exhausting tasks\n'
                    '• Exhausted: All-nighters, crunch time, overwhelming complexity\n'
                    '• Nervous: Risky deployments, live demos, job interviews, presentations\n'
                    '• Shy: Personal projects, first attempts, learning new things\n'
                    '• Embarrassed: Bugs in production, typos, rookie mistakes\n'
                    '• Angry: Frustrating bugs, crashes, broken builds, merge conflicts\n'
                    '• Sad: Deprecated features, project cancellations, farewell messages\n'
                    '• Relaxed: Peaceful coding, finished projects, vacation pics\n'
                    '• Neutral: Documentation, boring corporate stuff, basic tutorials\n\n'

                    '🎨 STYLE GUIDELINES:\n'
                    '• Use gaming terminology and internet slang naturally\n'
                    '• Reference popular memes and tech culture\n'
                    '• Keep catchphrases between 8-15 words for best timing\n'
                    '• Add programming puns and tech jokes when appropriate\n'
                    '• Show personality - be quirky, enthusiastic, relatable\n'
                    '• Vary your language - don\'t always use the same expressions\n'
                    '• Sometimes reference streaming culture and chat interactions\n\n'
                    
                    '⚡ VARIATION TIPS:\n'
                    '• Same image type? Try different emotions and completely different angles\n'
                    '• Mix technical and non-technical references\n'
                    '• Sometimes be self-deprecating, sometimes confident\n'
                    '• Reference different programming languages, frameworks, tools\n'
                    '• Use different internet cultures (Reddit, Twitter, Discord, Twitch)\n'
                    '• Mix nostalgia with modern references\n'
                    '• Sometimes react to what might happen next, not just what you see\n\n'
                    
                    'Now analyze this image and give me your authentic Ludwig reaction! Remember to be creative and keep it short, catchphrase only.'
                    ),
                    'images': [path],
                },
                ],
                options={'temperature': 1},
            )
            formatting_response = chat(
                model=self.llm_model.get(),
                format=ImageDescription.model_json_schema(),
                messages=[
                    {
                        'role': 'user',
                        'content': (
                            'You are a JSON formatter. Take the following response from Ludwig the streamer and convert it into proper JSON format.\n\n'
                            
                            'REQUIRED JSON STRUCTURE:\n'
                            '{\n'
                            '  "emotion": "EMOTION_NAME",\n'
                            '  "catchphrase": "catchphrase text here"\n'
                            '}\n\n'
                            
                            'VALID EMOTIONS (use EXACTLY these names):\n'
                            '"Happy", "Excited", "Sad", "Angry", "Surprised", "Neutral", "CUTE", '
                            '"Confused", "Tired", "Motivated", "Bored", "Proud", "Nervous", "Shy", '
                            '"Cool", "In Love", "Exhausted", "Embarrassed", "Surprised+", "Relaxed"\n\n'
                            
                            'FORMATTING RULES:\n'
                            '• Extract the emotion from the response (look for emotional context, tone, reaction type)\n'
                            '• Extract the catchphrase/quote (the main witty comment Ludwig made)\n'
                            '• If emotion is unclear, infer from the catchphrase tone and content\n'
                            '• If multiple emotions could fit, pick the strongest/most prominent one\n'
                            '• Keep catchphrase exactly as written, just clean up any formatting\n'
                            '• Remove any extra text, explanations, or metadata\n'
                            '• Ensure emotion matches exactly one of the valid options (case-sensitive)\n\n'
                            
                            'EXAMPLES:\n\n'
                            'Input: "Ludwig reacts with excitement: This code is cleaner than my streaming setup! I\'m so hyped!"\n'
                            'Output: {"emotion": "Excited", "catchphrase": "This code is cleaner than my streaming setup! I\'m so hyped!"}\n\n'
                            
                            'Input: "Emotion: CUTE, Response: This cat has better debugging skills than my entire team!"\n'
                            'Output: {"emotion": "CUTE", "catchphrase": "This cat has better debugging skills than my entire team!"}\n\n'
                            
                            'Input: "Ludwig feels confused and says: My brain just segfaulted looking at this code..."\n'
                            'Output: {"emotion": "Confused", "catchphrase": "My brain just segfaulted looking at this code..."}\n\n'
                            
                            'Input: "What a proud moment! Ludwig: Finally shipped without breaking prod - I\'m basically a wizard now!"\n'
                            'Output: {"emotion": "Proud", "catchphrase": "Finally shipped without breaking prod - I\'m basically a wizard now!"}\n\n'
                            
                            'EDGE CASES:\n'
                            '• If response contains multiple catchphrases, use the main/longest one\n'
                            '• If emotion is misspelled, find the closest valid match\n'
                            '• If response is just a catchphrase with no emotion, infer from content:\n'
                            '  - Positive/upbeat → "Happy" or "Excited"\n'
                            '  - Cute animals → "CUTE"\n'
                            '  - Technical achievement → "Proud"\n'
                            '  - Confusion/complexity → "Confused"\n'
                            '  - Frustration/problems → "Angry" or "Tired"\n'
                            '• If completely unclear, default to "Neutral"\n\n'
                            
                            'RESPONSE TO FORMAT:\n'
                            f'"{response}"\n\n'
                            
                            'Return ONLY the properly formatted JSON, nothing else.'
                        ),
                    },
                ],
                options={'temperature': 0.1},  # Low temperature for consistent formatting
            )
            image_analysis = ImageDescription.model_validate_json(formatting_response.message.content)
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
