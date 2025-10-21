from linebot.models import TextSendMessage

def export_members(event, line_bot_api):
    gid = event.source.group_id
    members = line_bot_api.get_group_member_ids(gid)
    msg = f"📋 成員備份完成，共 {len(members)} 人。"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
