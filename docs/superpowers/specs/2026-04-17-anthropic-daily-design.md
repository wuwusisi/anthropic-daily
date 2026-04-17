# Anthropic Daily - 设计文档

## 概述

一个自动化的 Anthropic 资讯日报系统。每天定时采集 Anthropic 相关信息源，通过 AI 生成中文摘要，发布为静态网页，并通过飞书机器人推送链接给用户。

## 目标用户

个人使用（单用户），用于跟踪 Anthropic 的产品动态和前沿设计理念。

## 系统架构

```
GitHub Actions (每天 UTC 4:00 = 北京时间 12:00)
    │
    ▼
Python 采集脚本
    ├── 抓取 8 个核心信源
    ├── 与 seen.json 对比，筛选新内容
    ├── 调用 MiniMax 2.7 生成摘要
    │
    ▼
HTML 生成器 (Jinja2)
    ├── 生成当日日报页面
    ├── 更新首页索引
    │
    ▼
Git push 到 gh-pages 分支
    → GitHub Pages 自动部署
    │
    ▼
飞书应用机器人 API
    → 私聊发送日报链接
```

单一仓库包含：采集脚本、GitHub Actions 配置、页面模板、历史数据。

## 信源采集

### 第一期核心信源（8 个）

| # | 信源 | URL | 采集方式 | 说明 |
|---|------|-----|----------|------|
| 1 | Anthropic 新闻 | anthropic.com/news | HTTP + BeautifulSoup | 官方产品与公司动态 |
| 2 | Anthropic 研究 | anthropic.com/research | HTTP + BeautifulSoup | 研究论文与对齐进展 |
| 3 | API 更新日志 | docs.anthropic.com/en/release-notes/overview | HTTP + BeautifulSoup | 开发者向的硬核更新 |
| 4 | 官方 System Prompts | docs.anthropic.com/en/release-notes/system-prompts | HTTP + BeautifulSoup | Claude 各版本底层 System Prompt 变动 |
| 5 | GitHub anthropics org | github.com/anthropics | GitHub REST API | 监控新 repo、release、重要 commit |
| 6 | Dario Amodei 博客 | darioamodei.com | HTTP + BeautifulSoup | CEO 长文，低频但重要 |
| 7 | Transformer Circuits | transformer-circuits.pub | HTTP + BeautifulSoup | 可解释性研究核心发布渠道 |
| 8 | Import AI | importai.substack.com/feed | RSS (feedparser) | Jack Clark 周刊，12 万+订阅 |

### 后续可扩展信源

- arXiv（按 Anthropic 作者搜索）
- Anthropic YouTube 频道
- Hacker News（hn.algolia.com API）
- LessWrong / Alignment Forum

### 去重与增量逻辑

- 每次采集后将已知条目的标识（URL 或标题 hash）存入 `data/seen.json`，提交到仓库
- 下次采集时对比该文件，只处理新内容
- 当天所有信源均无新内容时，跳过日报生成和飞书推送

### 容错

- 单个信源抓取失败不影响其他信源
- 失败的信源在日报末尾标注"本次未能获取"
- GitHub Actions 日志可随时查看排查问题

## AI 摘要生成

### 模型

MiniMax 2.7 API

### 调用策略

- 对每条新内容，采集标题 + 正文前 2000 字符作为输入
- 生成两个层级的摘要：brief（一句话）和 detail（3-5 句）

### Prompt 模板

```
你是一个 AI 行业资讯编辑。请根据以下文章内容生成：
1. brief: 一句话摘要（不超过 50 字）
2. detail: 详细摘要（3-5 句，提炼核心观点和关键信息）

要求：中文输出，专业术语保留英文原文（如 Constitutional AI、Tool Use）。
输出 JSON 格式：{"brief": "...", "detail": "..."}

文章标题：{title}
文章内容：{content}
```

### 成本控制

- 每天新内容预估 0-10 条，每条约 2K input + 200 output tokens
- 日均消耗极低
- 无新内容时不调用 API

## 日报网页

### 页面结构

