# A股本地股票买卖方案推荐平台

这是一个**本地运行**的 A 股股票买卖方案推荐平台。它会在每天晚上 20:00 自动更新数据，执行多套选股策略，再调用 AI 对候选股票进行综合分析，最终输出近期最推荐的 3 只股票及对应交易计划。

> 重要声明：本项目仅用于学习、研究和辅助决策，不构成任何投资建议。A 股市场风险高，任何策略都可能失效，请自行承担交易风险。

## 当前版本

当前版本是 v0.2 稳定性修复版，重点修复了：

- 日志与错误统计
- AkShare 数据清洗
- 本地日线缓存
- 股票风险过滤
- AI 输出校验
- Web 后台任务锁
- POST 手动触发任务
- HTML 输出转义
- 时区感知定时任务
- 基础 pytest 测试

修复记录见：

```text
docs/FIXES.md
```

## 核心流程

平台每天完成以下流程：

1. 自动更新 A 股行情、指数、基础财务字段和市场消息。
2. 按成交额排序并过滤高风险股票。
3. 运行多套适合 A 股的选股策略。
4. 为每只候选股生成买入时机、止损位、止盈位、仓位建议和持仓周期。
5. 调用 AI 综合分析：市场消息、盈利空间、回撤风险、资金热度、策略共振程度。
6. 输出当天或近期最推荐的 3 只股票交易方案。

## 当前内置策略

### 1. 趋势龙头策略

适合 A 股主线行情，比如 AI、半导体、机器人、高端制造等。

核心条件：

- 股价在 20 日均线和 60 日均线上方。
- 20 日均线高于 60 日均线。
- 近 20 日涨幅较强。
- 成交额没有明显萎缩。
- 大盘强势时加分。

交易计划：

- 买入时机：回踩 20 日线不破，或放量突破近期平台。
- 止损：跌破 20 日线或买入价下方 6%~8%。
- 止盈：达到 15%~25% 后分批止盈，或跌破 10 日线减仓。
- 持仓周期：5~20 个交易日。

### 2. 放量突破策略

适合指数放量、市场情绪上升时。

核心条件：

- 突破近 60 日高点。
- 当日成交量大于 20 日均量的 1.5 倍。
- 收盘价靠近当日高位。
- 避免涨跌停附近、停牌、低流动性股票。

交易计划：

- 买入时机：突破后次日不低开破位，或盘中回踩突破位企稳。
- 止损：跌回突破位下方 3%~5%。
- 止盈：第一目标 10%~15%，强势股用移动止盈。
- 持仓周期：3~10 个交易日。

### 3. 低波动质量趋势策略

适合震荡市和中线配置。

当前版本已接入：

- 价格趋势
- 波动率
- 最大回撤
- PE
- PB

后续建议接入 Tushare Pro 完善：

- ROE
- 毛利率
- 经营现金流
- 扣非净利增速

交易计划：

- 买入时机：回踩 60 日线或 20 日线企稳。
- 止损：跌破 60 日线或基本面显著恶化。
- 止盈：20% 以上分批兑现，趋势未破可继续持有。
- 持仓周期：20~60 个交易日。

### 4. 超跌反弹策略

适合市场急跌后的修复行情，不适合熊市单边下跌。

核心条件：

- RSI 低位重新上穿。
- 股价偏离 20 日均线后出现修复。
- 成交量没有明显萎缩。
- 弱势市场中过滤该策略。

交易计划：

- 买入时机：止跌阳线确认，或 RSI 上穿 30。
- 止损：跌破近期低点。
- 止盈：反弹至 20 日线附近先减仓。
- 持仓周期：2~8 个交易日。

## 风险过滤

当前会过滤：

- ST / *ST
- 退市股
- 北交所/旧市场代码
- 停牌或无效价格
- 涨跌停附近股票
- 成交额低于阈值的低流动性股票
- 历史数据不足的新股或次新股

