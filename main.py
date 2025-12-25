"""
Desktop Widgets Pro for Windows 11
FIXED: Widgets stay visible during "Show Desktop" gesture (3-finger swipe)
Widgets are embedded into the desktop layer!
"""

import tkinter as tk
from tkinter import ttk, messagebox
import calendar
from datetime import datetime, timedelta
import json
import os
import ctypes
from ctypes import wintypes
import sys
import winreg

# ============== WINDOWS API SETUP ==============
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Constants
GWL_EXSTYLE = -20
GWL_STYLE = -16
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOPMOST = 0x00000008
HWND_BOTTOM = 1
HWND_TOPMOST = -1
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
GW_HWNDPREV = 3
GA_ROOT = 2

# For finding desktop window
EnumWindows = user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
GetClassName = user32.GetClassNameW
FindWindow = user32.FindWindowW
FindWindowEx = user32.FindWindowExW
SendMessageTimeout = user32.SendMessageTimeoutW
SetParent = user32.SetParent
GetParent = user32.GetParent
SetWindowLong = user32.SetWindowLongW
GetWindowLong = user32.GetWindowLongW
SetWindowPos = user32.SetWindowPos
ShowWindow = user32.ShowWindow
GetWindowRect = user32.GetWindowRect
IsIconic = user32.IsIconic
GetForegroundWindow = user32.GetForegroundWindow

# ============== PATHS ==============
if getattr(sys, 'frozen', False):
    APP_PATH = sys.executable
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_PATH = os.path.abspath(__file__)
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(os.path.expanduser("~"), "desktop_widgets_pro_data.json")
STARTUP_FOLDER = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
SHORTCUT_NAME = "DesktopWidgetsPro.bat"
SHORTCUT_PATH = os.path.join(STARTUP_FOLDER, SHORTCUT_NAME)

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

# ============== FONTS ==============
FONTS = {
    "title": ("Segoe UI Semibold", 12),
    "header": ("Segoe UI Semibold", 11),
    "normal": ("Segoe UI", 10),
    "small": ("Segoe UI", 9),
    "tiny": ("Segoe UI", 8),
    "button": ("Segoe UI Semibold", 9),
    "icon": ("Segoe UI", 12),
    "clock": ("Segoe UI Light", 32),
    "clock_date": ("Segoe UI", 11),
}


# ============== DESKTOP INTEGRATION ==============
class DesktopIntegration:
    """Handles embedding widgets into the Windows desktop layer"""
    
    workerw = None
    
    @staticmethod
    def get_workerw():
        """Find the WorkerW window that hosts the desktop wallpaper"""
        if DesktopIntegration.workerw:
            return DesktopIntegration.workerw
        
        progman = FindWindow("Progman", None)
        if not progman:
            return None
        
        # Send message to spawn WorkerW
        result = ctypes.c_ulong()
        SendMessageTimeout(progman, 0x052C, 0, 0, 0x0000, 1000, ctypes.byref(result))
        
        workerw = None
        
        def enum_callback(hwnd, lparam):
            nonlocal workerw
            shell = FindWindowEx(hwnd, None, "SHELLDLL_DefView", None)
            if shell:
                workerw = FindWindowEx(None, hwnd, "WorkerW", None)
            return True
        
        EnumWindows(EnumWindowsProc(enum_callback), 0)
        
        DesktopIntegration.workerw = workerw
        return workerw
    
    @staticmethod
    def embed_to_desktop(hwnd):
        """Embed a window into the desktop layer"""
        try:
            workerw = DesktopIntegration.get_workerw()
            if workerw:
                # Set parent to WorkerW
                SetParent(hwnd, workerw)
                return True
            else:
                # Fallback: Set parent to Progman
                progman = FindWindow("Progman", None)
                if progman:
                    SetParent(hwnd, progman)
                    return True
        except Exception as e:
            print(f"Desktop embed error: {e}")
        return False
    
    @staticmethod
    def set_desktop_style(hwnd):
        """Set window styles for desktop integration"""
        try:
            # Remove from taskbar and alt-tab
            ex_style = GetWindowLong(hwnd, GWL_EXSTYLE)
            ex_style |= WS_EX_TOOLWINDOW
            ex_style |= WS_EX_NOACTIVATE
            SetWindowLong(hwnd, GWL_EXSTYLE, ex_style)
            return True
        except:
            return False


# ============== AUTOSTART FUNCTIONS ==============
def is_autostart_enabled():
    if os.path.exists(SHORTCUT_PATH):
        return True
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                            r"Software\Microsoft\Windows\CurrentVersion\Run",
                            0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, "DesktopWidgetsPro")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except:
        return False


def enable_autostart():
    success = False
    try:
        batch_content = f'@echo off\nstart "" "{APP_PATH}"\n'
        with open(SHORTCUT_PATH, 'w') as f:
            f.write(batch_content)
        success = True
    except Exception as e:
        print(f"Startup folder method failed: {e}")
    
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Run",
                            0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "DesktopWidgetsPro", 0, winreg.REG_SZ, f'"{APP_PATH}"')
        winreg.CloseKey(key)
        success = True
    except Exception as e:
        print(f"Registry method failed: {e}")
    
    return success


def disable_autostart():
    try:
        if os.path.exists(SHORTCUT_PATH):
            os.remove(SHORTCUT_PATH)
    except:
        pass
    
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Run",
                            0, winreg.KEY_SET_VALUE)
        try:
            winreg.DeleteValue(key, "DesktopWidgetsPro")
        except FileNotFoundError:
            pass
        winreg.CloseKey(key)
    except:
        pass


