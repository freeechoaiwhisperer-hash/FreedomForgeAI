TRIGGERS = ["joke", "tell me a joke", "/joke"]
DESCRIPTION = "Tells a random programming joke"

def handle(message: str) -> str:
    import random
    jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs.",
        "How many programmers does it take to change a lightbulb? None, that's a hardware problem.",
        "Why was the JavaScript developer sad? He didn't know how to null his feelings.",
        "A SQL query walks into a bar, walks up to two tables and asks: Can I join you?",
        "Why do Java developers wear glasses? Because they don't C#.",
        "There are 10 types of people — those who understand binary and those who don't.",
        "I would tell you a UDP joke but you might not get it.",
    ]
    return "😂  " + random.choice(jokes)
