# ============================================================
#  FreedomForge AI — ui/terms_tab.py
#  Terms of Service — shown on first launch and in app
# ============================================================

import customtkinter as ctk
from core import config

TERMS_TEXT = """
FREEDOMFORGE AI — TERMS OF SERVICE & COMMUNITY AGREEMENT
Version 1.0 — 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ABOUT THIS SOFTWARE
───────────────────
FreedomForge AI is free, open source software built by Ryan Dennison,
a single father, for his son and the world. This software is dedicated
to Miranda. She will never be forgotten.

The mission is simple: end every paywall and knowledge barrier that
stops regular people from having full access to the power of AI and
computers. This software will always be free for personal use.


WHO CAN USE THIS — FREE FOREVER
────────────────────────────────
• Personal use — always free
• Family use — always free
• Educational use — always free
• Nonprofits — always free
• Small organizations (under $250,000 annual revenue) — always free

Large commercial organizations (over $250,000 annual revenue) that use
this software in products or services must contact the developer for a
commercial license. Commercial license fees fund continued development
and keep this software free for everyone else.


WHAT THIS SOFTWARE DOES
───────────────────────
FreedomForge AI runs AI models entirely on your computer. Your
conversations, data, and files never leave your machine unless you
explicitly choose to share them. We do not collect data. We do not
track you. We do not have servers watching your conversations.


AGENT MODE & COMPUTER CONTROL
──────────────────────────────
Agent Mode allows the AI to execute commands on your computer.

BY ENABLING AGENT MODE YOU ACKNOWLEDGE:
• You are giving the AI permission to run commands on your system
• You are responsible for reviewing any commands before execution
• You can disable Agent Mode instantly at any time
• FreedomForge AI is not responsible for any unintended system changes
• Use Agent Mode only when you need it and disable it when you don't


ACCEPTABLE USE
──────────────
You MAY:
• Use this software for any legal personal or professional purpose
• Modify it and share your changes under the same open source license
• Use Agent Mode for legitimate automation on systems you own
• Use it for authorized security testing on systems you have permission to test
• Build plugins and contribute them to the community

You MAY NOT:
• Use this software to access systems without authorization
• Use Agent Mode to harm, damage, or compromise other people's systems
• Use this software for illegal surveillance or stalking
• Remove the open source license or Miranda's dedication from forks
• Use this software in a commercial product without a commercial license
  if your organization exceeds $250,000 annual revenue


SECURITY TESTING DISCLAIMER
────────────────────────────
FreedomForge AI may be used for legitimate penetration testing and
security research on systems you own or have written authorization to test.

UNAUTHORIZED ACCESS TO COMPUTER SYSTEMS IS ILLEGAL in most jurisdictions
including the United States (Computer Fraud and Abuse Act), United Kingdom
(Computer Misuse Act), and the European Union (Directive on Attacks Against
Information Systems).

The developer accepts no liability for illegal use of this software.
You have been informed. Choose wisely.


PRIVACY
───────
• No data is collected by FreedomForge AI
• Your conversations stay on your computer
• Crash reports are only sent if you explicitly choose to send them
• Crash reports are anonymized before sending — no personal info included
• Your encryption key never leaves your machine
• We have no servers, no accounts, no tracking


DONATIONS
─────────
FreedomForge AI is free. If this software has helped you and you want
to support its continued development, donations are welcome via
cryptocurrency. Details on the GitHub page.

All donations go directly to:
• Bug fixes and updates
• Adding new features
• Keeping the servers running (if needed in future)
• Making this software better for everyone

There is no obligation to donate. This software will remain free
regardless of whether donations are received.


FUTURE PAID FEATURES
────────────────────
If and when paid features are introduced, they will only be for
optional services that require ongoing infrastructure costs (such as
cloud-based features). The core local AI interface will always be free.
No existing free features will ever be moved behind a paywall.


WARRANTY DISCLAIMER
───────────────────
THIS SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND.
THE DEVELOPER IS NOT LIABLE FOR ANY DAMAGES ARISING FROM ITS USE.

This is an early prototype built by one person in their spare time.
Things may break. Please report bugs on GitHub.
I am doing my best. Bear with me.


CONTACT & REPORTING BUGS
─────────────────────────
Found a bug? Please report it on GitHub.
Every bug report makes this better for everyone.

Crash reports can be submitted anonymously from within the app.
Your privacy is respected even when reporting issues.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Built by Ryan Dennison for his son and the world.
Utilizing AI assistance.

🪄 Dedicated to Miranda. She will never be forgotten. 🪄
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


class TermsDialog(ctk.CTkToplevel):
    """First launch terms dialog — must be accepted to proceed."""

    def __init__(self, parent, on_accept, on_decline, theme: dict):
        super().__init__(parent)
        self.on_accept  = on_accept
        self.on_decline = on_decline
        T               = theme

        self.title("FreedomForge AI — Terms of Service")
        self.geometry("780x620")
        self.resizable(True, True)
        self.configure(fg_color=T["bg_panel"])
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", on_decline)

        # Header
        ctk.CTkLabel(
            self,
            text="⚒️  Before You Start",
            font=("Arial", 18, "bold"),
            text_color=T["gold"],
        ).pack(pady=(18, 2))

        ctk.CTkLabel(
            self,
            text="Please read and accept the Terms of Service to continue.",
            font=("Arial", 12),
            text_color=T["text_secondary"],
        ).pack(pady=(0, 10))

        # Terms text
        box = ctk.CTkTextbox(
            self,
            font=("Courier", 11),
            fg_color=T["bg_deep"],
            text_color=T["text_secondary"],
            wrap="word",
            state="normal",
        )
        box.pack(fill="both", expand=True, padx=16, pady=0)
        box.insert("1.0", TERMS_TEXT.strip())
        box.configure(state="disabled")

        # Accept row
        foot = ctk.CTkFrame(self, fg_color="transparent")
        foot.pack(fill="x", padx=16, pady=14)

        self._agree_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            foot,
            text="I have read and agree to the Terms of Service",
            variable=self._agree_var,
            font=("Arial", 13),
            text_color=T["text_primary"],
            command=self._on_checkbox,
        ).pack(side="left")

        self._accept_btn = ctk.CTkButton(
            foot,
            text="Accept & Continue  →",
            width=210, height=42,
            corner_radius=21,
            fg_color=T["bg_hover"],
            hover_color=T["bg_hover"],
            text_color=T["text_dim"],
            font=("Arial", 13, "bold"),
            state="disabled",
            command=self._accept,
        )
        self._accept_btn.pack(side="right")

        ctk.CTkButton(
            foot,
            text="Decline",
            width=100, height=42,
            corner_radius=21,
            fg_color="transparent",
            hover_color=T["bg_hover"],
            text_color=T["text_secondary"],
            command=on_decline,
        ).pack(side="right", padx=8)

    def _on_checkbox(self):
        if self._agree_var.get():
            self._accept_btn.configure(
                state="normal",
                fg_color="#1a5a9a",
                hover_color="#0d3d70",
                text_color="#ffffff",
            )
        else:
            self._accept_btn.configure(
                state="disabled",
                fg_color="#1a1a1a",
                text_color="#333333",
            )

    def _accept(self):
        if self._agree_var.get():
            config.set("terms_accepted", True)
            self.destroy()
            self.on_accept()


class TermsPanel(ctk.CTkFrame):
    """In-app Terms panel accessible from nav."""

    def __init__(self, master, theme: dict, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.theme = theme
        self._build()

    def apply_theme(self, theme: dict):
        self.theme = theme
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        T = self.theme

        ctk.CTkLabel(
            self,
            text="📋  Terms of Service",
            font=("Arial", 22, "bold"),
            text_color=T["text_primary"],
        ).pack(pady=(24, 4), padx=24, anchor="w")

        ctk.CTkLabel(
            self,
            text="Last updated: March 2026  •  Version 1.0",
            font=("Arial", 11),
            text_color=T["text_secondary"],
        ).pack(padx=24, anchor="w", pady=(0, 12))

        box = ctk.CTkTextbox(
            self,
            font=("Courier", 11),
            fg_color=T["bg_deep"],
            text_color=T["text_secondary"],
            wrap="word",
            state="normal",
        )
        box.pack(
            fill="both", expand=True,
            padx=16, pady=(0, 16))
        box.insert("1.0", TERMS_TEXT.strip())
        box.configure(state="disabled")
