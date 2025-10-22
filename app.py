from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, MemberJoinedEvent, MemberLeftEvent
)
import json
import os
from modules import protect, manage, helper, checkin, backup

app = Flask(__name__)

# 載入設定
config = json.load(open('config.json', 'r', encoding='utf-8'))
line_bot_api = LineBotApi(config["channel_access_token"])
handler = WebhookHandler(config["channel_secret"])

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 處理文字訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    group_id = event.source.group_id if event.source.type == "group" else None
    user_id = event.source.user_id

    # 防護功能
    if "http" in text:
        protect.link_guard(event, line_bot_api)

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

# 成員加入 / 離開事件
@handler.add(MemberJoinedEvent)
def joined(event):
    protect.member_join(event, line_bot_api)

@handler.add(MemberLeftEvent)
def left(event):
    protect.member_left(event, line_bot_api)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
    




