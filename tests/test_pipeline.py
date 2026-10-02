"""Pipeline tests. All network calls use synthetic responses; nothing goes online."""
import json
import os
import shutil
import sys
import tempfile
import unittest
import urllib.error
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collect  # noqa: E402
from brief import match_annotation, observations  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOW = datetime(2026, 10, 2, 0, 0, 0, tzinfo=timezone.utc)
START = NOW - timedelta(days=30)


def load_config():
    with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as f:
        config = json.load(f)
    config["manual_exclusions"] = []
    return config


def repo(name, stars, created="2025-01-01T00:00:00Z", desc="AI video generation tool", rid=None):
    return {"full_name": name, "html_url": f"https://github.com/{name}", "description": desc,
            "stargazers_count": stars, "created_at": created, "pushed_at": "2026-09-20T00:00:00Z",
            "size": 100, "id": rid or abs(hash(name)) % 10**8, "license": {"spdx_id": "MIT"}}


def release(rid, tag, published, body="Added a new generation pipeline with editable shots.", pre=False, draft=False):
    return {"id": rid, "tag_name": tag, "published_at": published, "html_url": f"https://example.com/{tag}",
            "body": body, "prerelease": pre, "draft": draft}


SEARCH = {
    ("text-to-video", "pushed"): [repo("a/vid1", 900), repo("a/vid2", 800), repo("a/vid3", 700), repo("a/vid4", 600)],
    ("text-to-video", "created"): [repo("a/vnew", 50, created="2026-09-20T00:00:00Z")],
    ("image-generation", "pushed"): [repo("a/vid1", 900), repo("b/img1", 500)],
    ("image-generation", "created"): [],
    ("text-to-speech", "pushed"): [repo("c/tts1", 400), repo("c/awesome-tts", 300, desc="awesome list")],
    ("text-to-speech", "created"): [],
    ("talking-head", "pushed"): [],
    ("talking-head", "created"): [],
}
RELEASES = {
    "a/vid1": [release(1, "v2.0", "2026-09-25T00:00:00Z"), release(2, "v2.1-rc", "2026-09-28T00:00:00Z", pre=True)],
    "a/vid2": [release(3, "v1.0", "2026-08-01T00:00:00Z")],
    "b/img1": [release(4, "v0.9", "2026-09-10T00:00:00Z")],
    "c/tts1": [release(5, "v3.0", "2026-09-15T00:00:00Z")],
}


def fake_http(fail_repo=None):
    def get(url, headers, timeout):
        if fail_repo and f"/repos/{fail_repo}/" in url:
            raise urllib.error.URLError("timed out")
        if "/search/repositories" in url:
            for (topic, field), items in SEARCH.items():
                if f"topic%3A{topic}+{field}" in url:
                    return 200, {"x-ratelimit-remaining": "9"}, json.dumps({"items": items}).encode()
        if url.endswith("/readme"):
            import base64
            content = base64.b64encode(("New project readme " * 30).encode()).decode()
            return 200, {}, json.dumps({"content": content}).encode()
        for name, rels in RELEASES.items():
            if f"/repos/{name}/releases" in url:
                return 200, {}, json.dumps(rels).encode()
        return 200, {}, b"[]"
    return get


class Sandbox(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, "data"))
        self.config = load_config()

    def tearDown(self):
        shutil.rmtree(self.root)

    def run_refresh(self, fail_repo=None, now=NOW):
        return collect.refresh(self.root, self.config, http_get=fake_http(fail_repo), sleep=lambda s: None, now=now)


class T1Window(unittest.TestCase):
    def test_boundaries_and_offsets(self):
        self.assertTrue(collect.in_window(START, START, NOW))
        self.assertFalse(collect.in_window(NOW, START, NOW))
        self.assertFalse(collect.in_window(START - timedelta(seconds=1), START, NOW))
        ts = collect.parse_ts("2026-09-02T07:30:00+08:00")
        self.assertEqual(collect.iso(ts), "2026-09-01T23:30:00Z")
        self.assertFalse(collect.in_window(ts, START + timedelta(days=1), NOW))


