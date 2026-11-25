# -*- coding: utf-8 -*-
"""从 issues.json 重建整张报名表 —— 无状态，每次全量重算，不需要写回仓库。"""

import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from parse import COLUMNS, to_row, is_signup  # noqa: E402

SRC = "issues.json"
OUT = "data/registrations.csv"


def main():
    if not os.path.exists(SRC):
        print(f"{SRC} not found, nothing to do")
        return

    with open(SRC, encoding="utf-8") as f:
        issues = json.load(f)

    rows = []
    for it in issues:
        if not is_signup(it.get("body") or ""):
            continue
        rows.append(to_row(it))

    rows.sort(key=lambda r: r["提交时间"])

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLUMNS})

    print(f"重建完成：{len(rows)} 条报名 → {OUT}")


if __name__ == "__main__":
    main()
