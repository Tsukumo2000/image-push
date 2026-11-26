---
name: local-financial-database
description: 本地财务数据库（data/stock.db）的结构与用法。任何财务分析开始前必须先读本文件，确认可用股票范围、报告期覆盖与工具命令。所有数字必须来自本库，不得凭记忆作答。
---

# 本地财务数据库

## 数据库位置

`data/stock.db`（SQLite，相对于本插件包根目录）

## 库内数据范围

本库为离线快照，**不联网、不更新**。覆盖以下 5 只 A 股上市公司：

| code | name | industry |
|---|---|---|
| 688981 | 中芯国际 | 半导体 |
| 603986 | 兆易创新 | 半导体 |
| 600900 | 长江电力 | 电力 |
| 601985 | 中国核电 | 电力 |
| 002230 | 科大讯飞 | AI |

财报覆盖：2022 年至 2026 年三季报（按报告期，含 0331/0630/0930/1231 四类）
行情覆盖：2022-01-04 至 2026-11-26 日线

**问到的公司不在这 5 家里 → 必须直接告知用户本库无该公司数据，不得用外部知识作答。**

## 表结构

### stocks
股票基本信息。字段：code（代码）、symbol（带市场前缀）、name（简称）、industry（所属行业）

### daily_quote
日线行情。字段：code、date（YYYY-MM-DD）、open、high、low、close、volume（股）、amount（元）、turnover（换手率，小数）
主键：(code, date)

### financial_report
三大报表，长表结构（一行一个科目值）。字段：code、report_date（YYYYMMDD，如 20241231）、statement（资产负债表/利润表/现金流量表）、item（科目名）、value（数值，单位：元）
主键：(code, report_date, statement, item)

## 常用科目名（必须用这些原始名称查询）

资产负债表：流动资产合计、流动负债合计、存货、资产总计、负债合计、所有者权益(或股东权益)合计、货币资金、应收账款、固定资产净值
利润表：营业收入、营业总收入、营业成本、研发费用、销售费用、管理费用、净利润、归属于母公司所有者的净利润
现金流量表：经营活动产生的现金流量净额、投资活动产生的现金流量净额、筹资活动产生的现金流量净额、购建固定资产、无形资产和其他长期资产支付的现金

## 工具

本插件自带工具脚本 `tools/query_finance.py`，是唯一的数据入口。**必须调用它取数，禁止自己心算或凭记忆给数字。**

```
python tools/query_finance.py list                          # 列出库内全部股票
python tools/query_finance.py quote <code> <起> <止>         # 行情区间，如 quote 688981 2024 2025
python tools/query_finance.py report <code> <期>             # 某期三表全部科目，如 report 688981 2024
python tools/query_finance.py item <code> <期> <科目>         # 单科目，支持模糊匹配
python tools/query_finance.py ratio <code> <期>              # 核心指标（流动/速动/资产负债率/净利率）
python tools/query_finance.py trend <code> <科目> [期数]      # 年度走势
```

报告期写法：`2024` 等价于 `20241231`；也可直接写 `20240930`。

## 使用纪律

1. 每次分析前先跑 `list` 确认目标公司在库内。
2. 取任何数字都通过工具，输出里带 `"source": "data/stock.db"` 即为库内数据。
3. 工具返回 `error`（如某期无数据）→ 把原始错误告诉用户，不要自行补数或推测。
4. 本库仅有 5 家公司——结论只能就这 5 家而言，不得外推到行业或全市场。