# ============== SCROLLABLE FRAME ==============
class ScrollableFrame(tk.Frame):
    """A frame with both horizontal and vertical scrollbars"""
    
    def __init__(self, parent, bg="white", scroll_x=True, scroll_y=True):
        super().__init__(parent, bg=bg)
        
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        
        if scroll_y:
            self.v_scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
            self.v_scrollbar.pack(side="right", fill="y")
            self.canvas.configure(yscrollcommand=self.v_scrollbar.set)
        
        if scroll_x:
            self.h_scrollbar = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
            self.h_scrollbar.pack(side="bottom", fill="x")
            self.canvas.configure(xscrollcommand=self.h_scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.inner_frame = tk.Frame(self.canvas, bg=bg)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        
        self.inner_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Mouse wheel
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Shift-MouseWheel>", self._on_shift_mousewheel)
        self.inner_frame.bind("<MouseWheel>", self._on_mousewheel)
    
    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_canvas_configure(self, event):
        pass
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _on_shift_mousewheel(self, event):
        self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def update_bg(self, bg):
        self.config(bg=bg)
        self.canvas.config(bg=bg)
        self.inner_frame.config(bg=bg)


# ============== BASE WIDGET CLASS ==============
class BaseWidget:
    """Base class for all widgets - embedded in desktop layer"""
    
    def __init__(self, master, title, widget_id, app, default_size=(320, 420), min_size=(200, 150)):
        self.app = app
        self.widget_id = widget_id
        self.master = master
        self.title_text = title
        self.min_width, self.min_height = min_size
        self.is_embedded = False
        
        widget_theme = app.data.get("widget_themes", {}).get(widget_id, app.data.get("theme", "🌊 Ocean Blue"))
        self.theme = THEMES.get(widget_theme, THEMES["🌊 Ocean Blue"])
        
        self.window = tk.Toplevel(master)
        self.window.title(title)
        self.window.overrideredirect(True)
        
        pos = app.data.get("widget_positions", {}).get(widget_id, {"x": 100, "y": 100})
        size = app.data.get("widget_sizes", {}).get(widget_id, {"w": default_size[0], "h": default_size[1]})
        
        self.window.geometry(f"{size['w']}x{size['h']}+{pos['x']}+{pos['y']}")
        
        self.drag_data = {"x": 0, "y": 0, "dragging": False}
        self.resize_data = {"active": False}
        
        self.window.attributes('-topmost', False)
        self.window.attributes('-alpha', 0.97)
        
        self.outer_frame = tk.Frame(self.window, bg="#888888", padx=1, pady=1)
        self.outer_frame.pack(fill="both", expand=True)
        
        self.container = tk.Frame(self.outer_frame, bg=self.theme["bg"])
        self.container.pack(fill="both", expand=True)
        
        self.create_header(title)
        
        self.content = tk.Frame(self.container, bg=self.theme["bg"])
        self.content.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        self.create_resize_grip()
        
        # Embed to desktop after window is ready
        self.window.after(200, self.embed_to_desktop)
        
        # Keep checking if window needs re-embedding
        self.window.after(1000, self.check_visibility)
    
    def embed_to_desktop(self):
        """Embed this widget into the desktop layer"""
        try:
            self.window.update_idletasks()
            hwnd = GetParent(self.window.winfo_id())
            
            # Set tool window style first
            DesktopIntegration.set_desktop_style(hwnd)
            
            # Embed into desktop
            if DesktopIntegration.embed_to_desktop(hwnd):
                self.is_embedded = True
                # Force show after embedding
                self.window.deiconify()
                self.window.lift()
        except Exception as e:
            print(f"Embed error for {self.widget_id}: {e}")
    
    def check_visibility(self):
        """Periodically check if widget is visible and restore if needed"""
        try:
            if self.widget_id not in self.app.data.get("hidden_widgets", []):
                hwnd = GetParent(self.window.winfo_id())
                
                # Check if minimized
                if IsIconic(hwnd):
                    ShowWindow(hwnd, 9)  # SW_RESTORE
                    self.window.deiconify()
                
                # Make sure it's visible
                if not self.window.winfo_viewable():
                    self.window.deiconify()
                    if not self.is_embedded:
                        self.embed_to_desktop()
        except:
            pass
        
        # Check again
        self.window.after(500, self.check_visibility)
    
    def create_header(self, title):
        self.header = tk.Frame(self.container, bg=self.theme["header"], height=36)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)
        
        self.title_label = tk.Label(
            self.header, text=f"  {title}", bg=self.theme["header"],
            fg=self.theme["text"], font=FONTS["title"], anchor="w"
        )
        self.title_label.pack(side="left", fill="x", expand=True, padx=3)
        
        controls = tk.Frame(self.header, bg=self.theme["header"])
        controls.pack(side="right", padx=3)
        
        self.color_btn = tk.Label(
            controls, text="🎨", bg=self.theme["header"],
            fg=self.theme["text"], font=FONTS["icon"], cursor="hand2"
        )
        self.color_btn.pack(side="left", padx=2)
        self.color_btn.bind("<Button-1>", self.show_color_menu)
        
        self.min_btn = tk.Label(
            controls, text="─", bg=self.theme["header"],
            fg=self.theme["text"], font=("Segoe UI", 12, "bold"), cursor="hand2"
        )
        self.min_btn.pack(side="left", padx=2)
        self.min_btn.bind("<Button-1>", self.minimize)
        
        self.close_btn = tk.Label(
            controls, text="✕", bg=self.theme["header"],
            fg=self.theme["text"], font=FONTS["icon"], cursor="hand2"
        )
        self.close_btn.pack(side="left", padx=2)
        self.close_btn.bind("<Button-1>", self.hide_widget)
        
        for widget in [self.header, self.title_label]:
            widget.bind("<Button-1>", self.start_drag)
            widget.bind("<B1-Motion>", self.do_drag)
            widget.bind("<ButtonRelease-1>", self.stop_drag)
    
    def show_color_menu(self, event=None):
        menu = tk.Menu(self.window, tearoff=0, font=FONTS["normal"])
        for theme_name in THEMES.keys():
            menu.add_command(label=theme_name, command=lambda t=theme_name: self.change_widget_theme(t))
        menu.post(event.x_root, event.y_root)
    
    def change_widget_theme(self, theme_name):
        self.theme = THEMES[theme_name]
        if "widget_themes" not in self.app.data:
            self.app.data["widget_themes"] = {}
        self.app.data["widget_themes"][self.widget_id] = theme_name
        self.app.save_data()
        self.update_theme()
    
    def create_resize_grip(self):
        self.resize_grip = tk.Label(
            self.container, text="⋱", bg=self.theme["bg"],
            fg=self.theme["accent"], font=("Segoe UI", 10), cursor="size_nw_se"
        )
        self.resize_grip.place(relx=1.0, rely=1.0, anchor="se")
        self.resize_grip.bind("<Button-1>", self.start_resize)
        self.resize_grip.bind("<B1-Motion>", self.do_resize)
        self.resize_grip.bind("<ButtonRelease-1>", self.stop_resize)
    
    def start_drag(self, event):
        self.drag_data["x"] = event.x_root - self.window.winfo_x()
        self.drag_data["y"] = event.y_root - self.window.winfo_y()
        self.drag_data["dragging"] = True
    
    def do_drag(self, event):
        if self.drag_data["dragging"]:
            x = event.x_root - self.drag_data["x"]
            y = event.y_root - self.drag_data["y"]
            self.window.geometry(f"+{x}+{y}")
    
    def stop_drag(self, event):
        self.drag_data["dragging"] = False
        self.save_position()
    
    def start_resize(self, event):
        self.resize_data["active"] = True
        self.resize_data["x"] = event.x_root
        self.resize_data["y"] = event.y_root
        self.resize_data["width"] = self.window.winfo_width()
        self.resize_data["height"] = self.window.winfo_height()
    
    def do_resize(self, event):
        if self.resize_data["active"]:
            dx = event.x_root - self.resize_data["x"]
            dy = event.y_root - self.resize_data["y"]
            new_w = max(self.min_width, self.resize_data["width"] + dx)
            new_h = max(self.min_height, self.resize_data["height"] + dy)
            self.window.geometry(f"{int(new_w)}x{int(new_h)}")
    
    def stop_resize(self, event):
        self.resize_data["active"] = False
        self.save_size()
        self.on_resize()
    
    def on_resize(self):
        pass
    
    def save_position(self):
        if "widget_positions" not in self.app.data:
            self.app.data["widget_positions"] = {}
        self.app.data["widget_positions"][self.widget_id] = {
            "x": self.window.winfo_x(), "y": self.window.winfo_y()
        }
        self.app.save_data()
    
    def save_size(self):
        if "widget_sizes" not in self.app.data:
            self.app.data["widget_sizes"] = {}
        self.app.data["widget_sizes"][self.widget_id] = {
            "w": self.window.winfo_width(), "h": self.window.winfo_height()
        }
        self.app.save_data()
    
    def minimize(self, event=None):
        self.window.withdraw()
        self.window.after(100, self.window.deiconify)
    
    def hide_widget(self, event=None):
        self.window.withdraw()
        if "hidden_widgets" not in self.app.data:
            self.app.data["hidden_widgets"] = []
        if self.widget_id not in self.app.data["hidden_widgets"]:
            self.app.data["hidden_widgets"].append(self.widget_id)
        self.app.save_data()
        self.app.update_control_panel()
    
    def show_widget(self):
        self.window.deiconify()
        if "hidden_widgets" in self.app.data and self.widget_id in self.app.data["hidden_widgets"]:
            self.app.data["hidden_widgets"].remove(self.widget_id)
        self.app.save_data()
        # Re-embed when showing
        self.window.after(100, self.embed_to_desktop)
    
    def update_theme(self):
        t = self.theme
        self.outer_frame.config(bg="#888888")
        self.container.config(bg=t["bg"])
        self.header.config(bg=t["header"])
        self.title_label.config(bg=t["header"], fg=t["text"])
        self.color_btn.config(bg=t["header"], fg=t["text"])
        self.min_btn.config(bg=t["header"], fg=t["text"])
        self.close_btn.config(bg=t["header"], fg=t["text"])
        self.content.config(bg=t["bg"])
        self.resize_grip.config(bg=t["bg"], fg=t["accent"])


