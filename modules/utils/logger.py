import datetime, os

def log(text):
    if not os.path.exists("logs"):
        os.makedirs("logs")
    with open("logs/bot.log", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.datetime.now()}] {text}\n")
