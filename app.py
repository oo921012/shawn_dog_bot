from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, MemberJoinedEvent, MemberLeftEvent
)
from linebot.exceptions import InvalidSignatureError, LineBotApiError
import json
import os

# ====== 你的功能模組 ======
from modules import protect, manage, helper, checkin, backup

app = Flask(__name__)

# ====== 載入設定 ======
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

line_bot_api = LineBotApi(config["channel_access_token"])
handler = WebhookHandler(config["channel_secret"])

# 健康檢查
@app.route("/", methods=["GET"])
def home():
    return "OK", 200

# ====== Webhook 入口 ======
@app.route("/callback", methods=['POST'])
def callback():
    # 1) 取簽章與 body（body 只能讀一次）
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)

    app.logger.info(f"[LINE] signature_len={len(signature)} body_len={len(body)}")

    # 2) 驗簽與處理
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.warning("[LINE] Invalid signature (check Channel Secret)")
        return "Invalid signature", 400
    except LineBotApiError as e:
        app.logger.exception(e)
        return "LINE API error", 500
    except Exception as e:
        app.logger.exception(e)
        return "Server error", 500

    # 3) LINE 需要 200 才算成功
    return "OK", 200

# ====== 文字訊息處理 ======
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = (event.message.text or "").strip()

    # 簡單防連結（可依需求加強）
    if "http://" in text or "https://" in text:
        protect.link_guard(event, line_bot_api)
        return

    # 指令處理
    if text.startswith("/addadmin"):
        manage.add_admin(event, line_bot_api)
    elif text.startswith("/ban"):
        manage.add_blacklist(event, line_bot_api)
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
        # 非指令就回覆個提示（可拿掉）
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="指令：/addadmin /ban /tagall /draw /checkin /inactive /backup")
        )

# ====== 成員加入/離開 ======
@handler.add(MemberJoinedEvent)
def joined(event):
    protect.member_join(event, line_bot_api)

@handler.add(MemberLeftEvent)
def left(event):
    protect.member_left(event, line_bot_api)

if __name__ == "__main__":
    # Render 會提供 PORT 環境變數。本地預設 10000。
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
