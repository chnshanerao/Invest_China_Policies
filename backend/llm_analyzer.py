"""
LLM-powered policy analysis using Claude API.
Analyzes collected signals to propose lifecycle/score updates.
"""
import json
import logging
import re
import sys
import os
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)

VALID_STAGES = ["规划期", "启动期", "扩张期", "验证期", "成熟期", "调整期", "衰退期"]
VALID_MOMENTUM = ["加速", "平稳", "减速"]

SCORING_RUBRIC = """
## 执行力度评分标准 (1-10分)
维度权重：资金投入规模30% | 政策文件密度20% | 领导层关注度25% | 配套措施完备度25%
分级：1-3低力度(偶有提及,无专项资金) | 4-6中力度(有规划,有资金,常规推进) | 7-8高力度(专项立法,大规模投入,高层频繁关注) | 9-10极高(写入党代会报告,举国推进)

## 执行效果评分标准 (1-10分)
维度权重：经济指标达成30% | 就业与人口效应15% | 产业集聚效应25% | 制度创新贡献15% | 社会/生态效益15%
分级：1-3效果差(投入远大于产出) | 4-6效果一般(部分目标达成) | 7-8效果好(多数目标达成,产生示范效应) | 9-10卓越(全面超额完成,产生全球影响力)

## 政策动量 (加速/平稳/减速)
加速：近期新增专项政策、投资加码、成效加速显现
平稳：按既定节奏推进，无明显变化信号
减速：力度或关注度下降，投资放缓，或推进受阻

## 生命周期阶段
规划期：政策酝酿讨论，尚未正式发文 | 启动期：文件已发布，机构组建，试点启动
扩张期：大规模资金投入，快速推进 | 验证期：初期建设完成，检验实际成效
成熟期：制度稳定，常态化运行 | 调整期：外部环境变化导致转型 | 衰退期：边际效益递减，逐步淡化

## 数据完整性铁律
- 如果信号中没有可验证的具体数据，请不要提议更改，confidence设为0
- 每个提议的更改必须引用具体信号（用signal_id引用）
- 推测、猜测、补全数据一律禁止
"""

ANALYSIS_SCHEMA = """{
  "policy_id": <int>,
  "lifecycle_stage_change": {"old": "<str>", "new": "<str>", "reasoning": "<str>", "signal_ids": [<int>]} | null,
  "intensity_update": {"old": <float>, "new": <float>, "basis": "<str>", "signal_ids": [<int>]} | null,
  "effectiveness_update": {"old": <float>, "new": <float>, "basis": "<str>", "signal_ids": [<int>]} | null,
  "momentum_change": {"old": "<str>", "new": "<str>", "reasoning": "<str>", "signal_ids": [<int>]} | null,
  "confidence": <float 0-1>,
  "overall_reasoning": "<str>",
  "data_sources_cited": ["<str>"]
}"""


