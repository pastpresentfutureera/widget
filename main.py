"""
Desktop Widgets Pro for Windows 11
PERMANENT Desktop Widgets - Won't hide on Show Desktop!
All columns visible with scroll when resized
"""

import tkinter as tk
from tkinter import ttk
import calendar
from datetime import datetime, timedelta
import json
import os
import ctypes
from ctypes import wintypes
import sys
import winreg
import time

# ============== WINDOWS API FOR DESKTOP EMBEDDING ==============
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Window messages and constants
WM_SPAWN_WORKER = 0x052C
GWL_EXSTYLE = -20
GWL_STYLE = -16
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000
WS_CHILD = 0x40000000
GW_OWNER = 4

# Function prototypes
FindWindow = user32.FindWindowW
FindWindowEx = user32.FindWindowExW
SendMessageTimeout = user32.SendMessageTimeoutW
SetParent = user32.SetParent
GetParent = user32.GetParent
SetWindowLong = user32.SetWindowLongW
GetWindowLong = user32.GetWindowLongW
EnumWindows = user32.EnumWindows
GetClassName = user32.GetClassNameW
ShowWindow = user32.ShowWindow
SetWindowPos = user32.SetWindowPos

EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))

# ============== PATHS ==============
if getattr(sys, 'frozen', False):
    APP_PATH = sys.executable
else:
    APP_PATH = os.path.abspath(__file__)

DATA_FILE = os.path.join(os.path.expanduser("~"), "desktop_widgets_pro_data.json")
STARTUP_FOLDER = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
SHORTCUT_PATH = os.path.join(STARTUP_FOLDER, "DesktopWidgetsPro.bat")

# ============== COLOR THEMES ==============
THEMES = {
    "🌸 Pastel Pink": {
        "bg": "#FFF0F5", "header": "#FFB6C1", "accent": "#FF69B4",
        "text": "#4A4A4A", "text_light": "#666666", "button": "#FFC0CB",
        "entry": "#FFFFFF", "border": "#FFB6C1", "highlight": "#FFE4E9"
    },
    "🌊 Ocean Blue": {
        "bg": "#F0F8FF", "header": "#87CEEB", "accent": "#4169E1",
        "text": "#2F4F4F", "text_light": "#5F7F7F", "button": "#B0E0E6",
        "entry": "#FFFFFF", "border": "#87CEEB", "highlight": "#E0F0FF"
    },
    "🌿 Mint Green": {
        "bg": "#F0FFF0", "header": "#90EE90", "accent": "#32CD32",
        "text": "#2F4F4F", "text_light": "#5F7F7F", "button": "#98FB98",
        "entry": "#FFFFFF", "border": "#90EE90", "highlight": "#E0FFE0"
    },
    "🍇 Lavender": {
        "bg": "#F8F0FF", "header": "#DDA0DD", "accent": "#9370DB",
        "text": "#4A4A4A", "text_light": "#6A6A8A", "button": "#E6E6FA",
        "entry": "#FFFFFF", "border": "#DDA0DD", "highlight": "#F0E0FF"
    },
    "🌻 Sunny Yellow": {
        "bg": "#FFFEF0", "header": "#FFE57F", "accent": "#FFC107",
        "text": "#4A4A4A", "text_light": "#6A6A6A", "button": "#FFF59D",
        "entry": "#FFFFFF", "border": "#FFE57F", "highlight": "#FFFDE0"
    },
    "🍑 Peach": {
        "bg": "#FFF5EE", "header": "#FFDAB9", "accent": "#FF8C00",
        "text": "#4A4A4A", "text_light": "#6A6A6A", "button": "#FFE4B5",
        "entry": "#FFFFFF", "border": "#FFDAB9", "highlight": "#FFF0E0"
    },
    "🌺 Coral": {
        "bg": "#FFF0EE", "header": "#F08080", "accent": "#CD5C5C",
        "text": "#4A4A4A", "text_light": "#6A6A6A", "button": "#FFA07A",
        "entry": "#FFFFFF", "border": "#F08080", "highlight": "#FFE0E0"
    },
    "🐬 Aqua": {
        "bg": "#F0FFFF", "header": "#7FDBDB", "accent": "#20B2AA",
        "text": "#2F4F4F", "text_light": "#5F7F7F", "button": "#AFEEEE",
        "entry": "#FFFFFF", "border": "#7FDBDB", "highlight": "#E0FFFF"
    },
    "🌙 Night Mode": {
        "bg": "#2D2D3A", "header": "#3D3D5C", "accent": "#7B68EE",
        "text": "#E8E8E8", "text_light": "#B0B0B0", "button": "#4D4D6A",
        "entry": "#3A3A4A", "border": "#5D5D7A", "highlight": "#4A4A5A"
    },
    "☁️ Cloud White": {
        "bg": "#FAFAFA", "header": "#E8E8E8", "accent": "#607D8B",
        "text": "#424242", "text_light": "#757575", "button": "#EEEEEE",
        "entry": "#FFFFFF", "border": "#E0E0E0", "highlight": "#F5F5F5"
    }
}

FONTS = {
    "title": ("Segoe UI Semibold", 12),
    "header": ("Segoe UI Semibold", 11),
    "normal": ("Segoe UI", 11),
    "small": ("Segoe UI", 10),
    "tiny": ("Segoe UI", 9),
    "button": ("Segoe UI Semibold", 10),
    "icon": ("Segoe UI", 14),
    "clock": ("Segoe UI Light", 36),
    "clock_date": ("Segoe UI", 12),
}


