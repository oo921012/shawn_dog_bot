# modules/manage.py
import json
import os
from typing import List
from linebot.models import TextSendMessage

CONFIG_PATH = "config.json"

# ---------- 基礎存取 ----------
def _load_config():
    if not os.path.exists(CONFIG_PATH):
        return {"admins": []}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_config(cfg: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def _is_admin(user_id: str) -> bool:
    cfg = _load_config()
    return user_id in cfg.get("admins", [])

def _bootstrap_if_empty(requester_id: str) -> bool:
    """若目前沒有任何管理員，第一位呼叫管理指令的人自動成為管理員。返回是否剛完成 bootstrap。"""
    cfg = _load_config()
    admins = cfg.get("admins", [])
    if not admins:
        cfg["admins"] = [requester_id]
        _save_config(cfg)
        return True
    return False

# ---------- 取得被 @ 的 userId ----------
def _extract_mentioned_user_ids(event) -> List[str]:
    """
    從訊息的 mention 抓 userId。
    LINE SDK: event.message.mention.mentionees -> each has .user_id (or .userId 預防不同拼法)
    """
    user_ids = []
    mention = getattr(event.message, "mention", None)
    if mention and getattr(mention, "mentionees", None):
        for m in mention.mentionees:
            uid = getattr(m, "user_id", None) or getattr(m, "userId", None)
            if uid:
                user_ids.append(uid)
    return list(dict.fromkeys(user_ids))  # 去重保序

# ---------- 指令回覆工具 ----------
def _reply(line_bot_api, reply_token, text: str):
    line_bot_api.reply_message(reply_token, TextSendMessage(text=text))

# ---------- /addadmin @某人 ----------
def add_admin_cmd(event, line_bot_api):
    requester_id = event.source.user_id

    # 啟動機制：若尚無任何管理員，第一個執行者成為管理員
    if _bootstrap_if_empty(requester_id):
        _reply(line_bot_api, event.reply_token, "✅ 已將你設為首位管理員（啟動完成）。再執行一次 /addadmin 可新增其他人。")
        return

    # 權限檢查
    if not _is_admin(requester_id):
        _reply(line_bot_api, event.reply_token, "⛔ 只有管理員可以新增管理員。")
        return

    target_ids = _extract_mentioned_user_ids(event)
    # 若沒 @，就把自己加入（允許補登）
    if not target_ids:
        target_ids = [requester_id]

    cfg = _load_config()
    cfg.setdefault("admins", [])
    added = []
    skipped = []
    for uid in target_ids:
        if uid not in cfg["admins"]:
            cfg["admins"].append(uid)
            added.append(uid)
        else:
            skipped.append(uid)
    _save_config(cfg)

    if added and skipped:
        _reply(line_bot_api, event.reply_token, f"✅ 已新增以下管理員：\n" +
               "\n".join(added) + "\n—\n（已存在管理員，略過）\n" + "\n".join(skipped))
    elif added:
        _reply(line_bot_api, event.reply_token, "✅ 已新增管理員：\n" + "\n".join(added))
    else:
        _reply(line_bot_api, event.reply_token, "ℹ️ 提到的成員都已經是管理員。")

# ---------- /deladmin @某人 ----------
def del_admin_cmd(event, line_bot_api):
    requester_id = event.source.user_id

    # 啟動機制：若尚無任何管理員，先把執行者設為管理員，避免無人可管
    if _bootstrap_if_empty(requester_id):
        _reply(line_bot_api, event.reply_token, "✅ 已將你設為首位管理員。請再執行一次 /deladmin。")
        return

    if not _is_admin(requester_id):
        _reply(line_bot_api, event.reply_token, "⛔ 只有管理員可以移除管理員。")
        return

    target_ids = _extract_mentioned_user_ids(event)
    if not target_ids:
        _reply(line_bot_api, event.reply_token, "請用 @ 提到要移除的成員，例如：/deladmin @某人")
        return

    cfg = _load_config()
    admins = cfg.get("admins", [])
    removed = []
    not_found = []

    for uid in target_ids:
        if uid in admins:
            admins.remove(uid)
            removed.append(uid)
        else:
            not_found.append(uid)

    # 至少保留一位管理員，避免把自己全刪光
    if not admins:
        # 如果被刪到空，強制把 requester 加回去
        admins.append(requester_id)

    cfg["admins"] = admins
    _save_config(cfg)

    parts = []
    if removed:
        parts.append("🗑️ 已移除管理員：\n" + "\n".join(removed))
    if not_found:
        parts.append("❓ 不是管理員（無法移除）：\n" + "\n".join(not_found))
    if parts:
        _reply(line_bot_api, event.reply_token, "\n—\n".join(parts))
    else:
        _reply(line_bot_api, event.reply_token, "沒有指定任何要移除的對象。")

# ---------- /listadmin ----------
def list_admins(event, line_bot_api):
    cfg = _load_config()
    admins = cfg.get("admins", [])
    if not admins:
        _reply(line_bot_api, event.reply_token, "目前沒有管理員。請由想成為管理員的人先執行 /addadmin 初始化。")
        return

    # 若在群組，可嘗試顯示名稱（可選）
    gid = getattr(event.source, "group_id", None)
    lines = []
    for uid in admins:
        display = uid
        if gid:
            try:
                prof = line_bot_api.get_group_member_profile(gid, uid)
                display = f"{prof.display_name} ({uid})"
            except Exception:
                pass
        lines.append(display)

    _reply(line_bot_api, event.reply_token, "👑 管理員列表：\n" + "\n".join(lines))
