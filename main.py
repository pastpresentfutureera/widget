"""
Desktop Widgets Ultimate v4.0
- Embedded into desktop wallpaper layer (won't hide on swipe)
- Responsive design: compact mode + expanded mode
- Scrollbars when content doesn't fit
- Works on Windows 10/11
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
import threading

# ============== WINDOWS API ==============
user32 = ctypes.windll.user32

# Constants
GWL_EXSTYLE = -20
GWL_STYLE = -16
WS_CHILD = 0x40000000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WS_EX_LAYERED = 0x00080000

# API Functions
FindWindow = user32.FindWindowW
FindWindowEx = user32.FindWindowExW
SendMessageTimeout = user32.SendMessageTimeoutW
SetParent = user32.SetParent
GetParent = user32.GetParent
SetWindowLong = user32.SetWindowLongW
GetWindowLong = user32.GetWindowLongW
ShowWindow = user32.ShowWindow
EnumWindows = user32.EnumWindows
GetClassName = user32.GetClassNameW

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))

# ============== PATHS ==============
if getattr(sys, 'frozen', False):
    APP_PATH = sys.executable
else:
    APP_PATH = os.path.abspath(__file__)

DATA_FILE = os.path.join(os.path.expanduser("~"), "desktop_widgets_ultimate_data.json")
STARTUP_FOLDER = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
SHORTCUT_PATH = os.path.join(STARTUP_FOLDER, "DesktopWidgets.bat")


# ============== DESKTOP WALLPAPER LAYER ==============
class DesktopWallpaperLayer:
    """Embeds windows into the desktop wallpaper layer"""
    
    _workerw = None
    _progman = None
    
    @classmethod
    def initialize(cls):
        """Initialize and find/create the WorkerW window"""
        try:
            # Find Program Manager
            cls._progman = FindWindow("Progman", None)
            if not cls._progman:
                return False
            
            # Send message to spawn WorkerW
            result = ctypes.c_ulong()
            SendMessageTimeout(cls._progman, 0x052C, 0, 0, 0x0000, 1000, ctypes.byref(result))
            
            time.sleep(0.2)
            
            # Find WorkerW
            def find_workerw(hwnd, lParam):
                class_name = ctypes.create_unicode_buffer(256)
                GetClassName(hwnd, class_name, 256)
                if class_name.value == "WorkerW":
                    shell = FindWindowEx(hwnd, None, "SHELLDLL_DefView", None)
                    if shell:
                        cls._workerw = FindWindowEx(None, hwnd, "WorkerW", None)
                return True
            
            EnumWindows(WNDENUMPROC(find_workerw), 0)
            
            # If WorkerW not found, use Progman
            if not cls._workerw:
                cls._workerw = cls._progman
            
            return cls._workerw is not None
            
        except Exception as e:
            print(f"Desktop init error: {e}")
            return False
    
    @classmethod
    def embed(cls, hwnd):
        """Embed a window into the desktop layer"""
        try:
            if not cls._workerw:
                cls.initialize()
            
            if cls._workerw:
                # Set as child of desktop layer
                SetParent(hwnd, cls._workerw)
                
                # Set window styles
                style = GetWindowLong(hwnd, GWL_EXSTYLE)
                style |= WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
                SetWindowLong(hwnd, GWL_EXSTYLE, style)
                
                # Show window
                ShowWindow(hwnd, 5)
                return True
        except Exception as e:
            print(f"Embed error: {e}")
        return False
    
    @classmethod
    def get_parent(cls):
        """Get the desktop layer window handle"""
        if not cls._workerw:
            cls.initialize()
        return cls._workerw


# ============== COLOR THEMES ==============
THEMES = {
    "🌸 Pink": {"bg": "#FFF0F5", "header": "#FFB6C1", "accent": "#FF69B4", "text": "#4A4A4A", "text_light": "#777", "button": "#FFC0CB", "entry": "#FFF", "border": "#FFB6C1"},
    "🌊 Blue": {"bg": "#F0F8FF", "header": "#87CEEB", "accent": "#4169E1", "text": "#2F4F4F", "text_light": "#5F7F7F", "button": "#B0E0E6", "entry": "#FFF", "border": "#87CEEB"},
    "🌿 Green": {"bg": "#F0FFF0", "header": "#90EE90", "accent": "#32CD32", "text": "#2F4F4F", "text_light": "#5F7F7F", "button": "#98FB98", "entry": "#FFF", "border": "#90EE90"},
    "🍇 Purple": {"bg": "#F8F0FF", "header": "#DDA0DD", "accent": "#9370DB", "text": "#4A4A4A", "text_light": "#6A6A8A", "button": "#E6E6FA", "entry": "#FFF", "border": "#DDA0DD"},
    "🌻 Yellow": {"bg": "#FFFEF0", "header": "#FFE57F", "accent": "#FFC107", "text": "#4A4A4A", "text_light": "#6A6A6A", "button": "#FFF59D", "entry": "#FFF", "border": "#FFE57F"},
    "🍑 Peach": {"bg": "#FFF5EE", "header": "#FFDAB9", "accent": "#FF8C00", "text": "#4A4A4A", "text_light": "#6A6A6A", "button": "#FFE4B5", "entry": "#FFF", "border": "#FFDAB9"},
    "🌙 Dark": {"bg": "#2D2D3A", "header": "#3D3D5C", "accent": "#7B68EE", "text": "#E8E8E8", "text_light": "#AAA", "button": "#4D4D6A", "entry": "#3A3A4A", "border": "#5D5D7A"},
    "☁️ White": {"bg": "#FAFAFA", "header": "#E8E8E8", "accent": "#607D8B", "text": "#424242", "text_light": "#757575", "button": "#EEE", "entry": "#FFF", "border": "#E0E0E0"},
}

FONTS = {
    "title": ("Segoe UI Semibold", 11),
    "header": ("Segoe UI Semibold", 10),
    "normal": ("Segoe UI", 10),
    "small": ("Segoe UI", 9),
    "tiny": ("Segoe UI", 8),
    "icon": ("Segoe UI", 12),
    "clock": ("Segoe UI Light", 28),
    "timer": ("Segoe UI Light", 36),
}

# Compact default sizes
COMPACT_SIZES = {
    "calendar": (280, 320),
    "todo": (250, 300),
    "day_planner": (250, 300),
    "week_planner": (500, 200),
    "monthly_planner": (260, 320),
    "sticky_notes": (260, 280),
    "pomodoro": (220, 280),
    "habit_tracker": (320, 220),
    "clock": (180, 120)
}

MIN_SIZES = {
    "calendar": (220, 250),
    "todo": (200, 220),
    "day_planner": (200, 220),
    "week_planner": (350, 150),
    "monthly_planner": (220, 250),
    "sticky_notes": (200, 200),
    "pomodoro": (180, 220),
    "habit_tracker": (280, 180),
    "clock": (150, 100)
}


# ============== AUTOSTART ==============
def is_autostart_enabled():
    return os.path.exists(SHORTCUT_PATH)

def enable_autostart():
    try:
        with open(SHORTCUT_PATH, 'w') as f:
            f.write(f'@echo off\nstart "" "{APP_PATH}"\n')
    except:
        pass

def disable_autostart():
    try:
        if os.path.exists(SHORTCUT_PATH):
            os.remove(SHORTCUT_PATH)
    except:
        pass


# ============== SCROLLABLE FRAME ==============
class ScrollFrame(tk.Frame):
    """Frame with scrollbars - content has FIXED minimum sizes"""
    
    def __init__(self, parent, bg="#FFF"):
        super().__init__(parent, bg=bg)
        
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.vbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.hbar = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=self.vbar.set, xscrollcommand=self.hbar.set)
        
        self.vbar.pack(side="right", fill="y")
        self.hbar.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.inner = tk.Frame(self.canvas, bg=bg)
        self.win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # Mouse wheel scroll
        self.canvas.bind("<MouseWheel>", self._scroll_y)
        self.inner.bind("<MouseWheel>", self._scroll_y)
        self.canvas.bind("<Shift-MouseWheel>", self._scroll_x)
    
    def _scroll_y(self, e):
        self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
    
    def _scroll_x(self, e):
        self.canvas.xview_scroll(int(-1 * (e.delta / 120)), "units")
    
    def set_bg(self, bg):
        self.config(bg=bg)
        self.canvas.config(bg=bg)
        self.inner.config(bg=bg)


# ============== BASE WIDGET ==============
class BaseWidget:
    """Base widget embedded into desktop wallpaper"""
    
    def __init__(self, master, title, wid, app):
        self.app = app
        self.wid = wid
        self.title_text = title
        
        # Sizes
        self.min_w, self.min_h = MIN_SIZES.get(wid, (180, 150))
        default = COMPACT_SIZES.get(wid, (250, 300))
        
        # Theme
        theme_name = app.data.get("widget_themes", {}).get(wid, app.data.get("theme", "🌊 Blue"))
        self.theme = THEMES.get(theme_name, THEMES["🌊 Blue"])
        
        # Create window
        self.win = tk.Toplevel(master)
        self.win.title(title)
        self.win.overrideredirect(True)
        self.win.attributes('-alpha', 0.96)
        
        # Position & size
        pos = app.data.get("positions", {}).get(wid, {"x": 50, "y": 50})
        size = app.data.get("sizes", {}).get(wid, {"w": default[0], "h": default[1]})
        self.win.geometry(f"{size['w']}x{size['h']}+{pos['x']}+{pos['y']}")
        
        # State
        self.drag = {}
        self.resize = {}
        self.expanded = size['w'] > default[0] * 1.3 or size['h'] > default[1] * 1.3
        
        # Build UI
        self.border = tk.Frame(self.win, bg=self.theme["border"], padx=1, pady=1)
        self.border.pack(fill="both", expand=True)
        
        self.main = tk.Frame(self.border, bg=self.theme["bg"])
        self.main.pack(fill="both", expand=True)
        
        self._header(title)
        
        self.content = tk.Frame(self.main, bg=self.theme["bg"])
        self.content.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        
        self._grip()
        
        # Embed to desktop after creation
        self.win.after(300, self._embed)
        
        # Track size changes
        self.win.bind("<Configure>", self._on_resize)
    
    def _embed(self):
        """Embed into desktop wallpaper layer"""
        try:
            self.win.update_idletasks()
            hwnd = GetParent(self.win.winfo_id())
            if DesktopWallpaperLayer.embed(hwnd):
                print(f"✓ {self.wid} embedded")
            else:
                print(f"✗ {self.wid} not embedded - using fallback")
        except Exception as e:
            print(f"Embed error: {e}")
    
    def _header(self, title):
        self.hdr = tk.Frame(self.main, bg=self.theme["header"], height=32)
        self.hdr.pack(fill="x")
        self.hdr.pack_propagate(False)
        
        self.title_lbl = tk.Label(self.hdr, text=f" {title}", bg=self.theme["header"],
                                  fg=self.theme["text"], font=FONTS["title"], anchor="w")
        self.title_lbl.pack(side="left", fill="x", expand=True)
        
        # Buttons
        btns = tk.Frame(self.hdr, bg=self.theme["header"])
        btns.pack(side="right", padx=3)
        
        for txt, cmd in [("🎨", self._theme_menu), ("✕", self._hide)]:
            b = tk.Label(btns, text=txt, bg=self.theme["header"], fg=self.theme["text"],
                        font=FONTS["icon"], cursor="hand2")
            b.pack(side="left", padx=2)
            b.bind("<Button-1>", cmd)
        
        # Drag
        for w in [self.hdr, self.title_lbl]:
            w.bind("<Button-1>", self._drag_start)
            w.bind("<B1-Motion>", self._drag_move)
            w.bind("<ButtonRelease-1>", self._drag_end)
    
    def _theme_menu(self, e):
        menu = tk.Menu(self.win, tearoff=0, font=FONTS["small"])
        for name in THEMES:
            menu.add_command(label=name, command=lambda n=name: self._set_theme(n))
        menu.post(e.x_root, e.y_root)
    
    def _set_theme(self, name):
        self.theme = THEMES[name]
        if "widget_themes" not in self.app.data:
            self.app.data["widget_themes"] = {}
        self.app.data["widget_themes"][self.wid] = name
        self.app.save()
        self.apply_theme()
    
    def _grip(self):
        self.grip = tk.Label(self.main, text="⋱", bg=self.theme["bg"], fg=self.theme["accent"],
                            font=("Segoe UI", 10), cursor="size_nw_se")
        self.grip.place(relx=1, rely=1, anchor="se")
        self.grip.bind("<Button-1>", self._resize_start)
        self.grip.bind("<B1-Motion>", self._resize_move)
        self.grip.bind("<ButtonRelease-1>", self._resize_end)
    
    def _drag_start(self, e):
        self.drag = {"x": e.x_root - self.win.winfo_x(), "y": e.y_root - self.win.winfo_y()}
    
    def _drag_move(self, e):
        if self.drag:
            self.win.geometry(f"+{e.x_root - self.drag['x']}+{e.y_root - self.drag['y']}")
    
    def _drag_end(self, e):
        self.drag = {}
        self._save_pos()
    
    def _resize_start(self, e):
        self.resize = {"x": e.x_root, "y": e.y_root, "w": self.win.winfo_width(), "h": self.win.winfo_height()}
    
    def _resize_move(self, e):
        if self.resize:
            nw = max(self.min_w, self.resize["w"] + e.x_root - self.resize["x"])
            nh = max(self.min_h, self.resize["h"] + e.y_root - self.resize["y"])
            self.win.geometry(f"{int(nw)}x{int(nh)}")
    
    def _resize_end(self, e):
        self.resize = {}
        self._save_size()
        self._check_expanded()
    
    def _on_resize(self, e):
        """Called when window size changes"""
        self._check_expanded()
    
    def _check_expanded(self):
        """Check if widget is in expanded mode"""
        default = COMPACT_SIZES.get(self.wid, (250, 300))
        w, h = self.win.winfo_width(), self.win.winfo_height()
        new_expanded = w > default[0] * 1.2 or h > default[1] * 1.2
        if new_expanded != self.expanded:
            self.expanded = new_expanded
            self.on_mode_change()
    
    def on_mode_change(self):
        """Override in subclasses to handle compact/expanded mode"""
        pass
    
    def _save_pos(self):
        if "positions" not in self.app.data:
            self.app.data["positions"] = {}
        self.app.data["positions"][self.wid] = {"x": self.win.winfo_x(), "y": self.win.winfo_y()}
        self.app.save()
    
    def _save_size(self):
        if "sizes" not in self.app.data:
            self.app.data["sizes"] = {}
        self.app.data["sizes"][self.wid] = {"w": self.win.winfo_width(), "h": self.win.winfo_height()}
        self.app.save()
    
    def _hide(self, e=None):
        self.win.withdraw()
        if "hidden" not in self.app.data:
            self.app.data["hidden"] = []
        if self.wid not in self.app.data["hidden"]:
            self.app.data["hidden"].append(self.wid)
        self.app.save()
        self.app.update_panel()
    
    def show(self):
        self.win.deiconify()
        if "hidden" in self.app.data and self.wid in self.app.data["hidden"]:
            self.app.data["hidden"].remove(self.wid)
        self.app.save()
        self.win.after(100, self._embed)
    
    def apply_theme(self):
        t = self.theme
        self.border.config(bg=t["border"])
        self.main.config(bg=t["bg"])
        self.hdr.config(bg=t["header"])
        self.title_lbl.config(bg=t["header"], fg=t["text"])
        self.content.config(bg=t["bg"])
        self.grip.config(bg=t["bg"], fg=t["accent"])


# ============== CALENDAR ==============
class CalendarWidget(BaseWidget):
    def __init__(self, master, app):
        super().__init__(master, "📅 Calendar", "calendar", app)
        self.date = datetime.now()
        self.build()
    
    def build(self):
        # Nav - always visible
        nav = tk.Frame(self.content, bg=self.theme["bg"])
        nav.pack(fill="x", pady=3)
        
        self.prev = tk.Button(nav, text="◀", command=self.prev_m, bg=self.theme["button"],
                             fg=self.theme["text"], font=FONTS["small"], bd=0, padx=6, cursor="hand2")
        self.prev.pack(side="left")
        
        self.month_lbl = tk.Label(nav, bg=self.theme["bg"], fg=self.theme["text"], font=FONTS["header"])
        self.month_lbl.pack(side="left", fill="x", expand=True)
        
        self.nxt = tk.Button(nav, text="▶", command=self.next_m, bg=self.theme["button"],
                            fg=self.theme["text"], font=FONTS["small"], bd=0, padx=6, cursor="hand2")
        self.nxt.pack(side="right")
        
        # Today button - only in expanded mode
        self.today_btn = tk.Button(nav, text="Today", command=self.go_today, bg=self.theme["accent"],
                                   fg="white", font=FONTS["tiny"], bd=0, padx=5, cursor="hand2")
        
        # Calendar scroll
        self.scroll = ScrollFrame(self.content, bg=self.theme["bg"])
        self.scroll.pack(fill="both", expand=True)
        self.grid = self.scroll.inner
        
        self.render()
    
    def render(self):
        for w in self.grid.winfo_children():
            w.destroy()
        
        year, month = self.date.year, self.date.month
        self.month_lbl.config(text=f"{calendar.month_abbr[month]} {year}")
        
        # Show today button only in expanded mode
        if self.expanded:
            self.today_btn.pack(side="right", padx=3)
        else:
            self.today_btn.pack_forget()
        
        # Day headers - FIXED WIDTH
        cell_w = 9 if self.expanded else 5
        days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"] if not self.expanded else ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        for c, d in enumerate(days):
            fg = "#E74C3C" if c >= 5 else self.theme["text"]
            tk.Label(self.grid, text=d, bg=self.theme["header"], fg=fg,
                    font=FONTS["tiny"], width=cell_w, relief="solid", bd=1).grid(row=0, column=c, sticky="nsew")
        
        # Cells - FIXED SIZE
        cal = calendar.monthcalendar(year, month)
        today = datetime.now()
        events = self.app.data.get("events", {})
        
        cell_h = 50 if self.expanded else 28
        
        for r, week in enumerate(cal):
            for c, day in enumerate(week):
                cell = tk.Frame(self.grid, bg=self.theme["entry"], relief="solid", bd=1,
                               width=cell_w * 8, height=cell_h)
                cell.grid(row=r + 1, column=c, sticky="nsew")
                cell.grid_propagate(False)
                
                if day != 0:
                    key = f"{year}-{month:02d}-{day:02d}"
                    is_today = (year == today.year and month == today.month and day == today.day)
                    is_wknd = c >= 5
                    
                    bg = self.theme["accent"] if is_today else self.theme["entry"]
                    fg = "white" if is_today else ("#E74C3C" if is_wknd else self.theme["text"])
                    
                    tk.Label(cell, text=str(day), bg=bg, fg=fg, font=FONTS["tiny"]).pack(anchor="nw")
                    
                    # Event text - only in expanded mode
                    if self.expanded:
                        txt = tk.Text(cell, height=2, width=8, bg=self.theme["entry"],
                                     fg=self.theme["text_light"], font=FONTS["tiny"], bd=0, wrap="word")
                        txt.pack(fill="both", expand=True, padx=1)
                        txt.insert("1.0", events.get(key, ""))
                        txt.bind("<KeyRelease>", lambda e, k=key, t=txt: self.save_ev(k, t))
                else:
                    cell.config(bg=self.theme["bg"])
    
    def save_ev(self, key, txt):
        if "events" not in self.app.data:
            self.app.data["events"] = {}
        text = txt.get("1.0", "end-1c").strip()
        if text:
            self.app.data["events"][key] = text
        elif key in self.app.data["events"]:
            del self.app.data["events"][key]
        self.app.save()
    
    def prev_m(self):
        self.date = self.date.replace(day=1) - timedelta(days=1)
        self.render()
    
    def next_m(self):
        self.date = self.date.replace(day=28) + timedelta(days=4)
        self.date = self.date.replace(day=1)
        self.render()
    
    def go_today(self):
        self.date = datetime.now()
        self.render()
    
    def on_mode_change(self):
        self.render()
    
    def apply_theme(self):
        super().apply_theme()
        self.scroll.set_bg(self.theme["bg"])
        self.render()


# ============== TODO ==============
class TodoWidget(BaseWidget):
    def __init__(self, master, app):
        super().__init__(master, "✅ To-Do", "todo", app)
        self.build()
    
    def build(self):
        # Add task - compact
        add = tk.Frame(self.content, bg=self.theme["bg"])
        add.pack(fill="x", pady=3)
        
        self.entry = tk.Entry(add, bg=self.theme["entry"], fg=self.theme["text"],
                             font=FONTS["small"], bd=1, relief="solid")
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 3))
        self.entry.bind("<Return>", self.add_task)
        
        tk.Button(add, text="+", command=self.add_task, bg=self.theme["accent"],
                 fg="white", font=FONTS["small"], bd=0, padx=6, cursor="hand2").pack(side="right")
        
        # Priority frame - only in expanded
        self.pri_frame = tk.Frame(self.content, bg=self.theme["bg"])
        self.priority = tk.StringVar(value="low")
        
        # Filter frame - only in expanded
        self.filt_frame = tk.Frame(self.content, bg=self.theme["bg"])
        self.filter = tk.StringVar(value="all")
        
        # Tasks scroll
        self.scroll = ScrollFrame(self.content, bg=self.theme["bg"])
        self.scroll.pack(fill="both", expand=True)
        self.tasks_fr = self.scroll.inner
        
        # Stats - only in expanded
        self.stats = tk.Label(self.content, bg=self.theme["bg"], fg=self.theme["text_light"], font=FONTS["tiny"])
        
        self.load()
    
    def load(self):
        for w in self.tasks_fr.winfo_children():
            w.destroy()
        
        # Show/hide expanded elements
        if self.expanded:
            # Priority buttons
            self.pri_frame.pack(fill="x", pady=2, before=self.scroll)
            for w in self.pri_frame.winfo_children():
                w.destroy()
            for sym, lvl in [("🔴", "high"), ("🟡", "med"), ("🟢", "low")]:
                tk.Radiobutton(self.pri_frame, text=sym, variable=self.priority, value=lvl,
                              bg=self.theme["bg"], font=("Segoe UI", 10), indicatoron=False,
                              selectcolor=self.theme["button"]).pack(side="left", padx=2)
            
            # Filter buttons
            self.filt_frame.pack(fill="x", pady=2, before=self.scroll)
            for w in self.filt_frame.winfo_children():
                w.destroy()
            for txt, val in [("All", "all"), ("Active", "active"), ("Done", "done")]:
                tk.Radiobutton(self.filt_frame, text=txt, variable=self.filter, value=val,
                              bg=self.theme["button"], fg=self.theme["text"], font=FONTS["tiny"],
                              indicatoron=False, selectcolor=self.theme["accent"],
                              command=self.load, padx=5).pack(side="left", padx=1)
            
            self.stats.pack(fill="x", pady=2)
        else:
            self.pri_frame.pack_forget()
            self.filt_frame.pack_forget()
            self.stats.pack_forget()
        
        tasks = self.app.data.get("todos", [])
        ftype = self.filter.get() if self.expanded else "all"
        
        done_count = sum(1 for t in tasks if t.get("done"))
        
        for task in tasks:
            if ftype == "active" and task.get("done"):
                continue
            if ftype == "done" and not task.get("done"):
                continue
            self._task_row(task, tasks.index(task))
        
        if self.expanded:
            self.stats.config(text=f"📊 {done_count}/{len(tasks)} done")
    
    def _task_row(self, task, idx):
        row = tk.Frame(self.tasks_fr, bg=self.theme["entry"], pady=3)
        row.pack(fill="x", pady=1, padx=1)
        
        # Priority icon only in expanded mode
        if self.expanded:
            icons = {"high": "🔴", "med": "🟡", "low": "🟢"}
            tk.Label(row, text=icons.get(task.get("priority", "low"), "●"),
                    bg=self.theme["entry"], font=("Segoe UI", 9)).pack(side="left", padx=2)
        
        var = tk.BooleanVar(value=task.get("done", False))
        tk.Checkbutton(row, variable=var, bg=self.theme["entry"],
                      command=lambda: self.toggle(idx, var.get())).pack(side="left")
        
        fg = self.theme["text_light"] if task.get("done") else self.theme["text"]
        font = ("Segoe UI", 9, "overstrike") if task.get("done") else FONTS["small"]
        tk.Label(row, text=task.get("text", "")[:25], bg=self.theme["entry"],
                fg=fg, font=font, anchor="w").pack(side="left", fill="x", expand=True, padx=3)
        
        del_btn = tk.Label(row, text="✕", bg=self.theme["entry"], fg="#E74C3C",
                          font=FONTS["tiny"], cursor="hand2")
        del_btn.pack(side="right", padx=2)
        del_btn.bind("<Button-1>", lambda e: self.delete(idx))
    
    def add_task(self, e=None):
        text = self.entry.get().strip()
        if text:
            if "todos" not in self.app.data:
                self.app.data["todos"] = []
            self.app.data["todos"].append({
                "text": text, "done": False,
                "priority": self.priority.get() if self.expanded else "low"
            })
            self.app.save()
            self.entry.delete(0, "end")
            self.load()
    
    def toggle(self, idx, done):
        if idx < len(self.app.data.get("todos", [])):
            self.app.data["todos"][idx]["done"] = done
            self.app.save()
            self.load()
    
    def delete(self, idx):
        if idx < len(self.app.data.get("todos", [])):
            del self.app.data["todos"][idx]
            self.app.save()
            self.load()
    
    def on_mode_change(self):
        self.load()
    
    def apply_theme(self):
        super().apply_theme()
        self.scroll.set_bg(self.theme["bg"])
        self.load()


# ============== DAY PLANNER ==============
class DayPlannerWidget(BaseWidget):
    def __init__(self, master, app):
        super().__init__(master, "📆 Day", "day_planner", app)
        self.date = datetime.now().strftime("%Y-%m-%d")
        self.entries = {}
        self.build()
    
    def build(self):
        # Nav
        nav = tk.Frame(self.content, bg=self.theme["bg"])
        nav.pack(fill="x", pady=3)
        
        tk.Button(nav, text="◀", command=self.prev_d, bg=self.theme["button"],
                 fg=self.theme["text"], font=FONTS["tiny"], bd=0, padx=5, cursor="hand2").pack(side="left")
        
        self.date_lbl = tk.Label(nav, bg=self.theme["bg"], fg=self.theme["text"], font=FONTS["small"])
        self.date_lbl.pack(side="left", fill="x", expand=True)
        
        self.today_btn = tk.Button(nav, text="Today", command=self.go_today, bg=self.theme["accent"],
                                   fg="white", font=FONTS["tiny"], bd=0, padx=4, cursor="hand2")
        
        tk.Button(nav, text="▶", command=self.next_d, bg=self.theme["button"],
                 fg=self.theme["text"], font=FONTS["tiny"], bd=0, padx=5, cursor="hand2").pack(side="right")
        
        # Time slots scroll
        self.scroll = ScrollFrame(self.content, bg=self.theme["bg"])
        self.scroll.pack(fill="both", expand=True)
        
        # Create time slots
        start_h = 6 if not self.expanded else 5
        end_h = 22 if not self.expanded else 24
        
        for h in range(start_h, end_h):
            row = tk.Frame(self.scroll.inner, bg=self.theme["bg"])
            row.pack(fill="x", pady=1)
            
            lbl = tk.Label(row, text=f"{h:02d}", bg=self.theme["header"],
                          fg=self.theme["text"], font=FONTS["tiny"], width=3)
            lbl.pack(side="left", padx=(0, 2))
            
            entry = tk.Entry(row, bg=self.theme["entry"], fg=self.theme["text"],
                           font=FONTS["tiny"], bd=1, relief="solid")
            entry.pack(side="left", fill="x", expand=True)
            entry.bind("<KeyRelease>", lambda e, hr=h: self.save_slot(hr))
            
            self.entries[h] = {"entry": entry, "label": lbl}
        
        self.load_data()
    
    def load_data(self):
        data = self.app.data.get("day_planner", {}).get(self.date, {})
        dt = datetime.strptime(self.date, "%Y-%m-%d")
        
        if self.expanded:
            self.date_lbl.config(text=dt.strftime("%A, %b %d"))
            self.today_btn.pack(side="right", padx=2)
        else:
            self.date_lbl.config(text=dt.strftime("%b %d"))
            self.today_btn.pack_forget()
        
        now_h = datetime.now().hour
        is_today = self.date == datetime.now().strftime("%Y-%m-%d")
        
        for h, w in self.entries.items():
            w["entry"].delete(0, "end")
            if str(h) in data:
                w["entry"].insert(0, data[str(h)])
            
            bg = self.theme["accent"] if (h == now_h and is_today) else self.theme["header"]
            fg = "white" if (h == now_h and is_today) else self.theme["text"]
            w["label"].config(bg=bg, fg=fg)
    
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
        self.app.save()
    
    def prev_d(self):
        self.date = (datetime.strptime(self.date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        self.load_data()
    
    def next_d(self):
        self.date = (datetime.strptime(self.date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        self.load_data()
    
    def go_today(self):
        self.date = datetime.now().strftime("%Y-%m-%d")
        self.load_data()
    
    def on_mode_change(self):
        self.load_data()
    
    def apply_theme(self):
        super().apply_theme()
        self.scroll.set_bg(self.theme["bg"])
        self.load_data()


# ============== WEEK PLANNER ==============
class WeekPlannerWidget(BaseWidget):
    def __init__(self, master, app):
        super().__init__(master, "📋 Week", "week_planner", app)
        self.week_start = datetime.now() - timedelta(days=datetime.now().weekday())
        self.day_widgets = {}
        self.build()
    
    def build(self):
        # Nav
        nav = tk.Frame(self.content, bg=self.theme["bg"])
        nav.pack(fill="x", pady=3)
        
        tk.Button(nav, text="◀", command=self.prev_w, bg=self.theme["button"],
                 fg=self.theme["text"], font=FONTS["tiny"], bd=0, padx=5, cursor="hand2").pack(side="left")
        
        self.week_lbl = tk.Label(nav, bg=self.theme["bg"], fg=self.theme["text"], font=FONTS["small"])
        self.week_lbl.pack(side="left", fill="x", expand=True)
        
        tk.Button(nav, text="▶", command=self.next_w, bg=self.theme["button"],
                 fg=self.theme["text"], font=FONTS["tiny"], bd=0, padx=5, cursor="hand2").pack(side="right")
        
        # Days scroll - HORIZONTAL
        self.scroll = ScrollFrame(self.content, bg=self.theme["bg"])
        self.scroll.pack(fill="both", expand=True)
        
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        col_w = 90 if self.expanded else 65
        
        for i, day in enumerate(days):
            col = tk.Frame(self.scroll.inner, bg=self.theme["entry"], relief="solid", bd=1, width=col_w)
            col.pack(side="left", fill="both", padx=1)
            col.pack_propagate(False)
            
            is_wknd = i >= 5
            hdr = tk.Label(col, text=day[:2] if not self.expanded else day[:3],
                          bg=self.theme["header"], fg="#E74C3C" if is_wknd else self.theme["text"],
                          font=FONTS["tiny"], pady=2)
            hdr.pack(fill="x")
            
            date_lbl = tk.Label(col, text="", bg=self.theme["header"],
                               fg=self.theme["text_light"], font=FONTS["tiny"])
            date_lbl.pack(fill="x")
            
            txt = tk.Text(col, bg=self.theme["entry"], fg=self.theme["text"],
                         font=FONTS["tiny"], bd=0, wrap="word", width=10, height=8)
            txt.pack(fill="both", expand=True, padx=2, pady=2)
            txt.bind("<KeyRelease>", lambda e, idx=i: self.save_day(idx))
            
            self.day_widgets[i] = {"col": col, "header": hdr, "date": date_lbl, "text": txt}
        
        self.load_data()
    
    def load_data(self):
        key = self.week_start.strftime("%Y-%m-%d")
        data = self.app.data.get("week_planner", {}).get(key, {})
        
        end = self.week_start + timedelta(days=6)
        self.week_lbl.config(text=f"{self.week_start.strftime('%b %d')} - {end.strftime('%b %d')}")
        
        today = datetime.now().date()
        
        for i, w in self.day_widgets.items():
            day_date = self.week_start + timedelta(days=i)
            w["date"].config(text=day_date.strftime("%d"))
            
            if day_date.date() == today:
                w["header"].config(bg=self.theme["accent"], fg="white")
                w["date"].config(bg=self.theme["accent"], fg="white")
            else:
                is_wknd = i >= 5
                w["header"].config(bg=self.theme["header"], fg="#E74C3C" if is_wknd else self.theme["text"])
                w["date"].config(bg=self.theme["header"], fg=self.theme["text_light"])
            
            w["text"].delete("1.0", "end")
            if str(i) in data:
                w["text"].insert("1.0", data[str(i)])
    
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
        self.app.save()
    
    def prev_w(self):
        self.week_start -= timedelta(days=7)
        self.load_data()
    
    def next_w(self):
        self.week_start += timedelta(days=7)
        self.load_data()
    
    def on_mode_change(self):
        # Rebuild columns for new size
        for w in self.scroll.inner.winfo_children():
            w.destroy()
        self.day_widgets = {}
        
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        col_w = 90 if self.expanded else 65
        
        for i, day in enumerate(days):
            col = tk.Frame(self.scroll.inner, bg=self.theme["entry"], relief="solid", bd=1, width=col_w)
            col.pack(side="left", fill="both", padx=1)
            col.pack_propagate(False)
            
            is_wknd = i >= 5
            hdr = tk.Label(col, text=day[:2] if not self.expanded else day[:3],
                          bg=self.theme["header"], fg="#E74C3C" if is_wknd else self.theme["text"],
                          font=FONTS["tiny"], pady=2)
            hdr.pack(fill="x")
            
            date_lbl = tk.Label(col, text="", bg=self.theme["header"],
                               fg=self.theme["text_light"], font=FONTS["tiny"])
            date_lbl.pack(fill="x")
            
            txt = tk.Text(col, bg=self.theme["entry"], fg=self.theme["text"],
                         font=FONTS["tiny"], bd=0, wrap="word", width=10, height=8)
            txt.pack(fill="both", expand=True, padx=2, pady=2)
            txt.bind("<KeyRelease>", lambda e, idx=i: self.save_day(idx))
            
            self.day_widgets[i] = {"col": col, "header": hdr, "date": date_lbl, "text": txt}
        
        self.load_data()
    
    def apply_theme(self):
        super().apply_theme()
        self.scroll.set_bg(self.theme["bg"])
        self.load_data()


# ============== MONTHLY PLANNER ==============
class MonthlyPlannerWidget(BaseWidget):
    def __init__(self, master, app):
        super().__init__(master, "🎯 Monthly", "monthly_planner", app)
        self.current = datetime.now()
        self.sections = {}
        self.build()
    
    def build(self):
        # Nav
        nav = tk.Frame(self.content, bg=self.theme["bg"])
        nav.pack(fill="x", pady=3)
        
        tk.Button(nav, text="◀", command=self.prev_m, bg=self.theme["button"],
                 fg=self.theme["text"], font=FONTS["tiny"], bd=0, padx=5, cursor="hand2").pack(side="left")
        
        self.month_lbl = tk.Label(nav, bg=self.theme["bg"], fg=self.theme["text"], font=FONTS["small"])
        self.month_lbl.pack(side="left", fill="x", expand=True)
        
        tk.Button(nav, text="▶", command=self.next_m, bg=self.theme["button"],
                 fg=self.theme["text"], font=FONTS["tiny"], bd=0, padx=5, cursor="hand2").pack(side="right")
        
        # Sections scroll
        self.scroll = ScrollFrame(self.content, bg=self.theme["bg"])
        self.scroll.pack(fill="both", expand=True)
        
        self.render_sections()
    
    def render_sections(self):
        for w in self.scroll.inner.winfo_children():
            w.destroy()
        self.sections = {}
        
        # Different sections based on mode
        if self.expanded:
            secs = [("🎯 Goals", "goals", "#4CAF50"), ("📝 Tasks", "tasks", "#2196F3"),
                    ("💡 Ideas", "ideas", "#FF9800"), ("📊 Review", "review", "#9C27B0")]
        else:
            secs = [("🎯 Goals", "goals", "#4CAF50"), ("📝 Tasks", "tasks", "#2196F3")]
        
        for title, key, color in secs:
            frame = tk.Frame(self.scroll.inner, bg=self.theme["entry"], relief="solid", bd=1)
            frame.pack(fill="x", pady=2)
            
            hdr = tk.Label(frame, text=title, bg=color, fg="white",
                          font=FONTS["tiny"], anchor="w", padx=6, pady=3)
            hdr.pack(fill="x")
            
            height = 3 if self.expanded else 2
            txt = tk.Text(frame, height=height, bg=self.theme["entry"], fg=self.theme["text"],
                         font=FONTS["tiny"], bd=0, wrap="word", padx=4, pady=2)
            txt.pack(fill="x")
            txt.bind("<KeyRelease>", lambda e, k=key: self.save_sec(k))
            
            self.sections[key] = {"text": txt}
        
        self.load_data()
    
    def load_data(self):
        key = self.current.strftime("%Y-%m")
        data = self.app.data.get("monthly", {}).get(key, {})
        
        self.month_lbl.config(text=f"{calendar.month_abbr[self.current.month]} {self.current.year}")
        
        for k, w in self.sections.items():
            w["text"].delete("1.0", "end")
            if k in data:
                w["text"].insert("1.0", data[k])
    
    def save_sec(self, key):
        if "monthly" not in self.app.data:
            self.app.data["monthly"] = {}
        mkey = self.current.strftime("%Y-%m")
        if mkey not in self.app.data["monthly"]:
            self.app.data["monthly"][mkey] = {}
        
        text = self.sections[key]["text"].get("1.0", "end-1c")
        if text.strip():
            self.app.data["monthly"][mkey][key] = text
        elif key in self.app.data["monthly"][mkey]:
            del self.app.data["monthly"][mkey][key]
        self.app.save()
    
    def prev_m(self):
        self.current = self.current.replace(day=1) - timedelta(days=1)
        self.load_data()
    
    def next_m(self):
        self.current = self.current.replace(day=28) + timedelta(days=4)
        self.current = self.current.replace(day=1)
        self.load_data()
    
    def on_mode_change(self):
        self.render_sections()
    
    def apply_theme(self):
        super().apply_theme()
        self.scroll.set_bg(self.theme["bg"])
        self.render_sections()


# ============== STICKY NOTES ==============
class StickyNotesWidget(BaseWidget):
    def __init__(self, master, app):
        super().__init__(master, "📝 Notes", "sticky_notes", app)
        self.colors = ["#FFFFA5", "#A5FFFA", "#FFA5FF", "#A5FFA5", "#FFA5A5", "#A5A5FF"]
        self.build()
    
    def build(self):
        # Add buttons
        add = tk.Frame(self.content, bg=self.theme["bg"])
        add.pack(fill="x", pady=3)
        
        tk.Label(add, text="Add:", bg=self.theme["bg"], fg=self.theme["text"],
                font=FONTS["tiny"]).pack(side="left", padx=2)
        
        for c in self.colors[:4] if not self.expanded else self.colors:
            tk.Button(add, text=" ", bg=c, bd=1, width=2,
                     command=lambda col=c: self.add_note(col), cursor="hand2").pack(side="left", padx=1)
        
        # Notes scroll
        self.scroll = ScrollFrame(self.content, bg=self.theme["bg"])
        self.scroll.pack(fill="both", expand=True)
        self.notes_fr = self.scroll.inner
        
        self.load()
    
    def load(self):
        for w in self.notes_fr.winfo_children():
            w.destroy()
        
        notes = self.app.data.get("notes", [])
        cols = 2 if self.expanded else 1
        note_w = 120 if self.expanded else 200
        note_h = 80 if self.expanded else 60
        
        row, col = 0, 0
        for i, note in enumerate(notes):
            self._note(i, note, row, col, note_w, note_h)
            col += 1
            if col >= cols:
                col = 0
                row += 1
    
    def _note(self, idx, note, row, col, w, h):
        color = note.get("color", "#FFFFA5")
        
        frame = tk.Frame(self.notes_fr, bg=color, relief="raised", bd=1, width=w, height=h)
        frame.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
        frame.grid_propagate(False)
        
        del_btn = tk.Label(frame, text="✕", bg=color, fg="#666", font=FONTS["tiny"], cursor="hand2")
        del_btn.pack(anchor="ne", padx=1)
        del_btn.bind("<Button-1>", lambda e: self.delete_note(idx))
        
        txt = tk.Text(frame, height=3, bg=color, fg="#333", font=FONTS["tiny"], bd=0, wrap="word")
        txt.pack(fill="both", expand=True, padx=3, pady=1)
        txt.insert("1.0", note.get("text", ""))
        txt.bind("<KeyRelease>", lambda e, i=idx, t=txt: self.save_note(i, t))
    
    def add_note(self, color):
        if "notes" not in self.app.data:
            self.app.data["notes"] = []
        self.app.data["notes"].append({"text": "", "color": color})
        self.app.save()
        self.load()
    
    def save_note(self, idx, txt):
        if idx < len(self.app.data.get("notes", [])):
            self.app.data["notes"][idx]["text"] = txt.get("1.0", "end-1c")
            self.app.save()
    
    def delete_note(self, idx):
        if idx < len(self.app.data.get("notes", [])):
            del self.app.data["notes"][idx]
            self.app.save()
            self.load()
    
    def on_mode_change(self):
        self.load()
    
    def apply_theme(self):
        super().apply_theme()
        self.scroll.set_bg(self.theme["bg"])
        self.load()


# ============== POMODORO ==============
class PomodoroWidget(BaseWidget):
    def __init__(self, master, app):
        super().__init__(master, "🍅 Pomodoro", "pomodoro", app)
        self.work = 25 * 60
        self.brk = 5 * 60
        self.long_brk = 15 * 60
        self.time = self.work
        self.running = False
        self.is_work = True
        self.sessions = 0
        self.build()
    
    def build(self):
        # Timer
        self.timer_lbl = tk.Label(self.content, text="25:00", bg=self.theme["bg"],
                                  fg=self.theme["accent"], font=FONTS["timer"])
        self.timer_lbl.pack(pady=8)
        
        # Status
        self.status_lbl = tk.Label(self.content, text="🍅 Work", bg=self.theme["bg"],
                                   fg=self.theme["text"], font=FONTS["small"])
        self.status_lbl.pack()
        
        # Sessions (compact)
        self.sess_lbl = tk.Label(self.content, text="", bg=self.theme["bg"],
                                 fg=self.theme["text_light"], font=FONTS["tiny"])
        self.sess_lbl.pack(pady=2)
        
        # Controls
        ctrl = tk.Frame(self.content, bg=self.theme["bg"])
        ctrl.pack(pady=8)
        
        self.start_btn = tk.Button(ctrl, text="▶", command=self.toggle, bg=self.theme["accent"],
                                   fg="white", font=FONTS["small"], bd=0, padx=12, cursor="hand2")
        self.start_btn.pack(side="left", padx=3)
        
        tk.Button(ctrl, text="↺", command=self.reset, bg=self.theme["button"],
                 fg=self.theme["text"], font=FONTS["small"], bd=0, padx=12, cursor="hand2").pack(side="left", padx=3)
        
        tk.Button(ctrl, text="⏭", command=self.skip, bg=self.theme["button"],
                 fg=self.theme["text"], font=FONTS["small"], bd=0, padx=12, cursor="hand2").pack(side="left", padx=3)
        
        # Settings frame (expanded only)
        self.settings_fr = tk.LabelFrame(self.content, text="⚙️ Settings", bg=self.theme["bg"],
                                         fg=self.theme["text"], font=FONTS["tiny"])
        
        # Stats frame (expanded only)
        self.stats_fr = tk.LabelFrame(self.content, text="📊 Focus Stats", bg=self.theme["bg"],
                                      fg=self.theme["text"], font=FONTS["tiny"])
        
        self.stats_labels = {}
        
        self.update_display()
        self.on_mode_change()
    
    def on_mode_change(self):
        if self.expanded:
            # Show settings
            self.settings_fr.pack(fill="x", pady=5, padx=5)
            for w in self.settings_fr.winfo_children():
                w.destroy()
            
            for txt, attr, default in [("Work:", "work", 25), ("Break:", "brk", 5), ("Long:", "long_brk", 15)]:
                row = tk.Frame(self.settings_fr, bg=self.theme["bg"])
                row.pack(fill="x", padx=5, pady=1)
                tk.Label(row, text=txt, bg=self.theme["bg"], fg=self.theme["text"],
                        font=FONTS["tiny"], width=5).pack(side="left")
                spin = tk.Spinbox(row, from_=1, to=60, width=4, font=FONTS["tiny"])
                spin.pack(side="left")
                spin.delete(0, "end")
                spin.insert(0, str(default))
                setattr(self, f"{attr}_spin", spin)
            
            # Show stats
            self.stats_fr.pack(fill="x", pady=5, padx=5)
            for w in self.stats_fr.winfo_children():
                w.destroy()
            
            for txt, key in [("Today:", "today"), ("Week:", "week"), ("Month:", "month")]:
                row = tk.Frame(self.stats_fr, bg=self.theme["bg"])
                row.pack(fill="x", padx=5, pady=1)
                tk.Label(row, text=txt, bg=self.theme["bg"], fg=self.theme["text"],
                        font=FONTS["tiny"], width=6).pack(side="left")
                lbl = tk.Label(row, text="0m", bg=self.theme["bg"], fg=self.theme["accent"],
                              font=FONTS["tiny"])
                lbl.pack(side="left")
                self.stats_labels[key] = lbl
            
            self.update_stats()
        else:
            self.settings_fr.pack_forget()
            self.stats_fr.pack_forget()
    
    def toggle(self):
        if self.running:
            self.running = False
            self.start_btn.config(text="▶", bg=self.theme["accent"])
        else:
            # Load settings if expanded
            if self.expanded:
                try:
                    self.work = int(self.work_spin.get()) * 60
                    self.brk = int(self.brk_spin.get()) * 60
                    self.long_brk = int(self.long_brk_spin.get()) * 60
                except:
                    pass
            
            self.running = True
            self.start_btn.config(text="⏸", bg="#FF9800")
            self.tick()
    
    def tick(self):
        if self.running and self.time > 0:
            m, s = divmod(self.time, 60)
            self.timer_lbl.config(text=f"{m:02d}:{s:02d}")
            self.time -= 1
            
            if self.is_work:
                self.add_focus(1)
            
            self.win.after(1000, self.tick)
        elif self.running:
            self.complete()
    
    def complete(self):
        try:
            import winsound
            winsound.MessageBeep()
        except:
            pass
        
        if self.is_work:
            self.sessions += 1
            self.add_session()
            
            if self.sessions % 4 == 0:
                self.time = self.long_brk
                self.status_lbl.config(text="☕ Long Break")
            else:
                self.time = self.brk
                self.status_lbl.config(text="☕ Break")
            self.is_work = False
        else:
            self.time = self.work
            self.status_lbl.config(text="🍅 Work")
            self.is_work = True
        
        self.update_display()
        self.tick()
    
    def skip(self):
        if self.is_work:
            self.time = self.brk
            self.status_lbl.config(text="☕ Break")
            self.is_work = False
        else:
            self.time = self.work
            self.status_lbl.config(text="🍅 Work")
            self.is_work = True
        self.update_display()
    
    def reset(self):
        self.running = False
        self.is_work = True
        self.time = self.work
        self.status_lbl.config(text="🍅 Work")
        self.start_btn.config(text="▶", bg=self.theme["accent"])
        self.update_display()
    
    def update_display(self):
        m, s = divmod(self.time, 60)
        self.timer_lbl.config(text=f"{m:02d}:{s:02d}")
        self.sess_lbl.config(text=f"Sessions: {self.sessions}")
    
    def add_focus(self, secs):
        if "pomo_stats" not in self.app.data:
            self.app.data["pomo_stats"] = {}
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.app.data["pomo_stats"]:
            self.app.data["pomo_stats"][today] = {"secs": 0, "sessions": 0}
        self.app.data["pomo_stats"][today]["secs"] += secs
        
        if self.app.data["pomo_stats"][today]["secs"] % 60 == 0:
            self.app.save()
            if self.expanded:
                self.update_stats()
    
    def add_session(self):
        if "pomo_stats" not in self.app.data:
            self.app.data["pomo_stats"] = {}
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.app.data["pomo_stats"]:
            self.app.data["pomo_stats"][today] = {"secs": 0, "sessions": 0}
        self.app.data["pomo_stats"][today]["sessions"] += 1
        self.app.save()
    
    def update_stats(self):
        stats = self.app.data.get("pomo_stats", {})
        now = datetime.now()
        
        # Today
        today = now.strftime("%Y-%m-%d")
        today_secs = stats.get(today, {}).get("secs", 0)
        self.stats_labels["today"].config(text=self.fmt_time(today_secs))
        
        # Week
        week_secs = 0
        for i in range(7):
            day = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            week_secs += stats.get(day, {}).get("secs", 0)
        self.stats_labels["week"].config(text=self.fmt_time(week_secs))
        
        # Month
        month_secs = 0
        for d, s in stats.items():
            if d.startswith(now.strftime("%Y-%m")):
                month_secs += s.get("secs", 0)
        self.stats_labels["month"].config(text=self.fmt_time(month_secs))
    
    def fmt_time(self, secs):
        if secs < 60:
            return f"{secs}s"
        elif secs < 3600:
            return f"{secs // 60}m"
        else:
            return f"{secs // 3600}h {(secs % 3600) // 60}m"
    
    def apply_theme(self):
        super().apply_theme()
        self.timer_lbl.config(bg=self.theme["bg"], fg=self.theme["accent"])
        self.status_lbl.config(bg=self.theme["bg"], fg=self.theme["text"])
        self.sess_lbl.config(bg=self.theme["bg"], fg=self.theme["text_light"])


# ============== HABIT TRACKER ==============
class HabitTrackerWidget(BaseWidget):
    def __init__(self, master, app):
        super().__init__(master, "📊 Habits", "habit_tracker", app)
        self.build()
    
    def build(self):
        # Add
        add = tk.Frame(self.content, bg=self.theme["bg"])
        add.pack(fill="x", pady=3)
        
        self.entry = tk.Entry(add, bg=self.theme["entry"], fg=self.theme["text"],
                             font=FONTS["tiny"], bd=1, relief="solid")
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 3))
        self.entry.bind("<Return>", self.add_habit)
        
        tk.Button(add, text="+", command=self.add_habit, bg=self.theme["accent"],
                 fg="white", font=FONTS["tiny"], bd=0, padx=5, cursor="hand2").pack(side="right")
        
        # Habits scroll
        self.scroll = ScrollFrame(self.content, bg=self.theme["bg"])
        self.scroll.pack(fill="both", expand=True)
        self.habits_fr = self.scroll.inner
        
        self.load()
    
    def get_week(self):
        today = datetime.now()
        return (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
    
    def load(self):
        for w in self.habits_fr.winfo_children():
            w.destroy()
        
        habits = self.app.data.get("habits", [])
        wk = self.get_week()
        
        # Header
        days = ["M", "T", "W", "T", "F", "S", "S"] if not self.expanded else ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        name_w = 12 if self.expanded else 8
        
        tk.Label(self.habits_fr, text="Habit", bg=self.theme["bg"], fg=self.theme["text"],
                font=FONTS["tiny"], width=name_w, anchor="w").grid(row=0, column=0, padx=2, pady=2)
        
        for c, d in enumerate(days):
            tk.Label(self.habits_fr, text=d, bg=self.theme["header"], fg=self.theme["text"],
                    font=FONTS["tiny"], width=3).grid(row=0, column=c + 1, padx=1, pady=2)
        
        for i, habit in enumerate(habits):
            self._habit_row(i, habit, wk, name_w)
    
    def _habit_row(self, idx, habit, wk, name_w):
        row = idx + 1
        
        name = habit["name"][:name_w - 2] if len(habit["name"]) > name_w - 2 else habit["name"]
        tk.Label(self.habits_fr, text=name, bg=self.theme["entry"], fg=self.theme["text"],
                font=FONTS["tiny"], width=name_w, anchor="w").grid(row=row, column=0, padx=2, pady=1)
        
        checked = habit.get("checked", {}).get(wk, [False] * 7)
        while len(checked) < 7:
            checked.append(False)
        
        for d in range(7):
            var = tk.BooleanVar(value=checked[d])
            tk.Checkbutton(self.habits_fr, variable=var, bg=self.theme["entry"],
                          command=lambda i=idx, day=d, v=var: self.toggle_day(i, day, v.get())
                          ).grid(row=row, column=d + 1, padx=1, pady=1)
        
        del_btn = tk.Label(self.habits_fr, text="✕", bg=self.theme["bg"], fg="#E74C3C",
                          font=FONTS["tiny"], cursor="hand2")
        del_btn.grid(row=row, column=8, padx=2)
        del_btn.bind("<Button-1>", lambda e: self.delete_habit(idx))
    
    def add_habit(self, e=None):
        name = self.entry.get().strip()
        if name:
            if "habits" not in self.app.data:
                self.app.data["habits"] = []
            self.app.data["habits"].append({"name": name, "checked": {}})
            self.app.save()
            self.entry.delete(0, "end")
            self.load()
    
    def toggle_day(self, idx, day, checked):
        if idx < len(self.app.data.get("habits", [])):
            wk = self.get_week()
            habit = self.app.data["habits"][idx]
            if "checked" not in habit:
                habit["checked"] = {}
            if wk not in habit["checked"]:
                habit["checked"][wk] = [False] * 7
            habit["checked"][wk][day] = checked
            self.app.save()
    
    def delete_habit(self, idx):
        if idx < len(self.app.data.get("habits", [])):
            del self.app.data["habits"][idx]
            self.app.save()
            self.load()
    
    def on_mode_change(self):
        self.load()
    
    def apply_theme(self):
        super().apply_theme()
        self.scroll.set_bg(self.theme["bg"])
        self.load()


# ============== CLOCK ==============
class ClockWidget(BaseWidget):
    def __init__(self, master, app):
        super().__init__(master, "🕐 Clock", "clock", app)
        self.build()
        self.tick()
    
    def build(self):
        self.time_lbl = tk.Label(self.content, text="", bg=self.theme["bg"],
                                 fg=self.theme["accent"], font=FONTS["clock"])
        self.time_lbl.pack(expand=True, pady=5)
        
        self.date_lbl = tk.Label(self.content, text="", bg=self.theme["bg"],
                                 fg=self.theme["text"], font=FONTS["small"])
        self.date_lbl.pack(pady=(0, 5))
    
    def tick(self):
        now = datetime.now()
        self.time_lbl.config(text=now.strftime("%H:%M:%S"))
        if self.expanded:
            self.date_lbl.config(text=now.strftime("%A, %B %d, %Y"))
        else:
            self.date_lbl.config(text=now.strftime("%b %d"))
        self.win.after(1000, self.tick)
    
    def apply_theme(self):
        super().apply_theme()
        self.time_lbl.config(bg=self.theme["bg"], fg=self.theme["accent"])
        self.date_lbl.config(bg=self.theme["bg"], fg=self.theme["text"])


# ============== MAIN APP ==============
class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        
        # Initialize desktop layer
        print("Initializing desktop layer...")
        DesktopWallpaperLayer.initialize()
        
        self.load()
        self.widgets = {}
        self.create_widgets()
        self.create_panel()
    
    def load(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except:
                self.data = {}
        else:
            self.data = {}
    
    def save(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def create_widgets(self):
        hidden = self.data.get("hidden", [])
        
        classes = {
            "calendar": CalendarWidget, "todo": TodoWidget, "day_planner": DayPlannerWidget,
            "week_planner": WeekPlannerWidget, "monthly_planner": MonthlyPlannerWidget,
            "sticky_notes": StickyNotesWidget, "pomodoro": PomodoroWidget,
            "habit_tracker": HabitTrackerWidget, "clock": ClockWidget
        }
        
        for wid, cls in classes.items():
            self.widgets[wid] = cls(self.root, self)
            if wid in hidden:
                self.widgets[wid].win.withdraw()
    
    def create_panel(self):
        self.panel = tk.Toplevel(self.root)
        self.panel.title("🎮 Widgets")
        self.panel.geometry("260x480")
        self.panel.resizable(False, False)
        self.panel.attributes('-topmost', True)
        
        theme = THEMES.get(self.data.get("theme", "🌊 Blue"))
        self.panel.configure(bg=theme["bg"])
        
        # Title
        tk.Label(self.panel, text="🖥️ Desktop Widgets", bg=theme["header"],
                fg=theme["text"], font=("Segoe UI Semibold", 12), pady=10).pack(fill="x")
        
        # Info
        tk.Label(self.panel, text="✅ Embedded in desktop!\n📐 Resize for more features",
                bg=theme["bg"], fg=theme["text_light"], font=FONTS["tiny"],
                pady=6).pack(fill="x", padx=10)
        
        # Autostart
        auto = tk.Frame(self.panel, bg=theme["bg"])
        auto.pack(fill="x", padx=10, pady=5)
        
        self.auto_var = tk.BooleanVar(value=is_autostart_enabled())
        tk.Checkbutton(auto, text="🚀 Start with Windows", variable=self.auto_var,
                      bg=theme["bg"], fg=theme["text"], font=FONTS["small"],
                      selectcolor=theme["entry"], command=self.toggle_auto).pack(anchor="w")
        
        # Widgets
        wframe = tk.LabelFrame(self.panel, text="📦 Widgets", bg=theme["bg"],
                              fg=theme["text"], font=FONTS["small"])
        wframe.pack(fill="x", padx=10, pady=5)
        
        names = {
            "calendar": "📅 Calendar", "todo": "✅ To-Do", "day_planner": "📆 Day",
            "week_planner": "📋 Week", "monthly_planner": "🎯 Monthly",
            "sticky_notes": "📝 Notes", "pomodoro": "🍅 Pomodoro",
            "habit_tracker": "📊 Habits", "clock": "🕐 Clock"
        }
        
        self.widget_vars = {}
        hidden = self.data.get("hidden", [])
        
        for wid, name in names.items():
            var = tk.BooleanVar(value=wid not in hidden)
            self.widget_vars[wid] = var
            tk.Checkbutton(wframe, text=name, variable=var, bg=theme["bg"],
                          fg=theme["text"], font=FONTS["small"], selectcolor=theme["entry"],
                          command=lambda w=wid: self.toggle_widget(w)).pack(anchor="w", padx=8)
        
        # Buttons
        btns = tk.Frame(self.panel, bg=theme["bg"])
        btns.pack(fill="x", padx=10, pady=8)
        
        tk.Button(btns, text="Show All", command=self.show_all, bg=theme["button"],
                 fg=theme["text"], font=FONTS["tiny"], bd=0, padx=10, cursor="hand2").pack(side="left", padx=3)
        tk.Button(btns, text="Hide All", command=self.hide_all, bg=theme["button"],
                 fg=theme["text"], font=FONTS["tiny"], bd=0, padx=10, cursor="hand2").pack(side="left", padx=3)
        
        # Exit
        tk.Button(self.panel, text="❌ Exit", command=self.exit_app, bg="#E74C3C",
                 fg="white", font=FONTS["small"], bd=0, padx=15, pady=5, cursor="hand2").pack(pady=10)
        
        self.panel.protocol("WM_DELETE_WINDOW", lambda: self.panel.iconify())
    
    def toggle_auto(self):
        if self.auto_var.get():
            enable_autostart()
        else:
            disable_autostart()
    
    def update_panel(self):
        hidden = self.data.get("hidden", [])
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
        self.save()
        self.root.quit()
        self.root.destroy()
        sys.exit()
    
    def run(self):
        self.root.mainloop()


# ============== START ==============
if __name__ == "__main__":
    app = App()
    app.run()
