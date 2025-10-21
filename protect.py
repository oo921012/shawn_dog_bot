from linebot.models import TextSendMessage

def link_guard(event, line_bot_api):
    text = event.message.text
    if "http" in text:
        line_bot_api.reply_message(event.reply_token,
            TextSendMessage(text="🚫 禁止發送連結，請遵守群規！"))
        try:
            line_bot_api.delete_message(event.message.id)
        except:
            pass

def member_join(event, line_bot_api):
    gid = event.source.group_id
    new_members = [m.user_id for m in event.joined.members]
    msg = f"🐶 歡迎新成員加入！共有 {len(new_members)} 人進群。"
    line_bot_api.push_message(gid, TextSendMessage(text=msg))

def member_left(event, line_bot_api):
    gid = event.source.group_id
    msg = "⚠️ 有成員離開群組，若非管理員操作請注意群組安全。"
    line_bot_api.push_message(gid, TextSendMessage(text=msg))
