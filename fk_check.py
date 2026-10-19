#!/usr/bin/env python3
"""fk-check: referential-integrity check between two CSV files.

Standard library only. Finds child rows whose foreign key has no matching
key in the parent file (orphans), and optionally parent keys that no child
uses. Supports composite keys (comma-separated column lists), trims
whitespace, and can match keys case-insensitively. Exits 1 when orphans
exceed --max-orphans, so it can gate a load.
"""
import argparse
import csv
import json
import sys
from collections import Counter


def cols(text):
    out = [c.strip() for c in text.split(",") if c.strip()]
    if not out:
        raise ValueError("empty key list")
    return out


def key_of(row, columns, ignore_case=False):
    vals = tuple((row.get(c) or "").strip() for c in columns)
    if all(v == "" for v in vals):
        return None
    return tuple(v.lower() for v in vals) if ignore_case else vals


def load(path, columns):
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        missing = [c for c in columns if c not in (r.fieldnames or [])]
        if missing:
            raise KeyError(f"{path}: missing column(s) {missing}")
        return list(r)


def check(parent_rows, pcols, child_rows, ccols, ignore_case=False):
    if len(pcols) != len(ccols):
        raise ValueError("parent and child key lists must be the same length")
    parent = {key_of(r, pcols, ignore_case) for r in parent_rows}
    parent.discard(None)
    orphans, null_fk, used = Counter(), 0, set()
    for r in child_rows:
        k = key_of(r, ccols, ignore_case)
        if k is None:
            null_fk += 1
        elif k in parent:
            used.add(k)
        else:
            orphans[k] += 1
    return {
        "parent_keys": len(parent),
        "child_rows": len(child_rows),
        "null_fk_rows": null_fk,
        "orphan_rows": sum(orphans.values()),
        "orphan_keys": [{"key": list(k), "rows": n} for k, n in orphans.most_common()],
        "unused_parent_keys": sorted(list(k) for k in parent - used),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Find child rows whose foreign key is missing from the parent CSV.")
    ap.add_argument("parent")
    ap.add_argument("child")
    ap.add_argument("--parent-key", required=True, help="parent key column(s), comma-separated")
    ap.add_argument("--child-key", help="child FK column(s), default: same as --parent-key")
    ap.add_argument("--ignore-case", action="store_true")
    ap.add_argument("--max-orphans", type=int, default=0, help="allowed orphan rows before exit 1")
    ap.add_argument("--show-unused", action="store_true", help="include parent keys no child uses")
    ap.add_argument("--limit", type=int, default=20, help="max orphan keys to list (default 20)")
    a = ap.parse_args(argv)
    try:
        pcols = cols(a.parent_key)
        ccols = cols(a.child_key or a.parent_key)
        res = check(load(a.parent, pcols), pcols, load(a.child, ccols), ccols, a.ignore_case)
    except (KeyError, ValueError) as e:
        print(f"fk-check: {e.args[0]}", file=sys.stderr)
        return 2
    res["orphan_keys"] = res["orphan_keys"][: a.limit]
    if not a.show_unused:
        res.pop("unused_parent_keys")
    res["status"] = "fail" if res["orphan_rows"] > a.max_orphans else "pass"
    print(json.dumps(res, indent=2))
    return 1 if res["status"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
