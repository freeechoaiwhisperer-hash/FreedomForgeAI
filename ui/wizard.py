import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import random
import threading
import time

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".freedomforge", "config.json")

MIRANDA_QUOTES = [
    "Rome wasn't built in a day, and neither is a local AI!",
    "Fun fact: I don't need coffee to work. You probably do though.",
    "Optimizing the bits and bobs. Almost there!",
    "You have excellent taste in AI software.",
    "Loading genius... please hold.",
    "The future is local. And it's looking good.",
    "I searched the internet for wisdom. Then I remembered — we don't need the internet.",
]


class SetupWizard:
    def __init__(self, root, on_complete=None, theme_name=None):
        self.root = root
        self.on_complete = on_complete
        self.theme_name = theme_name
        self.root.title("FreedomForge AI — First Run Setup")
        self.root.geometry("520x420")
        self.root.resizable(False, False)

        self.steps = ["welcome", "license", "folder", "download", "finish"]
        self.current_step_idx = 0
        self.models_path = ""
        self._popup_open = False

        self.main_frame = tk.Frame(self.root, padx=30, pady=20)
        self.main_frame.pack(expand=True, fill="both")
        self.show_step()

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_step(self):
        self.clear_frame()
        step = self.steps[self.current_step_idx]
        {
            "welcome": self.ui_welcome,
            "license": self.ui_license,
            "folder": self.ui_folder,
            "download": self.ui_download,
            "finish": self.ui_finish,
        }[step]()

    def next_step(self):
        if self.current_step_idx < len(self.steps) - 1:
            self.current_step_idx += 1
            self.show_step()

    def ui_welcome(self):
        tk.Label(self.main_frame, text="Miranda says:", font=("Arial", 11, "bold")).pack(pady=(10, 4))
        tk.Label(self.main_frame,
            text='"Hi! I\'m Miranda, your setup guide.\nLet\'s get you started."',
            wraplength=420, font=("Arial", 11), justify="center").pack(pady=16)
        tk.Label(self.main_frame,
            text="FreedomForge AI runs entirely on your computer.\nNo cloud. No subscription. No paywall. Ever.",
            wraplength=420, fg="#555").pack(pady=6)
        tk.Button(self.main_frame, text="Let's Go", command=self.next_step, width=16).pack(pady=24)

    def ui_license(self):
        tk.Label(self.main_frame, text="License Agreement", font=("Arial", 12, "bold")).pack(pady=8)
        box = tk.Text(self.main_frame, height=10, width=54, wrap="word")
        box.insert("1.0",
            "FreedomForge AI — Free & Open Source Software\n\n"
            "Free for personal use. Always.\n\n"
            "Commercial use (businesses over $250K revenue) requires a license.\n\n"
            "You may not resell or rebrand this software.\n\n"
            "By clicking Agree you accept these terms.")
        box.config(state="disabled")
        box.pack(pady=8)
        tk.Button(self.main_frame, text="I Agree", command=self.next_step, width=16).pack(pady=8)

    def ui_folder(self):
        tk.Label(self.main_frame, text="Choose Models Folder", font=("Arial", 12, "bold")).pack(pady=10)
        tk.Label(self.main_frame, text="Where should FreedomForge store your AI models?").pack()
        self.path_label = tk.Label(self.main_frame, text="No folder selected yet", fg="grey")
        self.path_label.pack(pady=10)

        def browse():
            path = filedialog.askdirectory()
            if path:
                self.models_path = path
                self.path_label.config(text=path, fg="black")

        tk.Button(self.main_frame, text="Browse...", command=browse).pack(pady=4)

        def continue_if_selected():
            if self.models_path:
                self.next_step()
            else:
                messagebox.showwarning("Hold on", "Please choose a folder first.")

        tk.Button(self.main_frame, text="Continue", command=continue_if_selected, width=16).pack(pady=16)

    def ui_download(self):
        tk.Label(self.main_frame, text="Setting Things Up...", font=("Arial", 12, "bold")).pack(pady=10)
        tk.Label(self.main_frame, text="Preparing your first AI model. This may take a moment.").pack()
        self.progress_canvas = tk.Canvas(self.main_frame, width=380, height=22, bg="#eee", highlightthickness=1)
        self.progress_canvas.pack(pady=20)
        self.progress_rect = self.progress_canvas.create_rectangle(0, 0, 0, 22, fill="#4a90d9", outline="")
        self.status_label = tk.Label(self.main_frame, text="Starting...", fg="#555")
        self.status_label.pack()
        threading.Thread(target=self._run_download, daemon=True).start()

    def _run_download(self):
        popup_targets = sorted(random.sample(range(20, 85), 2))
        popup_idx = 0
        for i in range(1, 101):
            time.sleep(0.04)
            self.root.after(0, self._update_progress, i)
            if popup_idx < len(popup_targets) and i == popup_targets[popup_idx]:
                self.root.after(0, self._show_miranda_popup)
                popup_idx += 1
                time.sleep(0.5)
        self.root.after(600, self.next_step)

    def _update_progress(self, pct):
        self.progress_canvas.coords(self.progress_rect, 0, 0, pct * 3.8, 22)
        self.status_label.config(text=f"{pct}% complete")

    def _show_miranda_popup(self):
        if self._popup_open:
            return
        self._popup_open = True
        quote = random.choice(MIRANDA_QUOTES)
        popup = tk.Toplevel(self.root)
        popup.title("Miranda says...")
        popup.geometry("320x140")
        popup.resizable(False, False)
        # grab_set() removed — popup appears without stealing focus
        tk.Label(popup, text="Miranda says:", font=("Arial", 10, "bold")).pack(pady=(14, 4))
        tk.Label(popup, text=f'"{quote}"', wraplength=280, font=("Arial", 10), justify="center").pack(pady=6)
        def close():
            self._popup_open = False
            popup.destroy()
        tk.Button(popup, text="OK", command=close, width=10).pack(pady=8)
        popup.protocol("WM_DELETE_WINDOW", close)

    def ui_finish(self):
        tk.Label(self.main_frame, text="You're all set!", font=("Arial", 14, "bold"), fg="#2a7a2a").pack(pady=20)
        tk.Label(self.main_frame,
            text="FreedomForge AI is ready.\nMiranda is signing off — she'll be in the About page if you want to say hi.",
            wraplength=420, justify="center").pack(pady=10)
        def finalize():
            self._save_config()
            if self.on_complete:
                self.on_complete()
            else:
                self.root.destroy()
        tk.Button(self.main_frame, text="Launch FreedomForge", command=finalize, width=22).pack(pady=24)

    def _save_config(self):
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        existing = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE) as f:
                    existing = json.load(f)
            except Exception:
                pass
        existing.update({"first_run_complete": True, "models_path": self.models_path})
        with open(CONFIG_FILE, "w") as f:
            json.dump(existing, f, indent=2)


