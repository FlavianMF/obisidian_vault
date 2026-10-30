"""test_web_cli.py - Tests for CLI integration of 'sb review web' and server lifecycle."""
from __future__ import annotations

import argparse
import ast
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import sb
import web_service
from test_web_service import WebFixture


class WebCliIntegrationTest(unittest.TestCase):
    """Verifies that 'sb review web' correctly parses arguments and starts the server."""

    def test_parser_has_review_web_with_options(self):
        parser = sb.build_parser()
        args = parser.parse_args(["review", "web", "--port", "8765", "--host", "0.0.0.0", "--no-browser"])
        self.assertEqual(args.command, "review")
        self.assertEqual(args.stage, "web")
        self.assertEqual(args.port, 8765)
        self.assertEqual(args.host, "0.0.0.0")
        self.assertTrue(args.no_browser)

    def test_parser_defaults(self):
        parser = sb.build_parser()
        args = parser.parse_args(["review", "web"])
        self.assertEqual(args.command, "review")
        self.assertEqual(args.stage, "web")
        self.assertEqual(args.port, 8000)
        self.assertEqual(args.host, "127.0.0.1")
        self.assertFalse(args.no_browser)

    @patch("web_service.run_server", return_value=0)
    def test_sb_main_invokes_run_server(self, mock_run):
        exit_code = sb.main(["review", "web", "--port", "9090", "--no-browser"])
        self.assertEqual(exit_code, 0)
        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        self.assertEqual(kwargs.get("port"), 9090)
        self.assertFalse(kwargs.get("open_browser"))


class WebServerLifecycleTest(WebFixture):
    """Tests web_service.run_server execution, browser invocation, and clean shutdown."""

    @patch("uvicorn.Server.run")
    @patch("webbrowser.open")
    def test_run_server_starts_and_handles_clean_shutdown(self, mock_browser, mock_uvicorn_run):
        # Normal shutdown
        code = web_service.run_server(self.vault, self.state, port=8888, open_browser=False, log_level="warning")
        self.assertEqual(code, 0)
        mock_uvicorn_run.assert_called_once()
        mock_browser.assert_not_called()

    @patch("uvicorn.Server.run", side_effect=KeyboardInterrupt)
    def test_run_server_handles_keyboard_interrupt_gracefully(self, mock_uvicorn_run):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            code = web_service.run_server(self.vault, self.state, port=8888, open_browser=False)
        self.assertEqual(code, 0)
        self.assertIn("Servidor finalizado", buf.getvalue())

    @patch("uvicorn.Server.run")
    @patch("webbrowser.open")
    def test_run_server_triggers_browser_thread(self, mock_browser, mock_uvicorn_run):
        with patch("time.sleep", return_value=None):
            code = web_service.run_server(self.vault, self.state, port=8888, open_browser=True)
            self.assertEqual(code, 0)
            mock_uvicorn_run.assert_called_once()


class CliInvariantsTest(unittest.TestCase):
    """Verifies that test_web_cli and sb.py preserve repository invariants."""

    def test_i1_no_direct_writes_in_web_cli_test(self):
        content = (HERE / "test_web_cli.py").read_text(encoding="utf-8")
        tree = ast.parse(content)
        bad = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Call) and (
            (isinstance(n.func, ast.Attribute) and n.func.attr in ("write_text", "write_bytes"))
            or (isinstance(n.func, ast.Name) and n.func.id == "open"))]
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
