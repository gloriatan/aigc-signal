"""Period diff: new / new version / removed / newly pending. No network."""
import json
import os
import sys
import unittest
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collect  # noqa: E402
from diff import REASON_NOT_SELECTED, REASON_OUT_OF_WINDOW, compute_diff  # noqa: E402
from test_pipeline import NOW, Sandbox  # noqa: E402


def project(pid, event_id, tag, published):
    return {"id": pid, "name": pid, "event": {"event_id": event_id, "tag": tag, "type": "release", "published_at": published}}


def brief(run_id, window_start, projects, pending=()):
    return {"meta": {"run_id": run_id, "window_start": window_start}, "projects": list(projects),
            "pending": [{"id": p, "name": p} for p in pending]}


class ComputeDiff(unittest.TestCase):
    prev = brief("20261001T000000Z", "2026-09-01T00:00:00Z", [
        project("a/same", "1", "v1", "2026-09-10T00:00:00Z"),
        project("b/bump", "2", "v1.0", "2026-09-05T00:00:00Z"),
        project("c/old", "3", "v3", "2026-09-02T00:00:00Z"),
        project("d/dropped", "4", "v4", "2026-09-20T00:00:00Z")], pending=["p/known"])
    cur = brief("20261005T000000Z", "2026-09-05T00:00:00Z", [
        project("a/same", "1", "v1", "2026-09-10T00:00:00Z"),
        project("b/bump", "5", "v1.1", "2026-10-01T00:00:00Z"),
        project("e/fresh", "6", "v0.1", "2026-10-02T00:00:00Z")], pending=["p/known", "p/new"])

    def test_statuses_and_summary(self):
        d = compute_diff(self.prev, self.cur)
        self.assertEqual({k: v["status"] for k, v in d["projects"].items()},
                         {"a/same": "same", "b/bump": "version", "e/fresh": "new"})
        self.assertEqual((d["projects"]["b/bump"]["from"]["tag"], d["projects"]["b/bump"]["to"]["tag"]), ("v1.0", "v1.1"))
        self.assertEqual({r["id"]: r["reason"] for r in d["removed"]},
                         {"c/old": REASON_OUT_OF_WINDOW, "d/dropped": REASON_NOT_SELECTED})
        self.assertEqual(d["pending_new"], ["p/new"])
        self.assertEqual(d["summary"], {"new": 1, "version": 1, "removed": 2, "pending_new": 1, "changed": 4})
        self.assertEqual((d["from_run"], d["to_run"]), ("20261001T000000Z", "20261005T000000Z"))

    def test_first_period_has_no_previous(self):
        d = compute_diff(None, self.cur)
        self.assertFalse(d["has_previous"])
        self.assertEqual(d["summary"]["changed"], 0)

    def test_inputs_not_modified(self):
        before = json.dumps([self.prev, self.cur], sort_keys=True)
        compute_diff(self.prev, self.cur)
        self.assertEqual(json.dumps([self.prev, self.cur], sort_keys=True), before)


class DiffInPipeline(Sandbox):
    def test_publish_writes_diff_against_previous_snapshot(self):
        with open(os.path.join(self.root, "selection.json"), "w", encoding="utf-8") as f:
            json.dump({"decisions": [{"decision": "select", "repo": "c/tts1", "event_id": "5", "tag": "v3.0", "reason": "r",
                                      "checks": {"aigc_relevant": True, "substantive_change": True, "source_ok": True}}]}, f)
        first, st = self.run_refresh()
        collect.publish(self.root, first, st)
        first_diff = collect.read_json(os.path.join(self.root, "data", "diff.json"))
        self.assertFalse(first_diff["has_previous"])
        later, st = self.run_refresh(now=NOW + timedelta(days=20))
        collect.publish(self.root, later, st)
        d = collect.read_json(os.path.join(self.root, "data", "diff.json"))
        self.assertEqual((d["from_run"], d["to_run"]), (first, later))
        self.assertEqual([(r["id"], r["reason"]) for r in d["removed"]], [("c/tts1", REASON_OUT_OF_WINDOW)])
        embedded = collect.read_json(os.path.join(self.root, "data", "brief.json"))["diff"]
        self.assertEqual(embedded, d)


if __name__ == "__main__":
    unittest.main()
