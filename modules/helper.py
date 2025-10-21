import random
from linebot.models import TextSendMessage

def tag_all(event, line_bot_api):
    gid = event.source.group_id
    members = line_bot_api.get_group_member_ids(gid)
    mentions = []
    text = "📣 全體標記：\n"
    for uid in members[:20]:
        mentions.append({"type": "user", "userId": uid})
        text += f"@{uid[:6]}... \n"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=text))

def draw_lottery(event, line_bot_api):
    candidates = ["Alice", "Bob", "Charlie", "David"]
    winner = random.choice(candidates)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"🎉 抽獎結果：{winner} 中獎！"))
