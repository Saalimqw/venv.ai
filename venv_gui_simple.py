"""
VENV AI - Optimized GUI for zero lag on lowest spec PCs.
Minimal, clean, functional design.
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import time
import os
import json
import subprocess
import queue

# Simple TTS System
_tts_queue = queue.Queue()
_speaking = False
_stop_tts = False

def _tts_worker():
    global _speaking, _stop_tts
    while True:
        try:
            text = _tts_queue.get(timeout=0.5)
        except queue.Empty:
            continue
        
        if text and not _stop_tts:
            _speaking = True
            try:
                safe = text.replace("'", "''").replace('"', '""')
                ps = f"Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Speak('{safe}');"
                proc = subprocess.Popen(
                    ["powershell", "-NoProfile", "-Command", ps],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                while proc.poll() is None:
                    if _stop_tts:
                        proc.kill()
                        break
                    time.sleep(0.1)
            except:
                pass
            _speaking = False
            _stop_tts = False

threading.Thread(target=_tts_worker, daemon=True).start()

def speak_text(text):
    if text:
        _tts_queue.put(text)

def stop_speaking():
    global _stop_tts
    _stop_tts = True
    with _tts_queue.mutex:
        _tts_queue.queue.clear()

# Simple AI
from agent.brain import run_agent

class VENVGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("VENV AI")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1a1a2e')
        
        # Colors
        self.bg = '#1a1a2e'
        self.fg = '#00d4ff'
        self.panel = '#252538'
        
        # Data
        self.history = []
        self.todos = []
        self.memory_file = os.path.join(os.path.dirname(__file__), "memory.json")
        
        # Create UI
        self.create_ui()
        
        # Load memory
        self.load_memory()
    
    def create_ui(self):
        # Main frame
        main = tk.Frame(self.root, bg=self.bg)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - System info
        left = tk.Frame(main, bg=self.panel, width=250)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left.pack_propagate(False)
        
        tk.Label(left, text="⚡ SYSTEM", font=('Consolas', 14, 'bold'), 
                bg=self.panel, fg=self.fg).pack(pady=10)
        
        self.cpu_label = tk.Label(left, text="CPU: --", font=('Consolas', 12),
                                  bg=self.panel, fg='white')
        self.cpu_label.pack(pady=5)
        
        self.ram_label = tk.Label(left, text="RAM: --", font=('Consolas', 12),
                                  bg=self.panel, fg='white')
        self.ram_label.pack(pady=5)
        
        # Center panel - Chat
        center = tk.Frame(main, bg=self.panel)
        center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        tk.Label(center, text="🤖 VENV AI", font=('Consolas', 20, 'bold'),
                bg=self.panel, fg=self.fg).pack(pady=10)
        
        # Chat area
        self.chat = scrolledtext.ScrolledText(center, width=60, height=25,
                                              font=('Consolas', 11),
                                              bg='#0a0a0a', fg='white',
                                              insertbackground=self.fg)
        self.chat.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        # Input area
        input_frame = tk.Frame(center, bg=self.panel)
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.entry = tk.Entry(input_frame, font=('Consolas', 12),
                             bg='#0a0a0a', fg=self.fg,
                             insertbackground=self.fg)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.entry.bind('<Return>', lambda e: self.send())
        
        tk.Button(input_frame, text="SEND", font=('Consolas', 10, 'bold'),
                 bg=self.fg, fg='black', command=self.send).pack(side=tk.RIGHT)
        
        # Buttons
        btn_frame = tk.Frame(center, bg=self.panel)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.voice_var = tk.BooleanVar(value=True)
        tk.Checkbutton(btn_frame, text="🔊 Voice", variable=self.voice_var,
                      font=('Consolas', 10), bg=self.panel, fg='white',
                      selectcolor=self.fg).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="⏹ STOP", font=('Consolas', 10),
                 bg='#ff4444', fg='white', command=self.stop).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="💾 SAVE", font=('Consolas', 10),
                 bg='#44ff44', fg='black', command=self.save).pack(side=tk.LEFT, padx=5)
        
        # Right panel - TODOs
        right = tk.Frame(main, bg=self.panel, width=300)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right.pack_propagate(False)
        
        tk.Label(right, text="📋 TODO LIST", font=('Consolas', 14, 'bold'),
                bg=self.panel, fg=self.fg).pack(pady=10)
        
        # Todo input
        todo_input = tk.Frame(right, bg=self.panel)
        todo_input.pack(fill=tk.X, padx=10, pady=5)
        
        self.todo_entry = tk.Entry(todo_input, font=('Consolas', 10),
                                   bg='#0a0a0a', fg='white')
        self.todo_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.todo_entry.bind('<Return>', lambda e: self.add_todo())
        
        tk.Button(todo_input, text="Add", font=('Consolas', 9),
                 bg=self.fg, fg='black', command=self.add_todo).pack(side=tk.RIGHT, padx=5)
        
        # Todo list
        self.todo_frame = tk.Frame(right, bg=self.panel)
        self.todo_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.update_todo_display()
    
    def send(self):
        msg = self.entry.get().strip()
        if not msg:
            return
        
        self.entry.delete(0, tk.END)
        self.add_message(f"You: {msg}")
        self.history.append({"role": "user", "content": msg})
        
        # Get AI response in thread
        def get_response():
            try:
                response = run_agent(msg, self.history)
                if isinstance(response, tuple):
                    response = response[0]
                self.root.after(0, lambda: self.show_response(response))
            except Exception as e:
                self.root.after(0, lambda: self.show_response(f"Error: {e}"))
        
        threading.Thread(target=get_response, daemon=True).start()
    
    def show_response(self, text):
        self.add_message(f"AI: {text}")
        self.history.append({"role": "assistant", "content": text})
        if self.voice_var.get():
            speak_text(text)
    
    def add_message(self, msg):
        self.chat.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.chat.see(tk.END)
    
    def stop(self):
        stop_speaking()
        self.add_message("🛑 AI stopped")
    
    def save(self):
        try:
            data = {
                "history": self.history[-100:],
                "todos": self.todos,
                "saved": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            self.add_message(f"✅ Saved {len(data['history'])} messages")
        except Exception as e:
            self.add_message(f"❌ Save error: {e}")
    
    def load_memory(self):
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.history = data.get("history", [])
                    self.todos = data.get("todos", [])
                    self.add_message(f"📂 Loaded {len(self.history)} messages")
                    self.update_todo_display()
        except Exception as e:
            self.add_message(f"⚠️ Load error: {e}")
    
    def add_todo(self):
        text = self.todo_entry.get().strip()
        if text:
            self.todos.append({"text": text, "done": False})
            self.todo_entry.delete(0, tk.END)
            self.update_todo_display()
    
    def toggle_todo(self, idx):
        if 0 <= idx < len(self.todos):
            self.todos[idx]["done"] = not self.todos[idx]["done"]
            self.update_todo_display()
    
    def delete_todo(self, idx):
        if 0 <= idx < len(self.todos):
            del self.todos[idx]
            self.update_todo_display()
    
    def update_todo_display(self):
        for w in self.todo_frame.winfo_children():
            w.destroy()
        
        for i, todo in enumerate(self.todos):
            frame = tk.Frame(self.todo_frame, bg=self.panel)
            frame.pack(fill=tk.X, pady=2)
            
            var = tk.BooleanVar(value=todo["done"])
            chk = tk.Checkbutton(frame, variable=var,
                                command=lambda i=i: self.toggle_todo(i),
                                bg=self.panel, selectcolor=self.fg)
            chk.pack(side=tk.LEFT)
            
            lbl = tk.Label(frame, text=todo["text"],
                          font=('Consolas', 10),
                          bg=self.panel, fg='#888888' if todo["done"] else 'white')
            lbl.pack(side=tk.LEFT, padx=5)
            
            tk.Button(frame, text="×", font=('Consolas', 10),
                     bg='#ff4444', fg='white',
                     command=lambda i=i: self.delete_todo(i)).pack(side=tk.RIGHT)

if __name__ == "__main__":
    root = tk.Tk()
    app = VENVGUI(root)
    root.mainloop()
