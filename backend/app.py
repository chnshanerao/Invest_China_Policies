import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from database import get_connection, init_db
from seed_data import seed_data
from data_collector import run_full_update
from update_scheduler import UpdateScheduler, run_full_update_cycle, run_signal_collection, run_llm_analysis
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
_scheduler = UpdateScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_data()
    if not config.anthropic_api_key:
        logger.warning("ANTHROPIC_API_KEY not set — LLM analysis disabled. News scraping still active.")
    _scheduler.start()
    logger.info(f"App started. Scheduler active. LLM enabled: {config.llm_enabled}")
    yield
    _scheduler.stop()


app = FastAPI(title="中国国家政策投资追踪系统", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    with open(os.path.join(FRONTEND_DIR, "index.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/api/categories")
async def get_categories():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM policy_categories ORDER BY sort_order")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


@app.get("/api/filters")
async def get_filter_options():
    conn = get_connection()
    cursor = conn.cursor()

    stage_order = ['规划期','启动期','扩张期','验证期','成熟期','调整期','衰退期']
    cursor.execute("SELECT DISTINCT lifecycle_stage FROM policies WHERE lifecycle_stage IS NOT NULL")
    raw_stages = [r[0] for r in cursor.fetchall()]
    stages = [s for s in stage_order if s in raw_stages]

    cursor.execute("SELECT DISTINCT policy_momentum FROM policies WHERE policy_momentum IS NOT NULL ORDER BY policy_momentum")
    momentums = [r[0] for r in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT region FROM policies WHERE region IS NOT NULL ORDER BY region")
    regions = [r[0] for r in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT risk_level FROM policies ORDER BY risk_level")
    risks = [r[0] for r in cursor.fetchall()]

    cursor.execute("SELECT id, name FROM policy_categories ORDER BY sort_order")
    categories = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        "stages": stages,
        "momentums": momentums,
        "regions": regions,
        "risks": risks,
        "categories": categories,
    }


@app.get("/api/policies/detail-table")
async def get_detail_table(
    lifecycle_stage: str = None,
    momentum: str = None,
    category_id: int = None,
    risk: str = None,
    sort_by: str = "lifecycle",
):
    conn = get_connection()
    cursor = conn.cursor()

    stage_order_sql = """
        CASE lifecycle_stage
            WHEN '规划期' THEN 1 WHEN '启动期' THEN 2 WHEN '扩张期' THEN 3
            WHEN '验证期' THEN 4 WHEN '成熟期' THEN 5 WHEN '调整期' THEN 6
            WHEN '衰退期' THEN 7 ELSE 8 END
    """

    query = f"""
        SELECT p.*, pc.name as category_name,
               (SELECT COUNT(*) FROM investment_opportunities io WHERE io.policy_id = p.id) as opportunity_count
        FROM policies p
        JOIN policy_categories pc ON p.category_id = pc.id
        WHERE 1=1
    """
    params = []
    if lifecycle_stage:
        query += " AND p.lifecycle_stage = ?"
        params.append(lifecycle_stage)
    if momentum:
        query += " AND p.policy_momentum = ?"
        params.append(momentum)
    if category_id:
        query += " AND p.category_id = ?"
        params.append(category_id)
    if risk:
        query += " AND p.risk_level = ?"
        params.append(risk)

    sort_map = {
        "lifecycle": f"{stage_order_sql}, p.execution_intensity DESC",
        "year": "p.established_year ASC",
        "intensity_desc": "p.execution_intensity DESC",
        "intensity_asc": "p.execution_intensity ASC",
        "effectiveness_desc": "p.execution_effectiveness DESC",
        "effectiveness_asc": "p.execution_effectiveness ASC",
        "category": "pc.sort_order, p.established_year",
    }
    query += f" ORDER BY {sort_map.get(sort_by, sort_map['lifecycle'])}"

    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


@app.get("/api/policies")
async def get_policies(
    category_id: int = None,
    search: str = None,
    risk: str = None,
    lifecycle_stage: str = None,
    momentum: str = None,
    region: str = None,
    sort_by: str = "category",
):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT p.*, pc.name as category_name, pc.name_en as category_name_en,
               (SELECT COUNT(*) FROM investment_opportunities io WHERE io.policy_id = p.id) as opportunity_count,
               (SELECT COUNT(*) FROM policy_news pn WHERE pn.policy_id = p.id) as news_count
        FROM policies p
        JOIN policy_categories pc ON p.category_id = pc.id
        WHERE 1=1
    """
    params = []
    if category_id:
        query += " AND p.category_id = ?"
        params.append(category_id)
    if search:
        query += " AND (p.name LIKE ? OR p.description LIKE ? OR p.region LIKE ? OR p.key_goals LIKE ?)"
        params.extend([f"%{search}%"] * 4)
    if risk:
        query += " AND p.risk_level = ?"
        params.append(risk)
    if lifecycle_stage:
        query += " AND p.lifecycle_stage = ?"
        params.append(lifecycle_stage)
    if momentum:
        query += " AND p.policy_momentum = ?"
        params.append(momentum)
    if region:
        query += " AND p.region LIKE ?"
        params.append(f"%{region}%")

    sort_map = {
        "category": "pc.sort_order, p.established_year",
        "year": "p.established_year DESC",
        "intensity": "p.execution_intensity DESC",
        "effectiveness": "p.execution_effectiveness DESC",
        "risk": "p.risk_level",
        "stage": "p.lifecycle_stage",
    }
    query += f" ORDER BY {sort_map.get(sort_by, sort_map['category'])}"

    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


@app.get("/api/policies/{policy_id}")
async def get_policy_detail(policy_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, pc.name as category_name
        FROM policies p JOIN policy_categories pc ON p.category_id = pc.id
        WHERE p.id = ?
    """, (policy_id,))
    policy = cursor.fetchone()
    if not policy:
        conn.close()
        raise HTTPException(404, "Policy not found")

    policy = dict(policy)

    cursor.execute("SELECT * FROM investment_opportunities WHERE policy_id = ? ORDER BY sector", (policy_id,))
    policy["opportunities"] = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM policy_news WHERE policy_id = ? ORDER BY collected_at DESC LIMIT 20", (policy_id,))
    policy["news"] = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM policy_metrics WHERE policy_id = ? ORDER BY metric_year DESC", (policy_id,))
    policy["metrics"] = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return policy


@app.get("/api/opportunities")
async def get_opportunities(sector: str = None, risk: str = None, horizon: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT io.*, p.name as policy_name, p.risk_level as policy_risk,
               p.lifecycle_stage as policy_lifecycle, p.policy_momentum
        FROM investment_opportunities io
        JOIN policies p ON io.policy_id = p.id
        WHERE 1=1
    """
    params = []
    if sector:
        query += " AND io.sector LIKE ?"
        params.append(f"%{sector}%")
    if risk:
        query += " AND io.risk_level = ?"
        params.append(risk)
    if horizon:
        query += " AND io.time_horizon = ?"
        params.append(horizon)
    query += " ORDER BY io.confidence_score DESC"

    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


@app.get("/api/dashboard/summary")
async def get_dashboard_summary():
    conn = get_connection()
    cursor = conn.cursor()

    total_policies = cursor.execute("SELECT COUNT(*) FROM policies").fetchone()[0]
    total_opps = cursor.execute("SELECT COUNT(*) FROM investment_opportunities").fetchone()[0]
    total_news = cursor.execute("SELECT COUNT(*) FROM policy_news").fetchone()[0]
    total_categories = cursor.execute("SELECT COUNT(*) FROM policy_categories").fetchone()[0]

    cursor.execute("""
        SELECT pc.name, COUNT(p.id) as count
        FROM policy_categories pc
        LEFT JOIN policies p ON p.category_id = pc.id
        GROUP BY pc.id ORDER BY pc.sort_order
    """)
    by_category = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT risk_level, COUNT(*) as count FROM policies GROUP BY risk_level")
    by_risk = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT lifecycle_stage, COUNT(*) as count
        FROM policies WHERE lifecycle_stage IS NOT NULL
        GROUP BY lifecycle_stage ORDER BY count DESC
    """)
    by_lifecycle = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT policy_momentum, COUNT(*) as count
        FROM policies WHERE policy_momentum IS NOT NULL
        GROUP BY policy_momentum ORDER BY count DESC
    """)
    by_momentum = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT io.sector, COUNT(*) as count
        FROM investment_opportunities io
        GROUP BY io.sector ORDER BY count DESC LIMIT 15
    """)
    by_sector = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT pn.sentiment, COUNT(*) as count
        FROM policy_news pn GROUP BY pn.sentiment
    """)
    sentiment_dist = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT du.update_type, du.status, du.records_updated, du.started_at, du.completed_at
        FROM data_updates du ORDER BY du.id DESC LIMIT 5
    """)
    recent_updates = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT AVG(execution_intensity) as avg_intensity,
               AVG(execution_effectiveness) as avg_effectiveness
        FROM policies
    """)
    avgs = dict(cursor.fetchone())

    conn.close()
    return {
        "total_policies": total_policies,
        "total_opportunities": total_opps,
        "total_news": total_news,
        "total_categories": total_categories,
        "by_category": by_category,
        "by_risk": by_risk,
        "by_lifecycle": by_lifecycle,
        "by_momentum": by_momentum,
        "by_sector": by_sector,
        "sentiment_distribution": sentiment_dist,
        "recent_updates": recent_updates,
        "avg_intensity": round(avgs["avg_intensity"] or 0, 1),
        "avg_effectiveness": round(avgs["avg_effectiveness"] or 0, 1),
    }


@app.get("/api/news")
async def get_news(policy_id: int = None, sentiment: str = None, limit: int = 50):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT pn.*, p.name as policy_name
        FROM policy_news pn
        JOIN policies p ON pn.policy_id = p.id
        WHERE 1=1
    """
    params = []
    if policy_id:
        query += " AND pn.policy_id = ?"
        params.append(policy_id)
    if sentiment:
        query += " AND pn.sentiment = ?"
        params.append(sentiment)
    query += " ORDER BY pn.collected_at DESC LIMIT ?"
    params.append(min(limit, 200))
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


