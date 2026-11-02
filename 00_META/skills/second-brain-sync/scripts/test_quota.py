import unittest
from quota import parse, Quota

CLAUDE_JSON = """{
  "provider": "claude-code",
  "available": true,
  "subscriptionType": "pro",
  "fiveHour": {
    "usedPercent": 68.0,
    "resetsAt": 1793638800000,
    "durationMinutes": 300
  },
  "sevenDay": {
    "usedPercent": 0.26,
    "resetsAt": 1794175200000,
    "durationMinutes": 10080
  }
}"""

ANTIGRAVITY_JSON = """{
  "provider": "antigravity",
  "available": true,
  "planName": "Google AI Pro",
  "groups": [
    {
      "displayName": "Gemini Models",
      "windows": [
        {
          "usedPercent": 9.01,
          "resetsAt": 1793639755000,
          "durationMinutes": 300,
          "bucketId": "gemini-5h",
          "windowKind": "5h"
        },
        {
          "usedPercent": 40.17,
          "resetsAt": 1793802264000,
          "durationMinutes": 10080,
          "bucketId": "gemini-weekly",
          "windowKind": "weekly"
        }
      ]
    }
  ]
}"""

class QuotaTest(unittest.TestCase):
    def test_parse_claude(self):
        q = parse(CLAUDE_JSON, "claude")
        self.assertEqual(q.harness, "claude")
        self.assertEqual(q.used_5h, 68.0)
        self.assertEqual(q.used_7d, 0.26)
        self.assertEqual(q.resets_at, 1793638800000)
        self.assertAlmostEqual(q.free_pct, 32.0, places=2)

    def test_parse_antigravity(self):
        q = parse(ANTIGRAVITY_JSON, "antigravity")
        self.assertEqual(q.harness, "antigravity")
        self.assertEqual(q.used_5h, 9.01)
        self.assertEqual(q.used_7d, 40.17)
        self.assertAlmostEqual(q.free_pct, 59.83, places=2)

    def test_missing_or_unknown_window_fails_closed(self):
        q = parse("{}", "claude")
        self.assertEqual(q.used_5h, 100.0)
        self.assertEqual(q.used_7d, 100.0)
        self.assertEqual(q.free_pct, 0.0)

    def test_invalid_json_raises_value_error(self):
        with self.assertRaises(ValueError):
            parse("invalid json", "claude")

if __name__ == "__main__":
    unittest.main()
