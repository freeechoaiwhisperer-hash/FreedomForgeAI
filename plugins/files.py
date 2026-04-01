TRIGGERS = ["list files", "show files", "ls", "/files"]
DESCRIPTION = "Lists files in the FreedomForge folder"

def handle(message: str) -> str:
    import os
    from utils.paths import APP_ROOT
    try:
        files = sorted(os.listdir(str(APP_ROOT)))
        visible = [f for f in files if not f.startswith(".")][:30]
        return "📁  Files in FreedomForge:\n" + "\n".join(f"  • {f}" for f in visible)
    except Exception as e:
        return f"❌  Could not list files: {e}"