@app.post("/api/update/trigger")
async def trigger_update():
    try:
        asyncio.create_task(run_full_update())
        return {"status": "started", "message": "数据更新已触发，后台运行中"}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/update/trigger-signals")
async def trigger_signals_only():
    """Trigger signal collection only (no LLM analysis)."""
    try:
        asyncio.create_task(run_signal_collection())
        return {"status": "started", "message": "信号采集已触发，后台运行中"}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/update/trigger-llm")
async def trigger_llm_update(force_all: bool = False):
    """Trigger full LLM update cycle (signal collection + LLM analysis + change application)."""
    if not config.anthropic_api_key:
        raise HTTPException(400, "ANTHROPIC_API_KEY 未配置。请在 .env 文件中设置后重启服务。")
    try:
        asyncio.create_task(run_full_update_cycle(force_all=force_all))
        return {"status": "started", "message": "LLM 更新已触发，后台运行中", "llm_enabled": config.llm_enabled}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/updates")
async def get_update_history():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM data_updates ORDER BY id DESC LIMIT 20")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


@app.get("/api/reviews/pending")
async def get_pending_reviews():
    """List all changes awaiting human review."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT l.*, p.name as policy_name, p.lifecycle_stage, p.execution_intensity,
               p.execution_effectiveness, p.policy_momentum
        FROM llm_analysis_log l
        JOIN policies p ON l.policy_id = p.id
        WHERE l.status = 'manual_review'
        ORDER BY l.created_at DESC
    """)
    rows = []
    for r in cursor.fetchall():
        row = dict(r)
        try:
            row["proposed_changes"] = json.loads(row["proposed_changes"] or "{}")
        except Exception:
            pass
        rows.append(row)
    conn.close()
    return rows


