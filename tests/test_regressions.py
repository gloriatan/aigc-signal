"""Regression tests for the issues fixed in the final version. No network: all HTTP is synthetic."""
import base64
import json
import os
import socket
import sys
import tempfile
import shutil
import unittest
import urllib.request
from datetime import timedelta
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collect  # noqa: E402
from brief import analysis, match_annotation  # noqa: E402
from editorial import decide  # noqa: E402
from test_pipeline import NOW, START, Sandbox, fake_http, load_config, release, repo  # noqa: E402

CHECKS = {"aigc_relevant": True, "substantive_change": True, "source_ok": True}


def ev(eid, published, sha="s1", etype="release", tag=None):
    return {"event_id": eid, "type": etype, "tag": tag or f"v{eid}", "published_at": published, "url": "u",
            "prerelease": False, "source_text": "notes", "source_sha256": sha}


def world():
    """Two qualified repos: a real project and an API resale page with a fresh event."""
    cands = {"a/tool": {"id": "a/tool", "category": "video", "description": "tool", "description_sha256": "dA"},
             "z/resale-api": {"id": "z/resale-api", "category": "video", "description": "pricing", "description_sha256": "dZ"}}
    a_ev, z_ev = ev("1", "2026-09-20T00:00:00Z"), ev("created:9", "2026-09-25T00:00:00Z", etype="created", tag=None)
    assessed = {"a/tool": {"status": "qualified", "chosen": a_ev, "events": [a_ev], "check_rank": 0},
                "z/resale-api": {"status": "qualified", "chosen": z_ev, "events": [z_ev], "check_rank": 1}}
    return cands, assessed


def select_a(**kw):
    return {"decision": "select", "repo": "a/tool", "event_id": "1", "tag": "v1", "source_sha256": "s1",
            "reason": "r", "checks": CHECKS, "decided_in_run": "OLD"} | kw


class CrossPeriodSelection(unittest.TestCase):
    def test_new_period_does_not_fall_back_to_rule_default(self):
        cands, assessed = world()
        out = decide(cands, assessed, {"decisions": [select_a()]}, 6)
        self.assertEqual([x["id"] for x in out["selected"]], ["a/tool"])
        self.assertEqual([x["id"] for x in out["pending"]], ["z/resale-api"])

    def test_empty_ledger_selects_nothing(self):
        cands, assessed = world()
        out = decide(cands, assessed, {"decisions": []}, 6)
        self.assertEqual(out["selected"], [])
        self.assertEqual(len(out["pending"]), 2)
        self.assertIn("尚无核查记录", out["pending"][0]["reasons"][0])

    def test_repo_exclusion_holds_then_lapses_when_repo_changes(self):
        cands, assessed = world()
        rule = {"decision": "exclude", "scope": "repo", "repo": "z/resale-api", "reason": "API转售",
                "fingerprint": {"description_sha256": "dZ"}}
        self.assertEqual([x["id"] for x in decide(cands, assessed, {"decisions": [rule]}, 6)["excluded"]], ["z/resale-api"])
        cands["z/resale-api"]["description_sha256"] = "changed"
        out = decide(cands, assessed, {"decisions": [rule]}, 6)
        self.assertEqual(out["excluded"], [])
        self.assertIn("仓库描述已变化", out["pending"][-1]["reasons"][0])

    def test_event_exclusion_does_not_cover_a_new_event(self):
        cands, assessed = world()
        rule = {"decision": "exclude", "scope": "event", "repo": "z/resale-api", "event_id": "created:8", "tag": "old"}
        out = decide(cands, assessed, {"decisions": [rule]}, 6)
        self.assertEqual(out["excluded"], [])
        self.assertIn("尚未核查", out["pending"][-1]["reasons"][0])

    def test_changed_source_or_failed_checks_go_to_pending(self):
        cands, assessed = world()
        out = decide(cands, assessed, {"decisions": [select_a(source_sha256="other")]}, 6)
        self.assertEqual(out["selected"], [])
        self.assertIn("来源说明已变化", out["pending"][0]["reasons"][0])
        out = decide(cands, assessed, {"decisions": [select_a(checks=CHECKS | {"source_ok": False})]}, 6)
        self.assertEqual(out["selected"], [])

    def test_event_out_of_window_is_reported_as_dropped(self):
        cands, assessed = world()
        assessed["a/tool"] = {"status": "checked_no_event", "chosen": None, "events": [], "check_rank": 0}
        out = decide(cands, assessed, {"decisions": [select_a()]}, 6)
        self.assertEqual(out["selected"], [])
        self.assertEqual(out["dropped"][0]["reason"], "本期检查后窗口内无合格事件")

    def test_newer_unreviewed_event_is_flagged(self):
        cands, assessed = world()
        newer = ev("2", "2026-09-28T00:00:00Z", sha="s2")
        assessed["a/tool"]["events"] = [newer, assessed["a/tool"]["events"][0]]
        out = decide(cands, assessed, {"decisions": [select_a()]}, 6)
        self.assertEqual(out["selected"][0]["event"]["event_id"], "1")
        self.assertEqual([e["event_id"] for e in out["selected"][0]["newer_unreviewed"]], ["2"])


