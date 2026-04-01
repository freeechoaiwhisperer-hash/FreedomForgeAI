TRIGGERS = ["calculate", "calc", "math", "/calc"]
DESCRIPTION = "Simple math calculator — try: calc 2 + 2"

def handle(message: str) -> str:
    try:
        expr = message.lower()
        for word in ["calculate", "calc", "math", "/calc"]:
            expr = expr.replace(word, "")
        expr = expr.strip()
        if not expr:
            return "Usage: calc 2 + 2"
        # Safe eval — no builtins, no imports
        result = eval(expr, {"__builtins__": {}}, {})
        return f"✅  {expr} = {result}"
    except Exception:
        return "❌  Invalid math expression. Try: calc 10 * 5"