@app.post("/api/reviews/{log_id}/approve")
async def approve_review(log_id: int):
    """Human approves a pending change — applies it to the DB."""
    from change_applier import ChangeApplier
    applier = ChangeApplier()
    ok = applier.approve_change(log_id)
    if not ok:
        raise HTTPException(404, "未找到待审核记录，或状态不是 manual_review")
    return {"status": "approved", "log_id": log_id}


@app.post("/api/reviews/{log_id}/reject")
async def reject_review(log_id: int, reason: str = ""):
    """Human rejects a pending change."""
    from change_applier import ChangeApplier
    applier = ChangeApplier()
    ok = applier.reject_change(log_id, reason)
    if not ok:
        raise HTTPException(404, "未找到记录")
    return {"status": "rejected", "log_id": log_id}


@app.get("/api/llm/history")
async def get_llm_history(
    policy_id: int = None, status: str = None, limit: int = 50
):
    """Paginated LLM analysis audit log."""
    conn = get_connection()
    query = """
        SELECT l.*, p.name as policy_name
        FROM llm_analysis_log l
        JOIN policies p ON l.policy_id = p.id
        WHERE 1=1
    """
    params = []
    if policy_id:
        query += " AND l.policy_id = ?"
        params.append(policy_id)
    if status:
        query += " AND l.status = ?"
        params.append(status)
    query += " ORDER BY l.created_at DESC LIMIT ?"
    params.append(min(limit, 200))
    rows = [dict(r) for r in conn.execute(query, params).fetchall()]
    conn.close()
    return rows