class KeywordFlags(unittest.TestCase):
    def test_flagged_new_repo_still_gets_created_event(self):
        cand = collect.build_candidates([("video", "s2", 0, repo("x/awesome-video-gen", 5, created="2026-09-20T00:00:00Z",
                                                                  desc="awesome prompts for video"))], load_config())["x/awesome-video-gen"]
        self.assertTrue(cand["review_flag"])
        event = collect.created_event(cand, "real readme text " * 40, START, NOW, 300)
        self.assertIsNotNone(event)
        self.assertEqual(event["type"], "created")

    def test_whole_word_matching(self):
        flags = collect.review_flag({"full_name": "a/wallpaper-gen", "description": "playlist maker"}, ["paper", "list"])
        self.assertEqual(flags, [])

    def test_flagged_repo_is_checked_when_slots_remain(self):
        cfg = load_config()
        hits = [("avatar", "s1", 0, repo("x/awesome-heads", 9, desc="awesome list"))]
        picks, _ = collect.allocate_main(collect.build_candidates(hits, cfg), cfg)
        self.assertIn("x/awesome-heads", picks["avatar"])


class AnnotationBinding(unittest.TestCase):
    event = {"event_id": "2", "tag": "v2.0", "source_sha256": "new", "source_text": "brand new notes"}

    def test_new_event_without_annotation_does_not_reuse_old(self):
        old = {"items": [{"repo": "a/vid1", "event_id": "1", "tag": "v1.0", "source_sha256": "old", "change": "旧结论"}]}
        out = match_annotation(old, "a/vid1", self.event)
        self.assertEqual(out["status"], "missing")
        self.assertNotIn("change", out)
        self.assertIn("待分析", out["reason"])

    def test_quote_missing_from_source_degrades(self):
        ann = {"items": [{"repo": "a/vid1", "event_id": "2", "tag": "v2.0", "source_sha256": "new",
                          "evidence": [{"id": "q1", "quote": "not in the notes"}]}]}
        sources = {"source_text": {"text": "brand new notes", "url": "u", "raw_file": "r", "label": "版本说明"}}
        out = match_annotation(ann, "a/vid1", self.event, sources)
        self.assertEqual(out["status"], "needs_review")
        ann["items"][0]["evidence"][0]["quote"] = "new   notes"
        out = match_annotation(ann, "a/vid1", self.event, sources)
        self.assertEqual(out["status"], "valid")
        self.assertEqual(out["evidence"][0]["before"], "brand ")

    def test_judgment_and_plan_degrade_with_their_evidence(self):
        projects = [{"id": "a/vid1", "event": {"event_id": "1"}, "annotation": {"status": "needs_review"}}]
        ann = {"period_judgment": {"text": "t", "depends_on": [["a/vid1", "1"]]},
               "team_plan": {"priority": [{"title": "p", "why": "w", "depends_on": [["a/vid1", "1"]]}],
                             "deferred": [{"title": "d", "reason": "r", "background": ["missing_bg"]}]}}
        out = analysis(ann, {"background": []}, projects)
        self.assertEqual(out["period_judgment"]["status"], "needs_review")
        self.assertNotIn("text", out["period_judgment"])
        self.assertEqual(out["team_plan"]["priority"][0]["status"], "needs_review")
        self.assertEqual(out["team_plan"]["deferred"][0]["status"], "needs_review")


class ScopeDisclosure(unittest.TestCase):
    def test_release_page_truncation(self):
        check = {"outcome": "ok", "url": "https://x/releases?per_page=2",
                 "body": [{"published_at": "2026-09-20T00:00:00Z"}, {"published_at": "2026-09-10T00:00:00Z"}]}
        self.assertTrue(collect.releases_truncated(check, START))
        check["body"][1]["published_at"] = "2026-08-01T00:00:00Z"
        self.assertFalse(collect.releases_truncated(check, START))