class T2Dedup(unittest.TestCase):
    def test_cross_category_repo_counted_once(self):
        hits = [("video", "s1", 0, repo("a/vid1", 900)), ("image", "s1", 0, repo("a/vid1", 900)),
                ("image", "s1", 1, repo("b/img1", 500)), ("speech", "s2", 0, repo("a/vid1", 900))]
        cands = collect.build_candidates(hits, load_config())
        self.assertEqual(sorted(cands), ["a/vid1", "b/img1"])
        self.assertEqual(cands["a/vid1"]["category"], "video")  # same rank, config order wins
        self.assertEqual(cands["a/vid1"]["also_in"], ["image", "speech"])

    def test_keyword_only_flags(self):
        cands = collect.build_candidates([("speech", "s1", 0, repo("c/awesome-tts", 1, desc="awesome list"))], load_config())
        self.assertIn("awesome", cands["c/awesome-tts"]["review_flag"])
        self.assertFalse(cands["c/awesome-tts"]["manually_excluded"])


class T3Allocation(unittest.TestCase):
    def test_flagged_rank_zero_does_not_crash(self):
        hits = [("video", "s1", 0, repo("a/awesome-video", 9, desc="awesome list")),
                ("video", "s1", 3, repo("b/video-list", 8, desc="video list"))]
        queue, _ = collect.category_queue(collect.build_candidates(hits, load_config()), "video")
        self.assertEqual([c["id"] for c in queue], ["a/awesome-video", "b/video-list"])

    def test_quota_reserve_and_backfill(self):
        hits = [("video", "s1", i, repo(f"v/{i}", 100 - i)) for i in range(6)]
        hits.append(("video", "s2", 0, repo("v/new", 5, created="2026-09-20T00:00:00Z")))
        hits.append(("image", "s1", 0, repo("i/0", 50)))
        picks, queues = collect.allocate_main(collect.build_candidates(hits, load_config()), load_config())
        self.assertIn("v/new", picks["video"])  # S2 top reserved
        self.assertEqual(picks["image"], ["i/0"])
        # image has 2 empty slots and speech/avatar 3 each: video takes backfill from its own queue
        self.assertEqual(len(picks["video"]), 7)
        self.assertEqual(picks["speech"], [])

    def test_unpicked_are_not_checked(self):
        sb = Sandbox()
        sb.setUp()
        try:
            sb.config["quota"]["per_category"] = 1
            sb.config["quota"]["recheck_per_category"] = 0
            run_id, _ = sb.run_refresh()
            collect.set_current(sb.root, run_id)
            brief = collect.build_brief(sb.root, run_id, "offline", {}, {})
            status = {c["id"]: c["status"] for c in brief["candidates"]}
            self.assertEqual(status["a/vid3"], "not_checked")
        finally:
            sb.tearDown()


class T4FailureKeepsData(Sandbox):
    def test_partial_keeps_raw_and_pointer(self):
        good, status = self.run_refresh()
        self.assertEqual(status, "complete")
        self.assertEqual(collect.publish(self.root, good, status), collect.EXIT_OK)
        bad, status = self.run_refresh(fail_repo="c/tts1", now=NOW + timedelta(hours=1))
        self.assertEqual(status, "partial")
        manifest = collect.read_json(os.path.join(self.root, "data", "runs", bad, "manifest.json"))
        ok = [r for r in manifest["requests"] if r["outcome"] == "ok"]
        self.assertTrue(ok and all(os.path.exists(os.path.join(self.root, "data", "runs", bad, r["raw_file"])) for r in ok))
        self.assertEqual(collect.publish(self.root, bad, status), collect.EXIT_PARTIAL)
        self.assertEqual(collect.current_run(self.root), good)

    def test_first_partial_adopted_with_gap(self):
        run_id, status = self.run_refresh(fail_repo="c/tts1")
        self.assertEqual(collect.publish(self.root, run_id, status), collect.EXIT_PARTIAL)
        self.assertEqual(collect.current_run(self.root), run_id)
        brief = collect.read_json(os.path.join(self.root, "data", "brief.json"))
        speech = next(c for c in brief["coverage"] if c["category"] == "speech")
        self.assertEqual(speech["check_failed"], 1)

    def test_failed_never_publishes(self):
        def down(url, headers, timeout):
            raise urllib.error.URLError("offline")
        run_id, status = collect.refresh(self.root, self.config, http_get=down, sleep=lambda s: None, now=NOW)
        self.assertEqual(status, "failed")
        self.assertEqual(collect.publish(self.root, run_id, status), collect.EXIT_FAILED)
        self.assertIsNone(collect.current_run(self.root))


