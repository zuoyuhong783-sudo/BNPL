"""Goal-driven diagnosis for the BNPL expert system.

This module does not define another approval policy. It sets a target limit,
asks the existing CLIPS-based evaluator for the current result, then tests
single-field changes at thresholds already present in the soft rules.

Run directly in PyCharm or from a terminal:
    python backward_diagnosis.py
    python backward_diagnosis.py my_applicant.json --target 10000
"""

from __future__ import annotations

import argparse
import json
from decimal import Decimal, ROUND_CEILING
from pathlib import Path
from typing import Any, Iterator

from bnpl_expert import Applicant, evaluate_dict


TARGET_CF = {1000: 0.40, 5000: 0.60, 10000: 0.85}
DEFAULT_INPUT = Path(__file__).parent / "example_diagnosis_applicant.json"


def candidate_changes(applicant: Applicant) -> Iterator[dict[str, Any]]:
    """Yield one-field scenarios using only thresholds in the existing rules."""
    months = applicant.account_age_months
    for threshold in (6, 12):
        if months < threshold:
            yield {
                "field": "account_age_months",
                "from": months,
                "to": threshold,
                "related_rule": "SR-05" if threshold == 6 else "SR-04",
                "description": f"注册时长达到{threshold}个月",
                "changes": {"account_age_months": threshold},
            }

    orders = applicant.completed_order_count
    if orders is not None:
        for threshold in (50, 100):
            if orders < threshold:
                yield {
                    "field": "completed_order_count",
                    "from": orders,
                    "to": threshold,
                    "related_rule": "SR-14" if threshold == 50 else "SR-13",
                    "description": f"完成订单数达到{threshold}笔",
                    "changes": {"completed_order_count": threshold},
                }

    if applicant.evaluation_type == "limit-review":
        streak = applicant.consecutive_on_time_repayments
        if streak is not None:
            for threshold in (3, 6):
                if streak < threshold:
                    yield {
                        "field": "consecutive_on_time_repayments",
                        "from": streak,
                        "to": threshold,
                        "related_rule": "SR-16" if threshold == 3 else "SR-15",
                        "description": f"连续按时还款达到{threshold}期",
                        "changes": {"consecutive_on_time_repayments": threshold},
                    }

        utilisation = applicant.credit_limit_utilisation_rate
        current_limit = applicant.current_credit_limit
        if utilisation is not None and current_limit is not None and current_limit > 0:
            if utilisation > 0.80:
                # The resulting available amount is rounded upward to cents so
                # the simulated utilisation cannot exceed 80% due to rounding.
                available = float(
                    (Decimal(str(current_limit)) * Decimal("0.20")).quantize(
                        Decimal("0.01"), rounding=ROUND_CEILING
                    )
                )
                yield {
                    "field": "available_credit_limit",
                    "from": applicant.available_credit_limit,
                    "to": available,
                    "related_rule": "SR-27",
                    "description": "通过偿还欠款使额度使用率降至80%或以下",
                    "changes": {"available_credit_limit": available},
                }


def diagnose(data: dict[str, Any], target_limit: int = 10000) -> dict[str, Any]:
    """Apply BD-01 through BD-05 to one applicant and target limit."""
    if target_limit not in TARGET_CF:
        raise ValueError("target_limit must be 1000, 5000, or 10000")

    applicant = Applicant.from_dict(data)
    current = evaluate_dict(data)
    base = {
        "target_limit": target_limit,
        "target_cf": TARGET_CF[target_limit],
        "current_decision": current["decision"],
        "current_limit_result": current["approved_limit"],
        "current_cf": current["combined_cf"],
        "evidence_coverage": current["evidence_coverage"],
        "cf_based_limit": current["cf_based_limit"],
        "tier_cap": current["tier_cap"],
    }

    # BD-01: hard rules take precedence; no CF or counterfactual simulation.
    if current["hard_decision"] is not None:
        return {
            **base,
            "status": "blocked-by-hard-rule",
            "blocking_rule": current["hard_decision"],
            "message": "硬规则阻断目标；本次不进行CF提额模拟。",
            "single_change_scenarios": [],
        }

    # BD-02: the existing decision has already achieved the requested limit.
    if current["approved_limit"] >= target_limit:
        return {
            **base,
            "status": "goal-achieved",
            "message": "当前评估结果已达到目标额度。",
            "single_change_scenarios": [],
        }

    # A higher CF cannot overcome the new-applicant evidence cap. Missing
    # fields must be supplied with genuine data and evaluated again.
    cap = current["tier_cap"]
    if cap is not None and cap["maximum_limit"] < target_limit:
        missing_fields = [
            name for name in (
                "average_monthly_spending",
                "completed_order_count",
                "external_credit_score",
                "external_overdue_record",
            )
            if getattr(applicant, name) is None
        ]
        return {
            **base,
            "status": "blocked-by-evidence-cap",
            "missing_evidence_fields": missing_fields,
            "message": (
                "目标额度超过当前信息覆盖率允许的最高档。请补充真实资料后重新评估；"
                "资料补齐不保证提额。"
            ),
            "single_change_scenarios": [],
        }

    # BD-03: calculate the gap from the current denominator and raw CF sum.
    maximum = current["applicable_positive_cf_max"]
    raw_sum = current["raw_cf_sum"]
    required_sum = TARGET_CF[target_limit] * maximum
    gap = max(0.0, required_sum - raw_sum)

    # BD-04: change one field at a time and rerun the exact same CLIPS rules.
    scenarios = []
    for candidate in candidate_changes(applicant):
        simulated_input = {**data, **candidate["changes"]}
        simulated = evaluate_dict(simulated_input)
        scenarios.append(
            {
                "field": candidate["field"],
                "from": candidate["from"],
                "to": candidate["to"],
                "related_rule": candidate["related_rule"],
                "description": candidate["description"],
                "simulated_cf": simulated["combined_cf"],
                "simulated_limit": simulated["approved_limit"],
                "reaches_goal": (
                    simulated["hard_decision"] is None
                    and simulated["approved_limit"] >= target_limit
                ),
            }
        )

    # BD-05: no single tested change is sufficient; do not promise approval.
    successful = [scenario for scenario in scenarios if scenario["reaches_goal"]]
    status = "single-change-options-found" if successful else "no-single-change-found"
    message = (
        "以下单项条件变化在其他资料不变时可达到目标；这不是立即提额承诺。"
        if successful
        else "在已测试的单项条件变化中，没有一项足以达到目标。"
    )
    return {
        **base,
        "status": status,
        "current_raw_cf_sum": raw_sum,
        "applicable_positive_cf_max": maximum,
        "required_raw_cf_sum": round(required_sum, 4),
        "raw_cf_gap": round(gap, 4),
        "message": message,
        "single_change_scenarios": scenarios,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose a target BNPL credit limit.")
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=DEFAULT_INPUT,
        help="Applicant JSON file (defaults to example_diagnosis_applicant.json)",
    )
    parser.add_argument(
        "--target", type=int, choices=sorted(TARGET_CF), default=10000,
        help="Target limit in CNY (default: 10000)",
    )
    args = parser.parse_args()
    with args.input.open("r", encoding="utf-8") as stream:
        data = json.load(stream)
    print(json.dumps(diagnose(data, args.target), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
