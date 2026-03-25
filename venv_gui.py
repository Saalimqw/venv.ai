"""
VENV AI GUI Interface with Glowing Ring TTS Visualization.
"""

import tkinter as tk
from tkinter import Canvas, scrolledtext, messagebox, ttk
import threading
import time
import math
import queue
import random
import os
import json
from datetime import datetime
import json
import subprocess

from system_monitor import get_system_status, format_system_status_speech
from voice import speak

# Fallback run_agent function in case agent.brain fails to import
def run_agent(user_message, history=None):
    """Fallback AI response function when agent.brain is not available."""
    try:
        # Try to import the real agent with API keys available
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        if os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY"):
            from agent.brain import run_agent as real_run_agent
            return real_run_agent(user_message, history)
    except ImportError:
        pass
    
    # Simple fallback responses
    responses = {
        "who is pm of india": "The current Prime Minister of India is Narendra Modi. He has held this position since May 2014.",
        "who is lalu yadav": "Lalu Prasad Yadav is an Indian politician and former Chief Minister of Bihar, leading the Rashtriya Janata Dal (RJD) party.",
        "hello": "Hello! I'm VENV AI, your personal assistant. How can I help you today?",
        "hi": "Hi there! I'm VENV AI. What can I do for you?",
    }
    
    user_lower = user_message.lower()
    for key, response in responses.items():
        if key in user_lower:
            return response, False
    
    return f"I understand you're asking about: '{user_message}'. However, I'm currently running in fallback mode. Please check your API configuration in config.py for full AI functionality.", False

# ── TTS ───────────────────────────────────────────────────────
import subprocess
import threading
import queue
import math
import time

# Global TTS control
_tts_queue = queue.Queue()
_speaking = False
_speak_lock = threading.Lock()
_stop_tts = False  # Global stop flag

