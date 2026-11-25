# -*- coding: utf-8 -*-
"""共享解析逻辑：把 GitHub Issue 的 markdown body 解析成结构化记录。"""

import re

COLUMNS = [
    "issue", "提交时间", "提交人",
    "姓名", "GitHub 用户名", "公司 / 学校", "身份",
    "你的电脑", "是否带电脑来现场", "本地模型经验",
    "试过 Linger 桌面端吗", "最近在折腾什么", "运行截图",
    "活动后愿意继续参与吗", "现场愿意开麦吗",
    "有什么能看到你的东西吗", "这份报名是怎么提交的",
    "审核状态", "评分", "备注",
]

ALIASES = {
    "姓名 / 花名": "姓名",
    "姓名": "姓名",
    "GitHub 用户名": "GitHub 用户名",
    "GitHub用户名": "GitHub 用户名",
    "公司/学校": "公司 / 学校",
    "公司 / 学校": "公司 / 学校",
    "公司 / 学校（可留空）": "公司 / 学校",
    "是否带电脑": "是否带电脑来现场",
    "是否带电脑来现场": "是否带电脑来现场",
    "最近在折腾什么": "最近在折腾什么",
    "运行截图": "运行截图",
    "活动后继续参与": "活动后愿意继续参与吗",
    "活动后愿意继续参与": "活动后愿意继续参与吗",
    "活动后愿意继续参与吗": "活动后愿意继续参与吗",
    "是否愿意现场开麦": "现场愿意开麦吗",
    "现场愿意开麦": "现场愿意开麦吗",
    "现场愿意开麦吗": "现场愿意开麦吗",
    "能看到你的东西": "有什么能看到你的东西吗",
    "有什么能看到你的东西吗": "有什么能看到你的东西吗",
    "这份表是你自己填的还是 Agent 帮你填的": "这份报名是怎么提交的",
    "这份报名是怎么提交的": "这份报名是怎么提交的",
}


def parse_issue(body: str) -> dict:
    """Issue body 形如：
    ### 姓名\n\n张三\n\n### 微信 / 手机\n\n138...
    """
    if not body:
        return {}
    blocks = re.split(r"(?m)^###\s+", body)
    data = {}
    for block in blocks[1:]:
        lines = block.split("\n")
        title = lines[0].strip()
        value = "\n".join(lines[1:]).strip()
        if value in ("_No response_", ""):
            value = ""
        data[title] = value
    return data


def normalize(raw: dict) -> dict:
    out = {}
    for k, v in raw.items():
        key = k.strip()
        # 去掉标题末尾括号备注，如「运行截图（图片链接，可留空）」
        key = re.sub(r"[（(][^（）()]*[）)]\s*$", "", key).strip()
        key = ALIASES.get(key, key)
        if key not in COLUMNS:
            continue
        if "\n- [" in v or v.startswith("- ["):
            picked = re.findall(r"(?m)^-\s*\[[xX]\]\s*(.+)$", v)
            v = ",".join(p.strip() for p in picked)
        out[key] = v
    return out


def is_signup(body: str) -> bool:
    """有「### 姓名」且填了内容，才当成报名单。"""
    raw = parse_issue(body)
    for k, v in raw.items():
        if k.strip() == "姓名" and v.strip():
            return True
    return False


def to_row(issue: dict) -> dict:
    body = issue.get("body") or ""
    rec = normalize(parse_issue(body))
    row = {c: "" for c in COLUMNS}
    row.update(rec)
    row["issue"] = f"#{issue.get('number', '')}"
    row["提交人"] = (issue.get("author") or {}).get("login", "") if isinstance(issue.get("author"), dict) else issue.get("author", "")
    created = issue.get("createdAt", "") or ""
    row["提交时间"] = created.replace("T", " ").replace("Z", "")[:19]
    row["审核状态"] = row.get("审核状态") or "待审核"
    return row
