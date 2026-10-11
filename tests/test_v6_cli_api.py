import json
import unittest

from nothos_cli.exporters import render
from nothos_cli.api import app


class TestExporters(unittest.TestCase):

    def setUp(self):
        self.data = {
            "query": "μυστήριον",
            "engine": "lsj",
            "ai": False,
            "results": [
                {
                    "lemma": "μυστήριον",
                    "definition": "secret rite",
                    "score": 0.99,
                }
            ],
            "report": "",
        }

    def test_json(self):
        result = json.loads(render(self.data, "json"))
        self.assertEqual(result["query"], "μυστήριον")

    def test_text(self):
        self.assertIn("μυστήριον", render(self.data, "text"))

    def test_markdown(self):
        self.assertIn("# NOTHOS Research", render(self.data, "markdown"))

    def test_html(self):
        self.assertIn("<html", render(self.data, "html"))


class TestAPI(unittest.TestCase):

    def test_routes(self):
        paths = {route.path for route in app.routes}
        self.assertIn("/health", paths)
        self.assertIn("/api/v1/search", paths)
        self.assertIn("/api/v1/research", paths)


if __name__ == "__main__":
    unittest.main()