默认最低成交额：

```env
MIN_AMOUNT=100000000
```

## 数据来源与更新方式

默认使用公开数据源，适合本地个人研究。

| 数据 | 默认来源 | 获取方式 |
|---|---|---|
| A 股实时/日线行情 | AkShare 东方财富接口 | `ak.stock_zh_a_spot_em` / `ak.stock_zh_a_hist` |
| 指数行情 | AkShare | `ak.stock_zh_index_daily_em` |
| 个股新闻 | AkShare 东方财富新闻接口 | `ak.stock_news_em` |
| 市场新闻 | AkShare 财经新闻接口 | 财联社/东方财富相关公开接口 |
| AI 分析 | OpenAI-compatible API | 本地 `.env` 配置 API Key |

日线数据会缓存到：

```text
data/cache/daily/{code}.csv
```

默认缓存有效期：

```env
CACHE_MAX_AGE_HOURS=18
```

## 本地运行

### 1. 克隆项目

```bash
git clone https://github.com/txq85721-wq/A.git
cd A
```

### 2. 创建虚拟环境

```bash
python -m venv .venv
source .venv/bin/activate  # Windows 使用 .venv\\Scripts\\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
```

关键配置：

```env
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
MAX_STOCKS_TO_SCAN=1500
MIN_AMOUNT=100000000
MIN_HISTORY_DAYS=120
DAILY_RUN_TIME=20:00
TIMEZONE=Asia/Shanghai
```

如果没有 AI Key，平台仍会输出规则策略结果，但 AI 综合分析会使用本地规则摘要代替。

### 5. 手动运行一次

```bash
python run.py --once
```

### 6. 启动本地 Web 平台

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

打开：

```text
http://127.0.0.1:8000
```

手动触发后台任务：

```bash
curl -X POST http://127.0.0.1:8000/run
```

查看任务状态：

```text
http://127.0.0.1:8000/status
```

### 7. 启动定时任务

```bash
python run.py --schedule
```

服务会按 `.env` 中的配置自动运行：

```env
DAILY_RUN_TIME=20:00
TIMEZONE=Asia/Shanghai
```

### 8. 运行测试

```bash
pytest
```

## 输出结果

推荐报告会写入：

```text
data/reports/latest_report.md
```

报告包含：

- 推荐股票代码和名称
- 推荐策略来源
- 买入时机
- 止损位
- 止盈位
- 建议仓位
- 持仓周期
- 推荐理由
- 最近市场消息
- 盈利空间和回撤风险评估
- 扫描统计、过滤原因、错误统计

## 项目结构

```text
A/
├── app/
│   ├── main.py              FastAPI Web 服务
│   ├── config.py            配置读取
│   ├── database.py          SQLite 存储
│   ├── scheduler.py         每晚定时任务
│   ├── pipeline.py          全流程编排
│   ├── ai_analyzer.py       AI 复核分析
│   ├── report.py            Markdown 报告生成
│   ├── task_manager.py      Web 后台任务锁
│   ├── utils.py             数据清洗、日志、JSON 提取
│   ├── data_sources/
│   │   └── akshare_source.py
│   └── strategies/
│       ├── indicators.py
│       ├── market_regime.py
│       ├── risk_filters.py
│       ├── trend_leader.py
│       ├── breakout.py
│       ├── quality_trend.py
│       └── oversold_rebound.py
├── tests/
├── docs/
│   └── FIXES.md
├── run.py
├── requirements.txt
├── .env.example
└── README.md
```

## 仍需注意

- AkShare 是公开数据源，接口可能变化或限流。
- 推荐结果必须结合第二天开盘表现确认，不能机械挂单。
- 当前没有接入真实交易接口，不会自动买卖。
- 当前质量因子仍不完整，建议后续接入 Tushare Pro 财务数据。
- 真正投入资金前，应先增加回测模块和模拟组合跟踪。
