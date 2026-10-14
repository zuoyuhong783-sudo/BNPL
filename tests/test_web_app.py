import http.client
import json
import threading
import unittest

from web_app import make_server


def applicant(**changes):
    data = {
        "identity_verified": True,
        "age": 28,
        "linked_card_type": "Credit",
        "account_age_months": 12,
        "repayment_fulfilment_rate": None,
        "average_monthly_spending": None,
        "completed_order_count": None,
        "consecutive_on_time_repayments": None,
        "adverse_credit_incidents_6m": 0,
        "device_stability": "Stable",
        "current_credit_limit": None,
        "available_credit_limit": None,
        "external_credit_score": None,
        "external_overdue_record": None,
    }
    data.update(changes)
    return data


class WebAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = make_server(port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_port

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def request(self, method, path, payload=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Content-Type": "application/json"} if body else {}
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        content = response.read()
        status = response.status
        connection.close()
        return status, content

    def test_frontend_is_served(self):
        status, content = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("先用后付", content.decode("utf-8"))
        self.assertIn("请仅使用虚构测试数据", content.decode("utf-8"))

    def test_health_check(self):
        status, content = self.request("GET", "/healthz")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(content), {"status": "ok"})

    def test_security_headers(self):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        connection.request("GET", "/")
        response = connection.getresponse()
        self.assertEqual(response.getheader("X-Frame-Options"), "DENY")
        self.assertEqual(response.getheader("X-Content-Type-Options"), "nosniff")
        self.assertIn("frame-ancestors 'none'", response.getheader("Content-Security-Policy"))
        response.read()
        connection.close()

    def test_non_json_request_is_rejected(self):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        connection.request(
            "POST", "/api/evaluate", body="{}", headers={"Content-Type": "text/plain"}
        )
        response = connection.getresponse()
        self.assertEqual(response.status, 415)
        response.read()
        connection.close()

    def test_sparse_new_user_is_capped(self):
        status, content = self.request("POST", "/api/evaluate", {"applicant": applicant()})
        self.assertEqual(status, 200)
        result = json.loads(content)["result"]
        self.assertEqual(result["combined_cf"], 1.0)
        self.assertEqual(result["approved_limit"], 1000)
        self.assertEqual(result["tier_cap"]["rule_id"], "EC-01")

    def test_hard_rule_rejects(self):
        status, content = self.request(
            "POST", "/api/evaluate", {"applicant": applicant(external_credit_score=430)}
        )
        self.assertEqual(status, 200)
        result = json.loads(content)["result"]
        self.assertEqual(result["approved_limit"], 0)
        self.assertEqual(result["hard_decision"]["rule_id"], "HR-05")

    def test_diagnosis_reports_evidence_cap(self):
        status, content = self.request(
            "POST", "/api/diagnose", {"applicant": applicant(), "target_limit": 10000}
        )
        self.assertEqual(status, 200)
        result = json.loads(content)["result"]
        self.assertEqual(result["status"], "blocked-by-evidence-cap")

    def test_invalid_input_returns_validation_error(self):
        status, content = self.request("POST", "/api/evaluate", {"applicant": applicant(age=-1)})
        self.assertEqual(status, 400)
        self.assertIn("age", json.loads(content)["error"])

    def test_unknown_asset_is_not_served(self):
        status, _ = self.request("GET", "/../bnpl_expert.py")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
