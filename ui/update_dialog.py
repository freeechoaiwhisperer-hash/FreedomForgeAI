# ============================================================
#  FreedomForge AI — ui/update_dialog.py
#  Update available notification dialog
# ============================================================

import webbrowser
import customtkinter as ctk


class UpdateDialog(ctk.CTkToplevel):

    def __init__(self, parent, theme: dict, update_info: dict,
                 current_version: str = "unknown"):
        super().__init__(parent)
        self.title("Update Available")
        self.geometry("520x360")
        self.resizable(False, False)
        self.configure(fg_color=theme["bg_panel"])
        self.transient(self.master)
        self.lift()

        T = theme

        ctk.CTkLabel(
            self, text="✨  New Version Available",
            font=("Arial", 16, "bold"),
            text_color=T["gold"],
        ).pack(pady=(20, 4))

        ctk.CTkLabel(
            self,
            text=f"Current: v{current_version}  →  Latest: v{update_info.get('latest_version', '?')}",
            font=("Arial", 13),
            text_color=T["text_secondary"],
        ).pack()

        notes_frame = ctk.CTkFrame(self, fg_color=T["bg_card"], corner_radius=10)
        notes_frame.pack(fill="both", expand=True, padx=20, pady=12)

        ctk.CTkLabel(
            notes_frame, text="What's new:",
            font=("Arial", 12, "bold"),
            text_color=T["accent2"],
        ).pack(anchor="w", padx=12, pady=(10, 0))

        notes_box = ctk.CTkTextbox(
            notes_frame,
            font=("Arial", 11),
            fg_color=T["bg_deep"],
            text_color=T["text_primary"],
            wrap="word",
            height=130,
        )
        notes_box.pack(fill="both", expand=True, padx=12, pady=8)
        notes = update_info.get("release_notes", "No release notes provided.")
        notes_box.insert("1.0", notes[:500])
        notes_box.configure(state="disabled")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=16)

        ctk.CTkButton(
            btn_frame,
            text="Download Update",
            width=160, height=38,
            fg_color=T["accent"],
            hover_color=T["accent_hover"],
            command=lambda: (
                webbrowser.open(update_info.get("download_url", "")),
                self.destroy()
            ),
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_frame,
            text="Later",
            width=120, height=38,
            fg_color=T["bg_hover"],
            hover_color=T["bg_card"],
            text_color=T["text_secondary"],
            command=self.destroy,
        ).pack(side="left", padx=8)
