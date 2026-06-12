"""
Orchestrates the full update cycle: signals → LLM analysis → change application.
Replaces the simple scheduled_weekly_update() in app.py.
"""
import asyncio
import json
import logging
import sys
import os
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_connection
from config import config
from signal_collector import SignalCollector
from change_applier import ChangeApplier

logger = logging.getLogger(__name__)


def _get_all_policies() -> list[dict]:
    conn = get_connection()
    rows = [dict(r) for r in conn.execute(
        """SELECT p.*, pc.name as category_name
           FROM policies p JOIN policy_categories pc ON p.category_id = pc.id
           ORDER BY p.id"""
    ).fetchall()]
    conn.close()
    return rows


def _get_unprocessed_signals(policy_id: int) -> list[dict]:
    conn = get_connection()
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM policy_signals WHERE policy_id = ? AND is_processed = 0 ORDER BY collected_at DESC LIMIT 20",
        (policy_id,),
    ).fetchall()]
    conn.close()
    return rows


def _mark_signals_processed(signal_ids: list[int], batch_id: str) -> None:
    if not signal_ids:
        return
    conn = get_connection()
    conn.execute(
        f"UPDATE policy_signals SET is_processed=1, batch_id=? WHERE id IN ({','.join('?' * len(signal_ids))})",
        [batch_id] + signal_ids,
    )
    conn.commit()
    conn.close()


def _log_update(update_type: str, status: str, records: int = 0, error: str = "", details: dict = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO data_updates (update_type, status, records_updated, error_message, details) VALUES (?, ?, ?, ?, ?)",
        (update_type, status, records, error, json.dumps(details or {})),
    )
    uid = cursor.lastrowid
    conn.commit()
    conn.close()
    return uid


def _finish_update(update_id: int, status: str, records: int, error: str = "", details: dict = None) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE data_updates SET status=?, records_updated=?, error_message=?, details=?, completed_at=datetime('now') WHERE id=?",
        (status, records, error, json.dumps(details or {}), update_id),
    )
    conn.commit()
    conn.close()


async def run_signal_collection(policies: list[dict] | None = None) -> dict:
    """Phase 1: collect signals for all (or given) policies."""
    if policies is None:
        policies = _get_all_policies()

    uid = _log_update("signal_collection", "running")
    logger.info(f"Signal collection starting for {len(policies)} policies...")

    collector = SignalCollector(rate_limit_seconds=config.scrape_rate_limit)
    total = await collector.collect_all_policies(policies, rate_limit=config.scrape_rate_limit)

    _finish_update(uid, "completed", total, details={"signals_collected": total})
    logger.info(f"Signal collection complete: {total} new signals")
    return {"signals_collected": total}


async def run_llm_analysis(batch_id: str | None = None, force_all: bool = False) -> dict:
    """Phase 2+3: LLM analysis of unprocessed signals → apply changes."""
    if not config.llm_enabled:
        logger.warning("LLM analysis skipped: llm_enabled=false or ANTHROPIC_API_KEY not set")
        return {"skipped": True, "reason": "LLM not configured"}

    try:
        from llm_analyzer import PolicyAnalyzer
    except ImportError as e:
        return {"error": f"Cannot import llm_analyzer: {e}"}

    batch_id = batch_id or uuid.uuid4().hex[:12]
    uid = _log_update("llm_analysis", "running", details={"batch_id": batch_id})
    logger.info(f"LLM analysis starting (batch {batch_id})...")

    policies = _get_all_policies()
    applier = ChangeApplier(auto_apply_threshold=config.auto_apply_threshold)
    analyzer = PolicyAnalyzer(api_key=config.anthropic_api_key, model=config.model)

    # Group policies with their unprocessed signals
    batch_size = config.max_policies_per_batch
    policies_with_signals: list[tuple[dict, list[dict]]] = []
    signals_by_policy: dict[int, list[dict]] = {}

    for p in policies:
        sigs = _get_unprocessed_signals(p["id"])
        if sigs or force_all:
            policies_with_signals.append((p, sigs))
            signals_by_policy[p["id"]] = sigs

    if not policies_with_signals:
        logger.info("No policies with new signals — skipping LLM analysis")
        _finish_update(uid, "completed", 0, details={"batch_id": batch_id, "skipped": "no new signals"})
        return {"analyzed": 0, "batch_id": batch_id}

    logger.info(f"Analyzing {len(policies_with_signals)} policies with new signals...")

    total_applied = 0
    total_review = 0
    total_cost = 0.0

    # Process in batches
    for i in range(0, len(policies_with_signals), batch_size):
        batch = policies_with_signals[i : i + batch_size]
        logger.info(f"  Batch {i//batch_size + 1}: {len(batch)} policies")

        results = analyzer.analyze_batch(batch)
        total_cost += sum(r.get("cost_usd", 0) for r in results)

        # Check daily cost cap
        if _daily_cost() + total_cost > config.max_daily_cost_usd:
            logger.warning(f"Daily cost cap reached (${config.max_daily_cost_usd}). Stopping.")
            break

        summary = applier.process_results(
            batch_id=batch_id,
            analysis_results=results,
            signals_by_policy=signals_by_policy,
            model_id=config.model,
        )
        total_applied += summary["auto_applied"]
        total_review += summary["pending_review"]

        # Mark signals as processed
        all_signal_ids = [s["id"] for _, sigs in batch for s in sigs]
        _mark_signals_processed(all_signal_ids, batch_id)

        await asyncio.sleep(2)  # brief pause between batches

    details = {
        "batch_id": batch_id,
        "policies_analyzed": len(policies_with_signals),
        "auto_applied": total_applied,
        "pending_review": total_review,
        "cost_usd": round(total_cost, 4),
    }
    _finish_update(uid, "completed", total_applied, details=details)
    logger.info(f"LLM analysis complete: {total_applied} auto-applied, {total_review} pending review, ${total_cost:.4f} cost")
    return details


def _daily_cost() -> float:
    """Sum cost_usd from llm_analysis_log in the past 24 hours."""
    try:
        conn = get_connection()
        row = conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM llm_analysis_log WHERE created_at > datetime('now', '-1 day')"
        ).fetchone()
        conn.close()
        return float(row[0])
    except Exception:
        return 0.0


async def run_full_update_cycle(force_all: bool = False) -> dict:
    """Complete cycle: signal collection + LLM analysis."""
    logger.info("=== Full update cycle starting ===")
    batch_id = uuid.uuid4().hex[:12]

    # Phase 1: collect signals (always runs)
    signal_result = await run_signal_collection()

    # Phase 2+3: LLM analysis (only if configured)
    llm_result = await run_llm_analysis(batch_id=batch_id, force_all=force_all)

    return {
        "batch_id": batch_id,
        "signals": signal_result,
        "llm": llm_result,
    }


class UpdateScheduler:
    def __init__(self):
        self._task: asyncio.Task | None = None

    def start(self):
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._loop())
        logger.info("UpdateScheduler started")

    def stop(self):
        if self._task:
            self._task.cancel()

    async def _loop(self):
        while True:
            interval_secs = config.update_interval_hours * 3600
            logger.info(f"Next update in {config.update_interval_hours}h")
            await asyncio.sleep(interval_secs)
            try:
                await run_full_update_cycle()
            except Exception as e:
                logger.error(f"Scheduled update failed: {e}")
