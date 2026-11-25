#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
活动 bot 的核心逻辑：
  1. 读取新提交的 Issue
  2. 按 ### 字段名 解析报名信息
  3. 追加进 data/registrations.csv（按 Issue 号去重）
  4. 推送一条通知到飞书群（如果配置了 FEISHU_WEBHOOK）

环境变量：
  ISSUE_BODY / ISSUE_NUMBER / ISSUE_URL / ISSUE_AUTHOR
  FEISHU_WEBHOOK（可选）
"""

import csv
import os
import re
import sys
import json
import urllib.request

CSV_PATH = "data/registrations.csv"

# CSV 列顺序（同时也是 Issue 里的字段名）
COLUMNS = [
    "issue", "提交时间", "提交人",
    "姓名", "微信 / 手机", "公司 / 学校", "身份",
    "你的电脑", "是否带电脑来现场", "本地模型经验",
    "试过 Linger 桌面端吗", "最近在折腾什么", "运行截图",
    "活动后愿意继续参与吗", "现场愿意开麦吗",
    "有什么能看到你的东西吗", "这份报名是怎么提交的",
    "审核状态", "评分", "备注",
]

# 字段名 -> CSV 列名（Issue 里的标题可能多个空格，这里做归一）
ALIASES = {
    "微信/手机": "微信 / 手机",
    "微信 / 手机": "微信 / 手机",
    "公司/学校": "公司 / 学校",
    "公司 / 学校": "公司 / 学校",
    "是否带电脑": "是否带电脑来现场",
    "最近在折腾什么": "最近在折腾什么",
    "运行截图": "运行截图",
    "活动后继续参与": "活动后愿意继续参与吗",
    "活动后愿意继续参与": "活动后愿意继续参与吗",
    "是否愿意现场开麦": "现场愿意开麦吗",
    "现场愿意开麦": "现场愿意开麦吗",
    "能看到你的东西": "有什么能看到你的东西吗",
    "有什么能看到你的东西吗": "有什么能看到你的东西吗",
    "这份表是你自己填的还是 Agent 帮你填的": "这份报名是怎么提交的",
    "这份报名是怎么提交的": "这份报名是怎么提交的",
}


def parse_issue(body: str) -> dict:
    """GitHub Issue Form 的 body 形如：
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
        # 去掉没有填写的占位（- [ ] 未勾选 / _No response_）
        if value in ("_No response_", "", "- [ ]"):
            value = ""
        data[title] = value
    return data


def normalize(raw: dict) -> dict:
    out = {}
    for k, v in raw.items():
        key = k.strip()
        # 去掉标题末尾的括号备注，如「运行截图（图片链接，可留空）」
        key = re.sub(r"[（(][^（）()]*[）)]\s*$", "", key).strip()
        key = ALIASES.get(key, key)
        if key in COLUMNS:
            # 复选框在 body 里是 "- [X] Ollama"，转成逗号分隔
            if "\n- [" in v or v.startswith("- ["):
                picked = re.findall(r"(?m)^-\s*\[[xX]\]\s*(.+)$", v)
                v = ",".join(p.strip() for p in picked)
            out[key] = v
    return out


def main():
    num = os.environ.get("ISSUE_NUMBER", "").strip()
    if not num:
        print("no issue number, skip")
        return

    raw = parse_issue(os.environ.get("ISSUE_BODY", ""))
    rec = normalize(raw)

    # 只处理真正的报名 issue
    if not rec.get("姓名"):
        print("not a signup issue, skip")
        return

    row = {c: "" for c in COLUMNS}
    row.update(rec)
    row["issue"] = f"#{num}"
    row["提交时间"] = (os.environ.get("ISSUE_CREATED_AT", "") or "").replace("T", " ").replace("Z", "")
    row["提交人"] = os.environ.get("ISSUE_AUTHOR", "")
    row["审核状态"] = "待审核"
    row["运行截图"] = row.get("运行截图", "").strip()

    # 读旧表
    existing = []
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            existing = [r for r in csv.DictReader(f)]

    # 按 issue 号去重（编辑 issue 时覆盖旧行）
    existing = [r for r in existing if r.get("issue") != row["issue"]]
    existing.append(row)

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in existing:
            w.writerow({c: r.get(c, "") for c in COLUMNS})

    print(f"written: {CSV_PATH} ({len(existing)} rows)")

    # 推送飞书
    hook = os.environ.get("FEISHU_WEBHOOK", "").strip()
    if not hook:
        print("FEISHU_WEBHOOK not set, skip notify")
        return

    text = (
        f"📥 新报名 #{num}\n"
        f"姓名：{rec.get('姓名','')}　｜　{rec.get('身份','')}\n"
        f"公司/学校：{rec.get('公司 / 学校','')}\n"
        f"电脑：{rec.get('你的电脑','')}\n"
        f"本地经验：{rec.get('本地模型经验','')}　｜　试过 Linger：{rec.get('试过 Linger 桌面端吗','')}\n\n"
        f"最近在折腾什么：\n{rec.get('最近在折腾什么','')}\n\n"
        f"继续参与：{rec.get('活动后愿意继续参与吗','')}　｜　开麦：{rec.get('现场愿意开麦吗','')}\n"
        f"提交方式：{rec.get('这份报名是怎么提交的','')}\n"
        f"微信/手机：{rec.get('微信 / 手机','')}\n"
        f"{os.environ.get('ISSUE_URL','')}"
    )
    payload = {"msg_type": "text", "content": {"text": text}}
    req = urllib.request.Request(
        hook,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print("feishu:", resp.status, resp.read().decode("utf-8")[:200])
    except Exception as e:
        print("feishu notify failed:", e)


if __name__ == "__main__":
    main()
