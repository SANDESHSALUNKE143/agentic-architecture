import unittest

import httpx

from agentic_sdk.http import JsonTransport, RemoteError


class TransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_token_propagation_and_fixed_path(self):
        def handler(request):
            self.assertEqual(request.headers["Authorization"], "Bearer synthetic")
            self.assertEqual(request.url.path, "/api/agent/catalog")
            return httpx.Response(200, json={"data": {}})

        t = JsonTransport(
            "https://example.invalid",
            lambda: "synthetic",
            transport=httpx.MockTransport(handler),
        )
        try:
            self.assertEqual(await t.request("GET", "/api/agent/catalog"), {"data": {}})
            with self.assertRaises(ValueError):
                await t.request("GET", "//other.invalid")
        finally:
            await t.aclose()

    async def test_redirect_and_errors_do_not_leak_or_retry(self):
        calls = []

        def handler(request):
            calls.append(request)
            return httpx.Response(
                302,
                headers={"Location": "https://other.invalid"},
                text="private-server-detail",
            )

        t = JsonTransport(
            "https://example.invalid",
            lambda: "synthetic",
            transport=httpx.MockTransport(handler),
        )
        try:
            with self.assertRaises(RemoteError) as error:
                await t.request("POST", "/refresh", body={})
            self.assertNotIn("private", str(error.exception))
            self.assertEqual(len(calls), 1)
        finally:
            await t.aclose()

    async def test_response_bound(self):
        t = JsonTransport(
            "https://example.invalid",
            lambda: "synthetic",
            max_response_bytes=10,
            transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"large": "x" * 100})),
        )
        try:
            with self.assertRaises(RemoteError):
                await t.request("GET", "/data")
        finally:
            await t.aclose()