# ============== CALENDAR WIDGET ==============
class CalendarWidget(BaseWidget):
    """Calendar with scrollable grid"""
    
    def __init__(self, master, app):
        super().__init__(master, "📅 Calendar", "calendar", app, (400, 450), (280, 250))
        self.current_date = datetime.now()
        self.create_content()
    
    def create_content(self):
        nav = tk.Frame(self.content, bg=self.theme["bg"])
        nav.pack(fill="x", pady=3)
        
        self.prev_btn = tk.Button(
            nav, text="◀", command=self.prev_month,
            bg=self.theme["button"], fg=self.theme["text"],
            font=FONTS["button"], bd=0, padx=8, cursor="hand2"
        )
        self.prev_btn.pack(side="left")
        
        self.month_label = tk.Label(
            nav, text="", bg=self.theme["bg"], fg=self.theme["text"],
            font=FONTS["header"]
        )
        self.month_label.pack(side="left", fill="x", expand=True)
        
        self.today_btn = tk.Button(
            nav, text="Today", command=self.go_today,
            bg=self.theme["accent"], fg="white",
            font=FONTS["tiny"], bd=0, padx=6, cursor="hand2"
        )
        self.today_btn.pack(side="right", padx=3)
        
        self.next_btn = tk.Button(
            nav, text="▶", command=self.next_month,
            bg=self.theme["button"], fg=self.theme["text"],
            font=FONTS["button"], bd=0, padx=8, cursor="hand2"
        )
        self.next_btn.pack(side="right")
        
        self.scroll_frame = ScrollableFrame(self.content, bg=self.theme["bg"], scroll_x=True, scroll_y=True)
        self.scroll_frame.pack(fill="both", expand=True)
        
        self.cal_frame = self.scroll_frame.inner_frame
        
        self.update_calendar()
    
    def update_calendar(self):
        for widget in self.cal_frame.winfo_children():
            widget.destroy()
        
        year = self.current_date.year
        month = self.current_date.month
        
        self.month_label.config(text=f"{calendar.month_name[month]} {year}")
        
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for col, day in enumerate(days):
            fg_color = "#E74C3C" if col >= 5 else self.theme["text"]
            lbl = tk.Label(
                self.cal_frame, text=day, bg=self.theme["header"],
                fg=fg_color, font=FONTS["small"], width=10, height=1,
                relief="solid", bd=1
            )
            lbl.grid(row=0, column=col, sticky="nsew", padx=0, pady=0)
        
        cal = calendar.monthcalendar(year, month)
        today = datetime.now()
        events = self.app.data.get("calendar_events", {})
        
        for row_idx, week in enumerate(cal):
            for col_idx, day in enumerate(week):
                cell = tk.Frame(self.cal_frame, bg=self.theme["entry"], 
                               relief="solid", bd=1, width=70, height=60)
                cell.grid(row=row_idx + 1, column=col_idx, sticky="nsew", padx=0, pady=0)
                cell.grid_propagate(False)
                
                if day != 0:
                    date_key = f"{year}-{month:02d}-{day:02d}"
                    
                    is_today = (year == today.year and month == today.month and day == today.day)
                    is_weekend = col_idx >= 5
                    
                    date_bg = self.theme["accent"] if is_today else self.theme["entry"]
                    date_fg = "white" if is_today else ("#E74C3C" if is_weekend else self.theme["text"])
                    
                    date_lbl = tk.Label(
                        cell, text=str(day), bg=date_bg, fg=date_fg,
                        font=FONTS["small"], anchor="nw"
                    )
                    date_lbl.pack(anchor="nw", padx=2, pady=1)
                    
                    event_text = events.get(date_key, "")
                    event_entry = tk.Text(
                        cell, height=2, width=8, bg=self.theme["entry"],
                        fg=self.theme["text_light"], font=FONTS["tiny"],
                        bd=0, wrap="word", relief="flat"
                    )
                    event_entry.pack(fill="both", expand=True, padx=1, pady=1)
                    event_entry.insert("1.0", event_text)
                    event_entry.bind("<KeyRelease>", lambda e, dk=date_key, et=event_entry: self.save_event(dk, et))
                else:
                    cell.config(bg=self.theme["bg"])
        
        self.cal_frame.update_idletasks()
        self.scroll_frame.canvas.configure(scrollregion=self.scroll_frame.canvas.bbox("all"))
    
    def save_event(self, date_key, text_widget):
        if "calendar_events" not in self.app.data:
            self.app.data["calendar_events"] = {}
        
        text = text_widget.get("1.0", "end-1c").strip()
        if text:
            self.app.data["calendar_events"][date_key] = text
        elif date_key in self.app.data["calendar_events"]:
            del self.app.data["calendar_events"][date_key]
        
        self.app.save_data()
    
    def prev_month(self):
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        self.update_calendar()
    
    def next_month(self):
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        self.update_calendar()
    
    def go_today(self):
        self.current_date = datetime.now()
        self.update_calendar()
    
    def update_theme(self):
        super().update_theme()
        t = self.theme
        self.prev_btn.config(bg=t["button"], fg=t["text"])
        self.next_btn.config(bg=t["button"], fg=t["text"])
        self.today_btn.config(bg=t["accent"])
        self.month_label.config(bg=t["bg"], fg=t["text"])
        self.scroll_frame.update_bg(t["bg"])
        self.update_calendar()


