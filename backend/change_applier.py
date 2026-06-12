"""
Validated change application with full audit trail.
Applies LLM-proposed changes to the policies table with confidence gating.
"""
import json
import logging
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_connection

logger = logging.getLogger(__name__)

VALID_STAGES = ["规划期", "启动期", "扩张期", "验证期", "成熟期", "调整期", "衰退期"]
VALID_MOMENTUM = ["加速", "平稳", "减速"]


class ChangeApplier:
    def __init__(self, auto_apply_threshold: float = 0.85):
        self._threshold = auto_apply_threshold

    def _validate(self, changes: dict) -> tuple[bool, str]:
        """Validate proposed changes. Returns (ok, error_msg)."""
        if lc := changes.get("lifecycle_stage_change"):
            new_stage = lc.get("new", "")
            if new_stage and new_stage not in VALID_STAGES:
                return False, f"Invalid lifecycle stage: {new_stage}"

        if iu := changes.get("intensity_update"):
            val = iu.get("new")
            if val is not None and not (1 <= float(val) <= 10):
                return False, f"Intensity out of range: {val}"

        if eu := changes.get("effectiveness_update"):
            val = eu.get("new")
            if val is not None and not (1 <= float(val) <= 10):
                return False, f"Effectiveness out of range: {val}"

        if mc := changes.get("momentum_change"):
            new_m = mc.get("new", "")
            if new_m and new_m not in VALID_MOMENTUM:
                return False, f"Invalid momentum: {new_m}"

        return True, ""

    def _has_actual_changes(self, changes: dict) -> bool:
        """Check if proposed changes differ from current values."""
        if changes.get("lifecycle_stage_change"):
            lc = changes["lifecycle_stage_change"]
            if lc.get("old") != lc.get("new"):
                return True
        if changes.get("intensity_update"):
            iu = changes["intensity_update"]
            if iu.get("old") != iu.get("new"):
                return True
        if changes.get("effectiveness_update"):
            eu = changes["effectiveness_update"]
            if eu.get("old") != eu.get("new"):
                return True
        if changes.get("momentum_change"):
            mc = changes["momentum_change"]
            if mc.get("old") != mc.get("new"):
                return True
        return False

    def _apply_to_db(self, policy_id: int, changes: dict) -> None:
        """Apply validated changes to the policies table."""
        fields = []
        params = []

        if lc := changes.get("lifecycle_stage_change"):
            if lc.get("new") and lc["new"] != lc.get("old"):
                fields.append("lifecycle_stage = ?")
                params.append(lc["new"])
                if lc.get("reasoning"):
                    fields.append("lifecycle_source = ?")
                    params.append(lc["reasoning"][:500])

        if iu := changes.get("intensity_update"):
            if iu.get("new") is not None and iu["new"] != iu.get("old"):
                fields.append("execution_intensity = ?")
                params.append(float(iu["new"]))
                if iu.get("basis"):
                    fields.append("intensity_basis = ?")
                    params.append(iu["basis"][:500])

        if eu := changes.get("effectiveness_update"):
            if eu.get("new") is not None and eu["new"] != eu.get("old"):
                fields.append("execution_effectiveness = ?")
                params.append(float(eu["new"]))
                if eu.get("basis"):
                    fields.append("effectiveness_basis = ?")
                    params.append(eu["basis"][:500])

        if mc := changes.get("momentum_change"):
            if mc.get("new") and mc["new"] != mc.get("old"):
                fields.append("policy_momentum = ?")
                params.append(mc["new"])

        if not fields:
            return

        fields.append("updated_at = datetime('now')")
        params.append(policy_id)

        conn = get_connection()
        try:
            conn.execute(
                f"UPDATE policies SET {', '.join(fields)} WHERE id = ?",
                params,
            )
            conn.commit()
        finally:
            conn.close()

    def _log_analysis(
        self,
        batch_id: str,
        policy_id: int,
        input_signals: list,
        llm_result: dict,
        parsed: dict | None,
        status: str,
        model_id: str,
    ) -> int:
        """Insert into llm_analysis_log, return log id."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO llm_analysis_log
               (batch_id, policy_id, analysis_type, input_signals, llm_response,
                proposed_changes, confidence, reasoning, status, model_id,
                prompt_tokens, completion_tokens, cost_usd)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                batch_id,
                policy_id,
                "lifecycle_update",
                json.dumps([s["id"] for s in input_signals], ensure_ascii=False),
                llm_result.get("raw_response") or llm_result.get("error", ""),
                json.dumps(parsed or {}, ensure_ascii=False),
                parsed.get("confidence", 0) if parsed else 0,
                parsed.get("overall_reasoning", llm_result.get("error", "")) if parsed else llm_result.get("error", ""),
                status,
                model_id,
                llm_result.get("prompt_tokens", 0),
                llm_result.get("completion_tokens", 0),
                llm_result.get("cost_usd", 0.0),
            ),
        )
        log_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return log_id

    def process_results(
        self,
        batch_id: str,
        analysis_results: list[dict],
        signals_by_policy: dict[int, list[dict]],
        model_id: str,
    ) -> dict:
        """
        Process LLM analysis results, apply changes or flag for review.
        Returns summary dict.
        """
        auto_applied = 0
        pending_review = 0
        rejected = 0
        errors = 0

        for result in analysis_results:
            policy_id = result["policy_id"]
            signals = signals_by_policy.get(policy_id, [])
            parsed = result.get("parsed")

            if result.get("error") and not parsed:
                self._log_analysis(batch_id, policy_id, signals, result, None, "error", model_id)
                errors += 1
                continue

            if not parsed:
                errors += 1
                continue

            confidence = float(parsed.get("confidence", 0))
            ok, err = self._validate(parsed)
            if not ok:
                logger.warning(f"  Validation failed for policy {policy_id}: {err}")
                self._log_analysis(batch_id, policy_id, signals, result, parsed, "rejected", model_id)
                rejected += 1
                continue

            if not self._has_actual_changes(parsed):
                # Nothing to change — log quietly as auto_applied with no DB write
                self._log_analysis(batch_id, policy_id, signals, result, parsed, "auto_applied", model_id)
                continue

            if confidence >= self._threshold:
                try:
                    self._apply_to_db(policy_id, parsed)
                    log_id = self._log_analysis(batch_id, policy_id, signals, result, parsed, "auto_applied", model_id)
                    # Mark applied_at
                    conn = get_connection()
                    conn.execute("UPDATE llm_analysis_log SET applied_at = datetime('now') WHERE id = ?", (log_id,))
                    conn.commit()
                    conn.close()
                    auto_applied += 1
                    logger.info(f"  Auto-applied changes for policy {policy_id} (confidence={confidence:.2f})")
                except Exception as e:
                    logger.error(f"  Failed to apply changes for policy {policy_id}: {e}")
                    errors += 1
            elif confidence >= 0.5:
                self._log_analysis(batch_id, policy_id, signals, result, parsed, "manual_review", model_id)
                pending_review += 1
                logger.info(f"  Flagged for review: policy {policy_id} (confidence={confidence:.2f})")
            else:
                self._log_analysis(batch_id, policy_id, signals, result, parsed, "rejected", model_id)
                rejected += 1

        return {
            "auto_applied": auto_applied,
            "pending_review": pending_review,
            "rejected": rejected,
            "errors": errors,
        }

    def approve_change(self, log_id: int) -> bool:
        """Human approves a pending change. Applies to DB."""
        conn = get_connection()
        row = conn.execute(
            "SELECT policy_id, proposed_changes FROM llm_analysis_log WHERE id = ? AND status = 'manual_review'",
            (log_id,),
        ).fetchone()
        if not row:
            conn.close()
            return False
        policy_id = row["policy_id"]
        changes = json.loads(row["proposed_changes"])
        try:
            self._apply_to_db(policy_id, changes)
            conn.execute(
                "UPDATE llm_analysis_log SET status='approved', reviewed_by='human', applied_at=datetime('now') WHERE id=?",
                (log_id,),
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"approve_change failed for log_id {log_id}: {e}")
            return False
        finally:
            conn.close()

    def reject_change(self, log_id: int, reason: str = "") -> bool:
        """Human rejects a pending change."""
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE llm_analysis_log SET status='rejected', reviewed_by='human', reasoning=reasoning||? WHERE id=?",
                (f"\n[拒绝原因] {reason}" if reason else "", log_id),
            )
            conn.commit()
            return True
        finally:
            conn.close()