```
┌─────────────────────────────────────┐
│  Anthropic Daily · 2026-04-17       │
│  共 N 条更新                         │
├─────────────────────────────────────┤
│                                     │
│  ▶ [来源标签] 标题                   │  ← 折叠状态，显示 brief
│                                     │
│  ▼ [来源标签] 标题                   │  ← 展开状态
│    ┌───────────────────────────┐    │
│    │ 详细摘要 (detail)         │    │
│    │ 🔗 原文链接                │    │
│    └───────────────────────────┘    │
│                                     │
├─────────────────────────────────────┤
│  ⚠ 本次未能获取: xxx               │  ← 失败信源提示（如有）
├─────────────────────────────────────┤
│  历史日报: 04-16 · 04-15 · 04-14   │
└─────────────────────────────────────┘
```

### 技术实现

- 纯静态 HTML + CSS + 少量 JS（展开/折叠交互）
- Python 使用 Jinja2 模板引擎渲染
- 每条内容带来源标签（新闻、研究、API、GitHub、博客等）
- 响应式布局，适配移动端（飞书内打开）
- 简洁阅读风格，浅色背景，适当留白
- 代码片段有语法高亮
- 首页 `index.html` 为历史日报索引，按日期倒序排列

### URL 结构

```
https://{username}.github.io/anthropic-daily/           → 首页（历史索引）
https://{username}.github.io/anthropic-daily/2026/04/17 → 当日日报
```

## 飞书推送

### 方式

复用已有飞书应用机器人（App ID: cli_a94611e058b95ccd），通过飞书发送消息 API 直接私聊推送。

### 消息内容

```
Anthropic 日报 · 2026-04-17
今日 N 条更新

🔗 日报链接
```

### 规则

- 无新内容时不推送
- 推送失败不影响日报网页的正常发布

## 定时调度

### GitHub Actions

- cron 表达式：`0 4 * * *`（UTC 4:00 = 北京时间 12:00）
- 支持 `workflow_dispatch` 手动触发（调试或补跑）

### 执行流程

```
12:00 GitHub Actions 触发
  → 安装 Python 依赖 (requirements.txt)
  → 运行采集脚本（遍历 8 个信源）
  → 对比 seen.json，筛选新内容
  → 有新内容？
      ├── 是 → MiniMax 生成摘要 → Jinja2 渲染 HTML → push 到 gh-pages → 飞书推送
      └── 否 → 跳过
  → 更新 seen.json，提交到 main 分支
预计总耗时 2-3 分钟
```

### 所需凭证（GitHub Secrets）

| Secret 名称 | 说明 |
|-------------|------|
| `MINIMAX_API_KEY` | MiniMax 2.7 API 密钥 |
| `FEISHU_APP_ID` | 飞书应用机器人 App ID |
| `FEISHU_APP_SECRET` | 飞书应用机器人 App Secret |

## 项目结构

```
anthropic-daily/
├── .github/
│   └── workflows/
│       └── daily.yml              # GitHub Actions 配置
├── src/
│   ├── collectors/                # 各信源采集器
│   │   ├── __init__.py
│   │   ├── base.py                # 采集器基类
│   │   ├── anthropic_news.py
│   │   ├── anthropic_research.py
│   │   ├── release_notes.py
│   │   ├── system_prompts.py
│   │   ├── github_org.py
│   │   ├── dario_blog.py
│   │   ├── transformer_circuits.py
│   │   └── import_ai.py
│   ├── summarizer.py              # MiniMax 摘要生成
│   ├── renderer.py                # Jinja2 HTML 渲染
│   ├── notifier.py                # 飞书推送
│   └── main.py                    # 入口：采集 → 摘要 → 渲染 → 推送
├── templates/
│   ├── daily.html                 # 日报页面模板
│   └── index.html                 # 首页索引模板
├── data/
│   └── seen.json                  # 已知条目记录
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-04-17-anthropic-daily-design.md
├── requirements.txt               # Python 依赖
└── README.md
```

## Python 依赖

```
requests
beautifulsoup4
feedparser
jinja2
```

## 后续扩展方向

- 增加信源（arXiv、YouTube、Hacker News、LessWrong）
- 内容可视化（架构图、数据图表）
- 关键词过滤 / 重要度评分
- 周报汇总模式
