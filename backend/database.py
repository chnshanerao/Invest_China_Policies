import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "policies.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS policy_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        name_en TEXT,
        description TEXT,
        sort_order INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS policies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        name_en TEXT,
        category_id INTEGER NOT NULL,
        established_year INTEGER,
        region TEXT,
        level TEXT DEFAULT '国家级',
        status TEXT DEFAULT '实施中',
        description TEXT,
        key_goals TEXT,
        total_investment_billion REAL,
        gdp_billion REAL,
        gdp_year INTEGER,
        fiscal_revenue_billion REAL,
        debt_billion REAL,
        population_million REAL,
        area_sqkm REAL,
        investment_efficiency REAL,
        fiscal_self_sufficiency REAL,
        roi_score REAL,
        overall_score REAL,
        risk_level TEXT DEFAULT '中',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES policy_categories(id)
    );

    CREATE TABLE IF NOT EXISTS investment_opportunities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        policy_id INTEGER NOT NULL,
        sector TEXT NOT NULL,
        opportunity_type TEXT,
        title TEXT NOT NULL,
        description TEXT,
        risk_level TEXT DEFAULT '中',
        potential_return TEXT,
        time_horizon TEXT,
        recommended_instruments TEXT,
        key_companies TEXT,
        key_etfs TEXT,
        status TEXT DEFAULT '活跃',
        confidence_score REAL DEFAULT 0.5,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (policy_id) REFERENCES policies(id)
    );

    CREATE TABLE IF NOT EXISTS policy_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        policy_id INTEGER NOT NULL,
        metric_name TEXT NOT NULL,
        metric_value REAL,
        metric_unit TEXT,
        metric_year INTEGER,
        source TEXT,
        collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (policy_id) REFERENCES policies(id)
    );

    CREATE TABLE IF NOT EXISTS policy_news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        policy_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        summary TEXT,
        source TEXT,
        url TEXT,
        published_at TEXT,
        sentiment TEXT DEFAULT '中性',
        impact_level TEXT DEFAULT '低',
        collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (policy_id) REFERENCES policies(id)
    );

    CREATE TABLE IF NOT EXISTS data_updates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        update_type TEXT NOT NULL,
        policy_id INTEGER,
        status TEXT DEFAULT 'pending',
        records_updated INTEGER DEFAULT 0,
        error_message TEXT,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        FOREIGN KEY (policy_id) REFERENCES policies(id)
    );

    CREATE TABLE IF NOT EXISTS market_indicators (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        policy_id INTEGER NOT NULL,
        indicator_name TEXT NOT NULL,
        indicator_value REAL,
        change_pct REAL,
        period TEXT,
        collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (policy_id) REFERENCES policies(id)
    );

    CREATE TABLE IF NOT EXISTS policy_signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        policy_id INTEGER,
        signal_type TEXT NOT NULL,
        signal_source TEXT NOT NULL,
        signal_title TEXT,
        signal_content TEXT NOT NULL,
        signal_date TEXT,
        is_processed INTEGER DEFAULT 0,
        batch_id TEXT,
        collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (policy_id) REFERENCES policies(id)
    );

    CREATE TABLE IF NOT EXISTS llm_analysis_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id TEXT NOT NULL,
        policy_id INTEGER NOT NULL,
        analysis_type TEXT NOT NULL,
        input_signals TEXT NOT NULL,
        llm_response TEXT,
        proposed_changes TEXT,
        confidence REAL DEFAULT 0,
        reasoning TEXT,
        status TEXT DEFAULT 'pending',
        reviewed_by TEXT,
        applied_at TIMESTAMP,
        model_id TEXT,
        prompt_tokens INTEGER,
        completion_tokens INTEGER,
        cost_usd REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (policy_id) REFERENCES policies(id)
    );

    CREATE TABLE IF NOT EXISTS update_config (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        description TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_policies_category ON policies(category_id);
    CREATE INDEX IF NOT EXISTS idx_opportunities_policy ON investment_opportunities(policy_id);
    CREATE INDEX IF NOT EXISTS idx_metrics_policy ON policy_metrics(policy_id);
    CREATE INDEX IF NOT EXISTS idx_news_policy ON policy_news(policy_id);
    CREATE INDEX IF NOT EXISTS idx_news_published ON policy_news(published_at);
    CREATE INDEX IF NOT EXISTS idx_market_policy ON market_indicators(policy_id);
    CREATE INDEX IF NOT EXISTS idx_signals_policy ON policy_signals(policy_id);
    CREATE INDEX IF NOT EXISTS idx_signals_processed ON policy_signals(is_processed);
    CREATE INDEX IF NOT EXISTS idx_llm_log_batch ON llm_analysis_log(batch_id);
    CREATE INDEX IF NOT EXISTS idx_llm_log_policy ON llm_analysis_log(policy_id);
    CREATE INDEX IF NOT EXISTS idx_llm_log_status ON llm_analysis_log(status);
    """)

    conn.commit()

    # Idempotent column migrations
    for col_name, col_def in [("details", "TEXT")]:
        try:
            conn.execute(f"ALTER TABLE data_updates ADD COLUMN {col_name} {col_def}")
            conn.commit()
        except Exception:
            pass

    conn.close()
    print(f"Database initialized at {DB_PATH}")


if __name__ == "__main__":
    init_db()