# ============== TODO WIDGET ==============
class TodoWidget(BaseWidget):
    """To-Do List"""
    
    def __init__(self, master, app):
        super().__init__(master, "✅ To-Do List", "todo", app, (300, 400), (200, 200))
        self.create_content()
    
    def create_content(self):
        add_frame = tk.Frame(self.content, bg=self.theme["bg"])
        add_frame.pack(fill="x", pady=3)
        
        self.task_entry = tk.Entry(
            add_frame, bg=self.theme["entry"], fg=self.theme["text"],
            font=FONTS["normal"], bd=1, relief="solid"
        )
        self.task_entry.pack(side="left", fill="x", expand=True, padx=(0, 3))
        self.task_entry.insert(0, "New task...")
        self.task_entry.bind("<FocusIn>", lambda e: self.task_entry.delete(0, "end") if self.task_entry.get() == "New task..." else None)
        self.task_entry.bind("<Return>", self.add_task)
        
        self.priority_var = tk.StringVar(value="low")
        for symbol, level in [("🔴", "high"), ("🟡", "medium"), ("🟢", "low")]:
            rb = tk.Radiobutton(
                add_frame, text=symbol, variable=self.priority_var,
                value=level, bg=self.theme["bg"], font=("Segoe UI", 10),
                indicatoron=False, bd=0, selectcolor=self.theme["highlight"]
            )
            rb.pack(side="left", padx=1)
        
        self.add_btn = tk.Button(
            add_frame, text="➕", command=self.add_task,
            bg=self.theme["accent"], fg="white",
            font=FONTS["button"], bd=0, padx=5, cursor="hand2"
        )
        self.add_btn.pack(side="right")
        
        filter_frame = tk.Frame(self.content, bg=self.theme["bg"])
        filter_frame.pack(fill="x", pady=3)
        
        self.filter_var = tk.StringVar(value="all")
        for text, value in [("All", "all"), ("Active", "active"), ("Done", "done")]:
            btn = tk.Radiobutton(
                filter_frame, text=text, variable=self.filter_var,
                value=value, bg=self.theme["button"], fg=self.theme["text"],
                font=FONTS["tiny"], indicatoron=False, bd=0, padx=6, pady=2,
                selectcolor=self.theme["accent"], command=self.load_tasks
            )
            btn.pack(side="left", padx=1)
        
        self.clear_btn = tk.Button(
            filter_frame, text="🗑️", command=self.clear_completed,
            bg=self.theme["button"], fg=self.theme["text"],
            font=FONTS["small"], bd=0, padx=5, cursor="hand2"
        )
        self.clear_btn.pack(side="right")
        
        self.scroll_frame = ScrollableFrame(self.content, bg=self.theme["bg"], scroll_x=False, scroll_y=True)
        self.scroll_frame.pack(fill="both", expand=True)
        
        self.task_container = self.scroll_frame.inner_frame
        
        self.stats_label = tk.Label(
            self.content, text="", bg=self.theme["bg"],
            fg=self.theme["text_light"], font=FONTS["tiny"]
        )
        self.stats_label.pack(fill="x", pady=2)
        
        self.load_tasks()
    
    def load_tasks(self):
        for widget in self.task_container.winfo_children():
            widget.destroy()
        
        tasks = self.app.data.get("todos", [])
        filter_type = self.filter_var.get()
        
        priority_order = {"high": 0, "medium": 1, "low": 2}
        sorted_tasks = sorted(tasks, key=lambda x: (x.get("done", False), priority_order.get(x.get("priority", "low"), 3)))
        
        total = len(tasks)
        done = sum(1 for t in tasks if t.get("done", False))
        
        for i, task in enumerate(sorted_tasks):
            if filter_type == "active" and task.get("done"):
                continue
            if filter_type == "done" and not task.get("done"):
                continue
            
            actual_idx = tasks.index(task)
            self.create_task_row(task, actual_idx)
        
        self.stats_label.config(text=f"📊 {done}/{total} done")
    
    def create_task_row(self, task, actual_idx):
        row = tk.Frame(self.task_container, bg=self.theme["entry"], pady=3)
        row.pack(fill="x", pady=1, padx=1)
        
        priority_colors = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        priority = task.get("priority", "low")
        
        tk.Label(row, text=priority_colors.get(priority, "●"),
                 bg=self.theme["entry"], font=("Segoe UI", 9)).pack(side="left", padx=2)
        
        var = tk.BooleanVar(value=task.get("done", False))
        cb = tk.Checkbutton(
            row, variable=var, bg=self.theme["entry"],
            activebackground=self.theme["entry"],
            command=lambda: self.toggle_task(actual_idx, var.get())
        )
        cb.pack(side="left")
        
        text = task.get("text", "")
        fg_color = self.theme["text_light"] if task.get("done") else self.theme["text"]
        font_style = ("Segoe UI", 9, "overstrike") if task.get("done") else FONTS["small"]
        
        lbl = tk.Label(
            row, text=text, bg=self.theme["entry"],
            fg=fg_color, font=font_style, anchor="w"
        )
        lbl.pack(side="left", fill="x", expand=True, padx=3)
        
        del_btn = tk.Label(
            row, text="✕", bg=self.theme["entry"],
            fg="#E74C3C", font=FONTS["tiny"], cursor="hand2"
        )
        del_btn.pack(side="right", padx=3)
        del_btn.bind("<Button-1>", lambda e: self.delete_task(actual_idx))
    
    def add_task(self, event=None):
        text = self.task_entry.get().strip()
        if text and text != "New task...":
            if "todos" not in self.app.data:
                self.app.data["todos"] = []
            
            self.app.data["todos"].append({
                "text": text,
                "done": False,
                "priority": self.priority_var.get()
            })
            self.app.save_data()
            self.task_entry.delete(0, "end")
            self.load_tasks()
    
    def toggle_task(self, index, done):
        if "todos" in self.app.data and index < len(self.app.data["todos"]):
            self.app.data["todos"][index]["done"] = done
            self.app.save_data()
            self.load_tasks()
    
    def delete_task(self, index):
        if "todos" in self.app.data and index < len(self.app.data["todos"]):
            del self.app.data["todos"][index]
            self.app.save_data()
            self.load_tasks()
    
    def clear_completed(self):
        if "todos" in self.app.data:
            self.app.data["todos"] = [t for t in self.app.data["todos"] if not t.get("done")]
            self.app.save_data()
            self.load_tasks()
    
    def update_theme(self):
        super().update_theme()
        t = self.theme
        self.task_entry.config(bg=t["entry"], fg=t["text"])
        self.add_btn.config(bg=t["accent"])
        self.clear_btn.config(bg=t["button"], fg=t["text"])
        self.scroll_frame.update_bg(t["bg"])
        self.stats_label.config(bg=t["bg"], fg=t["text_light"])
        self.load_tasks()


# ============== DAY PLANNER ==============
class DayPlannerWidget(BaseWidget):
    """Day Planner"""
    
    def __init__(self, master, app):
        super().__init__(master, "📆 Day Planner", "day_planner", app, (300, 400), (200, 200))
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.create_content()
    
    def create_content(self):
        nav = tk.Frame(self.content, bg=self.theme["bg"])
        nav.pack(fill="x", pady=3)
        
        self.prev_btn = tk.Button(
            nav, text="◀", command=self.prev_day,
            bg=self.theme["button"], fg=self.theme["text"],
            font=FONTS["button"], bd=0, padx=6, cursor="hand2"
        )
        self.prev_btn.pack(side="left")
        
        self.date_label = tk.Label(
            nav, text="", bg=self.theme["bg"], fg=self.theme["text"],
            font=FONTS["small"]
        )
        self.date_label.pack(side="left", fill="x", expand=True)
        
        self.today_btn = tk.Button(
            nav, text="Today", command=self.go_today,
            bg=self.theme["accent"], fg="white",
            font=FONTS["tiny"], bd=0, padx=5, cursor="hand2"
        )
        self.today_btn.pack(side="right", padx=2)
        
        self.next_btn = tk.Button(
            nav, text="▶", command=self.next_day,
            bg=self.theme["button"], fg=self.theme["text"],
            font=FONTS["button"], bd=0, padx=6, cursor="hand2"
        )
        self.next_btn.pack(side="right")
        
        self.scroll_frame = ScrollableFrame(self.content, bg=self.theme["bg"], scroll_x=False, scroll_y=True)
        self.scroll_frame.pack(fill="both", expand=True)
        
        self.slots_frame = self.scroll_frame.inner_frame
        self.time_entries = {}
        
        for hour in range(5, 24):
            self.create_time_slot(hour)
        
        self.load_day_data()
    
    def create_time_slot(self, hour):
        row = tk.Frame(self.slots_frame, bg=self.theme["bg"])
        row.pack(fill="x", pady=1)
        
        time_str = f"{hour:02d}:00"
        
        time_lbl = tk.Label(
            row, text=time_str, bg=self.theme["header"], fg=self.theme["text"],
            font=FONTS["tiny"], width=5
        )
        time_lbl.pack(side="left", padx=(0, 2))
        
        entry = tk.Entry(
            row, bg=self.theme["entry"], fg=self.theme["text"],
            font=FONTS["small"], bd=1, relief="solid"
        )
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<KeyRelease>", lambda e, h=hour: self.save_slot(h))
        
        self.time_entries[hour] = {"entry": entry, "label": time_lbl}
    
    def load_day_data(self):
        day_data = self.app.data.get("day_planner", {}).get(self.current_date, {})
        
        date_obj = datetime.strptime(self.current_date, "%Y-%m-%d")
        self.date_label.config(text=f"{date_obj.strftime('%A, %b %d')}")
        
        current_hour = datetime.now().hour
        is_today = self.current_date == datetime.now().strftime("%Y-%m-%d")
        
        for hour, widgets in self.time_entries.items():
            widgets["entry"].delete(0, "end")
            if str(hour) in day_data:
                widgets["entry"].insert(0, day_data[str(hour)])
            
            is_current = (hour == current_hour and is_today)
            bg = self.theme["accent"] if is_current else self.theme["header"]
            fg = "white" if is_current else self.theme["text"]
            widgets["label"].config(bg=bg, fg=fg)
    
    def save_slot(self, hour):
        if "day_planner" not in self.app.data:
            self.app.data["day_planner"] = {}
        if self.current_date not in self.app.data["day_planner"]:
            self.app.data["day_planner"][self.current_date] = {}
        
        text = self.time_entries[hour]["entry"].get()
        if text:
            self.app.data["day_planner"][self.current_date][str(hour)] = text
        elif str(hour) in self.app.data["day_planner"][self.current_date]:
            del self.app.data["day_planner"][self.current_date][str(hour)]
        
        self.app.save_data()
    
    def prev_day(self):
        date = datetime.strptime(self.current_date, "%Y-%m-%d") - timedelta(days=1)
        self.current_date = date.strftime("%Y-%m-%d")
        self.load_day_data()
    
    def next_day(self):
        date = datetime.strptime(self.current_date, "%Y-%m-%d") + timedelta(days=1)
        self.current_date = date.strftime("%Y-%m-%d")
        self.load_day_data()
    
    def go_today(self):
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.load_day_data()
    
    def update_theme(self):
        super().update_theme()
        t = self.theme
        self.prev_btn.config(bg=t["button"], fg=t["text"])
        self.next_btn.config(bg=t["button"], fg=t["text"])
        self.today_btn.config(bg=t["accent"])
        self.date_label.config(bg=t["bg"], fg=t["text"])
        self.scroll_frame.update_bg(t["bg"])
        self.load_day_data()


