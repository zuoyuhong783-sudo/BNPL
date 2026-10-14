import unittest

import clips

from bnpl_expert import Applicant, RULES_PATH, evaluate_dict, normalized_cf


def base_applicant(**overrides):
    data = {
        "identity_verified": True,
        "age": 28,
        "linked_card_type": "Credit",
        "account_age_months": 18,
        "repayment_fulfilment_rate": 0.99,
        "average_monthly_spending": 2600,
        "completed_order_count": 135,
        "consecutive_on_time_repayments": 8,
        "adverse_credit_incidents_6m": 0,
        "device_stability": "Stable",
        "current_credit_limit": None,
        "available_credit_limit": None,
        "external_credit_score": 820,
        "external_overdue_record": "None",
    }
    data.update(overrides)
    return data


class BNPLExpertTests(unittest.TestCase):
    def test_evidence_cap_boundary_rules_are_mutually_exclusive(self):
        for ratio, expected in ((0.6999, 1000), (0.70, 5000), (0.8999, 5000), (0.90, 10000)):
            with self.subTest(ratio=ratio):
                environment = clips.Environment()
                environment.load(str(RULES_PATH))
                environment.reset()
                environment.find_template("context").assert_fact(
                    **{"evaluation-type": clips.Symbol("new-application")}
                )
                environment.find_template("evidence-coverage").assert_fact(ratio=ratio)
                environment.run()
                caps = [
                    fact for fact in environment.facts()
                    if fact.template.name == "tier-cap"
                ]
                self.assertEqual(len(caps), 1)
                self.assertEqual(caps[0]["maximum-limit"], expected)

    def test_normalized_cf_uses_sum_over_applicable_positive_max(self):
        raw_sum, cf = normalized_cf(
            [{"cf": 0.45}, {"cf": 0.35}, {"cf": -0.25}], 2.50
        )
        self.assertAlmostEqual(raw_sum, 0.55)
        self.assertAlmostEqual(cf, 0.22)

    def test_negative_total_is_clamped_to_zero(self):
        raw_sum, cf = normalized_cf([{"cf": -0.70}], 2.50)
        self.assertAlmostEqual(raw_sum, -0.70)
        self.assertEqual(cf, 0)

    def test_new_high_quality_user_gets_top_limit(self):
        result = evaluate_dict(base_applicant())
        self.assertEqual(result["decision"], "approved")
        self.assertEqual(result["approved_limit"], 10000)
        self.assertEqual(result["limit_action"], "open")
        self.assertIsNone(result["hard_decision"])
        self.assertEqual(result["applicable_positive_cf_max"], 2.50)
        self.assertEqual(result["raw_cf_sum"], 2.50)
        self.assertEqual(result["evidence_coverage"], 1.0)
        self.assertEqual(result["tier_cap"]["rule_id"], "EC-03")
        self.assertFalse(result["cap_applied"])
        ids = {item["rule_id"] for item in result["triggered_soft_rules"]}
        self.assertNotIn("SR-07", ids)
        self.assertNotIn("SR-15", ids)

    def test_existing_user_uses_four_point_maximum(self):
        result = evaluate_dict(
            base_applicant(current_credit_limit=5000, available_credit_limit=2000)
        )
        self.assertEqual(result["applicable_positive_cf_max"], 4.00)
        self.assertEqual(result["raw_cf_sum"], 4.00)
        self.assertEqual(result["combined_cf"], 1.00)
        self.assertIsNone(result["tier_cap"])

    def test_sparse_new_user_is_capped_despite_perfect_cf(self):
        result = evaluate_dict(
            base_applicant(
                average_monthly_spending=None,
                completed_order_count=None,
                external_credit_score=None,
                external_overdue_record=None,
            )
        )
        self.assertEqual(result["combined_cf"], 1.0)
        self.assertEqual(result["evidence_coverage"], 0.42)
        self.assertEqual(result["cf_based_limit"], 10000)
        self.assertEqual(result["tier_cap"]["rule_id"], "EC-01")
        self.assertEqual(result["approved_limit"], 1000)
        self.assertTrue(result["cap_applied"])

    def test_medium_coverage_caps_new_user_at_5000(self):
        result = evaluate_dict(base_applicant(external_credit_score=None))
        self.assertEqual(result["combined_cf"], 1.0)
        self.assertEqual(result["evidence_coverage"], 0.78)
        self.assertEqual(result["tier_cap"]["rule_id"], "EC-02")
        self.assertEqual(result["approved_limit"], 5000)

    def test_cap_never_raises_a_low_cf_result(self):
        result = evaluate_dict(
            base_applicant(
                linked_card_type="None",
                account_age_months=0,
                device_stability="Changing",
                average_monthly_spending=None,
                completed_order_count=None,
                external_credit_score=None,
                external_overdue_record=None,
            )
        )
        self.assertEqual(result["cf_based_limit"], 0)
        self.assertEqual(result["approved_limit"], 0)
        self.assertFalse(result["cap_applied"])

    def test_unverified_new_user_is_rejected(self):
        result = evaluate_dict(base_applicant(identity_verified=False))
        self.assertEqual(result["decision"], "reject")
        self.assertEqual(result["approved_limit"], 0)
        self.assertEqual(result["hard_decision"]["rule_id"], "HR-01")

    def test_abnormal_existing_user_is_suspended(self):
        result = evaluate_dict(
            base_applicant(
                device_stability="Abnormal",
                current_credit_limit=5000,
                available_credit_limit=2000,
            )
        )
        self.assertEqual(result["decision"], "suspend")
        self.assertEqual(result["approved_limit"], 0)
        self.assertEqual(result["limit_action"], "set-to-zero")
        self.assertEqual(result["hard_decision"]["rule_id"], "HR-04")
        self.assertIsNone(result["combined_cf"])
        self.assertEqual(result["triggered_soft_rules"], [])

    def test_low_external_score_suspends_existing_user(self):
        result = evaluate_dict(
            base_applicant(
                external_credit_score=450,
                current_credit_limit=5000,
                available_credit_limit=3000,
            )
        )
        self.assertEqual(result["decision"], "suspend")
        self.assertEqual(result["approved_limit"], 0)
        self.assertEqual(result["hard_decision"]["rule_id"], "HR-05")

    def test_account_age_one_to_five_months_is_neutral(self):
        for months in range(1, 6):
            with self.subTest(months=months):
                result = evaluate_dict(base_applicant(account_age_months=months))
                ids = {item["rule_id"] for item in result["triggered_soft_rules"]}
                self.assertNotIn("SR-04", ids)
                self.assertNotIn("SR-05", ids)
                self.assertNotIn("SR-06", ids)

    def test_account_age_six_months_triggers_sr05(self):
        result = evaluate_dict(base_applicant(account_age_months=6))
        ids = {item["rule_id"] for item in result["triggered_soft_rules"]}
        self.assertIn("SR-05", ids)

    def test_missing_optional_values_are_neutral(self):
        result = evaluate_dict(
            base_applicant(
                repayment_fulfilment_rate=None,
                average_monthly_spending=None,
                completed_order_count=None,
                consecutive_on_time_repayments=None,
                adverse_credit_incidents_6m=None,
                external_credit_score=None,
                external_overdue_record=None,
            )
        )
        ids = {item["rule_id"] for item in result["triggered_soft_rules"]}
        self.assertFalse(ids & {"SR-07", "SR-11", "SR-13", "SR-15", "SR-20", "SR-26"})
        self.assertEqual(result["applicable_positive_cf_max"], 1.05)

    def test_invalid_available_limit_is_rejected(self):
        with self.assertRaises(ValueError):
            Applicant.from_dict(
                base_applicant(current_credit_limit=1000, available_credit_limit=1200)
            )


if __name__ == "__main__":
    unittest.main()
