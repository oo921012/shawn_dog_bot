# modules/manage.py
import json
import os
from typing import List
from linebot.models import TextSendMessage

CONFIG_PATH = "config.json"

# ---------- 共用：讀寫設定 ----------
def _load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        return {"admins": [], "blacklist": []}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    # 保證欄位存在
    cfg.setdefault("admins", [])
    cfg.setdefault("blacklist", [])
    return cfg

def _save_config(cfg: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

# ---------- 共用：小工具 ----------
def _reply(api, token, text: str):
    api.reply_message(token, TextSendMessage(text=text))

def _extract_mentioned_user_ids(event) -> List[str]:
    """
    從訊息的 mention 取得被 @ 的 userId。
    兼容 m.user_id / m.userId 兩種命名。
    """
    ids = []
    mention = getattr(event.message, "mention", None)
    if mention and getattr(mention, "mentionees", None):
        for m in mention.mentionees:
            uid = getattr(m, "user_id", None) or getattr(m, "userId", None)
            if uid:
                ids.append(uid)
    # 去重、保序
    seen = set()
    dedup = []
    for uid in ids:
        if uid not in seen:
            seen.add(uid)
            dedup.append(uid)
    return dedup

def is_admin(user_id: str) -> bool:
    """可供其他模組引用的權限判斷"""
    cfg = _load_config()
    return user_id in cfg.get("admins", [])

def _bootstrap_if_no_admins(requester_id: str) -> bool:
    """
    若尚無任何管理員：將呼叫者設為第一位管理員並回 True。
    否則回 False。
    """
    cfg = _load_config()
    if not cfg["admins"]:
        cfg["admins"] = [requester_id]
        _save_config(cfg)
        return True
    return False

# ========================
#        管理員指令
# ========================
def add_admin_cmd(event, line_bot_api):
    requester = event.source.user_id

    # 啟動：第一個呼叫的人直接成為管理員
    if _bootstrap_if_no_admins(requester):
        _reply(line_bot_api, event.reply_token, "✅ 已將你設為首位管理員（初始化完成）。再執行一次 /addadmin 可新增其他人。")
        return

    if not is_admin(requester):
        _reply(line_bot_api, event.reply_token, "⛔ 只有管理員可以新增管理員。")
        return

    target_ids = _extract_mentioned_user_ids(event) or [requester]  # 沒 @ 就把自己加入（補登）
    cfg = _load_config()
    added, skipped = [], []
    for uid in target_ids:
        if uid not in cfg["admins"]:
            cfg["admins"].append(uid)
            added.append(uid)
        else:
            skipped.append(uid)
    _save_config(cfg)

    msg = []
    if added:
        msg.append("✅ 已新增管理員：\n" + "\n".join(added))
    if skipped:
        msg.append("ℹ️ 已在管理員名單（略過）：\n" + "\n".join(skipped))
    _reply(line_bot_api, event.reply_token, "\n—\n".join(msg) or "沒有任何變更。")

def del_admin_cmd(event, line_bot_api):
    requester = event.source.user_id

    if _bootstrap_if_no_admins(requester):
        _reply(line_bot_api, event.reply_token, "✅ 已將你設為首位管理員。請再執行一次 /deladmin。")
        return

    if not is_admin(requester):
        _reply(line_bot_api, event.reply_token, "⛔ 只有管理員可以移除管理員。")
        return

    targets = _extract_mentioned_user_ids(event)
    if not targets:
        _reply(line_bot_api, event.reply_token, "請使用：/deladmin @某人")
        return

    cfg = _load_config()
    admins = cfg["admins"]
    removed, not_found = [], []
    for uid in targets:
        if uid in admins:
            admins.remove(uid)
            removed.append(uid)
        else:
            not_found.append(uid)

    # 至少保留一位管理員，避免全刪
    if not admins:
        admins.append(requester)

    cfg["admins"] = admins
    _save_config(cfg)

    parts = []
    if removed:
        parts.append("🗑️ 已移除管理員：\n" + "\n".join(removed))
    if not_found:
        parts.append("❓ 不在管理員名單：\n" + "\n".join(not_found))
    _reply(line_bot_api, event.reply_token, "\n—\n".join(parts) or "沒有任何變更。")

def list_admins(event, line_bot_api):
    cfg = _load_config()
    admins = cfg.get("admins", [])
    if not admins:
        _reply(line_bot_api, event.reply_token, "目前沒有管理員。請先執行 /addadmin 初始化。")
        return

    gid = getattr(event.source, "group_id", None)
    lines = []
    for uid in admins:
        disp = uid
        if gid:
            try:
                prof = line_bot_api.get_group_member_profile(gid, uid)
                disp = f"{prof.display_name} ({uid})"
            except Exception:
                pass
        lines.append(disp)
    _reply(line_bot_api, event.reply_token, "👑 管理員列表：\n" + "\n".join(lines))

# ========================
#        黑名單指令
# ========================
def add_blacklist(event, line_bot_api):
    requester = event.source.user_id
    if not is_admin(requester):
        _reply(line_bot_api, event.reply_token, "⛔ 只有管理員可以新增黑名單。")
        return

    targets = _extract_mentioned_user_ids(event)
    if not targets:
        _reply(line_bot_api, event.reply_token, "請使用：/ban @某人")
        return

    cfg = _load_config()
    bl = cfg["blacklist"]
    added, skipped = [], []
    for uid in targets:
        if uid not in bl:
            bl.append(uid)
            added.append(uid)
        else:
            skipped.append(uid)
    cfg["blacklist"] = bl
    _save_config(cfg)

    msg = []
    if added:
        msg.append("🚷 已加入黑名單：\n" + "\n".join(added))
    if skipped:
        msg.append("ℹ️ 已在黑名單（略過）：\n" + "\n".join(skipped))
    _reply(line_bot_api, event.reply_token, "\n—\n".join(msg) or "沒有任何變更。")

def remove_blacklist(event, line_bot_api):
    requester = event.source.user_id
    if not is_admin(requester):
        _reply(line_bot_api, event.reply_token, "⛔ 只有管理員可以移除黑名單。")
        return

    targets = _extract_mentioned_user_ids(event)
    if not targets:
        _reply(line_bot_api, event.reply_token, "請使用：/unban @某人")
        return

    cfg = _load_config()
    bl = cfg["blacklist"]
    removed, not_found = [], []
    for uid in targets:
        if uid in bl:
            bl.remove(uid)
            removed.append(uid)
        else:
            not_found.append(uid)
    cfg["blacklist"] = bl
    _save_config(cfg)

    parts = []
    if removed:
        parts.append("✅ 已解除黑名單：\n" + "\n".join(removed))
    if not_found:
        parts.append("❓ 不在黑名單：\n" + "\n".join(not_found))
    _reply(line_bot_api, event.reply_token, "\n—\n".join(parts) or "沒有任何變更。")

def list_blacklist(event, line_bot_api):
    cfg = _load_config()
    bl = cfg.get("blacklist", [])
    if not bl:
        _reply(line_bot_api, event.reply_token, "目前黑名單為空。")
        return

    gid = getattr(event.source, "group_id", None)
    lines = []
    for uid in bl:
        disp = uid
        if gid:
            try:
                prof = line_bot_api.get_group_member_profile(gid, uid)
                disp = f"{prof.display_name} ({uid})"
            except Exception:
                pass
        lines.append(disp)
    _reply(line_bot_api, event.reply_token, "🚷 黑名單列表：\n" + "\n".join(lines))