def _tts_worker():
    global _speaking, _stop_tts
    current_process = None
    while True:
        # Check if stop flag is set - wait until it's cleared
        if _stop_tts:
            time.sleep(0.1)
            continue
        
        try:
            # Get text from queue with timeout
            text = _tts_queue.get(timeout=0.1)
        except queue.Empty:
            continue
        
        if text and not _stop_tts:
            _speaking = True
            safe = text.replace("'", "''").replace('"', '""')
            ps = (
                "Add-Type -AssemblyName System.Speech; "
                "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                "$s.Rate = 0; "
                f"$s.Speak('{safe}');"
            )
            try:
                current_process = subprocess.Popen(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Non-blocking wait with stop check
                while current_process.poll() is None:
                    if _stop_tts:
                        try:
                            current_process.kill()
                            current_process.wait()
                        except:
                            pass
                        break
                    time.sleep(0.1)
                
            except Exception as e:
                pass
            finally:
                current_process = None
                _speaking = False
                _stop_tts = False

threading.Thread(target=_tts_worker, daemon=True).start()

def speak_with_ring(text: str):
    print(f"TTS: Attempting to speak: {text[:50]}...")
    with _speak_lock:
        _tts_queue.put(text)  # Use queue.put() instead of append()
    print(f"TTS: Added to queue, queue size: {_tts_queue.qsize()}")

def is_speaking() -> bool:
    return _speaking

# ── SPARK ─────────────────────────────────────────────────────────────
class Spark:
    def __init__(self):
        a = random.uniform(0, 2 * math.pi)
        self.x = 300 + 150 * math.cos(a)
        self.y = 280 + 150 * math.sin(a)
        spd = random.uniform(1.5, 3.5)
        self.vx = math.cos(a) * spd * random.uniform(0.2, 0.8) + random.uniform(-1.5, 1.5)
        self.vy = -random.uniform(1.0, 3.5)
        self.life = random.uniform(0.4, 1.1)
        self.ml = self.life
        self.sz = random.uniform(2, 5)
        self.hue = random.choice(("c", "g"))

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.06
        self.life -= dt
        return self.life > 0

    def color(self):
        a = max(0.0, self.life / self.ml)
        iv = int(255 * a)
        if self.hue == "c":
            return f"#{0:02x}{iv:02x}{int(240*a):02x}"
        else:
            return f"#{0:02x}{iv:02x}{int(100*a):02x}"


class VENVGUInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("VENV AI - Visual Intelligence Hub")
        self.root.geometry("1400x900")
        self.root.configure(bg='#0a0a0a')
        
        # Enhanced color scheme - Modern dark theme
        self.bg_color = '#0d1117'
        self.panel_color = '#161b22'
        self.accent_color = '#58a6ff'
        self.accent_secondary = '#f778ba'
        self.success_color = '#3fb950'
        self.warning_color = '#d29922'
        self.text_color = '#c9d1d9'
        self.text_dim = '#8b949e'
        
        # Animation variables
        self.animation_time = 0
        self.sparks = []
        self.orbit_angle = 0.0
        self.speak_t = 0.0
        self.last_spoken = ""
        self.ct = 0.0
        self.prev = time.time()
        self.current_command = ""  # Store current command for response handling
        self.memory_file = "venv_memory.json"  # Memory file for persistence
        self.is_speaking = False  # Track if AI is speaking
        self.stop_requested = False  # Track if stop was requested
        
        # TODO list functionality
        self.todo_items = []
        self.todo_widgets = []
        
        # System update queue
        self.update_queue = queue.Queue()
        self.transcript_queue = queue.Queue()
        
        # AI conversation history
        self.history = []
        
        # Setup GUI - CREATE WIDGETS FIRST
        self.setup_styles()
        self.create_widgets()
        self.load_memory()  # Load memory AFTER widgets created
        self.start_system_monitoring()
        self.bind_events()
        self.start_animations()
        
    def setup_styles(self):
        """Setup custom styles for ttk widgets."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure styles
        style.configure('Dark.TFrame', background=self.panel_color)
        style.configure('Dark.TLabel', background=self.panel_color, foreground=self.text_color)
        style.configure('Accent.TLabel', background=self.panel_color, foreground=self.accent_color)
        style.configure('Success.TLabel', background=self.panel_color, foreground=self.success_color)
        style.configure('Warning.TLabel', background=self.panel_color, foreground=self.warning_color)
        style.configure('Dark.TButton', background=self.accent_color, foreground=self.text_color)
        style.map('Dark.TButton', background=[('active', '#00a8cc')])
        
    def create_widgets(self):
        """Create all GUI widgets."""
        # Main container with gradient background
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Enhanced system monitoring
        self.create_left_panel(main_frame)
        
        # Center panel - Glowing Ring VENV
        self.create_center_panel(main_frame)
        
        # Right panel - Enhanced transcription
        self.create_right_panel(main_frame)
        
    def create_left_panel(self, parent):
        """Create enhanced left monitoring panel."""
        left_frame = tk.Frame(parent, bg=self.panel_color, width=320)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        left_frame.pack_propagate(False)
        
        # Title with glow effect
        title_frame = tk.Frame(left_frame, bg=self.panel_color)
        title_frame.pack(pady=15)
        
        title = tk.Label(title_frame, text="⚡ SYSTEM STATUS", 
                        font=('Consolas', 16, 'bold'),
                        bg=self.panel_color, fg=self.accent_color)
        title.pack()
        
        # System status cards
        self.create_status_card(left_frame, "🔥 CPU", "cpu_label", "0%", "#ff4444")
        self.create_status_card(left_frame, "🎮 GPU", "gpu_label", "0°C", "#4444ff")
        self.create_status_card(left_frame, "💾 RAM", "memory_label", "0%", "#44ff44")
        self.create_status_card(left_frame, "💿 DISK", "disk_label", "0%", "#ff44ff")
        
        # Enhanced system active indicator
        self.create_system_indicator(left_frame)
        
    def create_status_card(self, parent, title_text, label_attr, initial_text, color):
        """Create an enhanced status card."""
        card_frame = tk.Frame(parent, bg='#252538', relief=tk.RAISED, bd=1)
        card_frame.pack(fill=tk.X, padx=15, pady=8)
        
        # Title
        title = tk.Label(card_frame, text=title_text,
                     font=('Consolas', 12, 'bold'),
                     bg='#252538', fg=self.text_color)
        title.pack(anchor='w', padx=10, pady=(8, 2))
        
        # Value with color
        value_label = tk.Label(card_frame, text=initial_text,
                           font=('Consolas', 14, 'bold'),
                           bg='#252538', fg=color)
        value_label.pack(anchor='w', padx=10, pady=(2, 8))
        
        # Store reference
        setattr(self, label_attr, value_label)
        
    def create_system_indicator(self, parent):
        """Create animated system active indicator."""
        indicator_frame = tk.Frame(parent, bg=self.panel_color)
        indicator_frame.pack(pady=20)
        
        # Canvas for animation
        self.system_canvas = Canvas(indicator_frame, width=120, height=120,
                                bg=self.panel_color, highlightthickness=0)
        self.system_canvas.pack()
        
        # Status label
        self.system_status_label = tk.Label(indicator_frame, 
                                       text="⚡ SYSTEM ONLINE",
                                       font=('Consolas', 12, 'bold'),
                                       bg=self.panel_color, fg=self.success_color)
        self.system_status_label.pack(pady=5)
        
        # Terminate button with enhanced styling
        self.terminate_btn = tk.Button(indicator_frame, 
                                  text="⚠ TERMINATE",
                                  font=('Consolas', 10, 'bold'),
                                  bg=self.warning_color, fg=self.text_color,
                                  relief=tk.RAISED, bd=2,
                                  command=self.terminate_system)
        self.terminate_btn.pack(pady=5)
        
    def create_center_panel(self, parent):
        """Create center panel with glowing ring VENV."""
        center_frame = tk.Frame(parent, bg=self.panel_color, width=600)
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        center_frame.pack_propagate(False)
        
        # VENV Title with glow
        title_frame = tk.Frame(center_frame, bg=self.panel_color)
        title_frame.pack(pady=15)
        
        title = tk.Label(title_frame, text="🤖 VENV AI", 
                        font=('Consolas', 28, 'bold'),
                        bg=self.panel_color, fg=self.accent_color)
        title.pack()
        
        # Glowing Ring Canvas
        self.venv_face_canvas = Canvas(center_frame, 
                                  width=600, height=500,  # Increased height from 450 to 500
                                  bg='#0f0f1e', 
                                  highlightthickness=3,
                                  highlightbackground=self.accent_color)
        self.venv_face_canvas.pack(pady=15)
        
    def create_right_panel(self, parent):
        """Create enhanced right transcription panel with functional TODO list."""
        right_frame = tk.Frame(parent, bg=self.panel_color, width=420)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        # Title with icon
        title_frame = tk.Frame(right_frame, bg=self.panel_color)
        title_frame.pack(pady=15)
        
        title = tk.Label(title_frame, text="📝 SYSTEM_TRANSCRIPTION", 
                        font=('Consolas', 16, 'bold'),
                        bg=self.panel_color, fg=self.accent_color)
        title.pack()
        
        # FUNCTIONAL TODO LIST SECTION
        todo_frame = tk.Frame(right_frame, bg='#252538', relief=tk.RAISED, bd=2)
        todo_frame.pack(pady=10, padx=15, fill=tk.X)
        
        todo_title = tk.Label(todo_frame, text="📋 VENV AI TODO LIST", 
                            font=('Consolas', 12, 'bold'),
                            bg='#252538', fg=self.accent_color)
        todo_title.pack(pady=(8, 4))
        
        # Add new todo input
        input_frame = tk.Frame(todo_frame, bg='#252538')
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.todo_entry = tk.Entry(input_frame, 
                                  font=('Consolas', 10),
                                  bg='#0a0a0a', fg=self.accent_color,
                                  insertbackground=self.accent_color)
        self.todo_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        add_btn = tk.Button(input_frame, text="Add", 
                           font=('Consolas', 9, 'bold'),
                           bg=self.success_color, fg=self.text_color,
                           command=self.add_todo_item)
        add_btn.pack(side=tk.RIGHT)
        
        # Todo items container
        self.todo_container = tk.Frame(todo_frame, bg='#252538')
        self.todo_container.pack(fill=tk.X, padx=10, pady=5)
        
        # Create todo widgets
        self.create_todo_widgets()
        
        # Enhanced transcription area
        transcript_container = tk.Frame(right_frame, bg='#252538', relief=tk.SUNKEN, bd=2)
        transcript_container.pack(pady=10, padx=15, fill=tk.BOTH, expand=True)
        
        self.transcript_area = scrolledtext.ScrolledText(transcript_container, 
                                                        width=48, height=22,
                                                        font=('Consolas', 10),
                                                        bg='#0a0a0a', fg=self.text_color,
                                                        insertbackground=self.accent_color,
                                                        relief=tk.FLAT)
        self.transcript_area.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        # Command input with enhanced styling and Enter button
        command_frame = tk.Frame(right_frame, bg=self.panel_color)
        command_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(command_frame, text="💬 TYPE_COMMAND_HERE...", 
                font=('Consolas', 11, 'bold'),
                bg=self.panel_color, fg=self.text_color).pack(anchor='w')
        
        input_container = tk.Frame(command_frame, bg='#252538', relief=tk.RAISED, bd=2)
        input_container.pack(fill=tk.X, pady=5)
        
        # Input field and button container
        field_container = tk.Frame(input_container, bg='#252538')
        field_container.pack(fill=tk.X, padx=5, pady=5)
        
        self.command_entry = tk.Entry(field_container, 
                                     font=('Consolas', 11, 'bold'),
                                     bg='#0a0a0a', fg=self.accent_color,
                                     insertbackground=self.accent_color,
                                     relief=tk.FLAT)
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Enter button
        enter_btn = tk.Button(field_container, text="↵ ENTER", 
                          font=('Consolas', 10, 'bold'),
                          bg=self.success_color, fg=self.text_color,
                          command=self.process_command)
        enter_btn.pack(side=tk.RIGHT)
        
        # Voice toggle, stop button, and save button
        toggle_frame = tk.Frame(command_frame, bg=self.panel_color)
        toggle_frame.pack(anchor='w', pady=5)
        
        self.voice_enabled = tk.BooleanVar(value=True)
        voice_check = tk.Checkbutton(toggle_frame, text="🔊 Voice Output Enabled",
                                  variable=self.voice_enabled,
                                  font=('Consolas', 10, 'bold'),
                                  bg=self.panel_color, fg=self.text_color,
                                  selectcolor=self.accent_color)
        voice_check.pack(side=tk.LEFT, padx=(0, 10))
        
        # Stop AI button
        stop_btn = tk.Button(toggle_frame, text="⏹ STOP AI", 
                           font=('Consolas', 9, 'bold'),
                           bg='#ff4444', fg='white',
                           command=self.stop_ai)
        stop_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Save memory button - remove auto-save
        save_btn = tk.Button(toggle_frame, text="💾 Save Memory", 
                           font=('Consolas', 9, 'bold'),
                           bg=self.warning_color, fg=self.text_color,
                           command=self.manual_save_memory)
        save_btn.pack(side=tk.LEFT)
        
        # Bind Enter key for todo entry
        self.todo_entry.bind('<Return>', lambda e: self.add_todo_item())
        
    def create_todo_widgets(self):
        """Create interactive todo widgets."""
        # Clear existing widgets
        for widget in self.todo_widgets:
            widget.destroy()
        self.todo_widgets.clear()
        
        # Create todo item widgets
        for i, item in enumerate(self.todo_items):
            item_frame = tk.Frame(self.todo_container, bg='#252538')
            item_frame.pack(fill=tk.X, pady=2)
            
            # Checkbox
            var = tk.BooleanVar(value=item['completed'])
            checkbox = tk.Checkbutton(item_frame, 
                                    variable=var,
                                    font=('Consolas', 10),
                                    bg='#252538', fg=self.text_color,
                                    selectcolor='#252538',
                                    activebackground='#252538',
                                    command=lambda idx=i, v=var: self.toggle_todo(idx, v))
            checkbox.pack(side=tk.LEFT)
            
            # Todo text
            status = "✅" if item['completed'] else "⏳"
            todo_text = f"{status} {item['text']}"
            
            text_label = tk.Label(item_frame, text=todo_text,
                                font=('Consolas', 10),
                                bg='#252538', fg=self.text_color,
                                anchor='w')
            text_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            # Delete button
            del_btn = tk.Button(item_frame, text="✕",
                              font=('Consolas', 8, 'bold'),
                              bg=self.warning_color, fg=self.text_color,
                              command=lambda idx=i: self.delete_todo_item(idx))
            del_btn.pack(side=tk.RIGHT, padx=2)
            
            self.todo_widgets.append(item_frame)
    
    def add_todo_item(self):
        """Add a new todo item with optimized performance."""
        text = self.todo_entry.get().strip()
        if text:
            self.todo_items.append({"text": text, "completed": False})
            self.todo_entry.delete(0, tk.END)
            # Delayed widget creation to prevent lag
            self.root.after(50, self.create_todo_widgets)
            self.root.after(100, lambda: self.add_transcript(f"TODO: Added '{text}' to list"))
    
    def toggle_todo(self, index, var):
        """Toggle todo item completion status with optimized performance."""
        if 0 <= index < len(self.todo_items):
            self.todo_items[index]['completed'] = var.get()
            # Delayed widget creation to prevent lag
            self.root.after(50, self.create_todo_widgets)
            status = "completed" if var.get() else "uncompleted"
            self.root.after(100, lambda: self.add_transcript(f"TODO: {self.todo_items[index]['text']} marked as {status}"))
    
    def delete_todo_item(self, index):
        """Delete a todo item with optimized performance."""
        if 0 <= index < len(self.todo_items):
            deleted_text = self.todo_items[index]['text']
            del self.todo_items[index]
            # Delayed widget creation to prevent lag
            self.root.after(50, self.create_todo_widgets)
            self.root.after(100, lambda: self.add_transcript(f"TODO: Deleted '{deleted_text}' from list"))
    
    def stop_ai(self):
        """Stop AI from speaking immediately."""
        global _stop_tts
        _stop_tts = True
        self.stop_requested = True
        self.is_speaking = False
        
        # Clear TTS queue
        try:
            while not _tts_queue.empty():
                _tts_queue.get_nowait()
        except:
            pass
        
        self.add_transcript("🛑 AI STOPPED")
        
        # Reset immediately after clearing
        def reset():
            global _stop_tts
            _stop_tts = False
            self.stop_requested = False
        
        self.root.after(500, reset)  # 0.5 seconds - faster recovery
    
    def terminate_system(self):
        """Terminate the application."""
        if messagebox.askyesno("Terminate", "Are you sure you want to terminate VENV AI?"):
            self.root.quit()
    
    def manual_save_memory(self):
        """Manually save conversation history and TODO list to file."""
        try:
            # Create data to save
            data = {
                "history": self.history[-100:],
                "todo_items": self.todo_items,
                "saved_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Write to file
            filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv_memory.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.add_transcript(f"✅ Memory saved: {len(data['history'])} conversations, {len(data['todo_items'])} todos")
            
        except Exception as e:
            self.add_transcript(f"❌ Save failed: {e}")
    
    def save_memory(self):
        """Disabled auto-save function."""
        pass  # Do nothing - prevent auto-save
    
    def load_memory(self):
        """Load conversation history and TODO list from file."""
        try:
            filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv_memory.json")
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.history = data.get("history", [])
                    self.todo_items = data.get("todo_items", [])
                    self.add_transcript(f" Memory loaded: {len(self.history)} conversations, {len(self.todo_items)} todos")
                    # Display loaded todos immediately
                    self.create_todo_widgets()
            else:
                self.history = []
                self.todo_items = []
        except Exception as e:
            self.add_transcript(f" Could not load memory: {e}")
            self.history = []
            self.todo_items = []
        
    def bind_events(self):
        """Bind keyboard events and shortcuts."""
        # Bind Enter key for command entry
        self.command_entry.bind('<Return>', lambda e: self.process_command())
        
        # Bind F1 for system status
        self.root.bind('<F1>', lambda e: self.speak_system_status())
        
        # Bind Escape to terminate
        self.root.bind('<Escape>', lambda e: self.terminate_system())
    
    def add_transcript(self, message):
        """Add message to transcript area with auto-scroll."""
        timestamp = time.strftime("%H:%M:%S")
        self.transcript_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.transcript_area.see(tk.END)
        self.transcript_area.update_idletasks()
    
    def process_command(self):
        """Process user command with ultra-optimized performance."""
        command = self.command_entry.get().strip()
        if not command:
            return
        
        # Store current command for response handling
        self.current_command = command
        
        self.command_entry.delete(0, tk.END)
        self.add_transcript(f"USER: {command}")
        
        # Add to history immediately for context
        self.history.append({"role": "user", "content": f"User: {command}"})
        
        # Ultra-fast command processing - no delay
        def run_command_async():
            try:
                response = run_agent(command, self.history)
                self.root.after(0, lambda: self.handle_ai_response(response))  # No delay
            except Exception as e:
                error_msg = f"ERROR: {str(e)}"
                self.root.after(0, lambda: self.add_transcript(error_msg))
                self.history.append({"role": "assistant", "content": f"VENV: {error_msg}"})
        
        threading.Thread(target=run_command_async, daemon=True).start()
    
    def handle_ai_response(self, response):
        """Handle AI response with ultra-optimized performance."""
        # Handle tuple response (response, streamed) format
        if isinstance(response, tuple):
            response_text = response[0]  # Get actual response text
        else:
            response_text = response
        
        self.add_transcript(f"VENV: {response_text}")
        
        # Add to history immediately for context retention
        self.history.append({"role": "assistant", "content": f"VENV: {response_text}"})
        
        # Ultra-minimal TTS with immediate processing
        if self.voice_enabled.get() and not self.stop_requested:
            self.is_speaking = True
            self.last_spoken = response_text
            speak_with_ring(response_text)
            self.is_speaking = False
            self.stop_requested = False
    
    def draw_glowing_ring(self):
        """Draw optimized glowing ring TTS visualization."""
        # Constants for ring with proper sizing
        W, H = 600, 500
        CX, CY = 300, 250  # Centered properly
        BASE_R = 120  # Reduced to fit ring within canvas
        FPS = 10  # Further reduced from 30 to 10 for maximum performance
        
        # Colors
        BG = "#04060a"
        CYAN_IDLE = "#007a76"
        CYAN_SPEAK = "#00fff0"
        GREEN = "#00ff66"
        WHITE = "#d2ebe8"
        GRAY = "#3a5060"
        DIM_DOT = "#003a3a"
        
        now = time.time()
        dt = min(now - self.prev, 0.05)
        self.prev = now
        
        self.ct += dt
        if self.ct >= 0.5:
            self.ct = 0.0
        
        talking = is_speaking()
        
        if talking:
            self.speak_t += dt
            self.orbit_angle += dt * 1.5  # Reduced from 2.8 to 1.5
            # Reduced spark generation from 6 to 2
            for _ in range(2):
                self.sparks.append(Spark())
        self.sparks = [s for s in self.sparks if s.update(dt)]
        
        # Clear canvas
        self.venv_face_canvas.delete("all")
        
        # Simplified depth halos - reduced from 8 to 4
        for i in range(4):
            rr = BASE_R + 20 + i * 25  # Reduced spacing
            self.venv_face_canvas.create_oval(CX-rr, CY-rr, CX+rr, CY+rr,
                                        outline="#07111a", width=16, stipple="gray25")
        
        # Sparks - limited to max 10 for performance
        for s in self.sparks[:10]:
            c = s.color()
            r = max(1, int(s.sz * (s.life / s.ml)))
            x, y = int(s.x), int(s.y)
            self.venv_face_canvas.create_oval(x-r, y-r, x+r, y+r, fill=c, outline="")
        
        # Simplified orbiting dots
        for i in range(3):
            ang = self.orbit_angle + i * (2 * math.pi / 3)
            ox = int(CX + (BASE_R + 15) * math.cos(ang))
            oy = int(CY + (BASE_R + 15) * math.sin(ang))
            if talking:
                self.venv_face_canvas.create_oval(ox-6, oy-6, ox+6, oy+6,
                                            outline=GREEN, width=1, stipple="gray25")
                self.venv_face_canvas.create_oval(ox-3, oy-3, ox+3, oy+3,
                                            fill=GREEN, outline="")
            else:
                self.venv_face_canvas.create_oval(ox-2, oy-2, ox+2, oy+2,
                                            fill=DIM_DOT, outline="")
        
        # Optimized main ring - reduced layers from 16 to 8
        if talking:
            pulse = math.sin(self.speak_t * 5.0)  # Reduced from 7.0 to 5.0
            ring_r = int(BASE_R + 15 * pulse)  # Reduced from 20 to 15
            ring_w = 6  # Reduced from 8 to 6
            color = CYAN_SPEAK
        else:
            ring_r = BASE_R
            ring_w = 2  # Reduced from 3 to 2
            color = CYAN_IDLE
        
        # Simplified ring drawing - reduced layers
        for i in range(8, 0, -1):  # Reduced from 16 to 8
            rr = ring_r + i * 4  # Reduced from 6 to 4
            ww = ring_w + i  # Reduced from 2 to 1
            stipples = ["gray12","gray25","gray50","gray75"]
            st = stipples[min(i//2, len(stipples)-1)]
            self.venv_face_canvas.create_oval(CX-rr, CY-rr, CX+rr, CY+rr,
                                        outline=color, width=ww, stipple=st)
        
        # Minimal text rendering
        if self.last_spoken:
            words = self.last_spoken.split()
            lines, cur = [], ""  # Fixed: lines should be a list, not string
            for word in words:
                test = (cur + " " + word).strip()
                if len(test) <= 25:  # Reduced from 30 to 25
                    cur = test
                else:
                    lines.append(cur); cur = word
            if cur:
                lines.append(cur)
            lh = 26  # Increased from 24 to 26
            sy = CY - (len(lines) * lh) // 2
            tc = CYAN_SPEAK if talking else "#005a56"
            for i, ln in enumerate(lines):
                self.venv_face_canvas.create_text(CX, sy + i*lh, text=ln,
                                            fill=tc, font=('Consolas', 14, 'bold'))  # Increased font
        
        # Schedule next frame
        self.root.after(int(1000 / FPS), self.draw_glowing_ring)
        
    def draw_system_indicator(self):
        """Draw animated system active indicator."""
        self.system_canvas.delete("all")
        cx, cy = 60, 60
        radius = 45
        
        # Animated outer ring with glow effect
        for i in range(3):
            r = radius + i * 3
            self.system_canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                                         outline=self.success_color, width=2)
        
        # Pulsing inner circle
        pulse = abs(math.sin(self.animation_time * 0.05))
        pulse_size = radius * (0.6 + 0.4 * pulse)
        
        self.system_canvas.create_oval(cx-pulse_size, cy-pulse_size,
                                    cx+pulse_size, cy+pulse_size,
                                    fill=self.accent_color, outline='')
        
        # Rotating arc
        arc_angle = (self.animation_time * 2) % 360
        self.system_canvas.create_arc(cx-30, cy-30, cx+30, cy+30,
                                       start=arc_angle, extent=90,
                                       outline=self.accent_secondary, 
                                       width=3, style='arc')
        
        # Center core
        self.system_canvas.create_oval(cx-8, cy-8, cx+8, cy+8,
                                    fill=self.text_color, outline='')
        
    def start_animations(self):
        """Start minimal animations for zero lag."""
        def animate():
            self.animation_time += 1
            # Update only every 2 seconds (0.5 FPS) for zero lag
            if self.animation_time % 2 == 0:
                self.draw_system_indicator()
                self.draw_glowing_ring()
            self.root.after(2000, animate)  # 2 seconds - ultra slow for lowest spec PCs
        
        animate()
        
        # System monitoring - update every 60 seconds
        def update_system():
            self.update_system_display()
            self.root.after(60000, update_system)  # 60 seconds
        
        update_system()
        
    def start_system_monitoring(self):
        """Start optimized system monitoring thread."""
        def monitor_system():
            while True:
                try:
                    status = get_system_status()
                    self.update_queue.put(status)
                    time.sleep(3)  # Reduced from 2 to 3 seconds for less frequent updates
                except Exception as e:
                    print(f"System monitoring error: {e}")
                    time.sleep(5)
        
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
        
        # Start GUI update loop with reduced frequency
        self.update_system_display()
        
    def update_system_display(self):
        """Update system display from queue with optimized timing."""
        try:
            while not self.update_queue.empty():
                status = self.update_queue.get_nowait()
                self.update_system_labels(status)
        except queue.Empty:
            pass
        
        # Schedule next update with reduced frequency
        self.root.after(1000, self.update_system_display)  # Reduced from 500ms to 1000ms
        
    def update_system_labels(self, status):
        """Update system status labels with colors and formatting."""
        # CPU with color coding
        if "cpu" in status and "usage_percent" in status["cpu"]:
            cpu_usage = status["cpu"]["usage_percent"]
            cpu_temp = status["cpu"].get("temperature_celsius")
            
            # Color based on usage
            if cpu_usage < 50:
                cpu_color = "#44ff44"  # Green
            elif cpu_usage < 80:
                cpu_color = "#ffaa44"  # Yellow
            else:
                cpu_color = "#ff4444"  # Red
                
            temp_text = f" ({cpu_temp}°C)" if cpu_temp else ""
            self.cpu_label.config(text=f"{cpu_usage:.0f}%{temp_text}", fg=cpu_color)
        
        # GPU with color coding
        if "gpu" in status:
            if status["gpu"].get("usage_percent") is not None:
                gpu_usage = status["gpu"]["usage_percent"]
                gpu_temp = status["gpu"].get("temperature_celsius")
                gpu_name = status["gpu"].get("name", "Unknown")
                
                # Color based on usage
                if gpu_usage < 30:
                    gpu_color = "#4444ff"  # Blue
                elif gpu_usage < 60:
                    gpu_color = "#ffaa44"  # Yellow
                else:
                    gpu_color = "#ff4444"  # Red
                    
                temp_text = f" ({gpu_temp}°C)" if gpu_temp else ""
                usage_text = f" ({gpu_usage}%)" if gpu_usage else ""
                self.gpu_label.config(text=f"{gpu_temp or gpu_usage or gpu_name}{temp_text}{usage_text}", fg=gpu_color)
            else:
                self.gpu_label.config(text="N/A", fg="#666666")
        
        # Memory with color coding
        if "memory" in status and "usage_percent" in status["memory"]:
            mem_usage = status["memory"]["usage_percent"]
            mem_available = status["memory"]["available_gb"]
            
            # Color based on usage
            if mem_usage < 70:
                mem_color = "#44ff44"  # Green
            elif mem_usage < 85:
                mem_color = "#ffaa44"  # Yellow
            else:
                mem_color = "#ff4444"  # Red
                
            self.memory_label.config(text=f"{mem_usage:.0f}% ({mem_available:.1f}GB free)", fg=mem_color)
        
        # Disk with color coding
        if "disk" in status and "usage_percent" in status["disk"]:
            disk_usage = status["disk"]["usage_percent"]
            disk_free = status["disk"]["free_gb"]
            
            # Color based on usage
            if disk_usage < 80:
                disk_color = "#44ff44"  # Green
            elif disk_usage < 90:
                disk_color = "#ffaa44"  # Yellow
            else:
                disk_color = "#ff4444"  # Red
                
            self.disk_label.config(text=f"{disk_usage:.0f}% ({disk_free:.0f}GB free)", fg=disk_color)
            
    def start_system_monitoring(self):
        """Start ultra-optimized system monitoring thread."""
        def monitor_system():
            while True:
                try:
                    status = get_system_status()
                    self.update_queue.put(status)
                    time.sleep(10)  # Further increased from 3 to 10 seconds for zero lag
                except Exception as e:
                    print(f"System monitoring error: {e}")
                    time.sleep(15)
        
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
        
        # Start GUI update loop with reduced frequency
        self.update_system_display()

    def update_system_display(self):
        """Update system display from queue with optimized timing."""
        try:
            while not self.update_queue.empty():
                status = self.update_queue.get_nowait()
                self.update_system_labels(status)
        except queue.Empty:
            pass
        
        # Schedule next update with reduced frequency
        self.root.after(1000, self.update_system_display)  # Reduced from 500ms to 1000ms

def update_system_labels(self, status):
    """Update system status labels with colors and formatting."""
    # CPU with color coding
    if "cpu" in status and "usage_percent" in status["cpu"]:
        cpu_usage = status["cpu"]["usage_percent"]
        cpu_temp = status["cpu"].get("temperature_celsius")
        
        # Add response to transcript
        self.add_transcript(f"[{timestamp}] VENV: {response}")
        
        # Speak with glowing ring effect if enabled
        if self.voice_enabled.get():
            self.last_spoken = response
            speak_with_ring(response)
        
        # Update history
        self.history.append({"role": "user", "content": command})
        self.history.append({"role": "assistant", "content": response})
        if len(self.history) > 10:
            self.history = self.history[-10:]
            
    def add_transcript(self, text):
        """Add text to transcript area."""
        self.transcript_area.insert(tk.END, text + "\n")
        self.transcript_area.see(tk.END)
        
    def speak_system_status(self):
        """Speak current system status."""
        status = get_system_status()
        speech = format_system_status_speech(status)
        self.last_spoken = speech
        if self.voice_enabled.get():
            speak_with_ring(speech)
        self.add_transcript(f"SYSTEM STATUS: {speech}")
        
    def terminate_system(self):
        """Terminate the application."""
        if messagebox.askyesno("Terminate", "Are you sure you want to terminate VENV AI?"):
            self.root.quit()


def main():
    """Main function to run VENV GUI."""
    root = tk.Tk()
    app = VENVGUInterface(root)
    
    # Welcome message
    app.add_transcript("VENV AI System Initialized")
    app.add_transcript("Press F1 for system status report")
    app.add_transcript("Type commands in the input field below")
    
    root.mainloop()


if __name__ == "__main__":
    main()
