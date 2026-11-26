# dsh-finance-offline — 财报分析师·离线版

一个可以搬进**无外网环境**的 DSH 插件包。装完即用，不需要联网、不需要装 Python 依赖。

## 它是什么

通用大模型 + 本地财务数据库 + 确定性取数工具，三者组成一个**特化的财报分析 Agent**。

- **数据**：`data/stock.db`（SQLite，7.7 MB），5 只 A 股三年三表 + 日线行情
- **工具**：`tools/query_finance.py`，纯 Python 标准库，零第三方依赖
- **知识**：6 个 skill，其中 `local-financial-database` 描述库结构和取数纪律
- **边界**：联网工具已从 preset 层显式禁用，模型无法上网找答案

## 覆盖的数据范围

| 代码 | 名称 | 行业 |
|---|---|---|
| 688981 | 中芯国际 | 半导体 |
| 603986 | 兆易创新 | 半导体 |
| 600900 | 长江电力 | 电力 |
| 601985 | 中国核电 | 电力 |
| 002230 | 科大讯飞 | AI |

财报：2022 年至 2026 年三季报（三张报表全部科目）
行情：2022-01-04 至 2026-11-26 日线

## 安装

### 方式一：命令行（推荐）

```bash
dsh plugin --profile <profile名> add file:/path/to/dsh-finance-offline
```

安装后需要把插件名加进 profile 的 bundles 列表（`~/.dsh/profiles/<name>/package.json`）：

```json
"dsh": {
  "profile": {
    "bundles": [ "...", "dsh-finance-offline" ]
  }
}
```

### 方式二：DSH 界面

在插件管理里选择「从本地导入」，指向本目录。

### 安装后必做：注册 preset

插件自带的 `scripts/postinstall.js` 会自动把 preset 复制到 `~/.dsh/.agent-presets/financial-analyst-offline/`，
并把插件包的绝对路径注入进 skill 文件。如果 pnpm 因为「Already up to date」跳过了 postinstall，手动跑一次：

```bash
node scripts/postinstall.js
```

（Windows 上 node 若不在 PATH，用 DSH 自带的：
`"%DSH_DESKTOP_NODE_EXECUTABLE%" --expose-internals scripts/postinstall.js`）

## 使用

新建会话时选择 preset「**财报分析师·离线版**」，然后正常提问即可。

模型会：
1. 先加载 `local-financial-database` 确认库内有哪些股票
2. 调用 `query_finance.py` 取数（不会心算）
3. 库外股票直接告知无数据，不会去网上找

### 取数工具命令

```bash
python tools/query_finance.py list                      # 库内股票
python tools/query_finance.py ratio 688981 2024         # 核心指标
python tools/query_finance.py item 688981 2024 营业收入   # 单科目
python tools/query_finance.py trend 600900 营业收入 5     # 年度走势
python tools/query_finance.py report 002230 2024        # 某期三表全表
python tools/query_finance.py quote 688981 2024 2025    # 行情区间
```

## 已验证的行为（本机实测）

| 输入 | 预期 | 实测 |
|---|---|---|
| 中芯国际 2024 流动比率 | 1.7269 | ✅ 一致（并交叉核对了两科目原始值） |
| 贵州茅台 2024 流动比率 | 拒答 | ✅ 说明库内无此公司，零 web 调用 |
| 手工验算 106278648000 ÷ 61544471000 | 1.7269 | ✅ 一致 |

## 环境注意（重要）

DSH 的 Windows sandbox 要求「临时目录在工作区之外」。如果会话工作目录是
`C:\Users\<用户>`（用户主目录），而 TEMP 也在其下，**任何命令都会在启动前失败**：

```
Error: Windows ACL temp root must be outside the workspace
```

演示时请**把会话工作目录设为非用户主目录**（如 `D:\demo`），
并确保 DSH 权限模式允许执行命令（`DSH_PERMISSION_MODE=danger-full-access` 或界面里调权限）。

## 与社区版的关系

基于 `dsh-financial-analysis@0.1.1`（作者 toplchx）改造。原版的 5 个分析 skill、
规则文稿全部保留；改动是：

1. 数据从「联网拉取」改为「本地 SQLite 快照」
2. 新增确定性取数工具（原版只有说明文档，没有可执行工具）
3. 新增 `local-financial-database` skill 描述库结构
4. 显式禁用 web 工具（原版依赖联网）

原版 README 保留在 `README.original.md`。