# ============== DESKTOP INTEGRATION CLASS ==============
class DesktopLayer:
    """Manages embedding windows into the desktop layer"""
    
    _workerw = None
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Initialize the desktop layer - call once at startup"""
        if cls._initialized:
            return cls._workerw is not None
        
        cls._initialized = True
        
        try:
            # Find Progman (Program Manager)
            progman = FindWindow("Progman", None)
            if not progman:
                print("Could not find Progman")
                return False
            
            # Send message to spawn WorkerW behind desktop icons
            result = ctypes.c_ulong()
            SendMessageTimeout(
                progman,
                WM_SPAWN_WORKER,
                0, 0,
                0x0000,  # SMTO_NORMAL
                1000,
                ctypes.byref(result)
            )
            
            # Small delay to let Windows create the window
            time.sleep(0.1)
            
            # Find the WorkerW window
            workerw = None
            
            def enum_callback(hwnd, lparam):
                nonlocal workerw
                shell = FindWindowEx(hwnd, None, "SHELLDLL_DefView", None)
                if shell:
                    # Found SHELLDLL_DefView, get the WorkerW behind it
                    workerw = FindWindowEx(None, hwnd, "WorkerW", None)
                return True
            
            EnumWindows(EnumWindowsProc(enum_callback), 0)
            
            if workerw:
                cls._workerw = workerw
                print(f"Found WorkerW: {workerw}")
                return True
            else:
                # Fallback: use Progman directly
                cls._workerw = progman
                print(f"Using Progman as fallback: {progman}")
                return True
                
        except Exception as e:
            print(f"Desktop init error: {e}")
            return False
    
    @classmethod
    def embed_window(cls, hwnd):
        """Embed a window into the desktop layer"""
        if not cls._workerw:
            if not cls.initialize():
                return False
        
        try:
            # Set as child of WorkerW/Progman
            SetParent(hwnd, cls._workerw)
            
            # Remove from taskbar
            ex_style = GetWindowLong(hwnd, GWL_EXSTYLE)
            ex_style |= WS_EX_TOOLWINDOW
            ex_style &= ~WS_EX_APPWINDOW
            SetWindowLong(hwnd, GWL_EXSTYLE, ex_style)
            
            # Show the window
            ShowWindow(hwnd, 5)  # SW_SHOW
            
            return True
        except Exception as e:
            print(f"Embed error: {e}")
            return False


# ============== AUTOSTART FUNCTIONS ==============
def is_autostart_enabled():
    if os.path.exists(SHORTCUT_PATH):
        return True
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, "DesktopWidgetsPro")
        winreg.CloseKey(key)
        return True
    except:
        return False


def enable_autostart():
    try:
        with open(SHORTCUT_PATH, 'w') as f:
            f.write(f'@echo off\nstart "" "{APP_PATH}"\n')
    except:
        pass
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "DesktopWidgetsPro", 0, winreg.REG_SZ, f'"{APP_PATH}"')
        winreg.CloseKey(key)
    except:
        pass


def disable_autostart():
    try:
        if os.path.exists(SHORTCUT_PATH):
            os.remove(SHORTCUT_PATH)
    except:
        pass
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, "DesktopWidgetsPro")
        winreg.CloseKey(key)
    except:
        pass


# ============== SCROLLABLE FRAME WITH FIXED CONTENT ==============
class ScrollableFrame(tk.Frame):
    """Frame with scrollbars - content never shrinks"""
    
    def __init__(self, parent, bg="white"):
        super().__init__(parent, bg=bg)
        
        # Create canvas and scrollbars
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        
        self.v_scroll = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.h_scroll = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        
        # Layout
        self.v_scroll.pack(side="right", fill="y")
        self.h_scroll.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Inner frame for content
        self.inner = tk.Frame(self.canvas, bg=bg)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        
        # Bind events
        self.inner.bind("<Configure>", self._on_configure)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.inner.bind("<MouseWheel>", self._on_mousewheel)
    
    def _on_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def set_bg(self, bg):
        self.config(bg=bg)
        self.canvas.config(bg=bg)
        self.inner.config(bg=bg)


# ============== BASE WIDGET CLASS ==============
class BaseWidget:
    """Base widget class - embeds into desktop"""
    
    def __init__(self, master, title, widget_id, app, size=(380, 450), min_size=(280, 220)):
        self.app = app
        self.widget_id = widget_id
        self.min_w, self.min_h = min_size
        
        # Get theme
        widget_theme = app.data.get("widget_themes", {}).get(widget_id, app.data.get("theme", "🌊 Ocean Blue"))
        self.theme = THEMES.get(widget_theme, THEMES["🌊 Ocean Blue"])
        
        # Create window
        self.window = tk.Toplevel(master)
        self.window.title(title)
        self.window.overrideredirect(True)
        self.window.attributes('-alpha', 0.97)
        
        # Get saved position/size
        pos = app.data.get("widget_positions", {}).get(widget_id, {"x": 100, "y": 100})
        saved_size = app.data.get("widget_sizes", {}).get(widget_id, {"w": size[0], "h": size[1]})
        
        self.window.geometry(f"{saved_size['w']}x{saved_size['h']}+{pos['x']}+{pos['y']}")
        
        # Drag/resize state
        self.drag = {"x": 0, "y": 0, "active": False}
        self.resize = {"active": False}
        
        # Build UI
        self.border_frame = tk.Frame(self.window, bg=self.theme["border"], padx=2, pady=2)
        self.border_frame.pack(fill="both", expand=True)
        
        self.main_frame = tk.Frame(self.border_frame, bg=self.theme["bg"])
        self.main_frame.pack(fill="both", expand=True)
        
        self._create_header(title)
        
        self.content = tk.Frame(self.main_frame, bg=self.theme["bg"])
        self.content.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        
        self._create_resize_grip()
        
        # Embed to desktop after window is ready
        self.window.after(300, self._embed_to_desktop)
    
    def _embed_to_desktop(self):
        """Embed this widget into the desktop layer"""
        try:
            self.window.update_idletasks()
            hwnd = GetParent(self.window.winfo_id())
            if DesktopLayer.embed_window(hwnd):
                print(f"Embedded {self.widget_id} to desktop")
            else:
                print(f"Failed to embed {self.widget_id}")
        except Exception as e:
            print(f"Embed error for {self.widget_id}: {e}")
    
    def _create_header(self, title):
        self.header = tk.Frame(self.main_frame, bg=self.theme["header"], height=42)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)
        
        self.title_lbl = tk.Label(
            self.header, text=f"  {title}", bg=self.theme["header"],
            fg=self.theme["text"], font=FONTS["title"], anchor="w"
        )
        self.title_lbl.pack(side="left", fill="x", expand=True)
        
        # Control buttons
        ctrl = tk.Frame(self.header, bg=self.theme["header"])
        ctrl.pack(side="right", padx=5)
        
        for text, cmd in [("🎨", self._show_theme_menu), ("─", self._minimize), ("✕", self._hide)]:
            btn = tk.Label(ctrl, text=text, bg=self.theme["header"], fg=self.theme["text"],
                          font=FONTS["icon"], cursor="hand2")
            btn.pack(side="left", padx=4)
            if text == "🎨":
                btn.bind("<Button-1>", cmd)
            elif text == "─":
                btn.bind("<Button-1>", lambda e: self._minimize())
            else:
                btn.bind("<Button-1>", lambda e: self._hide())
        
        # Drag bindings
        for w in [self.header, self.title_lbl]:
            w.bind("<Button-1>", self._start_drag)
            w.bind("<B1-Motion>", self._do_drag)
            w.bind("<ButtonRelease-1>", self._stop_drag)
    
    def _show_theme_menu(self, event):
        menu = tk.Menu(self.window, tearoff=0, font=FONTS["normal"])
        for name in THEMES:
            menu.add_command(label=name, command=lambda n=name: self._set_theme(n))
        menu.post(event.x_root, event.y_root)
    
    def _set_theme(self, name):
        self.theme = THEMES[name]
        if "widget_themes" not in self.app.data:
            self.app.data["widget_themes"] = {}
        self.app.data["widget_themes"][self.widget_id] = name
        self.app.save_data()
        self.apply_theme()
    
    def _create_resize_grip(self):
        self.grip = tk.Label(self.main_frame, text="⋱", bg=self.theme["bg"],
                            fg=self.theme["accent"], font=("Segoe UI", 14), cursor="size_nw_se")
        self.grip.place(relx=1.0, rely=1.0, anchor="se")
        self.grip.bind("<Button-1>", self._start_resize)
        self.grip.bind("<B1-Motion>", self._do_resize)
        self.grip.bind("<ButtonRelease-1>", self._stop_resize)
    
    def _start_drag(self, e):
        self.drag = {"x": e.x_root - self.window.winfo_x(), "y": e.y_root - self.window.winfo_y(), "active": True}
    
    def _do_drag(self, e):
        if self.drag["active"]:
            self.window.geometry(f"+{e.x_root - self.drag['x']}+{e.y_root - self.drag['y']}")
    
    def _stop_drag(self, e):
        self.drag["active"] = False
        self._save_pos()
    
    def _start_resize(self, e):
        self.resize = {"x": e.x_root, "y": e.y_root, "w": self.window.winfo_width(),
                      "h": self.window.winfo_height(), "active": True}
    
    def _do_resize(self, e):
        if self.resize["active"]:
            nw = max(self.min_w, self.resize["w"] + e.x_root - self.resize["x"])
            nh = max(self.min_h, self.resize["h"] + e.y_root - self.resize["y"])
            self.window.geometry(f"{int(nw)}x{int(nh)}")
    
    def _stop_resize(self, e):
        self.resize["active"] = False
        self._save_size()
    
    def _save_pos(self):
        if "widget_positions" not in self.app.data:
            self.app.data["widget_positions"] = {}
        self.app.data["widget_positions"][self.widget_id] = {"x": self.window.winfo_x(), "y": self.window.winfo_y()}
        self.app.save_data()
    
    def _save_size(self):
        if "widget_sizes" not in self.app.data:
            self.app.data["widget_sizes"] = {}
        self.app.data["widget_sizes"][self.widget_id] = {"w": self.window.winfo_width(), "h": self.window.winfo_height()}
        self.app.save_data()
    
    def _minimize(self):
        self.window.withdraw()
        self.window.after(100, self.window.deiconify)
    
    def _hide(self):
        self.window.withdraw()
        if "hidden_widgets" not in self.app.data:
            self.app.data["hidden_widgets"] = []
        if self.widget_id not in self.app.data["hidden_widgets"]:
            self.app.data["hidden_widgets"].append(self.widget_id)
        self.app.save_data()
        self.app.update_panel()
    
    def show(self):
        self.window.deiconify()
        if "hidden_widgets" in self.app.data and self.widget_id in self.app.data["hidden_widgets"]:
            self.app.data["hidden_widgets"].remove(self.widget_id)
        self.app.save_data()
        self.window.after(200, self._embed_to_desktop)
    
    def apply_theme(self):
        t = self.theme
        self.border_frame.config(bg=t["border"])
        self.main_frame.config(bg=t["bg"])
        self.header.config(bg=t["header"])
        self.title_lbl.config(bg=t["header"], fg=t["text"])
        self.content.config(bg=t["bg"])
        self.grip.config(bg=t["bg"], fg=t["accent"])


# ============== CALENDAR WIDGET ==============
class CalendarWidget(BaseWidget):
    def __init__(self, master, app):
        super().__init__(master, "📅 Calendar", "calendar", app, (450, 500), (320, 300))
        self.current = datetime.now()
        self.build()
    
    def build(self):
        # Navigation
        nav = tk.Frame(self.content, bg=self.theme["bg"])
        nav.pack(fill="x", pady=5)
        
        self.prev_btn = tk.Button(nav, text="◀ Prev", command=self.prev_month,
                                  bg=self.theme["button"], fg=self.theme["text"],
                                  font=FONTS["button"], bd=0, padx=12, cursor="hand2")
        self.prev_btn.pack(side="left")
        
        self.month_lbl = tk.Label(nav, text="", bg=self.theme["bg"], fg=self.theme["text"], font=FONTS["header"])
        self.month_lbl.pack(side="left", fill="x", expand=True)
        
        self.today_btn = tk.Button(nav, text="Today", command=self.go_today,
                                   bg=self.theme["accent"], fg="white",
                                   font=FONTS["small"], bd=0, padx=10, cursor="hand2")
        self.today_btn.pack(side="right", padx=5)
        
        self.next_btn = tk.Button(nav, text="Next ▶", command=self.next_month,
                                  bg=self.theme["button"], fg=self.theme["text"],
                                  font=FONTS["button"], bd=0, padx=12, cursor="hand2")
        self.next_btn.pack(side="right")
        
        # Scrollable calendar grid
        self.scroll = ScrollableFrame(self.content, bg=self.theme["bg"])
        self.scroll.pack(fill="both", expand=True)
        
        self.grid_frame = self.scroll.inner
        self.render_calendar()
    
    def render_calendar(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        
        year, month = self.current.year, self.current.month
        self.month_lbl.config(text=f"{calendar.month_name[month]} {year}")
        
        # Day headers - FIXED WIDTH
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for c, d in enumerate(days):
            fg = "#E74C3C" if c >= 5 else self.theme["text"]
            lbl = tk.Label(self.grid_frame, text=d, bg=self.theme["header"], fg=fg,
                          font=FONTS["small"], width=9, height=1, relief="solid", bd=1)
            lbl.grid(row=0, column=c, sticky="nsew")
        
        # Calendar cells - FIXED SIZE
        cal = calendar.monthcalendar(year, month)
        today = datetime.now()
        events = self.app.data.get("calendar_events", {})
        
        for r, week in enumerate(cal):
            for c, day in enumerate(week):
                cell = tk.Frame(self.grid_frame, bg=self.theme["entry"], relief="solid", bd=1,
                               width=80, height=75)
                cell.grid(row=r+1, column=c, sticky="nsew")
                cell.grid_propagate(False)  # FIXED SIZE
                
                if day != 0:
                    key = f"{year}-{month:02d}-{day:02d}"
                    is_today = (year == today.year and month == today.month and day == today.day)
                    is_weekend = c >= 5
                    
                    bg = self.theme["accent"] if is_today else self.theme["entry"]
                    fg = "white" if is_today else ("#E74C3C" if is_weekend else self.theme["text"])
                    
                    # Date label
                    tk.Label(cell, text=str(day), bg=bg, fg=fg, font=FONTS["normal"]).pack(anchor="nw", padx=3, pady=1)
                    
                    # Event text
                    txt = tk.Text(cell, height=2, width=9, bg=self.theme["entry"],
                                 fg=self.theme["text_light"], font=FONTS["tiny"], bd=0, wrap="word")
                    txt.pack(fill="both", expand=True, padx=2, pady=1)
                    txt.insert("1.0", events.get(key, ""))
                    txt.bind("<KeyRelease>", lambda e, k=key, t=txt: self.save_event(k, t))
                else:
                    cell.config(bg=self.theme["bg"])
    
    def save_event(self, key, txt):
        if "calendar_events" not in self.app.data:
            self.app.data["calendar_events"] = {}
        text = txt.get("1.0", "end-1c").strip()
        if text:
            self.app.data["calendar_events"][key] = text
        elif key in self.app.data["calendar_events"]:
            del self.app.data["calendar_events"][key]
        self.app.save_data()
    
    def prev_month(self):
        self.current = self.current.replace(day=1) - timedelta(days=1)
        self.render_calendar()
    
    def next_month(self):
        self.current = self.current.replace(day=28) + timedelta(days=4)
        self.current = self.current.replace(day=1)
        self.render_calendar()
    
    def go_today(self):
        self.current = datetime.now()
        self.render_calendar()
    
    def apply_theme(self):
        super().apply_theme()
        t = self.theme
        self.prev_btn.config(bg=t["button"], fg=t["text"])
        self.next_btn.config(bg=t["button"], fg=t["text"])
        self.today_btn.config(bg=t["accent"])
        self.month_lbl.config(bg=t["bg"], fg=t["text"])
        self.scroll.set_bg(t["bg"])
        self.render_calendar()


# ============== TODO WIDGET ==============
class TodoWidget(BaseWidget):
    def __init__(self, master, app):
        super().__init__(master, "✅ To-Do List", "todo", app, (360, 480), (280, 280))
        self.build()
    
    def build(self):
        # Add task
        add_frame = tk.Frame(self.content, bg=self.theme["bg"])
        add_frame.pack(fill="x", pady=5)
        
        self.entry = tk.Entry(add_frame, bg=self.theme["entry"], fg=self.theme["text"],
                             font=FONTS["normal"], bd=2, relief="groove")
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.entry.insert(0, "New task...")
        self.entry.bind("<FocusIn>", lambda e: self.entry.delete(0, "end") if self.entry.get() == "New task..." else None)
        self.entry.bind("<Return>", self.add_task)
        
        self.priority = tk.StringVar(value="low")
        for sym, lvl in [("🔴", "high"), ("🟡", "medium"), ("🟢", "low")]:
            tk.Radiobutton(add_frame, text=sym, variable=self.priority, value=lvl,
                          bg=self.theme["bg"], font=("Segoe UI", 12),
                          indicatoron=False, selectcolor=self.theme["highlight"]).pack(side="left", padx=2)
        
        tk.Button(add_frame, text="➕", command=self.add_task, bg=self.theme["accent"],
                 fg="white", font=FONTS["button"], bd=0, padx=10, cursor="hand2").pack(side="right")
        
        # Filters
        filt = tk.Frame(self.content, bg=self.theme["bg"])
        filt.pack(fill="x", pady=5)
        
        self.filter = tk.StringVar(value="all")
        for txt, val in [("All", "all"), ("Active", "active"), ("Done", "done")]:
            tk.Radiobutton(filt, text=txt, variable=self.filter, value=val,
                          bg=self.theme["button"], fg=self.theme["text"], font=FONTS["small"],
                          indicatoron=False, selectcolor=self.theme["accent"],
                          command=self.load_tasks, padx=10, pady=3).pack(side="left", padx=2)
        
        tk.Button(filt, text="🗑️", command=self.clear_done, bg=self.theme["button"],
                 fg=self.theme["text"], font=FONTS["normal"], bd=0, padx=8, cursor="hand2").pack(side="right")
        
        # Task list
        self.scroll = ScrollableFrame(self.content, bg=self.theme["bg"])
        self.scroll.pack(fill="both", expand=True)
        
        self.task_frame = self.scroll.inner
        
        # Stats
        self.stats = tk.Label(self.content, text="", bg=self.theme["bg"],
                             fg=self.theme["text_light"], font=FONTS["small"])
        self.stats.pack(fill="x", pady=3)
        
        self.load_tasks()
    
    def load_tasks(self):
        for w in self.task_frame.winfo_children():
            w.destroy()
        
        tasks = self.app.data.get("todos", [])
        ftype = self.filter.get()
        
        order = {"high": 0, "medium": 1, "low": 2}
        sorted_tasks = sorted(tasks, key=lambda x: (x.get("done", False), order.get(x.get("priority", "low"), 3)))
        
        done = sum(1 for t in tasks if t.get("done"))
        
        for task in sorted_tasks:
            if ftype == "active" and task.get("done"):
                continue
            if ftype == "done" and not task.get("done"):
                continue
            idx = tasks.index(task)
            self._create_task_row(task, idx)
        
        self.stats.config(text=f"📊 {done}/{len(tasks)} completed")
    
    def _create_task_row(self, task, idx):
        row = tk.Frame(self.task_frame, bg=self.theme["entry"], pady=5)
        row.pack(fill="x", pady=2, padx=2)
        
        icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        tk.Label(row, text=icons.get(task.get("priority", "low"), "●"),
                bg=self.theme["entry"], font=("Segoe UI", 11)).pack(side="left", padx=3)
        
        var = tk.BooleanVar(value=task.get("done", False))
        tk.Checkbutton(row, variable=var, bg=self.theme["entry"],
                      command=lambda: self.toggle(idx, var.get())).pack(side="left")
        
        fg = self.theme["text_light"] if task.get("done") else self.theme["text"]
        font = ("Segoe UI", 10, "overstrike") if task.get("done") else FONTS["normal"]
        tk.Label(row, text=task.get("text", ""), bg=self.theme["entry"],
                fg=fg, font=font, anchor="w").pack(side="left", fill="x", expand=True, padx=5)
        
        del_btn = tk.Label(row, text="✕", bg=self.theme["entry"], fg="#E74C3C",
                          font=FONTS["normal"], cursor="hand2")
        del_btn.pack(side="right", padx=5)
        del_btn.bind("<Button-1>", lambda e: self.delete(idx))
    
    def add_task(self, e=None):
        text = self.entry.get().strip()
        if text and text != "New task...":
            if "todos" not in self.app.data:
                self.app.data["todos"] = []
            self.app.data["todos"].append({"text": text, "done": False, "priority": self.priority.get()})
            self.app.save_data()
            self.entry.delete(0, "end")
            self.load_tasks()
    
    def toggle(self, idx, done):
        if idx < len(self.app.data.get("todos", [])):
            self.app.data["todos"][idx]["done"] = done
            self.app.save_data()
            self.load_tasks()
    
    def delete(self, idx):
        if idx < len(self.app.data.get("todos", [])):
            del self.app.data["todos"][idx]
            self.app.save_data()
            self.load_tasks()
    
    def clear_done(self):
        self.app.data["todos"] = [t for t in self.app.data.get("todos", []) if not t.get("done")]
        self.app.save_data()
        self.load_tasks()
    
    def apply_theme(self):
        super().apply_theme()
        self.scroll.set_bg(self.theme["bg"])
        self.stats.config(bg=self.theme["bg"], fg=self.theme["text_light"])
        self.load_tasks()


# ============== DAY PLANNER ==============
class DayPlannerWidget(BaseWidget):
    def __init__(self, master, app):
        super().__init__(master, "📆 Day Planner", "day_planner", app, (360, 480), (280, 280))
        self.date = datetime.now().strftime("%Y-%m-%d")
        self.entries = {}
        self.build()
    
    def build(self):
        # Nav
        nav = tk.Frame(self.content, bg=self.theme["bg"])
        nav.pack(fill="x", pady=5)
        
        tk.Button(nav, text="◀", command=self.prev_day, bg=self.theme["button"],
                 fg=self.theme["text"], font=FONTS["button"], bd=0, padx=12, cursor="hand2").pack(side="left")
        
        self.date_lbl = tk.Label(nav, text="", bg=self.theme["bg"], fg=self.theme["text"], font=FONTS["header"])
        self.date_lbl.pack(side="left", fill="x", expand=True)
        
        tk.Button(nav, text="Today", command=self.go_today, bg=self.theme["accent"],
                 fg="white", font=FONTS["small"], bd=0, padx=10, cursor="hand2").pack(side="right", padx=5)
        tk.Button(nav, text="▶", command=self.next_day, bg=self.theme["button"],
                 fg=self.theme["text"], font=FONTS["button"], bd=0, padx=12, cursor="hand2").pack(side="right")
        
        # Time slots
        self.scroll = ScrollableFrame(self.content, bg=self.theme["bg"])
        self.scroll.pack(fill="both", expand=True)
        
        for h in range(5, 24):
            row = tk.Frame(self.scroll.inner, bg=self.theme["bg"])
            row.pack(fill="x", pady=2)
            
            lbl = tk.Label(row, text=f"{h:02d}:00", bg=self.theme["header"],
                          fg=self.theme["text"], font=FONTS["small"], width=6)
            lbl.pack(side="left", padx=(0, 3))
            
            entry = tk.Entry(row, bg=self.theme["entry"], fg=self.theme["text"],
                           font=FONTS["normal"], bd=2, relief="groove")
            entry.pack(side="left", fill="x", expand=True)
            entry.bind("<KeyRelease>", lambda e, hr=h: self.save_slot(hr))
            
            self.entries[h] = {"entry": entry, "label": lbl}
        
        self.load_data()
    
    def load_data(self):
        data = self.app.data.get("day_planner", {}).get(self.date, {})
        dt = datetime.strptime(self.date, "%Y-%m-%d")
        self.date_lbl.config(text=f"{dt.strftime('%A, %B %d')}")
        
        now_hour = datetime.now().hour
        is_today = self.date == datetime.now().strftime("%Y-%m-%d")
        
        for h, widgets in self.entries.items():
            widgets["entry"].delete(0, "end")
            if str(h) in data:
                widgets["entry"].insert(0, data[str(h)])
            
            bg = self.theme["accent"] if (h == now_hour and is_today) else self.theme["header"]
            fg = "white" if (h == now_hour and is_today) else self.theme["text"]
            widgets["label"].config(bg=bg, fg=fg)
    
    def save_slot(self, h):
        if "day_planner" not in self.app.data:
            self.app.data["day_planner"] = {}
        if self.date not in self.app.data["day_planner"]:
            self.app.data["day_planner"][self.date] = {}
        
        text = self.entries[h]["entry"].get()
        if text:
            self.app.data["day_planner"][self.date][str(h)] = text
        elif str(h) in self.app.data["day_planner"][self.date]:
            del self.app.data["day_planner"][self.date][str(h)]
        self.app.save_data()
    
    def prev_day(self):
        self.date = (datetime.strptime(self.date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        self.load_data()
    
    def next_day(self):
        self.date = (datetime.strptime(self.date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        self.load_data()
    
    def go_today(self):
        self.date = datetime.now().strftime("%Y-%m-%d")
        self.load_data()
    
    def apply_theme(self):
        super().apply_theme()
        self.scroll.set_bg(self.theme["bg"])
        self.load_data()


# ============== WEEK PLANNER ==============
class WeekPlannerWidget(BaseWidget):
    def __init__(self, master, app):
        super().__init__(master, "📋 Week Planner", "week_planner", app, (800, 400), (500, 280))
        self.week_start = datetime.now() - timedelta(days=datetime.now().weekday())
        self.day_widgets = {}
        self.build()
    
    def build(self):
        # Nav
        nav = tk.Frame(self.content, bg=self.theme["bg"])
        nav.pack(fill="x", pady=5)
        
        tk.Button(nav, text="◀ Prev", command=self.prev_week, bg=self.theme["button"],
                 fg=self.theme["text"], font=FONTS["button"], bd=0, padx=12, cursor="hand2").pack(side="left")
        
        self.week_lbl = tk.Label(nav, text="", bg=self.theme["bg"], fg=self.theme["text"], font=FONTS["header"])
        self.week_lbl.pack(side="left", fill="x", expand=True)
        
        tk.Button(nav, text="This Week", command=self.go_this_week, bg=self.theme["accent"],
                 fg="white", font=FONTS["small"], bd=0, padx=10, cursor="hand2").pack(side="right", padx=5)
        tk.Button(nav, text="Next ▶", command=self.next_week, bg=self.theme["button"],
                 fg=self.theme["text"], font=FONTS["button"], bd=0, padx=12, cursor="hand2").pack(side="right")
        
        # Days - HORIZONTAL SCROLL
        self.scroll = ScrollableFrame(self.content, bg=self.theme["bg"])
        self.scroll.pack(fill="both", expand=True)
        
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for i, day in enumerate(days):
            col = tk.Frame(self.scroll.inner, bg=self.theme["entry"], relief="ridge", bd=2, width=120)
            col.pack(side="left", fill="both", padx=2)
            col.pack_propagate(False)  # FIXED WIDTH
            
            is_weekend = i >= 5
            hdr = tk.Label(col, text=day[:3], bg=self.theme["header"],
                          fg="#E74C3C" if is_weekend else self.theme["text"],
                          font=FONTS["header"], pady=5)
            hdr.pack(fill="x")
            
            date_lbl = tk.Label(col, text="", bg=self.theme["header"],
                               fg=self.theme["text_light"], font=FONTS["small"])
            date_lbl.pack(fill="x")
            
            txt = tk.Text(col, bg=self.theme["entry"], fg=self.theme["text"],
                         font=FONTS["normal"], bd=0, wrap="word", width=14, height=14)
            txt.pack(fill="both", expand=True, padx=5, pady=5)
            txt.bind("<KeyRelease>", lambda e, idx=i: self.save_day(idx))
            
            self.day_widgets[i] = {"col": col, "header": hdr, "date": date_lbl, "text": txt}
        
        self.load_data()
    
    def load_data(self):
        key = self.week_start.strftime("%Y-%m-%d")
        data = self.app.data.get("week_planner", {}).get(key, {})
        
        end = self.week_start + timedelta(days=6)
        self.week_lbl.config(text=f"{self.week_start.strftime('%B %d')} - {end.strftime('%B %d, %Y')}")
        
        today = datetime.now().date()
        
        for i, widgets in self.day_widgets.items():
            day_date = self.week_start + timedelta(days=i)
            widgets["date"].config(text=day_date.strftime("%d"))
            
            if day_date.date() == today:
                widgets["header"].config(bg=self.theme["accent"], fg="white")
                widgets["date"].config(bg=self.theme["accent"], fg="white")
            else:
                is_weekend = i >= 5
                widgets["header"].config(bg=self.theme["header"], fg="#E74C3C" if is_weekend else self.theme["text"])
                widgets["date"].config(bg=self.theme["header"], fg=self.theme["text_light"])
            
            widgets["text"].delete("1.0", "end")
            if str(i) in data:
                widgets["text"].insert("1.0", data[str(i)])
    
    def save_day(self, idx):
        if "week_planner" not in self.app.data:
            self.app.data["week_planner"] = {}
        key = self.week_start.strftime("%Y-%m-%d")
        if key not in self.app.data["week_planner"]:
            self.app.data["week_planner"][key] = {}
        
        text = self.day_widgets[idx]["text"].get("1.0", "end-1c")
        if text.strip():
            self.app.data["week_planner"][key][str(idx)] = text
        elif str(idx) in self.app.data["week_planner"][key]:
            del self.app.data["week_planner"][key][str(idx)]
        self.app.save_data()
    
    def prev_week(self):
        self.week_start -= timedelta(days=7)
        self.load_data()
    
    def next_week(self):
        self.week_start += timedelta(days=7)
        self.load_data()
    
    def go_this_week(self):
        self.week_start = datetime.now() - timedelta(days=datetime.now().weekday())
        self.load_data()
    
    def apply_theme(self):
        super().apply_theme()
        self.scroll.set_bg(self.theme["bg"])
        self.load_data()


# ============== MONTHLY PLANNER ==============
class MonthlyPlannerWidget(BaseWidget):
    def __init__(self, master, app):
        super().__init__(master, "🎯 Monthly Planner", "monthly_planner", app, (380, 500), (300, 320))
        self.current = datetime.now()
        self.sections = {}
        self.build()
    
    def build(self):
        # Nav
        nav = tk.Frame(self.content, bg=self.theme["bg"])
        nav.pack(fill="x", pady=5)
        
        tk.Button(nav, text="◀", command=self.prev_month, bg=self.theme["button"],
                 fg=self.theme["text"], font=FONTS["button"], bd=0, padx=12, cursor="hand2").pack(side="left")
        
        self.month_lbl = tk.Label(nav, text="", bg=self.theme["bg"], fg=self.theme["text"], font=FONTS["header"])
        self.month_lbl.pack(side="left", fill="x", expand=True)
        
        tk.Button(nav, text="▶", command=self.next_month, bg=self.theme["button"],
                 fg=self.theme["text"], font=FONTS["button"], bd=0, padx=12, cursor="hand2").pack(side="right")
        
        # Sections
        self.scroll = ScrollableFrame(self.content, bg=self.theme["bg"])
        self.scroll.pack(fill="both", expand=True)
        
        secs = [("🎯 Goals", "goals", "#4CAF50"), ("📝 Tasks", "tasks", "#2196F3"),
                ("💡 Ideas", "ideas", "#FF9800"), ("📊 Review", "review", "#9C27B0"),
                ("✨ Notes", "notes", "#607D8B")]
        
        for title, key, color in secs:
            frame = tk.Frame(self.scroll.inner, bg=self.theme["entry"], relief="ridge", bd=2)
            frame.pack(fill="x", pady=3)
            
            hdr = tk.Label(frame, text=title, bg=color, fg="white",
                          font=FONTS["header"], anchor="w", padx=10, pady=5)
            hdr.pack(fill="x")
            
            txt = tk.Text(frame, height=4, bg=self.theme["entry"], fg=self.theme["text"],
                         font=FONTS["normal"], bd=0, wrap="word", padx=8, pady=5)
            txt.pack(fill="x")
            txt.bind("<KeyRelease>", lambda e, k=key: self.save_section(k))
            
            self.sections[key] = {"frame": frame, "header": hdr, "text": txt, "color": color}
        
        self.load_data()
    
    def load_data(self):
        key = self.current.strftime("%Y-%m")
        data = self.app.data.get("monthly_planner", {}).get(key, {})
        
        self.month_lbl.config(text=f"{calendar.month_name[self.current.month]} {self.current.year}")
        
        for k, widgets in self.sections.items():
            widgets["text"].delete("1.0", "end")
            if k in data:
                widgets["text"].insert("1.0", data[k])
    
    def save_section(self, key):
        if "monthly_planner" not in self.app.data:
            self.app.data["monthly_planner"] = {}
        mkey = self.current.strftime("%Y-%m")
        if mkey not in self.app.data["monthly_planner"]:
            self.app.data["monthly_planner"][mkey] = {}
        
        text = self.sections[key]["text"].get("1.0", "end-1c")
        if text.strip():
            self.app.data["monthly_planner"][mkey][key] = text
        elif key in self.app.data["monthly_planner"][mkey]:
            del self.app.data["monthly_planner"][mkey][key]
        self.app.save_data()
    
    def prev_month(self):
        self.current = self.current.replace(day=1) - timedelta(days=1)
        self.load_data()
    
    def next_month(self):
        self.current = self.current.replace(day=28) + timedelta(days=4)
        self.current = self.current.replace(day=1)
        self.load_data()
    
    def apply_theme(self):
        super().apply_theme()
        self.scroll.set_bg(self.theme["bg"])
        for k, w in self.sections.items():
            w["frame"].config(bg=self.theme["entry"])
            w["text"].config(bg=self.theme["entry"], fg=self.theme["text"])


# ============== STICKY NOTES ==============
class StickyNotesWidget(BaseWidget):
    def __init__(self, master, app):
        super().__init__(master, "📝 Sticky Notes", "sticky_notes", app, (380, 420), (280, 280))
        self.colors = ["#FFFFA5", "#A5FFFA", "#FFA5FF", "#A5FFA5", "#FFA5A5", "#A5A5FF"]
        self.build()
    
    def build(self):
        # Add buttons
        add_frame = tk.Frame(self.content, bg=self.theme["bg"])
        add_frame.pack(fill="x", pady=5)
        
        tk.Label(add_frame, text="Add note:", bg=self.theme["bg"],
                fg=self.theme["text"], font=FONTS["normal"]).pack(side="left", padx=5)
        
        for c in self.colors:
            tk.Button(add_frame, text="  ", bg=c, bd=2, relief="raised", width=3,
                     command=lambda col=c: self.add_note(col), cursor="hand2").pack(side="left", padx=2)
        
        # Notes
        self.scroll = ScrollableFrame(self.content, bg=self.theme["bg"])
        self.scroll.pack(fill="both", expand=True)
        
        self.notes_frame = self.scroll.inner
        self.load_notes()
    
    def load_notes(self):
        for w in self.notes_frame.winfo_children():
            w.destroy()
        
        notes = self.app.data.get("sticky_notes", [])
        row, col = 0, 0
        
        for i, note in enumerate(notes):
            self._create_note(i, note, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1
    
    def _create_note(self, idx, note, row, col):
        color = note.get("color", "#FFFFA5")
        
        frame = tk.Frame(self.notes_frame, bg=color, relief="raised", bd=2, width=150, height=110)
        frame.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
        frame.grid_propagate(False)
        
        del_btn = tk.Label(frame, text="✕", bg=color, fg="#666", font=FONTS["normal"], cursor="hand2")
        del_btn.pack(anchor="ne", padx=2)
        del_btn.bind("<Button-1>", lambda e: self.delete_note(idx))
        
        txt = tk.Text(frame, height=4, width=18, bg=color, fg="#333",
                     font=FONTS["normal"], bd=0, wrap="word")
        txt.pack(fill="both", expand=True, padx=5, pady=2)
        txt.insert("1.0", note.get("text", ""))
        txt.bind("<KeyRelease>", lambda e, i=idx, t=txt: self.save_note(i, t))
        
        self.notes_frame.columnconfigure(col, weight=1)
        self.notes_frame.rowconfigure(row, weight=1)
    
    def add_note(self, color):
        if "sticky_notes" not in self.app.data:
            self.app.data["sticky_notes"] = []
        self.app.data["sticky_notes"].append({"text": "", "color": color})
        self.app.save_data()
        self.load_notes()
    
    def save_note(self, idx, txt):
        if idx < len(self.app.data.get("sticky_notes", [])):
            self.app.data["sticky_notes"][idx]["text"] = txt.get("1.0", "end-1c")
            self.app.save_data()
    
    def delete_note(self, idx):
        if idx < len(self.app.data.get("sticky_notes", [])):
            del self.app.data["sticky_notes"][idx]
            self.app.save_data()
            self.load_notes()
    
    def apply_theme(self):
        super().apply_theme()
        self.scroll.set_bg(self.theme["bg"])
        self.load_notes()


# ============== POMODORO ==============
class PomodoroWidget(BaseWidget):
    def __init__(self, master, app):
        super().__init__(master, "🍅 Pomodoro", "pomodoro", app, (300, 360), (240, 280))
        self.work = 25 * 60
        self.brk = 5 * 60
        self.time = self.work
        self.running = False
        self.is_work = True
        self.sessions = 0
        self.build()
    
    def build(self):
        self.timer_lbl = tk.Label(self.content, text="25:00", bg=self.theme["bg"],
                                  fg=self.theme["accent"], font=("Segoe UI Light", 52))
        self.timer_lbl.pack(pady=15)
        
        self.status_lbl = tk.Label(self.content, text="🍅 Work Time", bg=self.theme["bg"],
                                   fg=self.theme["text"], font=FONTS["header"])
        self.status_lbl.pack()
        
        self.sess_lbl = tk.Label(self.content, text="Sessions: 0", bg=self.theme["bg"],
                                 fg=self.theme["text_light"], font=FONTS["small"])
        self.sess_lbl.pack(pady=5)
        
        ctrl = tk.Frame(self.content, bg=self.theme["bg"])
        ctrl.pack(pady=15)
        
        self.start_btn = tk.Button(ctrl, text="▶ Start", command=self.toggle,
                                   bg=self.theme["accent"], fg="white",
                                   font=FONTS["button"], bd=0, padx=20, pady=8, cursor="hand2")
        self.start_btn.pack(side="left", padx=5)
        
        tk.Button(ctrl, text="↺ Reset", command=self.reset,
                 bg=self.theme["button"], fg=self.theme["text"],
                 font=FONTS["button"], bd=0, padx=20, pady=8, cursor="hand2").pack(side="left", padx=5)
        
        # Settings
        sett = tk.Frame(self.content, bg=self.theme["bg"])
        sett.pack(pady=10)
        
        tk.Label(sett, text="Work:", bg=self.theme["bg"], fg=self.theme["text"], font=FONTS["small"]).pack(side="left")
        self.work_spin = tk.Spinbox(sett, from_=1, to=60, width=4, font=FONTS["small"])
        self.work_spin.pack(side="left", padx=3)
        self.work_spin.delete(0, "end")
        self.work_spin.insert(0, "25")
        
        tk.Label(sett, text="  Break:", bg=self.theme["bg"], fg=self.theme["text"], font=FONTS["small"]).pack(side="left")
        self.brk_spin = tk.Spinbox(sett, from_=1, to=30, width=4, font=FONTS["small"])
        self.brk_spin.pack(side="left", padx=3)
        self.brk_spin.delete(0, "end")
        self.brk_spin.insert(0, "5")
    
    def toggle(self):
        if self.running:
            self.running = False
            self.start_btn.config(text="▶ Start", bg=self.theme["accent"])
        else:
            try:
                self.work = int(self.work_spin.get()) * 60
                self.brk = int(self.brk_spin.get()) * 60
            except:
                pass
            self.running = True
            self.start_btn.config(text="⏸ Pause", bg="#FF9800")
            self.run()
    
    def run(self):
        if self.running and self.time > 0:
            m, s = divmod(self.time, 60)
            self.timer_lbl.config(text=f"{m:02d}:{s:02d}")
            self.time -= 1
            self.window.after(1000, self.run)
        elif self.running:
            self.complete()
    
    def complete(self):
        if self.is_work:
            self.sessions += 1
            self.sess_lbl.config(text=f"Sessions: {self.sessions}")
            self.time = self.brk
            self.status_lbl.config(text="☕ Break!")
            self.is_work = False
        else:
            self.time = self.work
            self.status_lbl.config(text="🍅 Work Time")
            self.is_work = True
        
        try:
            import winsound
            winsound.MessageBeep()
        except:
            pass
        
        self.run()
    
    def reset(self):
        self.running = False
        self.is_work = True
        try:
            self.work = int(self.work_spin.get()) * 60
        except:
            self.work = 25 * 60
        self.time = self.work
        m, s = divmod(self.time, 60)
        self.timer_lbl.config(text=f"{m:02d}:{s:02d}")
        self.status_lbl.config(text="🍅 Work Time")
        self.start_btn.config(text="▶ Start", bg=self.theme["accent"])
    
    def apply_theme(self):
        super().apply_theme()
        self.timer_lbl.config(bg=self.theme["bg"], fg=self.theme["accent"])
        self.status_lbl.config(bg=self.theme["bg"], fg=self.theme["text"])
        self.sess_lbl.config(bg=self.theme["bg"], fg=self.theme["text_light"])


# ============== HABIT TRACKER ==============
class HabitTrackerWidget(BaseWidget):
    def __init__(self, master, app):
        super().__init__(master, "📊 Habits", "habit_tracker", app, (450, 400), (350, 280))
        self.habits_data = {}
        self.build()
    
    def build(self):
        # Add
        add_frame = tk.Frame(self.content, bg=self.theme["bg"])
        add_frame.pack(fill="x", pady=5)
        
        self.entry = tk.Entry(add_frame, bg=self.theme["entry"], fg=self.theme["text"],
                             font=FONTS["normal"], bd=2, relief="groove")
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.entry.bind("<Return>", self.add_habit)
        
        tk.Button(add_frame, text="➕ Add", command=self.add_habit, bg=self.theme["accent"],
                 fg="white", font=FONTS["button"], bd=0, padx=12, cursor="hand2").pack(side="right")
        
        # Habits - SCROLLABLE
        self.scroll = ScrollableFrame(self.content, bg=self.theme["bg"])
        self.scroll.pack(fill="both", expand=True)
        
        self.habits_frame = self.scroll.inner
        self.load_habits()
    
    def get_week_key(self):
        today = datetime.now()
        return (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
    
    def load_habits(self):
        for w in self.habits_frame.winfo_children():
            w.destroy()
        
        habits = self.app.data.get("habits", [])
        wk = self.get_week_key()
        
        # Header - FIXED WIDTHS
        tk.Label(self.habits_frame, text="Habit", bg=self.theme["bg"], fg=self.theme["text"],
                font=FONTS["header"], width=16, anchor="w").grid(row=0, column=0, padx=3, pady=3)
        
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for c, d in enumerate(days):
            tk.Label(self.habits_frame, text=d, bg=self.theme["header"], fg=self.theme["text"],
                    font=FONTS["small"], width=4).grid(row=0, column=c+1, padx=2, pady=3)
        
        tk.Label(self.habits_frame, text="", width=3, bg=self.theme["bg"]).grid(row=0, column=8)
        
        for i, habit in enumerate(habits):
            self._create_habit_row(i, habit, wk)
    
    def _create_habit_row(self, idx, habit, wk):
        row = idx + 1
        
        tk.Label(self.habits_frame, text=habit["name"][:16], bg=self.theme["entry"],
                fg=self.theme["text"], font=FONTS["normal"], width=16, anchor="w"
                ).grid(row=row, column=0, padx=3, pady=2, sticky="w")
        
        checked = habit.get("checked", {}).get(wk, [False] * 7)
        while len(checked) < 7:
            checked.append(False)
        
        for d in range(7):
            var = tk.BooleanVar(value=checked[d])
            tk.Checkbutton(self.habits_frame, variable=var, bg=self.theme["entry"],
                          command=lambda i=idx, day=d, v=var: self.toggle_day(i, day, v.get())
                          ).grid(row=row, column=d+1, padx=2, pady=2)
        
        del_btn = tk.Label(self.habits_frame, text="✕", bg=self.theme["bg"],
                          fg="#E74C3C", font=FONTS["normal"], cursor="hand2")
        del_btn.grid(row=row, column=8, padx=3)
        del_btn.bind("<Button-1>", lambda e: self.delete_habit(idx))
    
    def add_habit(self, e=None):
        name = self.entry.get().strip()
        if name:
            if "habits" not in self.app.data:
                self.app.data["habits"] = []
            self.app.data["habits"].append({"name": name, "checked": {}})
            self.app.save_data()
            self.entry.delete(0, "end")
            self.load_habits()
    
    def toggle_day(self, idx, day, checked):
        if idx < len(self.app.data.get("habits", [])):
            wk = self.get_week_key()
            habit = self.app.data["habits"][idx]
            if "checked" not in habit:
                habit["checked"] = {}
            if wk not in habit["checked"]:
                habit["checked"][wk] = [False] * 7
            habit["checked"][wk][day] = checked
            self.app.save_data()
    
    def delete_habit(self, idx):
        if idx < len(self.app.data.get("habits", [])):
            del self.app.data["habits"][idx]
            self.app.save_data()
            self.load_habits()
    
    def apply_theme(self):
        super().apply_theme()
        self.scroll.set_bg(self.theme["bg"])
        self.load_habits()


# ============== CLOCK ==============
class ClockWidget(BaseWidget):
    def __init__(self, master, app):
        super().__init__(master, "🕐 Clock", "clock", app, (280, 200), (200, 150))
        self.build()
        self.tick()
    
    def build(self):
        self.time_lbl = tk.Label(self.content, text="", bg=self.theme["bg"],
                                 fg=self.theme["accent"], font=FONTS["clock"])
        self.time_lbl.pack(expand=True, pady=10)
        
        self.date_lbl = tk.Label(self.content, text="", bg=self.theme["bg"],
                                 fg=self.theme["text"], font=FONTS["clock_date"])
        self.date_lbl.pack(pady=(0, 10))
    
    def tick(self):
        now = datetime.now()
        self.time_lbl.config(text=now.strftime("%H:%M:%S"))
        self.date_lbl.config(text=now.strftime("%A, %B %d"))
        self.window.after(1000, self.tick)
    
    def apply_theme(self):
        super().apply_theme()
        self.time_lbl.config(bg=self.theme["bg"], fg=self.theme["accent"])
        self.date_lbl.config(bg=self.theme["bg"], fg=self.theme["text"])


# ============== MAIN APP ==============
class DesktopWidgetsApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        
        # Initialize desktop layer FIRST
        print("Initializing desktop layer...")
        DesktopLayer.initialize()
        
        self.load_data()
        self.widgets = {}
        self.create_widgets()
        self.create_panel()
    
    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except:
                self.data = self.default_data()
        else:
            self.data = self.default_data()
    
    def default_data(self):
        return {
            "theme": "🌊 Ocean Blue", "widget_themes": {}, "calendar_events": {},
            "todos": [], "day_planner": {}, "week_planner": {}, "monthly_planner": {},
            "sticky_notes": [], "habits": [], "widget_positions": {}, "widget_sizes": {},
            "hidden_widgets": []
        }
    
    def save_data(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def create_widgets(self):
        hidden = self.data.get("hidden_widgets", [])
        
        classes = {
            "calendar": CalendarWidget, "todo": TodoWidget, "day_planner": DayPlannerWidget,
            "week_planner": WeekPlannerWidget, "monthly_planner": MonthlyPlannerWidget,
            "sticky_notes": StickyNotesWidget, "pomodoro": PomodoroWidget,
            "habit_tracker": HabitTrackerWidget, "clock": ClockWidget
        }
        
        for wid, cls in classes.items():
            self.widgets[wid] = cls(self.root, self)
            if wid in hidden:
                self.widgets[wid].window.withdraw()
    
    def create_panel(self):
        self.panel = tk.Toplevel(self.root)
        self.panel.title("🎮 Control Panel")
        self.panel.geometry("320x580")
        self.panel.resizable(False, False)
        self.panel.attributes('-topmost', True)
        
        theme = THEMES.get(self.data.get("theme", "🌊 Ocean Blue"))
        self.panel.configure(bg=theme["bg"])
        
        # Title
        tk.Label(self.panel, text="🖥️ Desktop Widgets Pro", bg=theme["header"],
                fg=theme["text"], font=("Segoe UI Semibold", 14), pady=12).pack(fill="x")
        
        # Desktop mode info
        tk.Label(self.panel, text="✅ Widgets stuck to desktop!\nWon't hide on 3-finger swipe",
                bg=theme["highlight"], fg=theme["text"], font=FONTS["small"],
                pady=8).pack(fill="x", padx=10, pady=8)
        
        # Autostart
        auto_frame = tk.LabelFrame(self.panel, text="⚡ Startup", bg=theme["bg"],
                                   fg=theme["text"], font=FONTS["header"])
        auto_frame.pack(fill="x", padx=10, pady=5)
        
        self.auto_var = tk.BooleanVar(value=is_autostart_enabled())
        tk.Checkbutton(auto_frame, text="🚀 Start with Windows", variable=self.auto_var,
                      bg=theme["bg"], fg=theme["text"], font=FONTS["normal"],
                      selectcolor=theme["entry"], command=self.toggle_autostart).pack(anchor="w", padx=10, pady=5)
        
        self.auto_status = tk.Label(auto_frame, text="", bg=theme["bg"], font=FONTS["small"])
        self.auto_status.pack(anchor="w", padx=10)
        self.update_auto_status()
        
        # Widgets
        widgets_frame = tk.LabelFrame(self.panel, text="📦 Show/Hide Widgets",
                                      bg=theme["bg"], fg=theme["text"], font=FONTS["header"])
        widgets_frame.pack(fill="x", padx=10, pady=5)
        
        names = {
            "calendar": "📅 Calendar", "todo": "✅ To-Do List", "day_planner": "📆 Day Planner",
            "week_planner": "📋 Week Planner", "monthly_planner": "🎯 Monthly Planner",
            "sticky_notes": "📝 Sticky Notes", "pomodoro": "🍅 Pomodoro",
            "habit_tracker": "📊 Habit Tracker", "clock": "🕐 Clock"
        }
        
        self.widget_vars = {}
        hidden = self.data.get("hidden_widgets", [])
        
        for wid, name in names.items():
            var = tk.BooleanVar(value=wid not in hidden)
            self.widget_vars[wid] = var
            tk.Checkbutton(widgets_frame, text=name, variable=var, bg=theme["bg"],
                          fg=theme["text"], font=FONTS["normal"], selectcolor=theme["entry"],
                          command=lambda w=wid: self.toggle_widget(w)).pack(anchor="w", padx=10, pady=2)
        
        # Buttons
        btn_frame = tk.Frame(self.panel, bg=theme["bg"])
        btn_frame.pack(fill="x", padx=10, pady=8)
        
        tk.Button(btn_frame, text="👁️ Show All", command=self.show_all, bg=theme["button"],
                 fg=theme["text"], font=FONTS["button"], bd=0, padx=15, cursor="hand2").pack(side="left", padx=5)
        tk.Button(btn_frame, text="🙈 Hide All", command=self.hide_all, bg=theme["button"],
                 fg=theme["text"], font=FONTS["button"], bd=0, padx=15, cursor="hand2").pack(side="left", padx=5)
        
        # Exit
        tk.Button(self.panel, text="❌ Exit Application", command=self.exit_app,
                 bg="#E74C3C", fg="white", font=FONTS["button"], bd=0,
                 padx=20, pady=8, cursor="hand2").pack(pady=15)
        
        self.panel.protocol("WM_DELETE_WINDOW", lambda: self.panel.iconify())
    
    def toggle_autostart(self):
        if self.auto_var.get():
            enable_autostart()
        else:
            disable_autostart()
        self.update_auto_status()
    
    def update_auto_status(self):
        if is_autostart_enabled():
            self.auto_status.config(text="✅ Enabled", fg="#27AE60")
        else:
            self.auto_status.config(text="❌ Disabled", fg="#E74C3C")
    
    def update_panel(self):
        hidden = self.data.get("hidden_widgets", [])
        for wid, var in self.widget_vars.items():
            var.set(wid not in hidden)
    
    def toggle_widget(self, wid):
        if self.widget_vars[wid].get():
            self.widgets[wid].show()
        else:
            self.widgets[wid]._hide()
    
    def show_all(self):
        for wid, widget in self.widgets.items():
            widget.show()
            self.widget_vars[wid].set(True)
    
    def hide_all(self):
        for wid, widget in self.widgets.items():
            widget._hide()
            self.widget_vars[wid].set(False)
    
    def exit_app(self):
        self.save_data()
        self.root.quit()
        self.root.destroy()
        sys.exit()
    
    def run(self):
        self.root.mainloop()


# ============== START ==============
if __name__ == "__main__":
    app = DesktopWidgetsApp()
    app.run()