# ============== WEEK PLANNER ==============
class WeekPlannerWidget(BaseWidget):
    """Horizontal Week Planner"""
    
    def __init__(self, master, app):
        super().__init__(master, "📋 Week Planner", "week_planner", app, (600, 320), (300, 200))
        self.current_week_start = self.get_week_start(datetime.now())
        self.create_content()
    
    def get_week_start(self, date):
        return date - timedelta(days=date.weekday())
    
    def create_content(self):
        nav = tk.Frame(self.content, bg=self.theme["bg"])
        nav.pack(fill="x", pady=3)
        
        self.prev_btn = tk.Button(
            nav, text="◀ Prev", command=self.prev_week,
            bg=self.theme["button"], fg=self.theme["text"],
            font=FONTS["button"], bd=0, padx=8, cursor="hand2"
        )
        self.prev_btn.pack(side="left")
        
        self.week_label = tk.Label(
            nav, text="", bg=self.theme["bg"], fg=self.theme["text"],
            font=FONTS["small"]
        )
        self.week_label.pack(side="left", fill="x", expand=True)
        
        self.this_week_btn = tk.Button(
            nav, text="This Week", command=self.go_this_week,
            bg=self.theme["accent"], fg="white",
            font=FONTS["tiny"], bd=0, padx=6, cursor="hand2"
        )
        self.this_week_btn.pack(side="right", padx=3)
        
        self.next_btn = tk.Button(
            nav, text="Next ▶", command=self.next_week,
            bg=self.theme["button"], fg=self.theme["text"],
            font=FONTS["button"], bd=0, padx=8, cursor="hand2"
        )
        self.next_btn.pack(side="right")
        
        self.scroll_frame = ScrollableFrame(self.content, bg=self.theme["bg"], scroll_x=True, scroll_y=True)
        self.scroll_frame.pack(fill="both", expand=True)
        
        self.days_frame = self.scroll_frame.inner_frame
        
        self.day_widgets = {}
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for i, day in enumerate(days):
            self.create_day_column(i, day)
        
        self.load_week_data()
    
    def create_day_column(self, index, day_name):
        col = tk.Frame(self.days_frame, bg=self.theme["entry"], 
                      relief="solid", bd=1, width=100)
        col.pack(side="left", fill="y", padx=1)
        col.pack_propagate(False)
        
        is_weekend = index >= 5
        header_fg = "#E74C3C" if is_weekend else self.theme["text"]
        
        header = tk.Label(
            col, text=day_name[:3], bg=self.theme["header"], fg=header_fg,
            font=FONTS["small"], pady=3
        )
        header.pack(fill="x")
        
        date_lbl = tk.Label(
            col, text="", bg=self.theme["header"], fg=self.theme["text_light"],
            font=FONTS["tiny"]
        )
        date_lbl.pack(fill="x")
        
        text = tk.Text(
            col, bg=self.theme["entry"], fg=self.theme["text"],
            font=FONTS["small"], bd=0, wrap="word", width=12, height=10
        )
        text.pack(fill="both", expand=True, padx=3, pady=3)
        text.bind("<KeyRelease>", lambda e, idx=index: self.save_day(idx))
        
        self.day_widgets[index] = {"frame": col, "header": header, "date": date_lbl, "text": text}
    
    def load_week_data(self):
        week_key = self.current_week_start.strftime("%Y-%m-%d")
        week_data = self.app.data.get("week_planner", {}).get(week_key, {})
        
        week_end = self.current_week_start + timedelta(days=6)
        self.week_label.config(
            text=f"{self.current_week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}"
        )
        
        today = datetime.now().date()
        
        for i, widgets in self.day_widgets.items():
            day_date = self.current_week_start + timedelta(days=i)
            widgets["date"].config(text=day_date.strftime("%d"))
            
            if day_date.date() == today:
                widgets["header"].config(bg=self.theme["accent"], fg="white")
                widgets["date"].config(bg=self.theme["accent"], fg="white")
            else:
                is_weekend = i >= 5
                widgets["header"].config(bg=self.theme["header"], fg="#E74C3C" if is_weekend else self.theme["text"])
                widgets["date"].config(bg=self.theme["header"], fg=self.theme["text_light"])
            
            widgets["text"].delete("1.0", "end")
            if str(i) in week_data:
                widgets["text"].insert("1.0", week_data[str(i)])
    
    def save_day(self, day_index):
        if "week_planner" not in self.app.data:
            self.app.data["week_planner"] = {}
        
        week_key = self.current_week_start.strftime("%Y-%m-%d")
        if week_key not in self.app.data["week_planner"]:
            self.app.data["week_planner"][week_key] = {}
        
        text = self.day_widgets[day_index]["text"].get("1.0", "end-1c")
        if text.strip():
            self.app.data["week_planner"][week_key][str(day_index)] = text
        elif str(day_index) in self.app.data["week_planner"][week_key]:
            del self.app.data["week_planner"][week_key][str(day_index)]
        
        self.app.save_data()
    
    def prev_week(self):
        self.current_week_start -= timedelta(days=7)
        self.load_week_data()
    
    def next_week(self):
        self.current_week_start += timedelta(days=7)
        self.load_week_data()
    
    def go_this_week(self):
        self.current_week_start = self.get_week_start(datetime.now())
        self.load_week_data()
    
    def update_theme(self):
        super().update_theme()
        t = self.theme
        self.prev_btn.config(bg=t["button"], fg=t["text"])
        self.next_btn.config(bg=t["button"], fg=t["text"])
        self.this_week_btn.config(bg=t["accent"])
        self.week_label.config(bg=t["bg"], fg=t["text"])
        self.scroll_frame.update_bg(t["bg"])
        self.load_week_data()


