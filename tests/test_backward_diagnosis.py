import unittest
from copy import deepcopy

from backward_diagnosis import diagnose


def example_user():
    return {
        "identity_verified": True,
        "age": 28,
        "linked_card_type": "Credit",
        "account_age_months": 8,
        "repayment_fulfilment_rate": 0.99,
        "average_monthly_spending": 2600,
        "completed_order_count": 135,
        "consecutive_on_time_repayments": 8,
        "adverse_credit_incidents_6m": 0,
        "device_stability": "Stable",
        "current_credit_limit": 5000,
        "available_credit_limit": 250,
        "external_credit_score": 820,
        "external_overdue_record": "None",
    }


class BackwardDiagnosisTests(unittest.TestCase):
    def test_new_user_evidence_cap_blocks_higher_goal(self):
        data = example_user()
        data["current_credit_limit"] = None
        data["available_credit_limit"] = None
        data["average_monthly_spending"] = None
        data["completed_order_count"] = None
        data["external_credit_score"] = None
        data["external_overdue_record"] = None
        result = diagnose(data, 10000)
        self.assertEqual(result["status"], "blocked-by-evidence-cap")
        self.assertEqual(result["cf_based_limit"], 10000)
        self.assertEqual(result["tier_cap"]["maximum_limit"], 1000)
        self.assertIn("external_credit_score", result["missing_evidence_fields"])
        self.assertEqual(result["single_change_scenarios"], [])

    def test_goal_decomposition_and_two_verified_options(self):
        result = diagnose(example_user(), 10000)
        self.assertEqual(result["status"], "single-change-options-found")
        self.assertEqual(result["current_cf"], 0.8125)
        self.assertEqual(result["current_limit_result"], 5000)
        self.assertEqual(result["required_raw_cf_sum"], 3.4)
        self.assertEqual(result["raw_cf_gap"], 0.15)
        successful = {
            (item["field"], item["to"]): item
            for item in result["single_change_scenarios"]
            if item["reaches_goal"]
        }
        self.assertEqual(successful[("account_age_months", 12)]["simulated_cf"], 0.85)
        self.assertEqual(successful[("available_credit_limit", 1000.0)]["simulated_cf"], 0.9625)

    def test_hard_rule_stops_diagnosis(self):
        data = example_user()
        data["device_stability"] = "Abnormal"
        result = diagnose(data, 10000)
        self.assertEqual(result["status"], "blocked-by-hard-rule")
        self.assertEqual(result["blocking_rule"]["rule_id"], "HR-04")
        self.assertIsNone(result["current_cf"])
        self.assertEqual(result["single_change_scenarios"], [])

    def test_already_achieved_target(self):
        data = example_user()
        data["account_age_months"] = 12
        result = diagnose(data, 10000)
        self.assertEqual(result["status"], "goal-achieved")
        self.assertEqual(result["single_change_scenarios"], [])

    def test_no_single_change_is_reported_without_a_promise(self):
        data = example_user()
        data.update(
            linked_card_type="None",
            account_age_months=1,
            repayment_fulfilment_rate=0.80,
            average_monthly_spending=0,
            completed_order_count=0,
            consecutive_on_time_repayments=0,
            available_credit_limit=5000,
            external_credit_score=500,
            external_overdue_record="Serious",
        )
        result = diagnose(data, 10000)
        self.assertEqual(result["status"], "no-single-change-found")
        self.assertTrue(result["single_change_scenarios"])
        self.assertFalse(any(x["reaches_goal"] for x in result["single_change_scenarios"]))

    def test_input_is_not_mutated(self):
        data = example_user()
        original = deepcopy(data)
        diagnose(data, 10000)
        self.assertEqual(data, original)

    def test_target_must_be_an_existing_tier(self):
        with self.assertRaises(ValueError):
            diagnose(example_user(), 7500)


if __name__ == "__main__":
    unittest.main()