class PolicyAnalyzer:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise RuntimeError("anthropic package not installed. Run: pip install anthropic")
        self._model = model

    def _build_system_prompt(self) -> str:
        return (
            "你是一位中国国家政策分析专家，专门评估政策生命周期和执行效果。\n"
            "你的任务是基于提供的真实信号数据，对政策状态提出有据可查的更新建议。\n\n"
            + SCORING_RUBRIC
        )

    def _build_user_prompt(self, policy: dict, signals: list[dict]) -> str:
        signals_text = "\n".join(
            f"[信号{s['id']}] 类型:{s['signal_type']} | 来源:{s['signal_source'][:60]}\n"
            f"  标题: {s.get('signal_title','')}\n"
            f"  内容: {s.get('signal_content','')[:300]}\n"
            f"  日期: {s.get('signal_date','')}"
            for s in signals
        )
        if not signals_text:
            signals_text = "（本周期无新信号）"

        current_state = (
            f"政策名称: {policy['name']}\n"
            f"类别: {policy.get('category_name', '')}\n"
            f"设立年份: {policy.get('established_year', '')}\n"
            f"当前生命周期阶段: {policy.get('lifecycle_stage', '')}\n"
            f"当前执行力度: {policy.get('execution_intensity', '')}/10\n"
            f"当前执行效果: {policy.get('execution_effectiveness', '')}/10\n"
            f"当前政策动量: {policy.get('policy_momentum', '')}\n"
            f"现有力度评分依据: {policy.get('intensity_basis', '') or '无'}\n"
            f"现有效果评分依据: {policy.get('effectiveness_basis', '') or '无'}\n"
            f"现有生命周期依据: {policy.get('lifecycle_source', '') or '无'}\n"
            f"数据验证级别: {policy.get('data_verified', 0)} (0=未验证 1=部分验证 2=已验证)"
        )

        return (
            f"## 政策当前状态\n{current_state}\n\n"
            f"## 本周期收集到的新信号 ({len(signals)}条)\n{signals_text}\n\n"
            f"## 任务\n"
            f"基于上述信号，判断是否需要更新该政策的状态。\n"
            f"如果信号内容不足以支持某项更改，该字段设为null，confidence相应降低。\n"
            f"严禁基于已知知识猜测——只能使用上方提供的信号作为依据。\n\n"
            f"请严格按以下JSON格式输出（不要包含Markdown代码块）：\n{ANALYSIS_SCHEMA}"
        )

    def _parse_response(self, text: str) -> dict | None:
        # Strip markdown code fences if present
        text = re.sub(r"```(?:json)?\s*", "", text).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try extracting first JSON object
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group())
                except json.JSONDecodeError:
                    pass
        return None

    def _estimate_cost(self, usage) -> float:
        # Sonnet pricing: $3/M input, $15/M output
        input_cost = (getattr(usage, "input_tokens", 0) / 1_000_000) * 3.0
        output_cost = (getattr(usage, "output_tokens", 0) / 1_000_000) * 15.0
        return round(input_cost + output_cost, 6)

    def analyze_policy(self, policy: dict, signals: list[dict]) -> dict:
        """Analyze one policy. Returns structured result dict."""
        user_prompt = self._build_user_prompt(policy, signals)
        result = {
            "policy_id": policy["id"],
            "raw_response": None,
            "parsed": None,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "cost_usd": 0.0,
            "error": None,
        }

        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=self._build_system_prompt(),
                messages=[{"role": "user", "content": user_prompt}],
            )
            raw = response.content[0].text
            result["raw_response"] = raw
            result["prompt_tokens"] = response.usage.input_tokens
            result["completion_tokens"] = response.usage.output_tokens
            result["cost_usd"] = self._estimate_cost(response.usage)

            parsed = self._parse_response(raw)
            if parsed is None:
                # Re-prompt once
                retry = self._client.messages.create(
                    model=self._model,
                    max_tokens=1024,
                    system=self._build_system_prompt(),
                    messages=[
                        {"role": "user", "content": user_prompt},
                        {"role": "assistant", "content": raw},
                        {"role": "user", "content": "你的回复不是合法的JSON。请只输出JSON对象，不要包含任何其他文字。"},
                    ],
                )
                raw2 = retry.content[0].text
                result["raw_response"] = raw2
                result["prompt_tokens"] += retry.usage.input_tokens
                result["completion_tokens"] += retry.usage.output_tokens
                result["cost_usd"] += self._estimate_cost(retry.usage)
                parsed = self._parse_response(raw2)

            if parsed:
                parsed["policy_id"] = policy["id"]
                result["parsed"] = parsed
            else:
                result["error"] = "Failed to parse LLM response after retry"

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"LLM analysis error for policy {policy['id']} ({policy['name']}): {e}")

        return result

    def analyze_batch(self, policies_with_signals: list[tuple[dict, list[dict]]]) -> list[dict]:
        """Analyze multiple policies. Returns list of result dicts."""
        results = []
        for policy, signals in policies_with_signals:
            logger.info(f"  Analyzing: {policy['name']} ({len(signals)} signals)")
            result = self.analyze_policy(policy, signals)
            results.append(result)
        return results

    def detect_new_policies(self, unmatched_signals: list[dict]) -> list[dict]:
        """Detect if unmatched signals reference a genuinely new national-level policy."""
        if not unmatched_signals:
            return []

        signals_text = "\n".join(
            f"[{s['id']}] {s.get('signal_title', '')}: {s.get('signal_content', '')[:200]}"
            for s in unmatched_signals[:20]
        )
        prompt = (
            "以下是未匹配到现有政策的信号，请判断其中是否出现了新的国家级战略政策（非地方政策，非子政策）：\n\n"
            + signals_text
            + "\n\n如有新政策，请输出JSON数组，每项包含：{name, description, category_hint, confidence}。"
            "如无新政策，输出空数组[]。只有confidence>=0.95才应列出。"
        )
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            text = re.sub(r"```(?:json)?\s*", "", response.content[0].text).strip()
            return json.loads(text) if text.startswith("[") else []
        except Exception as e:
            logger.warning(f"New policy detection error: {e}")
            return []