# ============== MONTHLY PLANNER ==============
class MonthlyPlannerWidget(BaseWidget):
    """Monthly Planner"""
    
    def __init__(self, master, app):
        super().__init__(master, "🎯 Monthly Planner", "monthly_planner", app, (320, 400), (200, 200))
        self.current_date = datetime.now()
        self.create_content()
    
    def create_content(self):
        nav = tk.Frame(self.content, bg=self.theme["bg"])
        nav.pack(fill="x", pady=3)
        
        self.prev_btn = tk.Button(
            nav, text="◀", command=self.prev_month,
            bg=self.theme["button"], fg=self.theme["text"],
            font=FONTS["button"], bd=0, padx=6, cursor="hand2"
        )
        self.prev_btn.pack(side="left")
        
        self.month_label = tk.Label(
            nav, text="", bg=self.theme["bg"], fg=self.theme["text"],
            font=FONTS["header"]
        )
        self.month_label.pack(side="left", fill="x", expand=True)
        
        self.next_btn = tk.Button(
            nav, text="▶", command=self.next_month,
            bg=self.theme["button"], fg=self.theme["text"],
            font=FONTS["button"], bd=0, padx=6, cursor="hand2"
        )
        self.next_btn.pack(side="right")
        
        self.scroll_frame = ScrollableFrame(self.content, bg=self.theme["bg"], scroll_x=False, scroll_y=True)
        self.scroll_frame.pack(fill="both", expand=True)
        
        self.sections_frame = self.scroll_frame.inner_frame
        self.section_widgets = {}
        
        sections = [
            ("🎯 Goals", "goals", "#4CAF50"),
            ("📝 Tasks", "tasks", "#2196F3"),
            ("💡 Ideas", "ideas", "#FF9800"),
            ("📊 Review", "review", "#9C27B0"),
            ("✨ Notes", "notes", "#607D8B")
        ]
        
        for title, key, color in sections:
            self.create_section(title, key, color)
        
        self.load_month_data()
    
    def create_section(self, title, key, color):
        frame = tk.Frame(self.sections_frame, bg=self.theme["entry"], relief="solid", bd=1)
        frame.pack(fill="x", pady=2)
        
        header = tk.Label(
            frame, text=title, bg=color, fg="white",
            font=FONTS["small"], anchor="w", padx=8, pady=3
        )
        header.pack(fill="x")
        
        text = tk.Text(
            frame, height=3, bg=self.theme["entry"], fg=self.theme["text"],
            font=FONTS["small"], bd=0, wrap="word", padx=5, pady=3
        )
        text.pack(fill="x")
        text.bind("<KeyRelease>", lambda e, k=key: self.save_section(k))
        
        self.section_widgets[key] = {"frame": frame, "header": header, "text": text, "color": color}
    
    def load_month_data(self):
        month_key = self.current_date.strftime("%Y-%m")
        month_data = self.app.data.get("monthly_planner", {}).get(month_key, {})
        
        self.month_label.config(
            text=f"{calendar.month_name[self.current_date.month]} {self.current_date.year}"
        )
        
        for key, widgets in self.section_widgets.items():
            widgets["text"].delete("1.0", "end")
            if key in month_data:
                widgets["text"].insert("1.0", month_data[key])
    
    def save_section(self, section_key):
        if "monthly_planner" not in self.app.data:
            self.app.data["monthly_planner"] = {}
        
        month_key = self.current_date.strftime("%Y-%m")
        if month_key not in self.app.data["monthly_planner"]:
            self.app.data["monthly_planner"][month_key] = {}
        
        text = self.section_widgets[section_key]["text"].get("1.0", "end-1c")
        if text.strip():
            self.app.data["monthly_planner"][month_key][section_key] = text
        elif section_key in self.app.data["monthly_planner"][month_key]:
            del self.app.data["monthly_planner"][month_key][section_key]
        
        self.app.save_data()
    
    def prev_month(self):
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        self.load_month_data()
    
    def next_month(self):
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        self.load_month_data()
    
    def update_theme(self):
        super().update_theme()
        t = self.theme
        self.prev_btn.config(bg=t["button"], fg=t["text"])
        self.next_btn.config(bg=t["button"], fg=t["text"])
        self.month_label.config(bg=t["bg"], fg=t["text"])
        self.scroll_frame.update_bg(t["bg"])
        for key, widgets in self.section_widgets.items():
            widgets["frame"].config(bg=t["entry"])
            widgets["text"].config(bg=t["entry"], fg=t["text"])


