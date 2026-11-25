# -*- coding: utf-8 -*-
"""新报名时推一条到飞书群。没配 FEISHU_WEBHOOK 就静默跳过。"""

import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from parse import normalize, parse_issue  # noqa: E402


def main():
    hook = (os.environ.get("FEISHU_WEBHOOK") or "").strip()
    if not hook:
        print("FEISHU_WEBHOOK 未配置，跳过推送")
        return

    body = os.environ.get("ISSUE_BODY", "")
    rec = normalize(parse_issue(body))
    if not rec.get("姓名"):
        print("不是报名单，跳过")
        return

    num = os.environ.get("ISSUE_NUMBER", "")
    url = os.environ.get("ISSUE_URL", "")

    text = (
        f"📥 新报名 #{num}\n"
        f"姓名：{rec.get('姓名','')}　｜　{rec.get('身份','')}\n"
        f"GitHub：{rec.get('GitHub 用户名','')}\n"
        f"公司/学校：{rec.get('公司 / 学校','') or '（未填）'}\n"
        f"电脑：{rec.get('你的电脑','')}\n"
        f"本地经验：{rec.get('本地模型经验','')}　｜　试过 Linger：{rec.get('试过 Linger 桌面端吗','')}\n\n"
        f"最近在折腾什么：\n{rec.get('最近在折腾什么','')}\n\n"
        f"继续参与：{rec.get('活动后愿意继续参与吗','')}　｜　开麦：{rec.get('现场愿意开麦吗','')}\n"
        f"提交方式：{rec.get('这份报名是怎么提交的','')}\n"
        f"{url}\n通过后记得私信他要微信和真实姓名"
    )

    payload = {"msg_type": "text", "content": {"text": text}}
    req = urllib.request.Request(
        hook,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print("飞书推送:", resp.status, resp.read().decode("utf-8")[:160])
    except Exception as e:
        print("飞书推送失败:", e)


if __name__ == "__main__":
    main()