class T4bReadme(Sandbox):
    def test_readme_404_is_checked_not_failed(self):
        base = fake_http()

        def get(url, headers, timeout):
            if url.endswith("/readme"):
                return 404, {}, b'{"message": "Not Found"}'
            return base(url, headers, timeout)
        run_id, status = collect.refresh(self.root, self.config, http_get=get, sleep=lambda s: None, now=NOW)
        self.assertEqual(status, "complete")
        brief = collect.build_brief(self.root, run_id, "offline", {}, {})
        self.assertEqual({c["id"]: c["status"] for c in brief["candidates"]}["a/vnew"], "checked_no_event")


class T5Offline(Sandbox):
    def test_rebuild_identical_and_missing_raw(self):
        run_id, _ = self.run_refresh()
        a = collect.build_brief(self.root, run_id, "offline", {}, {})
        b = collect.build_brief(self.root, run_id, "refresh", {}, {})
        for x in (a, b):
            x["meta"].pop("generated_at")
            x["meta"].pop("mode")
        self.assertEqual(a, b)
        self.assertEqual(a["meta"]["window_end"], collect.iso(NOW))
        os.remove(os.path.join(self.root, "data", "runs", run_id, "raw", "0001.json"))
        with self.assertRaises(collect.InputError):
            collect.build_brief(self.root, run_id, "offline", {}, {})


EVENT = {"event_id": "1", "tag": "v2.0", "source_sha256": "abc"}


class T6Annotation(unittest.TestCase):
    def ann(self, **kw):
        base = {"repo": "a/vid1", "event_id": "1", "tag": "v2.0", "source_sha256": "abc",
                "change": "旧解读", "review_status": "user_reviewed", "reviewed_at": "2026-10-02T00:00:00Z"}
        return {"items": [base | kw]}

    def test_match_states(self):
        self.assertEqual(match_annotation(self.ann(), "a/vid1", EVENT)["status"], "valid")
        changed = match_annotation(self.ann(source_sha256="zzz"), "a/vid1", EVENT)
        self.assertEqual(changed["status"], "needs_review")
        self.assertNotIn("change", changed)
        self.assertEqual(match_annotation({"items": []}, "a/vid1", EVENT)["status"], "missing")

    def test_reviewed_requires_timestamp(self):
        out = match_annotation(self.ann(reviewed_at=None), "a/vid1", EVENT)
        self.assertEqual(out["review_status"], "ai_draft")

    def test_observation_degrades(self):
        projects = [{"id": "a/vid1", "event": EVENT, "annotation": {"status": "needs_review"}}]
        obs = observations({"observations": [{"title": "t", "body": "b", "depends_on": [["a/vid1", "1"], ["b/img1", "4"]]}]}, projects)
        self.assertEqual(obs[0]["status"], "needs_review")
        self.assertNotIn("body", obs[0])


class T8EventChoice(unittest.TestCase):
    def test_formal_over_prerelease_and_draft_ignored(self):
        rels = [release(1, "v2.0", "2026-09-25T00:00:00Z"), release(2, "v2.1-rc", "2026-09-28T00:00:00Z", pre=True),
                release(3, "v3", "2026-09-29T00:00:00Z", draft=True), release(4, "v0", "2026-08-01T00:00:00Z")]
        events = collect.release_events(rels, START, NOW)
        self.assertEqual([e["tag"] for e in events], ["v2.1-rc", "v2.0"])
        self.assertEqual(collect.choose_event(events)["tag"], "v2.0")

    def test_prerelease_only_and_empty_notes(self):
        events = collect.release_events([release(2, "rc", "2026-09-28T00:00:00Z", pre=True),
                                         release(5, "v1", "2026-09-29T00:00:00Z", body="")], START, NOW)
        chosen = collect.choose_event(events)
        self.assertEqual((chosen["tag"], chosen["prerelease"]), ("rc", True))


if __name__ == "__main__":
    unittest.main()
