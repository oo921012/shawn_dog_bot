# app.py (production-stable, aligned with new manage.py)
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    MemberJoinedEvent, MemberLeftEvent
)
from linebot.exceptions import InvalidSignatureError, LineBotApiError
import json, os

# ===== 匯入你的功能模組 =====
from modules import protect, manage, helper, checkin, backup

app = Flask(__name__)

# ===== 載入設定 =====
with open("config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)
CHANNEL_ACCESS_TOKEN = cfg["channel_access_token"]
CHANNEL_SECRET = cfg["channel_secret"]

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 健康檢查
@app.route("/", methods=["GET"])
def home():
    return "OK", 200

# ===== Webhook 入口 =====
@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_data(as_text=True)                    # 只能讀一次
    signature = request.headers.get("X-Line-Signature", "")

    # 方便除錯：長度要 > 0
    app.logger.info(f"[LINE] sig_len={len(signature)} body_len={len(body)}")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.warning("[LINE] Invalid signature — 請檢查 Channel secret")
        return "Invalid signature", 400
    except LineBotApiError as e:
        app.logger.exception(e)
        return "LINE API error", 500
    except Exception as e:
        app.logger.exception(e)
        return "Server error", 500

    return "OK", 200

# ===== 文字訊息處理 =====
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = (event.message.text or "").strip()

    # 基礎網址防護
    if "http://" in text or "https://" in text:
        protect.link_guard(event, line_bot_api)
        return

    # 指令路由（管理員 / 黑名單）
    if text.startswith("/addadmin"):
        manage.add_admin_cmd(event, line_bot_api)
    elif text.startswith("/deladmin"):
        manage.del_admin_cmd(event, line_bot_api)
    elif text.startswith("/listadmin"):
        manage.list_admins(event, line_bot_api)
    elif text.startswith("/ban"):
        manage.add_blacklist(event, line_bot_api)
    elif text.startswith("/unban"):
        manage.remove_blacklist(event, line_bot_api)
    elif text.startswith("/listban"):
        manage.list_blacklist(event, line_bot_api)

    # 其他助手功能
    elif text.startswith("/tagall"):
        helper.tag_all(event, line_bot_api)
    elif text.startswith("/draw"):
        helper.draw_lottery(event, line_bot_api)
    elif text.startswith("/checkin"):
        checkin.sign_in(event, line_bot_api)
    elif text.startswith("/inactive"):
        checkin.show_inactive(event, line_bot_api)
    elif text.startswith("/backup"):
        backup.export_members(event, line_bot_api)
    else:
        # 非指令的預設回覆（可自行移除）
        try:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=(
                        "指令：\n"
                        "/addadmin /deladmin /listadmin\n"
                        "/ban /unban /listban\n"
                        "/tagall /draw /checkin /inactive /backup"
                    )
                )
            )
        except Exception:
            pass

# ===== 成員加入/離開 =====
@handler.add(MemberJoinedEvent)
def joined(event):
    protect.member_join(event, line_bot_api)

@handler.add(MemberLeftEvent)
def left(event):
    protect.member_left(event, line_bot_api)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render 會注入 PORT；本機預設 10000
    app.run(host="0.0.0.0", port=port)
