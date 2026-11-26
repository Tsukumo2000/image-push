# dsh-financial-analysis —— DeepSeek Harness 财务报表分析插件

- **Preset**：`财报分析师`（financial-analyst）—— 专用 Agent 预设，注入财报分析师 persona；
- **Skills**：5 项可加载技能（资产负债表/利润表/现金流量表/三表钩稽关系/财报获取）；
- **报告**：`report/` 目录含《财务报表分析最终报告》与规则分册；
- **数据**：分析新案例时通过财经数据 API（AKShare/Tushare）或网络公开信息（新浪财经/东方财富/web_search）获取最新公司财务报告。

---

## 一、目录结构

```
dsh-financial-analysis/
├── package.json                              # npm 包清单（声明 dsh.bundle.patch）
├── cordis.patch.yml                          # bundle 装配标记
├── config/agent-presets/financial-analyst/   # 财报分析师 preset
│   ├── preset.yml                            # 预设元数据（名称/描述/排序）
│   ├── agent.cordis.yml                      # 预设组成（persona + 工具 + 技能挂载）
│   └── skills/
│       ├── balance-sheet-analysis/SKILL.md        # 资产负债表分析
│       ├── income-statement-analysis/SKILL.md     # 利润表分析
│       ├── cash-flow-analysis/SKILL.md            # 现金流量表分析
│       ├── three-statement-articulation/SKILL.md  # 三张报表钩稽关系
│       └── finding-financial-reports/SKILL.md     # 财报获取（F10 路径 + API/网络取数）
└── report/                                   # 规则提炼成果（最终报告+规则分册）
    ├── 00-财务报表分析最终报告.md
    ├── 01-资产负债表-规则.md
    ├── 02-利润表-规则.md
    ├── 03-现金流量表-规则.md
    ├── 04-三张报表的勾稽关系-规则.md
    └── 05-如何在软件上找财报-规则.md
```

---

## 二、安装

> 安装deepseek harness
> 确认已装 DSH Web 且 `dsh` 命令可用。`dsh plugin` 是 pnpm 转发器，**方式一/二需要 `pnpm` 可用**
> （`npm install -g pnpm` 或 `corepack enable pnpm`）；不想装 pnpm 时请用**方式三**。

### 方式一：从 npm 安装（推荐，面向使用者）

插件发布到 npm 后（包名 `dsh-financial-analysis`）：

```powershell
# 1. 安装到 web profile（默认从 npm registry 拉取）
dsh plugin --profile web add dsh-financial-analysis

# 2. 重启 dsh web 使 bundle 生效
dsh web
```

> **⚠️ 必做：让「财报分析师」预设被发现**
>
> agent-presets 只扫描「自带根」与用户根 `$DSH_HOME/.agent-presets`（默认 `$HOME/.dsh/.agent-presets`），
> **bundle 内的 preset 目录不会自动进入发现列表**，因此安装后必须把 preset 复制到用户预设根
> （新会话立即生效，无需重启进程；**插件升级后需重复执行**以更新预设）。
> 请按你的操作系统执行对应命令：

**Windows（PowerShell）**

```powershell
$pkg  = "$env:USERPROFILE\.dsh\profiles\web\node_modules\dsh-financial-analysis"
$dest = "$env:USERPROFILE\.dsh\.agent-presets\financial-analyst"
New-Item -ItemType Directory -Path $dest -Force | Out-Null
Copy-Item -Path "$pkg\config\agent-presets\financial-analyst\*" -Destination $dest -Recurse -Force
```

**macOS（Apple）/ Linux（bash 或 zsh）**

```bash
pkg="$HOME/.dsh/profiles/web/node_modules/dsh-financial-analysis"
dest="$HOME/.dsh/.agent-presets/financial-analyst"
mkdir -p "$dest"
cp -R "$pkg/config/agent-presets/financial-analyst/." "$dest/"
```

> **验证**：查看 `$HOME/.dsh/.agent-presets/financial-analyst` 是否包含 `agent.cordis.yml`、`preset.yml`、`skills/`。
> 若 `node_modules/dsh-financial-analysis` 不存在（pnpm 布局差异），先用 `dsh plugin --profile web list`
> 确认包已加入 bundles，再找到实际安装位置（如 `node_modules/.pnpm/dsh-financial-analysis*/node_modules/dsh-financial-analysis`）复制。

### 方式二：本地目录安装（开发/本机）

```powershell
# 在插件包目录内（相对路径会锚定到当前目录），或使用绝对路径
cd ${your_dir}\financial-analysis-plugin
dsh plugin --profile web add .
```

安装后同样执行方式一中的**「必做」复制步骤**，并重启 `dsh web`。

### 方式三：用户预设目录部署（免 pnpm，仅预设能力）

不装 bundle、只要「财报分析师」预设时，直接把 preset 复制到用户预设根
（发现是"每次读取"式的，新会话立即可见，无需重启、无需 pnpm）：

**Windows（PowerShell）**

```powershell
$dest = "$env:USERPROFILE\.dsh\.agent-presets\financial-analyst"
New-Item -ItemType Directory -Path $dest -Force | Out-Null
Copy-Item -Path "${your_dir}\financial-analysis-plugin\config\agent-presets\financial-analyst\*" `
          -Destination $dest -Recurse -Force