@app.get("/api/llm/costs")
async def get_llm_costs():
    """Aggregate token usage and cost from llm_analysis_log."""
    conn = get_connection()
    today = dict(conn.execute("""
        SELECT COALESCE(SUM(cost_usd),0) as cost,
               COALESCE(SUM(prompt_tokens),0) as input_tokens,
               COALESCE(SUM(completion_tokens),0) as output_tokens,
               COUNT(*) as calls
        FROM llm_analysis_log WHERE created_at > datetime('now', '-1 day')
    """).fetchone())
    total = dict(conn.execute("""
        SELECT COALESCE(SUM(cost_usd),0) as cost,
               COALESCE(SUM(prompt_tokens),0) as input_tokens,
               COALESCE(SUM(completion_tokens),0) as output_tokens,
               COUNT(*) as calls
        FROM llm_analysis_log
    """).fetchone())
    conn.close()
    return {
        "today": today,
        "total": total,
        "daily_cap_usd": config.max_daily_cost_usd,
    }


@app.get("/api/llm/config")
async def get_llm_config():
    """Return current LLM configuration (not the API key)."""
    return {
        **config.as_dict(),
        "llm_active": config.llm_enabled,
        "api_key_configured": bool(config.anthropic_api_key),
    }


@app.put("/api/llm/config")
async def update_llm_config(updates: dict):
    """Update configuration values in update_config table."""
    allowed = {"auto_apply_threshold", "anthropic_model", "max_policies_per_batch",
                "scrape_rate_limit_seconds", "update_interval_hours", "max_daily_cost_usd",
                "llm_enabled", "signal_collection_enabled"}
    updated = []
    for key, value in updates.items():
        if key in allowed:
            config.set(key, str(value))
            updated.append(key)
    return {"updated": updated}


@app.post("/api/llm/api-key")
async def set_api_key(body: dict):
    """Set the Anthropic API key at runtime (stored in .env and environment)."""
    key = body.get("api_key", "").strip()
    if not key:
        raise HTTPException(400, "api_key is required")
    if not key.startswith("sk-ant-"):
        raise HTTPException(400, "Invalid API key format. Should start with sk-ant-")
    os.environ["ANTHROPIC_API_KEY"] = key
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    with open(env_path, "w") as f:
        f.write(f"ANTHROPIC_API_KEY={key}\n")
    logger.info("API key updated via settings page")
    return {"status": "ok", "api_key_configured": True}


@app.get("/api/signals")
async def get_signals(policy_id: int = None, signal_type: str = None, processed: int = None, limit: int = 50):
    """Browse collected raw signals."""
    conn = get_connection()
    query = """
        SELECT s.*, p.name as policy_name
        FROM policy_signals s
        LEFT JOIN policies p ON s.policy_id = p.id
        WHERE 1=1
    """
    params = []
    if policy_id:
        query += " AND s.policy_id = ?"
        params.append(policy_id)
    if signal_type:
        query += " AND s.signal_type = ?"
        params.append(signal_type)
    if processed is not None:
        query += " AND s.is_processed = ?"
        params.append(processed)
    query += " ORDER BY s.collected_at DESC LIMIT ?"
    params.append(min(limit, 500))
    rows = [dict(r) for r in conn.execute(query, params).fetchall()]
    conn.close()
    return rows


@app.get("/api/sectors")
async def get_sectors():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT io.sector, COUNT(*) as count,
               GROUP_CONCAT(DISTINCT p.name) as related_policies
        FROM investment_opportunities io
        JOIN policies p ON io.policy_id = p.id
        GROUP BY io.sector ORDER BY count DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


