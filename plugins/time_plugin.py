TRIGGERS = ["what time", "current time", "/time", "what's the time"]
DESCRIPTION = "Shows current date and time"

def handle(message: str) -> str:
    from datetime import datetime
    now = datetime.now()
    return (
        f"🕒  {now.strftime('%I:%M %p')}\n"
        f"📅  {now.strftime('%A, %B %d, %Y')}"
    )