# Keep old name as alias for backwards compatibility
class FreedomForgeWizard:
    def __init__(self, root):
        self.root = root
        self.root.title("FreedomForge AI — First Run Setup")
        self.root.geometry("520x420")
        self.root.resizable(False, False)

        self.steps = ["welcome", "license", "folder", "download", "finish"]
        self.current_step_idx = 0
        self.models_path = ""
        self._popup_open = False

        self.main_frame = tk.Frame(self.root, padx=30, pady=20)
        self.main_frame.pack(expand=True, fill="both")
        self.show_step()

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_step(self):
        self.clear_frame()
        step = self.steps[self.current_step_idx]
        {
            "welcome": self.ui_welcome,
            "license": self.ui_license,
            "folder": self.ui_folder,
            "download": self.ui_download,
            "finish": self.ui_finish,
        }[step]()

    def next_step(self):
        if self.current_step_idx < len(self.steps) - 1:
            self.current_step_idx += 1
            self.show_step()

    def ui_welcome(self):
        tk.Label(self.main_frame, text="Miranda says:", font=("Arial", 11, "bold")).pack(pady=(10, 4))
        tk.Label(self.main_frame,
            text='"Hi! I\'m Miranda, your setup guide.\nLet\'s get you started."',
            wraplength=420, font=("Arial", 11), justify="center").pack(pady=16)
        tk.Label(self.main_frame,
            text="FreedomForge AI runs entirely on your computer.\nNo cloud. No subscription. No paywall. Ever.",
            wraplength=420, fg="#555").pack(pady=6)
        tk.Button(self.main_frame, text="Let's Go", command=self.next_step, width=16).pack(pady=24)

    def ui_license(self):
        tk.Label(self.main_frame, text="License Agreement", font=("Arial", 12, "bold")).pack(pady=8)
        box = tk.Text(self.main_frame, height=10, width=54, wrap="word")
        box.insert("1.0",
            "FreedomForge AI — Free & Open Source Software\n\n"
            "Free for personal use. Always.\n\n"
            "Commercial use (businesses over $250K revenue) requires a license.\n\n"
            "You may not resell or rebrand this software.\n\n"
            "By clicking Agree you accept these terms.")
        box.config(state="disabled")
        box.pack(pady=8)
        tk.Button(self.main_frame, text="I Agree", command=self.next_step, width=16).pack(pady=8)

    def ui_folder(self):
        tk.Label(self.main_frame, text="Choose Models Folder", font=("Arial", 12, "bold")).pack(pady=10)
        tk.Label(self.main_frame, text="Where should FreedomForge store your AI models?").pack()
        self.path_label = tk.Label(self.main_frame, text="No folder selected yet", fg="grey")
        self.path_label.pack(pady=10)

        def browse():
            path = filedialog.askdirectory()
            if path:
                self.models_path = path
                self.path_label.config(text=path, fg="black")

        tk.Button(self.main_frame, text="Browse...", command=browse).pack(pady=4)

        def continue_if_selected():
            if self.models_path:
                self.next_step()
            else:
                messagebox.showwarning("Hold on", "Please choose a folder first.")

        tk.Button(self.main_frame, text="Continue", command=continue_if_selected, width=16).pack(pady=16)

    def ui_download(self):
        tk.Label(self.main_frame, text="Setting Things Up...", font=("Arial", 12, "bold")).pack(pady=10)
        tk.Label(self.main_frame, text="Preparing your first AI model. This may take a moment.").pack()
        self.progress_canvas = tk.Canvas(self.main_frame, width=380, height=22, bg="#eee", highlightthickness=1)
        self.progress_canvas.pack(pady=20)
        self.progress_rect = self.progress_canvas.create_rectangle(0, 0, 0, 22, fill="#4a90d9", outline="")
        self.status_label = tk.Label(self.main_frame, text="Starting...", fg="#555")
        self.status_label.pack()
        threading.Thread(target=self._run_download, daemon=True).start()

    def _run_download(self):
        popup_targets = sorted(random.sample(range(20, 85), 2))
        popup_idx = 0
        for i in range(1, 101):
            time.sleep(0.04)
            self.root.after(0, self._update_progress, i)
            if popup_idx < len(popup_targets) and i == popup_targets[popup_idx]:
                self.root.after(0, self._show_miranda_popup)
                popup_idx += 1
                time.sleep(0.5)
        self.root.after(600, self.next_step)

    def _update_progress(self, pct):
        self.progress_canvas.coords(self.progress_rect, 0, 0, pct * 3.8, 22)
        self.status_label.config(text=f"{pct}% complete")

    def _show_miranda_popup(self):
        if self._popup_open:
            return
        self._popup_open = True
        quote = random.choice(MIRANDA_QUOTES)
        popup = tk.Toplevel(self.root)
        popup.title("Miranda says...")
        popup.geometry("320x140")
        popup.resizable(False, False)
        # grab_set() removed — popup appears without stealing focus
        tk.Label(popup, text="Miranda says:", font=("Arial", 10, "bold")).pack(pady=(14, 4))
        tk.Label(popup, text=f'"{quote}"', wraplength=280, font=("Arial", 10), justify="center").pack(pady=6)
        def close():
            self._popup_open = False
            popup.destroy()
        tk.Button(popup, text="OK", command=close, width=10).pack(pady=8)
        popup.protocol("WM_DELETE_WINDOW", close)

    def ui_finish(self):
        tk.Label(self.main_frame, text="You're all set!", font=("Arial", 14, "bold"), fg="#2a7a2a").pack(pady=20)
        tk.Label(self.main_frame,
            text="FreedomForge AI is ready.\nMiranda is signing off — she'll be in the About page if you want to say hi.",
            wraplength=420, justify="center").pack(pady=10)
        def finalize():
            self._save_config()
            self.root.destroy()
        tk.Button(self.main_frame, text="Launch FreedomForge", command=finalize, width=22).pack(pady=24)

    def _save_config(self):
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        existing = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE) as f:
                    existing = json.load(f)
            except Exception:
                pass
        existing.update({"first_run_complete": True, "models_path": self.models_path})
        with open(CONFIG_FILE, "w") as f:
            json.dump(existing, f, indent=2)


def should_run_wizard() -> bool:
    if not os.path.exists(CONFIG_FILE):
        return True
    try:
        with open(CONFIG_FILE) as f:
            return not json.load(f).get("first_run_complete", False)
    except Exception:
        return True


if __name__ == "__main__":
    if should_run_wizard():
        root = tk.Tk()
        FreedomForgeWizard(root)
        root.mainloop()
