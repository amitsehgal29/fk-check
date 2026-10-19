import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import fk_check as f

S = Path(__file__).parent / "samples"
P = [{"id": "1", "c": "AE"}, {"id": "2", "c": "AE"}, {"id": "3", "c": "IN"}]


class CoreTests(unittest.TestCase):
    def test_orphans_and_nulls(self):
        child = [{"fk": "1"}, {"fk": "9"}, {"fk": "9"}, {"fk": " "}]
        r = f.check(P, ["id"], child, ["fk"])
        self.assertEqual((r["orphan_rows"], r["null_fk_rows"]), (2, 1))
        self.assertEqual(r["orphan_keys"], [{"key": ["9"], "rows": 2}])
        self.assertEqual(r["unused_parent_keys"], [["2"], ["3"]])

    def test_composite_key(self):
        child = [{"fk": "1", "cc": "AE"}, {"fk": "1", "cc": "IN"}]
        r = f.check(P, ["id", "c"], child, ["fk", "cc"])
        self.assertEqual(r["orphan_keys"], [{"key": ["1", "IN"], "rows": 1}])

    def test_ignore_case(self):
        self.assertEqual(f.check([{"k": "AbC"}], ["k"], [{"k": "abc"}], ["k"], True)["orphan_rows"], 0)
        self.assertEqual(f.check([{"k": "AbC"}], ["k"], [{"k": "abc"}], ["k"])["orphan_rows"], 1)

    def test_key_length_mismatch(self):
        with self.assertRaises(ValueError):
            f.check(P, ["id"], [], ["a", "b"])


class CliTests(unittest.TestCase):
    def run_cli(self, *a):
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            code = f.main([str(S / "customers.csv"), str(S / "orders.csv"), "--parent-key", "customer_id", *a])
        return code, (json.loads(out.getvalue()) if out.getvalue() else None)

    def test_fails_on_orphans(self):
        code, r = self.run_cli()
        self.assertEqual((code, r["status"], r["orphan_rows"]), (1, "fail", 3))

    def test_tolerance_and_case(self):
        code, r = self.run_cli("--ignore-case", "--max-orphans", "2")
        self.assertEqual((code, r["orphan_rows"]), (0, 2))

    def test_missing_column(self):
        code, _ = self.run_cli("--child-key", "nope")
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
