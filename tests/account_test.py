"""Account-read contracts; no live calls."""

import math
import unittest
from unittest.mock import patch

import requests

from pangram import AccountBalance, AccountLimits, AccountUsage, Pangram, PangramRequestError
from pangram.text_classifier import API_ENDPOINT
from tests.pangram_test import MockResponse


class Response(MockResponse):
    def __init__(self, data=None, status=200, headers=None, text=""):
        super().__init__(status_code=status, json_data=data, text=text)
        self.headers = headers or {}


class TestAccountReads(unittest.TestCase):
    def setUp(self):
        self.client = Pangram(api_key="test-key")

    @patch("pangram.text_classifier.requests.get")
    def test_balance_preserves_decimal_strings_and_negative_amounts(self, get):
        payload = {
            "purchased_balance_usd": "-10.00001",
            "subscription_included_balance_usd": "2.50000",
            "available_balance_usd": "-7.50001",
        }
        get.return_value = Response(payload)
        self.assertEqual(self.client.get_balance(timeout=3), payload)
        get.assert_called_once_with(
            f"{API_ENDPOINT}/balance", headers={"x-api-key": "test-key"},
            params=None, timeout=3, allow_redirects=False,
        )

    @patch("pangram.text_classifier.requests.get")
    def test_usage_omits_default_month_and_preserves_selected_month(self, get):
        payload = {"month": "2026-10", "total_requests": 12, "total_cost_usd": "0.123456"}
        get.return_value = Response(payload)
        self.assertEqual(self.client.get_usage(), payload)
        self.assertIsNone(get.call_args.kwargs["params"])
        self.assertEqual(self.client.get_usage(month="2026-10"), payload)
        self.assertEqual(get.call_args.kwargs["params"], {"month": "2026-10"})
        self.assertEqual(get.call_args.args, (f"{API_ENDPOINT}/usage",))

    @patch("pangram.text_classifier.requests.get")
    def test_invalid_month_never_reaches_api(self, get):
        for month in ["", "2026-1", "2026-13", "0000-01", "2026-10-01", " 2026-10", 202610]:
            with self.subTest(month=month), self.assertRaises(ValueError):
                self.client.get_usage(month)
        get.assert_not_called()

    @patch("pangram.text_classifier.requests.get")
    def test_fractional_and_unconfigured_limits(self, get):
        for value in [2.5, 1, None]:
            with self.subTest(value=value):
                get.return_value = Response({"qps_limit": value})
                self.assertEqual(self.client.get_limits(), {"qps_limit": value})
                self.assertEqual(get.call_args.args, (f"{API_ENDPOINT}/limits",))

    @patch("pangram.text_classifier.requests.get")
    def test_rate_limit_exposes_status_and_retry_after_without_retry(self, get):
        get.return_value = Response(status=429, text='{"detail":"Account read limit exceeded"}', headers={"Retry-After": "7"})
        with self.assertRaises(PangramRequestError) as raised:
            self.client.get_balance()
        self.assertEqual(raised.exception.status_code, 429)
        self.assertEqual(raised.exception.retry_after, 7)
        get.assert_called_once()

    @patch("pangram.text_classifier.requests.get")
    def test_http_failures_propagate_status_without_retry(self, get):
        for status in [301, 401, 422, 503]:
            with self.subTest(status=status):
                get.reset_mock()
                get.return_value = Response(status=status, text="request rejected")
                with self.assertRaises(PangramRequestError) as raised:
                    self.client.get_usage("2026-10")
                self.assertEqual(raised.exception.status_code, status)
                get.assert_called_once()

    @patch("pangram.text_classifier.requests.get")
    def test_malformed_account_responses_are_rejected(self, get):
        cases = [
            (self.client.get_balance, {}),
            (self.client.get_balance, {"purchased_balance_usd": 10}),
            (self.client.get_balance, {"purchased_balance_usd": "NaN", "subscription_included_balance_usd": "0", "available_balance_usd": "0"}),
            (self.client.get_usage, {"month": "bad", "total_requests": 0, "total_cost_usd": "0"}),
            (self.client.get_usage, {"month": "2026-10", "total_requests": True, "total_cost_usd": "0"}),
            (self.client.get_usage, {"month": "2026-10", "total_requests": 0, "total_cost_usd": 0}),
            (self.client.get_limits, {}),
            (self.client.get_limits, {"qps_limit": True}),
            (self.client.get_limits, {"qps_limit": "5"}),
            (self.client.get_limits, {"qps_limit": math.inf}),
            (self.client.get_limits, {"qps_limit": 10 ** 1000}),
            (self.client.get_limits, []),
        ]
        for method, payload in cases:
            with self.subTest(method=method.__name__, payload=payload):
                get.return_value = Response(payload)
                with self.assertRaises(PangramRequestError):
                    method()

    @patch("pangram.text_classifier.requests.get")
    def test_usage_rejects_a_response_for_a_different_month(self, get):
        get.return_value = Response({"month": "2026-11", "total_requests": 0, "total_cost_usd": "0.000000"})
        with self.assertRaises(PangramRequestError):
            self.client.get_usage("2026-10")

    @patch("pangram.text_classifier.requests.get", side_effect=requests.ConnectionError("unavailable"))
    def test_transport_errors_are_wrapped_without_retry(self, get):
        with self.assertRaises(PangramRequestError) as raised:
            self.client.get_limits()
        self.assertIsNone(raised.exception.status_code)
        get.assert_called_once()

    @patch("pangram.text_classifier.requests.get")
    def test_non_json_response_is_rejected(self, get):
        get.return_value = Response(text="invalid")
        get.return_value.json = lambda: (_ for _ in ()).throw(ValueError("not JSON"))
        with self.assertRaises(PangramRequestError):
            self.client.get_limits()

    @patch("pangram.text_classifier.requests.get")
    def test_invalid_timeouts_never_reach_api(self, get):
        for method in [self.client.get_balance, self.client.get_usage, self.client.get_limits]:
            for timeout in [0, -1, math.nan, math.inf, 10 ** 1000, True, "30", None]:
                with self.subTest(method=method.__name__, timeout=timeout), self.assertRaises(ValueError):
                    method(timeout=timeout)
        get.assert_not_called()

    def test_account_types_are_public(self):
        self.assertIn("subscription_included_balance_usd", AccountBalance.__required_keys__)
        self.assertIn("total_cost_usd", AccountUsage.__required_keys__)
        self.assertIn("qps_limit", AccountLimits.__required_keys__)


if __name__ == "__main__":
    unittest.main()
