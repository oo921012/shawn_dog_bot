import json
from linebot.models import TextSendMessage

def add_admin(event, line_bot_api):
    uid = event.source.user_id
    cfg = json.load(open("config.json", "r", encoding="utf-8"))
    if uid not in cfg["admins"]:
        cfg["admins"].append(uid)
        json.dump(cfg, open("config.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        msg = "✅ 已將你加入管理員列表。"
    else:
        msg = "⚠️ 你已是管理員。"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))

def add_blacklist(event, line_bot_api):
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="🚷 黑名單功能尚未啟用（可擴充封鎖行為）"))