# ============== STICKY NOTES ==============
class StickyNotesWidget(BaseWidget):
    """Sticky Notes"""
    
    def __init__(self, master, app):
        super().__init__(master, "📝 Sticky Notes", "sticky_notes", app, (320, 350), (200, 200))
        self.note_colors = ["#FFFFA5", "#A5FFFA", "#FFA5FF", "#A5FFA5", "#FFA5A5", "#A5A5FF"]
        self.create_content()
    
    def create_content(self):
        add_frame = tk.Frame(self.content, bg=self.theme["bg"])
        add_frame.pack(fill="x", pady=3)
        
        tk.Label(add_frame, text="Add:", bg=self.theme["bg"], fg=self.theme["text"], 
                font=FONTS["tiny"]).pack(side="left", padx=3)
        
        for color in self.note_colors:
            btn = tk.Button(
                add_frame, text=" ", bg=color, bd=1, relief="solid", width=2,
                command=lambda c=color: self.add_note(c), cursor="hand2"
            )
            btn.pack(side="left", padx=1)
        
        self.scroll_frame = ScrollableFrame(self.content, bg=self.theme["bg"], scroll_x=False, scroll_y=True)
        self.scroll_frame.pack(fill="both", expand=True)
        
        self.notes_frame = self.scroll_frame.inner_frame
        
        self.load_notes()
    
    def load_notes(self):
        for widget in self.notes_frame.winfo_children():
            widget.destroy()
        
        notes = self.app.data.get("sticky_notes", [])
        
        row = 0
        col = 0
        for i, note in enumerate(notes):
            self.create_note_card(i, note, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1
    
    def create_note_card(self, index, note, row, col):
        color = note.get("color", "#FFFFA5")
        
        frame = tk.Frame(self.notes_frame, bg=color, relief="solid", bd=1, width=120, height=80)
        frame.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
        frame.grid_propagate(False)
        
        del_btn = tk.Label(frame, text="✕", bg=color, fg="#666666", font=FONTS["tiny"], cursor="hand2")
        del_btn.pack(anchor="ne", padx=1)
        del_btn.bind("<Button-1>", lambda e: self.delete_note(index))
        
        text = tk.Text(frame, height=3, width=14, bg=color, fg="#333333", font=FONTS["tiny"], bd=0, wrap="word")
        text.pack(fill="both", expand=True, padx=3, pady=1)
        text.insert("1.0", note.get("text", ""))
        text.bind("<KeyRelease>", lambda e, idx=index, t=text: self.save_note(idx, t))
        
        self.notes_frame.columnconfigure(col, weight=1)
        self.notes_frame.rowconfigure(row, weight=1)
    
    def add_note(self, color):
        if "sticky_notes" not in self.app.data:
            self.app.data["sticky_notes"] = []
        self.app.data["sticky_notes"].append({"text": "", "color": color})
        self.app.save_data()
        self.load_notes()
    
    def save_note(self, index, text_widget):
        if index < len(self.app.data.get("sticky_notes", [])):
            self.app.data["sticky_notes"][index]["text"] = text_widget.get("1.0", "end-1c")
            self.app.save_data()
    
    def delete_note(self, index):
        if index < len(self.app.data.get("sticky_notes", [])):
            del self.app.data["sticky_notes"][index]
            self.app.save_data()
            self.load_notes()
    
    def update_theme(self):
        super().update_theme()
        self.scroll_frame.update_bg(self.theme["bg"])
        self.load_notes()


# ============== POMODORO ==============
class PomodoroWidget(BaseWidget):
    """Pomodoro Timer"""
    
    def __init__(self, master, app):
        super().__init__(master, "🍅 Pomodoro", "pomodoro", app, (250, 280), (180, 200))
        self.work_time = 25 * 60
        self.break_time = 5 * 60
        self.current_time = self.work_time
        self.is_running = False
        self.is_work = True
        self.sessions = 0
        self.create_content()
    
    def create_content(self):
        self.timer_label = tk.Label(
            self.content, text="25:00", bg=self.theme["bg"],
            fg=self.theme["accent"], font=("Segoe UI Light", 40)
        )
        self.timer_label.pack(pady=10)
        
        self.status_label = tk.Label(
            self.content, text="🍅 Work", bg=self.theme["bg"],
            fg=self.theme["text"], font=FONTS["normal"]
        )
        self.status_label.pack()
        
        self.sessions_label = tk.Label(
            self.content, text="Sessions: 0", bg=self.theme["bg"],
            fg=self.theme["text_light"], font=FONTS["tiny"]
        )
        self.sessions_label.pack(pady=3)
        
        controls = tk.Frame(self.content, bg=self.theme["bg"])
        controls.pack(pady=10)
        
        self.start_btn = tk.Button(
            controls, text="▶", command=self.toggle_timer,
            bg=self.theme["accent"], fg="white",
            font=FONTS["button"], bd=0, padx=15, pady=5, cursor="hand2"
        )
        self.start_btn.pack(side="left", padx=3)
        
        self.reset_btn = tk.Button(
            controls, text="↺", command=self.reset_timer,
            bg=self.theme["button"], fg=self.theme["text"],
            font=FONTS["button"], bd=0, padx=15, pady=5, cursor="hand2"
        )
        self.reset_btn.pack(side="left", padx=3)
        
        settings = tk.Frame(self.content, bg=self.theme["bg"])
        settings.pack(pady=5)
        
        tk.Label(settings, text="Work:", bg=self.theme["bg"], fg=self.theme["text"], font=FONTS["tiny"]).pack(side="left")
        self.work_spin = tk.Spinbox(settings, from_=1, to=60, width=3, font=FONTS["tiny"])
        self.work_spin.pack(side="left", padx=1)
        self.work_spin.delete(0, "end")
        self.work_spin.insert(0, "25")
        
        tk.Label(settings, text=" Break:", bg=self.theme["bg"], fg=self.theme["text"], font=FONTS["tiny"]).pack(side="left")
        self.break_spin = tk.Spinbox(settings, from_=1, to=30, width=3, font=FONTS["tiny"])
        self.break_spin.pack(side="left", padx=1)
        self.break_spin.delete(0, "end")
        self.break_spin.insert(0, "5")
    
    def toggle_timer(self):
        if self.is_running:
            self.is_running = False
            self.start_btn.config(text="▶", bg=self.theme["accent"])
        else:
            try:
                self.work_time = int(self.work_spin.get()) * 60
                self.break_time = int(self.break_spin.get()) * 60
            except:
                pass
            self.is_running = True
            self.start_btn.config(text="⏸", bg="#FF9800")
            self.run_timer()
    
    def run_timer(self):
        if self.is_running and self.current_time > 0:
            mins, secs = divmod(self.current_time, 60)
            self.timer_label.config(text=f"{mins:02d}:{secs:02d}")
            self.current_time -= 1
            self.window.after(1000, self.run_timer)
        elif self.is_running:
            self.timer_complete()
    
    def timer_complete(self):
        if self.is_work:
            self.sessions += 1
            self.sessions_label.config(text=f"Sessions: {self.sessions}")
            self.current_time = self.break_time
            self.status_label.config(text="☕ Break")
            self.is_work = False
        else:
            self.current_time = self.work_time
            self.status_label.config(text="🍅 Work")
            self.is_work = True
        
        try:
            import winsound
            winsound.MessageBeep()
        except:
            pass
        
        self.run_timer()
    
    def reset_timer(self):
        self.is_running = False
        self.is_work = True
        try:
            self.work_time = int(self.work_spin.get()) * 60
        except:
            self.work_time = 25 * 60
        self.current_time = self.work_time
        mins, secs = divmod(self.current_time, 60)
        self.timer_label.config(text=f"{mins:02d}:{secs:02d}")
        self.status_label.config(text="🍅 Work")
        self.start_btn.config(text="▶", bg=self.theme["accent"])
    
    def update_theme(self):
        super().update_theme()
        t = self.theme
        self.timer_label.config(bg=t["bg"], fg=t["accent"])
        self.status_label.config(bg=t["bg"], fg=t["text"])
        self.sessions_label.config(bg=t["bg"], fg=t["text_light"])
        self.reset_btn.config(bg=t["button"], fg=t["text"])


# ============== HABIT TRACKER ==============
class HabitTrackerWidget(BaseWidget):
    """Habit Tracker"""
    
    def __init__(self, master, app):
        super().__init__(master, "📊 Habits", "habit_tracker", app, (350, 320), (250, 180))
        self.create_content()
    
    def create_content(self):
        add_frame = tk.Frame(self.content, bg=self.theme["bg"])
        add_frame.pack(fill="x", pady=3)
        
        self.habit_entry = tk.Entry(
            add_frame, bg=self.theme["entry"], fg=self.theme["text"],
            font=FONTS["small"], bd=1, relief="solid"
        )
        self.habit_entry.pack(side="left", fill="x", expand=True, padx=(0, 3))
        self.habit_entry.bind("<Return>", self.add_habit)
        
        self.add_btn = tk.Button(
            add_frame, text="➕", command=self.add_habit,
            bg=self.theme["accent"], fg="white",
            font=FONTS["button"], bd=0, padx=6, cursor="hand2"
        )
        self.add_btn.pack(side="right")
        
        self.scroll_frame = ScrollableFrame(self.content, bg=self.theme["bg"], scroll_x=True, scroll_y=True)
        self.scroll_frame.pack(fill="both", expand=True)
        
        self.habits_frame = self.scroll_frame.inner_frame
        
        self.load_habits()
    
    def get_week_key(self):
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        return week_start.strftime("%Y-%m-%d")
    
    def load_habits(self):
        for widget in self.habits_frame.winfo_children():
            widget.destroy()
        
        habits = self.app.data.get("habits", [])
        week_key = self.get_week_key()
        
        tk.Label(self.habits_frame, text="Habit", bg=self.theme["bg"], fg=self.theme["text"],
                font=FONTS["small"], width=12, anchor="w").grid(row=0, column=0, padx=2, pady=2)
        
        days = ["M", "T", "W", "T", "F", "S", "S"]
        for col, day in enumerate(days):
            tk.Label(self.habits_frame, text=day, bg=self.theme["header"], fg=self.theme["text"],
                    font=FONTS["tiny"], width=3).grid(row=0, column=col+1, padx=1, pady=2)
        
        tk.Label(self.habits_frame, text="", width=2, bg=self.theme["bg"]).grid(row=0, column=8)
        
        for i, habit in enumerate(habits):
            self.create_habit_row(i, habit, week_key)
    
    def create_habit_row(self, index, habit, week_key):
        row_num = index + 1
        
        tk.Label(self.habits_frame, text=habit["name"][:12], bg=self.theme["entry"],
                fg=self.theme["text"], font=FONTS["tiny"], width=12, anchor="w"
                ).grid(row=row_num, column=0, padx=2, pady=1, sticky="w")
        
        checked = habit.get("checked", {}).get(week_key, [False] * 7)
        while len(checked) < 7:
            checked.append(False)
        
        for day in range(7):
            var = tk.BooleanVar(value=checked[day])
            cb = tk.Checkbutton(
                self.habits_frame, variable=var, bg=self.theme["entry"],
                activebackground=self.theme["entry"],
                command=lambda idx=index, d=day, v=var: self.toggle_day(idx, d, v.get())
            )
            cb.grid(row=row_num, column=day+1, padx=1, pady=1)
        
        del_btn = tk.Label(self.habits_frame, text="✕", bg=self.theme["bg"],
                          fg="#E74C3C", font=FONTS["tiny"], cursor="hand2")
        del_btn.grid(row=row_num, column=8, padx=2)
        del_btn.bind("<Button-1>", lambda e: self.delete_habit(index))
    
    def add_habit(self, event=None):
        name = self.habit_entry.get().strip()
        if name:
            if "habits" not in self.app.data:
                self.app.data["habits"] = []
            self.app.data["habits"].append({"name": name, "checked": {}})
            self.app.save_data()
            self.habit_entry.delete(0, "end")
            self.load_habits()
    
    def toggle_day(self, habit_index, day, checked):
        if "habits" in self.app.data and habit_index < len(self.app.data["habits"]):
            week_key = self.get_week_key()
            habit = self.app.data["habits"][habit_index]
            if "checked" not in habit:
                habit["checked"] = {}
            if week_key not in habit["checked"]:
                habit["checked"][week_key] = [False] * 7
            habit["checked"][week_key][day] = checked
            self.app.save_data()
    
    def delete_habit(self, index):
        if "habits" in self.app.data and index < len(self.app.data["habits"]):
            del self.app.data["habits"][index]
            self.app.save_data()
            self.load_habits()
    
    def update_theme(self):
        super().update_theme()
        t = self.theme
        self.habit_entry.config(bg=t["entry"], fg=t["text"])
        self.add_btn.config(bg=t["accent"])
        self.scroll_frame.update_bg(t["bg"])
        self.load_habits()


# ============== CLOCK ==============
class ClockWidget(BaseWidget):
    """Digital Clock"""
    
    def __init__(self, master, app):
        super().__init__(master, "🕐 Clock", "clock", app, (220, 150), (150, 100))
        self.create_content()
        self.update_clock()
    
    def create_content(self):
        self.time_label = tk.Label(
            self.content, text="", bg=self.theme["bg"],
            fg=self.theme["accent"], font=FONTS["clock"]
        )
        self.time_label.pack(expand=True)
        
        self.date_label = tk.Label(
            self.content, text="", bg=self.theme["bg"],
            fg=self.theme["text"], font=FONTS["small"]
        )
        self.date_label.pack(pady=(0, 5))
    
    def update_clock(self):
        now = datetime.now()
        self.time_label.config(text=now.strftime("%H:%M:%S"))
        self.date_label.config(text=now.strftime("%a, %b %d"))
        self.window.after(1000, self.update_clock)
    
    def update_theme(self):
        super().update_theme()
        self.time_label.config(bg=self.theme["bg"], fg=self.theme["accent"])
        self.date_label.config(bg=self.theme["bg"], fg=self.theme["text"])


# ============== MAIN APPLICATION ==============
class DesktopWidgetsApp:
    """Main Application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        
        self.load_data()
        self.widgets = {}
        self.create_widgets()
        self.create_control_panel()
    
    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except:
                self.data = self.get_default_data()
        else:
            self.data = self.get_default_data()
    
    def get_default_data(self):
        return {
            "theme": "🌊 Ocean Blue",
            "widget_themes": {},
            "calendar_events": {},
            "todos": [],
            "day_planner": {},
            "week_planner": {},
            "monthly_planner": {},
            "sticky_notes": [],
            "habits": [],
            "widget_positions": {},
            "widget_sizes": {},
            "hidden_widgets": []
        }
    
    def save_data(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving: {e}")
    
    def create_widgets(self):
        hidden = self.data.get("hidden_widgets", [])
        
        widget_classes = {
            "calendar": CalendarWidget,
            "todo": TodoWidget,
            "day_planner": DayPlannerWidget,
            "week_planner": WeekPlannerWidget,
            "monthly_planner": MonthlyPlannerWidget,
            "sticky_notes": StickyNotesWidget,
            "pomodoro": PomodoroWidget,
            "habit_tracker": HabitTrackerWidget,
            "clock": ClockWidget
        }
        
        for widget_id, widget_class in widget_classes.items():
            self.widgets[widget_id] = widget_class(self.root, self)
            if widget_id in hidden:
                self.widgets[widget_id].window.withdraw()
    
    def create_control_panel(self):
        self.control = tk.Toplevel(self.root)
        self.control.title("🎮 Control Panel")
        self.control.geometry("280x520")
        self.control.resizable(False, False)
        self.control.attributes('-topmost', True)
        
        theme = THEMES.get(self.data.get("theme", "🌊 Ocean Blue"), THEMES["🌊 Ocean Blue"])
        self.control.configure(bg=theme["bg"])
        
        tk.Label(
            self.control, text="🖥️ Desktop Widgets",
            bg=theme["header"], fg=theme["text"],
            font=("Segoe UI Semibold", 13), pady=10
        ).pack(fill="x")
        
        # Info about desktop integration
        tk.Label(
            self.control,
            text="✨ Widgets stay on desktop!\n(Won't hide on 3-finger swipe)",
            bg=theme["highlight"], fg=theme["text"],
            font=FONTS["tiny"], pady=5
        ).pack(fill="x", padx=8, pady=5)
        
        # Autostart
        auto_frame = tk.LabelFrame(
            self.control, text="⚡ Startup",
            bg=theme["bg"], fg=theme["text"], font=FONTS["small"]
        )
        auto_frame.pack(fill="x", padx=8, pady=5)
        
        self.autostart_var = tk.BooleanVar(value=is_autostart_enabled())
        
        tk.Checkbutton(
            auto_frame, text="🚀 Start with Windows",
            variable=self.autostart_var, bg=theme["bg"], fg=theme["text"],
            font=FONTS["small"], activebackground=theme["bg"],
            selectcolor=theme["entry"], command=self.toggle_autostart
        ).pack(anchor="w", padx=8, pady=3)
        
        self.autostart_status = tk.Label(
            auto_frame, text="", bg=theme["bg"], font=FONTS["tiny"]
        )
        self.autostart_status.pack(anchor="w", padx=8)
        self.update_autostart_status()
        
        # Widgets
        widgets_frame = tk.LabelFrame(
            self.control, text="📦 Widgets",
            bg=theme["bg"], fg=theme["text"], font=FONTS["small"]
        )
        widgets_frame.pack(fill="x", padx=8, pady=5)
        
        widget_names = {
            "calendar": "📅 Calendar",
            "todo": "✅ To-Do",
            "day_planner": "📆 Day Planner",
            "week_planner": "📋 Week Planner",
            "monthly_planner": "🎯 Monthly",
            "sticky_notes": "📝 Sticky Notes",
            "pomodoro": "🍅 Pomodoro",
            "habit_tracker": "📊 Habits",
            "clock": "🕐 Clock"
        }
        
        self.widget_vars = {}
        hidden = self.data.get("hidden_widgets", [])
        
        for widget_id, widget_name in widget_names.items():
            var = tk.BooleanVar(value=widget_id not in hidden)
            self.widget_vars[widget_id] = var
            
            tk.Checkbutton(
                widgets_frame, text=widget_name, variable=var,
                bg=theme["bg"], fg=theme["text"], font=FONTS["small"],
                activebackground=theme["bg"], selectcolor=theme["entry"],
                command=lambda wid=widget_id: self.toggle_widget(wid)
            ).pack(anchor="w", padx=8, pady=1)
        
        # Buttons
        btn_frame = tk.Frame(self.control, bg=theme["bg"])
        btn_frame.pack(fill="x", padx=8, pady=5)
        
        tk.Button(
            btn_frame, text="👁️ Show All", command=self.show_all,
            bg=theme["button"], fg=theme["text"], font=FONTS["button"],
            bd=0, padx=10, cursor="hand2"
        ).pack(side="left", padx=3)
        
        tk.Button(
            btn_frame, text="🙈 Hide All", command=self.hide_all,
            bg=theme["button"], fg=theme["text"], font=FONTS["button"],
            bd=0, padx=10, cursor="hand2"
        ).pack(side="left", padx=3)
        
        # Exit
        tk.Button(
            self.control, text="❌ Exit", command=self.exit_app,
            bg="#E74C3C", fg="white", font=FONTS["button"],
            bd=0, padx=15, pady=5, cursor="hand2"
        ).pack(pady=8)
        
        self.control.protocol("WM_DELETE_WINDOW", self.minimize_control)
    
    def toggle_autostart(self):
        if self.autostart_var.get():
            enable_autostart()
        else:
            disable_autostart()
        self.update_autostart_status()
    
    def update_autostart_status(self):
        if is_autostart_enabled():
            self.autostart_status.config(text="✅ Enabled", fg="#27AE60")
        else:
            self.autostart_status.config(text="❌ Disabled", fg="#E74C3C")
    
    def update_control_panel(self):
        hidden = self.data.get("hidden_widgets", [])
        for widget_id, var in self.widget_vars.items():
            var.set(widget_id not in hidden)
    
    def minimize_control(self):
        self.control.iconify()
    
    def toggle_widget(self, widget_id):
        if self.widget_vars[widget_id].get():
            self.widgets[widget_id].show_widget()
        else:
            self.widgets[widget_id].hide_widget()
    
    def show_all(self):
        for widget_id, widget in self.widgets.items():
            widget.show_widget()
            self.widget_vars[widget_id].set(True)
    
    def hide_all(self):
        for widget_id, widget in self.widgets.items():
            widget.hide_widget()
            self.widget_vars[widget_id].set(False)
    
    def exit_app(self):
        self.save_data()
        self.root.quit()
        self.root.destroy()
        sys.exit()
    
    def run(self):
        self.root.mainloop()


# ============== ENTRY POINT ==============
if __name__ == "__main__":
    app = DesktopWidgetsApp()
    app.run()