class OfflineAndSnapshots(Sandbox):
    @staticmethod
    def slurp(path):
        with open(path, encoding="utf-8") as f:
            return f.read()

    def test_offline_rebuild_makes_no_network_call(self):
        run_id, status = self.run_refresh()
        collect.publish(self.root, run_id, status)

        def blocked(*a, **k):
            raise AssertionError("offline rebuild tried to use the network")
        with mock.patch.object(urllib.request, "urlopen", blocked), mock.patch.object(socket, "create_connection", blocked):
            self.assertEqual(collect.cmd_offline(self.root, None), collect.EXIT_OK)

    def test_failed_refresh_keeps_last_report(self):
        run_id, status = self.run_refresh()
        collect.publish(self.root, run_id, status)
        report = os.path.join(self.root, "report.md")
        before = self.slurp(report)

        def down(url, headers, timeout):
            raise OSError("offline")
        bad, st = collect.refresh(self.root, self.config, http_get=down, sleep=lambda s: None, now=NOW + timedelta(hours=2))
        self.assertEqual(collect.publish(self.root, bad, st), collect.EXIT_FAILED)
        self.assertEqual(self.slurp(report), before)
        self.assertEqual(collect.current_run(self.root), run_id)

    def test_new_period_keeps_snapshot_and_lists_removed(self):
        with open(os.path.join(self.root, "selection.json"), "w", encoding="utf-8") as f:
            json.dump({"decisions": [{"decision": "select", "repo": "c/tts1", "event_id": "5", "tag": "v3.0",
                                      "reason": "r", "checks": CHECKS}]}, f)
        first, st = self.run_refresh()
        collect.publish(self.root, first, st)
        self.assertEqual([p["id"] for p in collect.read_json(os.path.join(self.root, "data", "brief.json"))["projects"]], ["c/tts1"])
        later, st = self.run_refresh(now=NOW + timedelta(days=20))  # c/tts1 release (09-15) leaves the window
        collect.publish(self.root, later, st)
        brief = collect.read_json(os.path.join(self.root, "data", "brief.json"))
        self.assertEqual(brief["projects"], [])
        self.assertIn("早于本期窗口起点", brief["changes_since_previous"]["removed"][0]["reason"])
        self.assertTrue(os.path.exists(os.path.join(self.root, "data", "runs", first, "snapshot", "report.md")))
        self.assertTrue(all(p["id"] != "a/vid1" for p in brief["projects"]))  # qualified but unreviewed stays out


class DeliverableConsistency(unittest.TestCase):
    """Checks the shipped outputs: one data source for the dashboard, its fallback and the Markdown."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def read(self, *parts):
        with open(os.path.join(self.root, *parts), encoding="utf-8") as f:
            return f.read()

    def test_three_views_agree(self):
        brief = json.loads(self.read("data", "brief.json"))
        md, html, data_js = self.read("report.md"), self.read("site", "index.html"), self.read("site", "data.js")
        embedded = json.loads(data_js[len("window.SIGNAL_DATA = "):-2].replace("<\\/", "</"))
        self.assertEqual(embedded["brief"], brief)
        self.assertEqual(embedded["report"], md)
        for p in brief["projects"]:
            title = p["annotation"].get("update_title") or p["name"]
            for view in (md, html):
                self.assertIn(title, view)
                self.assertIn(p["event"]["published_at"][:10], view)
                self.assertIn(p["event"]["url"], view)
        for x in brief["pending"]:
            self.assertIn(x["name"], md)
            self.assertIn(x["name"], html)

    def test_no_required_external_resources(self):
        for parts in (("site", "index.html"),):
            page = self.read(*parts)
            self.assertNotRegex(page, r'<(script|link|img|iframe)[^>]+(src|href)="(https?:)?//')
            self.assertNotIn("@import", page)
        self.assertNotIn("http", self.read("site", "style.css"))

    def test_light_theme_on_every_open(self):
        index, app = self.read("site", "index.html"), self.read("site", "app.js")
        self.assertIn('data-theme="light"', index)
        self.assertNotIn("localStorage", index + app)
        self.assertNotIn("prefers-color-scheme", self.read("site", "style.css"))


if __name__ == "__main__":
    unittest.main()