@app.get("/api/scoring-methodology")
async def get_scoring_methodology():
    return {
        "lifecycle_stages": [
            {"stage": "规划期", "stage_en": "Planning", "definition": "政策酝酿讨论阶段，尚未正式发文实施", "typical_duration": "不定"},
            {"stage": "启动期", "stage_en": "Launch", "definition": "政策文件已发布，领导机构组建，试点启动，配套细则制定中", "typical_duration": "0-2年"},
            {"stage": "扩张期", "stage_en": "Expansion", "definition": "大规模资金投入，快速推进，政策红利集中释放，各地积极响应", "typical_duration": "2-5年"},
            {"stage": "验证期", "stage_en": "Validation", "definition": "初期建设基本完成，开始检验实际成效，问题和矛盾暴露，政策优化调整", "typical_duration": "3-7年"},
            {"stage": "成熟期", "stage_en": "Maturity", "definition": "制度框架稳定，运行进入常态化，效果可度量，不再需要持续高强度政策推动", "typical_duration": "5-15+年"},
            {"stage": "调整期", "stage_en": "Adjustment", "definition": "外部环境变化或内在矛盾导致政策方向转型，力度和重心发生明显变化", "typical_duration": "不定"},
            {"stage": "衰退期", "stage_en": "Decline", "definition": "边际效益持续递减，政策关注度下降，逐步被新政策替代或淡化", "typical_duration": "不定"},
        ],
        "intensity_scoring": {
            "description": "执行力度评分(1-10分)，衡量政策推进的投入力度",
            "criteria": [
                {"factor": "资金投入规模", "weight": "30%", "description": "中央及地方财政专项资金、专项债、基金规模。数据来源：财政部预算报告、发改委批复"},
                {"factor": "政策文件密度", "weight": "20%", "description": "近3年相关政策文件出台数量与级别(国务院/部委/地方)。数据来源：gov.cn政策库"},
                {"factor": "领导层关注度", "weight": "25%", "description": "是否写入政府工作报告、中央经济工作会议、政治局会议。数据来源：官方会议通报"},
                {"factor": "配套措施完备度", "weight": "25%", "description": "法律法规、实施细则、考核机制、组织架构是否齐备。数据来源：全国人大法律库、部委规章"},
            ],
            "scale": "1-3分:低力度(偶有提及,无专项资金) | 4-6分:中力度(有规划,有资金,常规推进) | 7-8分:高力度(专项立法,大规模投入,高层频繁关注) | 9-10分:极高力度(写入党代会报告,举国推进,政治任务级别)"
        },
        "effectiveness_scoring": {
            "description": "执行效果评分(1-10分)，衡量政策实际产出效果",
            "criteria": [
                {"factor": "经济指标达成", "weight": "30%", "description": "GDP贡献、产业产值、税收等量化目标完成率。数据来源：国家统计局、各省市统计公报"},
                {"factor": "就业与人口效应", "weight": "15%", "description": "新增就业、人口集聚能力。数据来源：人社部、统计局人口普查"},
                {"factor": "产业集聚效应", "weight": "25%", "description": "龙头企业数量、产业链完整度、全球竞争力。数据来源：工信部、各产业协会"},
                {"factor": "制度创新贡献", "weight": "15%", "description": "可复制推广的制度成果数量。数据来源：商务部自贸区经验推广通报"},
                {"factor": "社会/生态效益", "weight": "15%", "description": "环境改善、民生提升等非经济指标。数据来源：生态环境部、卫健委"},
            ],
            "scale": "1-3分:效果差(投入远大于产出,目标未达成) | 4-6分:效果一般(部分目标达成,仍有明显短板) | 7-8分:效果好(多数目标达成或超额,产生示范效应) | 9-10分:效果卓越(全面超额完成,产生全球影响力)"
        },
        "momentum_definition": {
            "description": "政策动量评估，基于近1-2年的变化趋势",
            "criteria": {
                "加速": "政策力度或效果在近期有明显增强趋势：新增专项政策、投资加码、成效加速显现",
                "平稳": "政策按既定节奏推进，无明显加速或减速信号",
                "减速": "政策力度或关注度下降，投资放缓，或外部环境导致推进受阻",
            }
        },
        "data_integrity_rules": [
            "所有GDP、投资、财政、债务等数值必须有明确的官方统计来源",
            "无法从官方渠道验证的数值字段标记为NULL(在界面显示为'-')",
            "生命周期阶段判定必须基于可观察的客观事实(政策文件、统计数据、公开报道)",
            "评分依据(intensity_basis/effectiveness_basis)必须注明具体数据来源",
            "data_verified字段: 0=未验证 1=部分验证(有来源但数据可能不完整) 2=已验证(核心数据有官方来源)",
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
