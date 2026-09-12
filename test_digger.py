import unittest
import json
from datetime import datetime, timezone
from digger.digger import DiggerEngine, LogEntry

class TestDiggerEngine(unittest.TestCase):
    def setUp(self):
        self.engine = DiggerEngine()

    def test_extract_identifiers(self):
        # Should extract UUIDs and custom prefixes
        raw = "Processing req-9912 for user usr_abc123 with token 123e4567-e89b-12d3-a456-426614174000"
        ids = self.engine.extract_identifiers(raw)
        self.assertIn("req-9912", ids)
        self.assertIn("usr_abc123", ids)
        self.assertIn("123e4567-e89b-12d3-a456-426614174000", ids)

    def test_sniff_format_json(self):
        lines = [
            json.dumps({"ts": "2026-09-12T10:00:00Z", "msg": "test"}),
            json.dumps({"ts": "2026-09-12T10:00:01Z", "msg": "test2"})
        ] * 10 # 20 lines of JSON
        self.assertEqual(self.engine.sniff_format(lines), "JSON")

    def test_sniff_format_mixed(self):
        lines = [
            "2026-09-12T10:00:00Z [INFO] ISO string",
            "[10:00:01.000] [WARN] Bracket string",
            json.dumps({"ts": "2026-09-12T10:00:02Z", "msg": "json string"}),
            "Sep 12 10:00:03 [ERROR] Syslog string"
        ] * 5 # 20 mixed lines
        self.assertEqual(self.engine.sniff_format(lines), "MIXED")

    def test_parse_line_iso(self):
        raw = "2026-09-12T10:02:14.001Z [ERROR] Failed ord_123"
        entry = self.engine.parse_line(
            line=raw,
            file_path="web.log",
            line_number=1,
            service="web",
            file_mtime=datetime.now(),
            forced_format="ISO8601"
        )
        self.assertEqual(entry.severity, "ERROR")
        self.assertEqual(entry.service, "web")
        self.assertIn("ord_123", entry.identifiers)
        self.assertIsNotNone(entry.timestamp)
        self.assertEqual(entry.timestamp.year, 2026)

if __name__ == '__main__':
    unittest.main()
