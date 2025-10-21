import json, os, datetime
from linebot.models import TextSendMessage

def sign_in(event, line_bot_api):
    uid = event.source.user_id
    today = str(datetime.date.today())
    db = {}
    if os.path.exists("database/checkin.json"):
        db = json.load(open("database/checkin.json", "r", encoding="utf-8"))
    db[uid] = today
    json.dump(db, open("database/checkin.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"📅 shawn的狗：簽到成功！({today})"))

def show_inactive(event, line_bot_api):
    if not os.path.exists("database/checkin.json"):
        msg = "還沒有人簽到過。"
    else:
        db = json.load(open("database/checkin.json", "r", encoding="utf-8"))
        cutoff = datetime.date.today() - datetime.timedelta(days=3)
        inactive = [u for u, d in db.items() if datetime.date.fromisoformat(d) < cutoff]
        msg = f"潛水名單（3天未簽到）共 {len(inactive)} 人。"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
