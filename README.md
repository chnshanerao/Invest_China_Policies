# 中国国家政策投资追踪系统

> Policy Investment Tracker — 追踪 92 项国家级战略政策的生命周期、执行力度、投资机会

## 为什么需要这个系统？

在中国，无论是**投资、择业、选城市、家庭规划**，都离不开对国家政策的理解。但 92 项国家级战略政策纷繁复杂，普通人很难分辨：

- 这个政策是**真金白银在砸钱**，还是**喊了个口号**？
- 我所在的行业/城市，背后的政策是在**加速**还是**衰退**？
- 同样叫"国家战略"，**深圳特区**和**霍尔果斯**的执行效果差了 5 倍，怎么看出来？

本系统用**数据驱动**的方式，给每项政策打分、追踪生命周期、识别投资机会——让任何人都能**一目了然**地概览中国所有现行政策。

## 快速启动

```bash
# 1. 克隆项目
git clone https://github.com/chnshanerao/Invest_China_Policies_Rao-stalk.git
cd Invest_China_Policies_Rao-stalk

# 2. 安装依赖
pip install fastapi uvicorn aiohttp beautifulsoup4

# 3. 启动（自动初始化数据库和 92 项政策数据）
python3 backend/app.py

# 4. 打开浏览器访问 http://localhost:8080
```

启动后即可看到完整的 92 项政策数据，包含生命周期评分、投资机会等——**无需任何额外配置**。

## 配置 AI 自动更新（可选）

系统内置 AI 驱动的自动更新引擎。配置后，系统可以自动从官方数据源采集最新信号，使用 Claude 分析并更新政策评分。

### 方式一：通过设置页面（推荐）

1. 启动系统后，点击导航栏 **「设置」** 标签
2. 在 **API Key** 栏输入你的 [Anthropic API Key](https://console.anthropic.com/)
3. 点击 **「保存设置」**
4. 点击 **「AI 分析更新」** 按钮触发更新

### 方式二：通过 .env 文件

在项目根目录创建 `.env` 文件：
```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxx
```

重启服务即可。

### 更新流程

```
第一步：采集信号
  ├── gov.cn 政策文件搜索
  ├── 国家统计局数据
  ├── 百度新闻
  └── 国务院/政治局领导信号

第二步：AI 分析（Claude）
  每个政策：当前状态 + 新信号 → 结构化评估
  输出：生命周期变化？力度/效果分数调整？

第三步：置信度门控
  ≥ 85% → 自动应用
  50-85% → 标记为「待人工审核」（设置页面可审批）
  < 50% → 拒绝（信号不足）
```

不配置 API Key 也完全不影响使用——系统自带完整的 92 项政策初始数据。

## 功能页面

| 页面 | 说明 |
|------|------|
| **仪表板** | 生命周期分布、动量趋势、风险矩阵、热门行业 TOP 12 |
| **生命周期** | 泳道式布局，按 7 个生命阶段分栏展示所有政策 |
| **明细数据** | 92 项政策 × 17 列全量表格，含数据来源和评分依据 |
| **政策列表** | 可筛选的政策卡片，支持多维度筛选和搜索 |
| **投资机会** | 72 个投资方向，含股票代码、ETF、风险/回报/期限 |
| **政策新闻** | 自动采集的政策相关新闻，附情绪分析 |
| **设置** | API Key 配置、一键更新、费用统计、人工审核面板 |

## 核心特性

- **7 阶段生命周期模型**：规划期 → 启动期 → 扩张期 → 验证期 → 成熟期 → 调整期 → 衰退期
- **量化评分体系**：执行力度 (1-10) + 执行效果 (1-10)，附评分依据与权重说明
- **政策动量评估**：加速 / 平稳 / 减速
- **数据完整性保障**：41 项重点政策标注官方数据来源，无法验证的字段一律留空，不做臆测
- **AI 自动更新**：接入 Claude API 后，自动采集信号 → 分析 → 更新，置信度门控 + 人工审核

## 政策覆盖范围

| 类别 | 数量 | 示例 |
|------|------|------|
| 国际战略 | 3 | 一带一路、RCEP、中国-东盟自贸区 |
| 区域重大战略 | 7 | 京津冀协同、粤港澳大湾区、长三角一体化 |
| 经济特区 | 7 | 深圳、海南自贸港、雄安新区 |
| 国家级新区 | 19 | 浦东新区、天津滨海、两江新区 |
| 自贸试验区/港 | 22 | 上海自贸区、海南自贸港、新疆自贸区 |
| 基础设施超级工程 | 9 | 八纵八横高铁网、川藏铁路、东数西算 |
| 产业战略 | 8 | 中国制造2025、新能源汽车、双碳战略 |
| 科技创新战略 | 6 | 人工智能、量子科技、商业航天 |
| 民生与社会战略 | 4 | 房住不炒、三孩政策、乡村振兴 |
| 安全与治理战略 | 7 | 粮食安全、能源安全、国防现代化 |

## 项目结构

```
policy-tracker/
├── backend/
│   ├── app.py                  # FastAPI 主应用 + API 端点
│   ├── database.py             # SQLite 数据库 (9 张表)
│   ├── seed_data.py            # 92 项政策 + 72 个投资机会
│   ├── lifecycle_assessment.py # 生命周期评估数据
│   ├── data_sources.py         # 41 项政策的可验证数据来源
│   ├── data_collector.py       # 新闻采集 + 情绪分析
│   ├── config.py               # 配置管理（API Key、模型等）
│   ├── signal_collector.py     # 多源信号采集（gov.cn/统计局/新闻）
│   ├── llm_analyzer.py         # Claude API 分析引擎
│   ├── change_applier.py       # 置信度门控 + 审计追踪
│   └── update_scheduler.py     # 定时更新调度器
├── frontend/
│   ├── index.html              # 单页应用（7 个标签页）
│   ├── css/style.css           # 暗色主题样式
│   └── js/app.js               # 前端交互与可视化
└── .env                        # API Key（不提交到 Git）
```

## API 接口

| 接口 | 说明 |
|------|------|
| `GET /api/dashboard/summary` | 仪表板汇总数据 |
| `GET /api/policies` | 政策列表（支持筛选和排序） |
| `GET /api/policies/detail-table` | 明细数据表 |
| `GET /api/opportunities` | 投资机会列表 |
| `GET /api/news` | 政策新闻 |
| `GET /api/scoring-methodology` | 评分方法论 |
| `POST /api/update/trigger-llm` | 触发 AI 更新（采集+分析+应用） |
| `POST /api/update/trigger-signals` | 仅采集信号 |
| `GET /api/reviews/pending` | 待人工审核的变更 |
| `POST /api/reviews/{id}/approve` | 批准变更 |
| `GET /api/llm/config` | 查看/修改配置 |
| `POST /api/llm/api-key` | 设置 API Key |
| `GET /api/llm/costs` | 费用统计 |

## 技术栈

- **后端**：Python 3 / FastAPI / SQLite (WAL mode)
- **前端**：原生 HTML / CSS / JavaScript（无框架依赖）
- **AI 分析**：Anthropic Claude API（可选）
- **数据采集**：aiohttp + BeautifulSoup
- **定时更新**：asyncio 调度器（可配置间隔）

## 许可证

MIT
