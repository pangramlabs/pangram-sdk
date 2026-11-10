"""Account-read contracts and ZDR transport/privacy boundaries; no live calls."""

import inspect
import math
import unittest
from unittest.mock import patch

import requests

from pangram import AccountBalance, AccountLimits, AccountUsage, Pangram, PangramRequestError
from pangram.text_classifier import API_ENDPOINT, ZDR_API_ENDPOINT
from tests.pangram_test import MockResponse, pangram_4_success_response


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
            for timeout in [0, -1, math.nan, math.inf, True, "30", None]:
                with self.subTest(method=method.__name__, timeout=timeout), self.assertRaises(ValueError):
                    method(timeout=timeout)
        get.assert_not_called()

    def test_account_types_are_public(self):
        self.assertIn("subscription_included_balance_usd", AccountBalance.__required_keys__)
        self.assertIn("total_cost_usd", AccountUsage.__required_keys__)
        self.assertIn("qps_limit", AccountLimits.__required_keys__)


class TestZDR(unittest.TestCase):
    def setUp(self):
        self.client = Pangram(api_key="test-key")

    @patch("pangram.text_classifier.requests.get")
    @patch("pangram.text_classifier.requests.post")
    def test_one_post_to_zdr_without_redirects_polling_or_fallback(self, post, get):
        payload = pangram_4_success_response()
        post.return_value = Response(payload)
        self.assertEqual(self.client.predict_zdr("hello", model=" pangram-4 "), payload)
        post.assert_called_once_with(
            ZDR_API_ENDPOINT, json={"text": "hello", "model": "pangram-4"},
            headers={"Content-Type": "application/json", "x-api-key": "test-key"},
            timeout=(10, 610), allow_redirects=False,
        )
        get.assert_not_called()

    @patch("pangram.text_classifier.requests.post")
    def test_small_timeout_bounds_both_connection_and_read(self, post):
        post.return_value = Response(pangram_4_success_response())
        self.client.predict_zdr("hello", model="pangram-4", timeout=0.5)
        self.assertEqual(post.call_args.kwargs["timeout"], (0.5, 0.5))

    @patch("pangram.text_classifier.requests.get")
    @patch("pangram.text_classifier.requests.post")
    def test_timeouts_and_network_errors_never_retry_or_leak_content(self, post, get):
        for error in [requests.Timeout("secret text test-key"), requests.ConnectionError("secret text test-key")]:
            with self.subTest(error=type(error).__name__):
                post.reset_mock()
                post.side_effect = error
                expected = TimeoutError if isinstance(error, requests.Timeout) else PangramRequestError
                with self.assertRaises(expected) as raised:
                    self.client.predict_zdr("secret text", model="pangram-4")
                self.assertNotIn("secret text", str(raised.exception))
                self.assertNotIn("test-key", str(raised.exception))
                self.assertIn("another charge", str(raised.exception))
                post.assert_called_once()
        get.assert_not_called()

    @patch("pangram.text_classifier.requests.post")
    def test_http_errors_and_redirects_never_retry_or_echo_response(self, post):
        for status in [307, 401, 402, 403, 429, 503, 504]:
            with self.subTest(status=status):
                post.reset_mock()
                post.return_value = Response(status=status, text="secret text test-key", headers={"Retry-After": "3"})
                with self.assertRaises(PangramRequestError) as raised:
                    self.client.predict_zdr("secret text", model="pangram-4")
                self.assertEqual(raised.exception.status_code, status)
                self.assertEqual(raised.exception.retry_after, 3)
                self.assertNotIn("secret text", str(raised.exception))
                self.assertNotIn("test-key", str(raised.exception))
                post.assert_called_once()

    @patch("pangram.text_classifier.requests.post")
    def test_failed_nonterminal_and_malformed_responses_are_not_returned(self, post):
        for payload in [None, [], {}, {"stage": "STAGE_PREPROCESSING"}, {"stage": "STAGE_FAILED", "headline": "secret text"}]:
            with self.subTest(payload=payload):
                post.reset_mock()
                post.return_value = Response(payload)
                with self.assertRaises(PangramRequestError) as raised:
                    self.client.predict_zdr("secret text", model="pangram-4")
                self.assertNotIn("secret text", str(raised.exception))
                post.assert_called_once()

    @patch("pangram.text_classifier.requests.post")
    def test_invalid_json_does_not_echo_response(self, post):
        post.return_value = Response(text="secret text")
        post.return_value.json = lambda: (_ for _ in ()).throw(ValueError("secret text"))
        with self.assertRaises(PangramRequestError) as raised:
            self.client.predict_zdr("secret text", model="pangram-4")
        self.assertNotIn("secret text", str(raised.exception))

    @patch("pangram.text_classifier.requests.post")
    def test_invalid_inputs_never_reach_api(self, post):
        for text, model in [("", "pangram-4"), ("  ", "pangram-4"), (None, "pangram-4"), ("hello", None), ("hello", ""), ("hello", 4)]:
            with self.subTest(text=text, model=model), self.assertRaises(ValueError):
                self.client.predict_zdr(text, model=model)
        for timeout in [0, -1, math.nan, math.inf, True, "610", None]:
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                self.client.predict_zdr("hello", model="pangram-4", timeout=timeout)
        post.assert_not_called()

    def test_model_is_required_and_unsupported_options_are_not_exposed(self):
        parameters = inspect.signature(Pangram.predict_zdr).parameters
        self.assertEqual(parameters["model"].kind, inspect.Parameter.KEYWORD_ONLY)
        self.assertIs(parameters["model"].default, inspect.Parameter.empty)
        for option in ["public_dashboard_link", "webhook_delivery", "end_user_email", "poll_interval"]:
            self.assertNotIn(option, parameters)


if __name__ == "__main__":
    unittest.main()
