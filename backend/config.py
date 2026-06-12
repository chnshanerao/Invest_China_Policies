import os
import sqlite3
from pathlib import Path

# Load .env if present (no dependency on python-dotenv)
_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


_DEFAULTS = {
    "llm_enabled": "true",
    "auto_apply_threshold": "0.85",
    "anthropic_model": "claude-sonnet-4-6",
    "max_policies_per_batch": "10",
    "scrape_rate_limit_seconds": "3",
    "update_interval_hours": "168",
    "max_daily_cost_usd": "5.0",
    "signal_collection_enabled": "true",
}


def _get_db_path():
    return Path(__file__).parent.parent / "data" / "policies.db"


def _read_db_config(key: str) -> str | None:
    try:
        conn = sqlite3.connect(str(_get_db_path()))
        row = conn.execute("SELECT value FROM update_config WHERE key = ?", (key,)).fetchone()
        conn.close()
        return row[0] if row else None
    except Exception:
        return None


def _set_db_config(key: str, value: str, description: str = "") -> None:
    conn = sqlite3.connect(str(_get_db_path()))
    conn.execute(
        "INSERT OR REPLACE INTO update_config (key, value, description, updated_at) VALUES (?, ?, ?, datetime('now'))",
        (key, value, description),
    )
    conn.commit()
    conn.close()


class Config:
    """Runtime configuration. Reads from DB → falls back to defaults."""

    def _get(self, key: str) -> str:
        return _read_db_config(key) or _DEFAULTS.get(key, "")

    @property
    def anthropic_api_key(self) -> str | None:
        return os.environ.get("ANTHROPIC_API_KEY") or None

    @property
    def llm_enabled(self) -> bool:
        if not self.anthropic_api_key:
            return False
        return self._get("llm_enabled").lower() == "true"

    @property
    def auto_apply_threshold(self) -> float:
        return float(self._get("auto_apply_threshold"))

    @property
    def model(self) -> str:
        return self._get("anthropic_model")

    @property
    def max_policies_per_batch(self) -> int:
        return int(self._get("max_policies_per_batch"))

    @property
    def scrape_rate_limit(self) -> float:
        return float(self._get("scrape_rate_limit_seconds"))

    @property
    def update_interval_hours(self) -> float:
        return float(self._get("update_interval_hours"))

    @property
    def max_daily_cost_usd(self) -> float:
        return float(self._get("max_daily_cost_usd"))

    @property
    def signal_collection_enabled(self) -> bool:
        return self._get("signal_collection_enabled").lower() == "true"

    def set(self, key: str, value: str, description: str = "") -> None:
        _set_db_config(key, value, description)

    def as_dict(self) -> dict:
        return {k: self._get(k) for k in _DEFAULTS}


config = Config()
