import io
import json
import unittest
from unittest.mock import patch

from public_api_docs_mcp import server


DOC = {"title": "Example", "version": "CURRENT", "url": "https://api-docs.hoppscotch.io/view/abc/CURRENT",
       "versions": [{"version": "CURRENT"}], "environmentVariables": '[{"key":"BASE_URL"}]'}
TREE = {"requests": [], "folders": [{"name": "Users", "requests": [{
    "id": "req1", "name": "Create", "method": "POST", "endpoint": "/users",
    "description": "Create a user", "auth": {"authType": "bearer", "token": "do-not-return"},
    "params": [{"key": "api_key", "value": "do-not-return"}],
    "headers": [{"key": "Content-Type", "value": "application/json"}],
    "body": {"contentType": "application/json", "body": "{}"},
    "responses": {"Created": {"name": "Created", "status": "OK", "code": 201, "body": "{}"}},
}]}]}


class ServerTest(unittest.TestCase):
    def test_url_and_lookup(self):
        self.assertEqual(
            server._api_url("https://api-docs.hoppscotch.io/view/abc/CURRENT"),
            "https://api.hoppscotch.io/v1/published-docs/abc/CURRENT",
        )
        with self.assertRaises(server.ToolError):
            server._api_url("https://example.com/view/abc")
        with patch.dict(server.os.environ, {"HOPPSCOTCH_DOC_URL": ""}):
            with self.assertRaises(server.ToolError):
                server._api_url("")
        with patch.dict(server.os.environ, {
            "HOPPSCOTCH_DOCS_ORIGIN": "http://localhost:3000",
            "HOPPSCOTCH_API_BASE_URL": "http://localhost:3170/v1",
        }):
            self.assertEqual(server._api_url("http://localhost:3000/view/abc"),
                             "http://localhost:3170/v1/published-docs/abc")
        with patch.object(server, "_load", return_value=(DOC, TREE)):
            overview = server.get_document()
            self.assertEqual(overview["endpoint_count"], 1)
            self.assertEqual(overview["variables"], ["BASE_URL"])
            self.assertEqual(overview["folders"], [{"path": "Users", "endpoint_count": 1}])
            self.assertEqual(server.list_endpoints(folder="User")["total"], 0)
            self.assertEqual(server.list_endpoints(method="get")["total"], 0)
            found = server.list_endpoints(folder="users", method="post", query="create")
            self.assertEqual(found["endpoints"][0]["id"], "req1")
            detail = server.get_endpoint("req1", response_name="Created")
            self.assertEqual(detail["folder"], "Users")
            self.assertEqual(detail["params"][0]["value"], "[redacted]")
            self.assertEqual(detail["response"]["code"], 201)
            self.assertNotIn("do-not-return", str(detail))
            self.assertEqual(server.get_endpoint("req1")["response"]["code"], 201)
            with self.assertRaises(server.ToolError):
                server.get_endpoint("req1", response_name="Missing")

    def test_compact_search_for_broad_tasks(self):
        tree = {"requests": [
            {"id": "product", "name": "List products", "method": "GET", "endpoint": "/products"},
            {"id": "tenant-list", "name": "List tenants", "method": "GET",
             "endpoint": "/tenants", "description": "All tenants and their settings " * 20},
            {"id": "tenant-one", "name": "Get tenant", "method": "GET",
             "endpoint": "/tenants/{id}", "body": {"body": "sensitive sample"}},
            {"id": "account", "name": "Account lookup", "method": "GET",
             "endpoint": "/accounts", "responses": {"OK": {"body": '{"tenantId": "abc"}'}}},
        ]}
        with patch.object(server, "_load", return_value=(DOC, tree)):
            result = server.search_documentation(
                "create complete product page, use all tenant to get tenant data", limit=1)
            self.assertEqual(result["total"], 4)
            self.assertEqual(result["endpoints"][0]["id"], "tenant-list")
            self.assertEqual(result["next_offset"], 1)
            self.assertLessEqual(len(result["endpoints"][0]["description"]), 180)
            self.assertNotIn("sensitive sample", str(result))
            self.assertEqual(server.search_documentation("tenant", offset=2)["endpoints"][0]["id"],
                             "account")
            self.assertEqual(server.search_documentation("accounts")["total"], 1)
            self.assertEqual(server.search_documentation("get data")["total"], 4)
            with self.assertRaises(server.ToolError):
                server.search_documentation("!")
            with self.assertRaises(server.ToolError):
                server.search_documentation("tenant", limit=51)

    def test_postman(self):
        api = server._api_url("https://documenter.getpostman.com/view/123/abc?version=2.0#some-id")
        self.assertEqual(
            api, "https://documenter.gw.postman.com/api/collections/123/abc?segregateAuth=true&versionTag=2.0")
        for bad in ("http://documenter.getpostman.com/view/123/abc",
                    "https://documenter.getpostman.com/view/123/..",
                    "https://documenter.getpostman.com/view/123/abc?version=../x",
                    "https://documenter.getpostman.com.evil.test/view/123/abc"):
            with self.assertRaises(server.ToolError):
                server._api_url(bad)
        big = json.dumps({"data": [{"id": n, "image": "x" * 9000} for n in range(9)]})
        response = {"name": "OK", "status": "OK", "code": 200, "body": big}
        data = {
            "info": {"name": "Shop", "description": "<html><body><p>Sell &amp; buy</p></body></html>"},
            "variable": [{"key": "BASE_URL", "value": "hidden"}],
            "item": [{"name": "Auth", "item": [{"name": "Nested", "item": [{
                "id": "login", "name": "Login",
                "request": {
                    "method": "POST", "url": "{{BASE_URL}}/login/:shop?token=do-not-return",
                    "description": "<p>Use <code>email</code></p>\n",
                    "auth": {"type": "bearer", "bearer": {"basicConfig": [{"value": "do-not-return"}]}},
                    "header": [{"key": "X-Api-Key", "value": "do-not-return"}],
                    "urlObject": {"variable": [{"key": "shop", "value": "1", "description": {"content": "<p>Shop id</p>"}}], "query": [
                        {"key": "token", "value": "do-not-return", "disabled": True}]},
                    "body": {"mode": "raw", "raw": '{"email": "a"}'}},
                "response": [{**response, "name": "Bad", "code": 400, "body": "no"}, response, response],
            }]}]}],
        }
        with patch.object(server, "urlopen", return_value=io.BytesIO(json.dumps(data).encode())):
            server._fetch.cache_clear()
            url = "https://documenter.getpostman.com/view/123/abc"
            overview = server.get_document(url)
            self.assertEqual(overview["description"], "Sell & buy")
            self.assertEqual(overview["folders"], [{"path": "Auth/Nested", "endpoint_count": 1}])
            self.assertEqual(overview["variables"], ["BASE_URL"])
            detail = server.get_endpoint("login", doc_url=url)
            self.assertNotIn("do-not-return", str(detail))
            self.assertEqual(detail["endpoint"], "{{BASE_URL}}/login/:shop")
            self.assertEqual(detail["description"], "Use email")
            self.assertEqual(detail["auth_type"], "bearer")
            self.assertEqual(detail["params"][0]["description"], "Shop id")
            self.assertEqual([row["type"] for row in detail["params"]], ["path", "query"])
            self.assertEqual(detail["body"], {"contentType": "raw", "body": '{"email": "a"}'})
            self.assertFalse(detail["body_truncated"])
            self.assertEqual([r["name"] for r in detail["responses"]], ["Bad", "OK", "OK (2)"])
            self.assertEqual(detail["response"]["name"], "OK")
            self.assertTrue(detail["response"]["truncated"])
            self.assertLess(len(detail["response"]["body"]), 2000)
            self.assertIn("6 more items", json.loads(detail["response"]["body"])["data"][-1])
            full = server.get_endpoint("login", doc_url=url, full_bodies=True)
            self.assertEqual(full["response"]["body"], big)


if __name__ == "__main__":
    unittest.main()
