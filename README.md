# Linger 杭州站 · 报名 Bot

一个「活动自己的 bot」。

每个人的 Agent 通过向这个仓库**提 Issue** 跟它说话；提交后自动：
1. 解析报名信息
2. 追加进 `data/registrations.csv`（公开可见的表格）
3. 推一条消息到你指定的飞书群
4. 在 Issue 下回一条「已收到」

团队只需要干一件事：**在 Issue 上打标签**（`approved` / `waitlist` / `rejected`）。

---

## 目录

```
.
├── SKILL.md                        ← 给报名者 Agent 的技能文件（核心）
├── .github/
│   ├── ISSUE_TEMPLATE/signup.yml   ← 报名表单（人类点着填）
│   └── workflows/collect.yml       ← 活动 bot 本体
├── scripts/collect.py              ← 解析 + 写表 + 推飞书
└── data/registrations.csv          ← 报名总表（自动维护）
```

---

## 上线步骤（约 15 分钟）

### 1. 建仓库

GitHub 上新建一个 **public** 仓库，比如 `linger-hangzhou-meetup`。
把本目录的文件全部推上去。

### 2. 开启 Issues

仓库 Settings → General → Features → 勾选 **Issues**。

### 3. 开启 Action 写权限

Settings → Actions → General → Workflow permissions →
选 **Read and write permissions** → Save。

> 不勾这个，Action 没法把表格提交回去。

### 4. 建飞书群机器人（推送用，可选）

1. 打开飞书「Linger 杭州站 · 筹备组」群
2. 群设置 → 群机器人 → 添加机器人 → **自定义机器人**
3. 复制 Webhook 地址（`https://open.feishu.cn/open-apis/bot/v2/hook/xxxx`）

### 5. 把 Webhook 存成 Secret

仓库 Settings → Secrets and variables → Actions → New repository secret

- Name: `FEISHU_WEBHOOK`
- Value: 上面复制的地址

> 不配也能用，只是不推群，表格照常生成。

### 6. 自测

打开 `Issues → New issue → 报名 Linger 杭州站`，随便填一条提交。

30 秒内应该看到：
- Issue 下出现「✅ 报名已收到」
- `data/registrations.csv` 多一行
- 飞书群收到一条消息

---

## 怎么让别人报名

三种方式，都能进同一张表：

| 方式 | 给谁 | 入口 |
|---|---|---|
| **网页表单** | 大多数人 | `https://github.com/你/仓库/issues/new?template=signup.yml` |
| **Agent 提 Issue** | 会用 Agent 的人 | 把 `SKILL.md` 给他，或让他 `gh issue create` |
| **自己写 issue** | 有 GitHub 习惯的人 | 同上，手写 body |

---

## 团队怎么审

1. 打开 Issues，看 `signup` 标签那批
2. 按三样东西判断（30 秒一个）：
   - **截图**：有没有真的终端/界面
   - **「卡点在哪一层」**：有没有说到具体某一层
   - **GitHub 账号**：点进提交人主页看最近有没有 commit
3. 打标签：`approved` / `waitlist` / `rejected`
4. 审完导出：`data/registrations.csv` 直接下载

---

## 已知限制

- **Issue 是公开的。** 手机号会暴露给所有人。SKILL.md 里已经要求 Agent 提醒用户只填后四位，完整号码走私信。
- **截图要有 GitHub 账号才能传**（拖进输入框自动生成链接）。
- **没有 GitHub 的人做不了。** 这是这个方案的门槛，也是它筛人的方式。

---

## 为什么这么设计

报名动作本身就是筛选：

- 会 `gh issue create` 的人，一定配好过开发环境
- 能说清「卡点在哪一层」的人，一定真的跑过本地模型
- 提交方式那一栏选「Agent 帮我填的」的人，就是你想要的共建候选

**跑不通的人也会告诉你卡在哪** —— 这比报名表本身更有信息量。