```

**macOS（Apple）/ Linux（bash 或 zsh）**

```bash
dest="$HOME/.dsh/.agent-presets/financial-analyst"
mkdir -p "$dest"
cp -R "${your_dir}/financial-analysis-plugin/config/agent-presets/financial-analyst/." "$dest/"
```

（`${your_dir}` 为插件源码所在目录，例如 `D:/aispace` 或 `/home/user/aispace`）

---

## 三、使用步骤

1. **启动 DSH Web**（若未运行）：`dsh web`，打开浏览器访问 Web 界面（默认 http://127.0.0.1:3080）。
2. **新建会话并选择预设**：在 Agent 预设列表中选择 **「财报分析师」**（financial-analyst）；
   若列表未出现，先确认方式一中的「必做」复制步骤已执行，再刷新页面。
3. **开始提问**，例如：
   - “帮我分析某公司的资产负债表，重点看存货和合同负债的变化说明什么”
   - “分析这家公司的现金流量表：经营/投资/筹资都是什么方向？”
   - “验证三张报表的钩稽关系：它是不是先搞钱再扩产？”
   - “在软件上怎么看这家公司的营收结构和海外占比？”
   - “用 AKShare 拉取某公司最近几期季报和年报的三大报表，并做一份完整分析”
   - “帮我搜索某公司最新一期的财报数据（营收/净利/研发费用等）”
   - “综合评估一下这家公司的财务健康状况和风险信号”
4. Agent 会按需加载对应技能（balance-sheet-analysis 等）并按照提炼的规则输出结构化分析；
   分析**新案例**时，通过**财经数据 API（AKShare、Tushare，Python 运行）**或**网络公开信息
   （新浪财经、东方财富，web_search 检索）**获取最新财务报告，注明报告期与来源并交叉核验。

---

## 四、环境依赖

| 能力 | 依赖 | 说明 |
|---|---|---|
| 财经数据 API（AKShare/Tushare） | Python 3.9+，`pip install akshare tushare pandas` | agent 通过 pwsh 运行 Python 取数；未安装时自动回退到网络公开信息 |
| Tushare | 需在 tushare.pro 注册并配置 token | 未配置 token 时自动改用 AKShare 或网络公开信息 |
| 网络检索（web_search） | 部署自带 `web` 服务（deepseek-official 提供方） | 标准 web profile 自带，无需额外配置 |
| 行情软件查看 | 无（操作指南） | 仅作为查看方法说明 |

---

## 五、能力内容

| 技能 | 覆盖内容 |
|---|---|
| balance-sheet-analysis | 时点快照概念、恒等式、科目两面性；货币资金/应收/存货/固定资产/在建工程/商誉/合同负债/预付/借款/权益的判断规则；结构比重→同比环比→商业模式互验三步框架；风险信号 |
| income-statement-analysis | 时间段概念、层层剥开结构；收入/成本/毛利率/四费/营业利润/营业外收入/净利润规则；六步框架；行业费用结构特征（半导体高研发低销售、化妆品反之） |
| cash-flow-analysis | 流水账概念、最难造假；三大结构；销售收现/购买付现/CAPEX/筹资分红科目规则；经营+投资−筹资−等正负号组合情景判断；风险信号 |
| three-statement-articulation | 三表定位（根基/过程/结果）；商业模式四循环；筹资/投资/经营三步对应；案例验证法（先搞钱→等订单→扩产→放量）；利润表看增长内驱力 |
| finding-financial-reports | F10资料→经营分析→财务分析路径；资产负债表百分比报表；利润表单季环比；现金流量表三大结构；**财经数据 API（AKShare/Tushare）与网络公开信息（新浪财经/东方财富/web_search）获取最新财报** |

**核心分析铁律**：不看公司自我介绍看科目构成；没有无缘无故的大涨大跌；用"破案"视角交叉验证三张报表；科技公司先看研发费用；经营(−)+投资(−)+筹资(+)为危险组合；新案例用财经数据 API 或网络公开信息获取最新数据，注明报告期与来源。

---

## 六、验证清单

- [ ] `dsh plugin --profile web list` 能看到 `dsh-financial-analysis`（方式一/二）
- [ ] `$DSH_HOME/.agent-presets/financial-analyst/` 存在且含 `agent.cordis.yml`、`preset.yml` 与 `skills/`（「必做」复制步骤）
- [ ] Web 新建会话时预设列表出现「财报分析师」（刷新页面）
- [ ] 提问后 agent 能调用 `web_search` 与 `pwsh`（运行 Python 取数），并输出结构化分析

---

## 七、常见问题

**Q1：新预设没有出现在列表里？**
先确认执行了方式一中的「必做」复制步骤——preset 应位于用户预设根
`$HOME/.dsh/.agent-presets/financial-analyst`（Windows 为 `%USERPROFILE%\.dsh\.agent-presets\financial-analyst`，
不是 `.dsh/skills`），再刷新页面；新预设无需重启进程。

**Q2：`dsh plugin` 报 pnpm 错误？**
安装 pnpm（`npm install -g pnpm` 或 `corepack enable pnpm`）后重试；或直接使用方式三。

**Q3：只想加技能不想换预设？**
把 `skills/` 下任意 SKILL.md 复制到项目 `.dsh/skills/<技能名>/` 或 `$DSH_HOME/skills/` 即可被通用发现。

**Q4：如何卸载？**
方式一/二：`dsh plugin --profile web remove dsh-financial-analysis`；方式三：
删除 `$env:USERPROFILE\.dsh\.agent-presets\financial-analyst`。两种都装过则都清理。

**Q5：取数失败或 akshare 报错？**
确认 Python 已装且 `pip install akshare tushare pandas` 成功；接口失败时 agent 会自动换备用接口
（东财→新浪→同花顺）或改用 web_search；网络受限时以官方公告/公开信息为准。

---

