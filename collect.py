#!/usr/bin/env python3
"""AIGC Signal: fetch recent AIGC open-source events from GitHub and build a brief.

Usage:
  python3 collect.py --refresh                 fetch a new period, then build outputs
  python3 collect.py --offline [--run RUN_ID]  rebuild from saved raw responses only
  python3 collect.py --accept-partial RUN_ID   adopt a partial period as current
"""
import argparse
import base64
import http.client
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from brief import assemble
from diff import compute_diff
from render import render_data_js, render_report
from render_html import render_site_index

ROOT = os.path.dirname(os.path.abspath(__file__))
API = "https://api.github.com"
SCHEMA_VERSION = "1"
EXIT_OK, EXIT_PARTIAL, EXIT_FAILED, EXIT_CONFIG = 0, 1, 2, 3
STATUSES = ["qualified", "checked_no_event", "manually_excluded", "not_checked", "check_failed"]


class InputError(Exception):
    """Offline inputs missing or corrupted."""


# ---------- small utilities ----------

def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0)


def parse_ts(value):
    """Parse an ISO 8601 timestamp (Z or offset) into an aware UTC datetime."""
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def in_window(ts, start, end):
    return ts is not None and start <= ts < end


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def normalize_text(text):
    return (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()


def text_sha(text):
    return sha256_bytes(normalize_text(text).encode("utf-8"))


def atomic_write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp, path)


def write_json(path, obj):
    atomic_write(path, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def read_json(path, default=None):
    if not os.path.exists(path):
        if default is not None:
            return default
        raise InputError(f"缺少文件: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------- HTTP and raw storage ----------

def default_http_get(url, headers, timeout):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, {k.lower(): v for k, v in resp.headers.items()}, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in e.headers.items()}, e.read()


class Fetcher:
    """Issues GitHub requests, saves each success immediately, keeps an incremental manifest."""

    def __init__(self, run_dir, manifest, config, token=None, http_get=None, sleep=time.sleep):
        self.run_dir, self.manifest, self.config = run_dir, manifest, config
        self.http_get, self.sleep = http_get or default_http_get, sleep
        self.headers = {"Accept": "application/vnd.github+json", "User-Agent": "aigc-signal-brief"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
        self.count, self.retries, self.stopped = 0, 0, None

    def _record(self, **rec):
        rec["seq"] = len(self.manifest["requests"]) + 1
        rec.setdefault("fetched_at", iso(utc_now()))
        self.manifest["requests"].append(rec)
        write_json(os.path.join(self.run_dir, "manifest.json"), self.manifest)
        return rec

    def _save_raw(self, url, status, headers, body):
        name = f"raw/{len(self.manifest['requests']) + 1:04d}.json"
        payload = {"url": url, "fetched_at": iso(utc_now()), "http_status": status,
                   "rate_limit": {"remaining": headers.get("x-ratelimit-remaining"),
                                  "reset": headers.get("x-ratelimit-reset")},
                   "body": body}
        content = json.dumps(payload, ensure_ascii=False, indent=1)
        atomic_write(os.path.join(self.run_dir, name), content)
        return name, sha256_bytes(content.encode("utf-8"))

    def get(self, url, purpose, category=None, repo=None, kind=None):
        meta = {"purpose": purpose, "category": category, "repo": repo, "kind": kind, "url": url}
        if self.stopped or self.count >= self.config["quota"]["request_cap"]:
            self.stopped = self.stopped or "request_cap"
            self._record(**meta, http_status=None, outcome="skipped", error=self.stopped, attempts=0,
                         raw_file=None, raw_sha256=None)
            return None
        attempt = 0
        while True:
            attempt += 1
            self.count += 1
            status, headers, body, error = self._try(url)
            if status == 200:
                try:
                    data = json.loads(body.decode("utf-8"))
                except ValueError as e:
                    status, error = None, f"invalid json: {e}"
                else:
                    raw_file, digest = self._save_raw(url, status, headers, data)
                    self._record(**meta, http_status=200, outcome="ok", error=None, attempts=attempt,
                                 raw_file=raw_file, raw_sha256=digest)
                    return data
            if status == 404 and purpose == "readme":
                self._record(**meta, http_status=404, outcome="not_found", error=None, attempts=attempt,
                             raw_file=None, raw_sha256=None)
                return None
            if status in (403, 429) and (headers.get("x-ratelimit-remaining") == "0"
                                         or "retry-after" in headers):
                self.stopped = "rate_limited"
                self.manifest["rate_limit_reset"] = headers.get("x-ratelimit-reset")
                error = f"rate limited (reset={headers.get('x-ratelimit-reset')})"
            elif self._can_retry(status, attempt):
                self.retries += 1
                self.sleep(self.config["http"]["retry_wait_sec"])
                continue
            self._record(**meta, http_status=status, outcome="failed", attempts=attempt,
                         error=error or f"HTTP {status}", raw_file=None, raw_sha256=None)
            return None

    def _try(self, url):
        try:
            status, headers, body = self.http_get(url, self.headers, self.config["http"]["timeout_sec"])
            return status, headers, body, None
        except (urllib.error.URLError, OSError, TimeoutError, http.client.HTTPException) as e:
            return None, {}, b"", f"network error: {e}"

    def _can_retry(self, status, attempt):
        transient = status is None or status >= 500
        return (transient and attempt < 2 and self.retries < self.config["quota"]["retry_cap"]
                and self.count < self.config["quota"]["request_cap"])


# ---------- candidates and allocation (pure functions) ----------

def search_url(topic, kind, start_date, per_page):
    field = "pushed" if kind == "s1" else "created"
    q = f"topic:{topic} {field}:>={start_date} archived:false fork:false"
    return f"{API}/search/repositories?" + urllib.parse.urlencode(
        {"q": q, "sort": "stars", "order": "desc", "per_page": per_page})


def review_flag(item, keywords):
    """Hints for human review only. Whole-token match, so "wallpaper" does not hit "paper"."""
    text = f"{item.get('full_name', '')} {item.get('description') or ''}".lower()
    tokens = set(re.findall(r"[a-z0-9]+", text))
    hits = [k for k in keywords if k in tokens]
    if not (item.get("description") or "").strip():
        hits.append("empty_description")
    return hits


def build_candidates(search_hits, config):
    """search_hits: list of (category_key, kind, rank, item[, raw_file]). Returns dict repo_id -> candidate."""
    cat_index = {c["key"]: i for i, c in enumerate(config["categories"])}
    exclusions = {e["repo"].lower(): e for e in config["manual_exclusions"]}
    cands = {}
    for hit in search_hits:
        cat, kind, rank, item = hit[:4]
        rid = item["full_name"].lower()
        cand = cands.setdefault(rid, {
            "id": rid, "name": item["full_name"], "repo_url": item["html_url"],
            "description": item.get("description") or "", "stars_snapshot": item.get("stargazers_count"),
            "created_at": item.get("created_at"), "pushed_at": item.get("pushed_at"),
            "size": item.get("size", 0), "repo_numeric_id": item.get("id"),
            "license_spdx": (item.get("license") or {}).get("spdx_id"),
            "review_flag": review_flag(item, config["review_keywords"]),
            "description_sha256": text_sha(item.get("description")),
            "manually_excluded": False, "exclusion_lapsed": False, "hits": []})
        cand["hits"].append({"category": cat, "kind": kind, "rank": rank, "raw_file": hit[4] if len(hit) > 4 else None})
    for rid, cand in cands.items():
        rule = exclusions.get(rid)
        if rule:
            # An exclusion holds only while the repo still looks like the evidence it was based on.
            pinned = rule.get("description_sha256")
            cand["manually_excluded"] = not pinned or pinned == cand["description_sha256"]
            cand["exclusion_lapsed"] = not cand["manually_excluded"]
        best = min(cand["hits"], key=lambda h: (h["rank"], h["kind"] != "s1", cat_index[h["category"]]))
        cand["category"] = best["category"]
        cand["also_in"] = sorted({h["category"] for h in cand["hits"]} - {best["category"]},
                                 key=cat_index.get)
    return cands


def category_queue(cands, cat, s2_reserved=1):
    """Check order within a category: S1 unflagged, S2 unflagged, then flagged.

    Flags only lower the check order; flagged repos are still checked when slots remain.
    Returns (queue, ids of the top S2-only repos reserved for new projects)."""
    def rank(c, kind):
        ranks = [h["rank"] for h in c["hits"] if h["category"] == cat and h["kind"] == kind]
        return min(ranks) if ranks else None

    pool = [c for c in cands.values() if c["category"] == cat and not c["manually_excluded"]]
    a = sorted([c for c in pool if not c["review_flag"] and rank(c, "s1") is not None],
               key=lambda c: rank(c, "s1"))
    b = sorted([c for c in pool if not c["review_flag"] and rank(c, "s1") is None],
               key=lambda c: rank(c, "s2"))
    flagged = sorted([c for c in pool if c["review_flag"]],
                     key=lambda c: (rank(c, "s1") is None,
                                    rank(c, "s1") if rank(c, "s1") is not None else rank(c, "s2")))
    return a + b + flagged, [c["id"] for c in b[:s2_reserved]]


def allocate_main(cands, config):
    """Main round: per-category quota, S2 top reserved, deficits backfilled round-robin."""
    per = config["quota"]["per_category"]
    keys = [c["key"] for c in config["categories"]]
    queues, picks = {}, {}
    reserved = config["quota"].get("s2_reserved", 1)
    for key in keys:
        queue, s2_top = category_queue(cands, key, reserved)
        queues[key] = [c["id"] for c in queue]
        chosen = list(s2_top)[:per]
        chosen += [rid for rid in queues[key] if rid not in chosen][: per - len(chosen)]
        picks[key] = sorted(chosen, key=queues[key].index)
    deficit = sum(per - len(picks[k]) for k in keys)
    while deficit > 0:
        progressed = False
        for key in keys:
            rest = [rid for rid in queues[key] if rid not in picks[key]]
            if deficit > 0 and rest:
                picks[key].append(rest[0])
                deficit -= 1
                progressed = True
        if not progressed:
            break
    return picks, queues


# ---------- events and statuses ----------

def release_events(releases, start, end):
    events = []
    for r in releases or []:
        ts = parse_ts(r.get("published_at"))
        if r.get("draft") or not in_window(ts, start, end):
            continue
        body = normalize_text(r.get("body"))
        events.append({"event_id": str(r["id"]), "type": "prerelease" if r.get("prerelease") else "release",
                       "tag": r.get("tag_name"), "published_at": r.get("published_at"),
                       "url": r.get("html_url"), "prerelease": bool(r.get("prerelease")),
                       "source_text": body, "source_sha256": text_sha(body)})
    return sorted(events, key=lambda e: e["published_at"], reverse=True)


def created_event(cand, readme_text, start, end, min_chars):
    if not in_window(parse_ts(cand["created_at"]), start, end):
        return None
    # Keyword flags are review hints only; they never block recognising a new repository.
    ok = (cand["size"] > 0 and readme_text is not None and len(normalize_text(readme_text)) >= min_chars)
    if not ok:
        return None
    text = normalize_text(readme_text)
    return {"event_id": f"created:{cand['repo_numeric_id']}", "type": "created", "tag": None,
            "published_at": cand["created_at"], "url": cand["repo_url"], "prerelease": False,
            "source_text": text, "source_sha256": text_sha(text)}


def choose_event(events):
    """Latest formal release with notes, else latest prerelease with notes, else created."""
    with_notes = [e for e in events if e["type"] != "created" and e["source_text"]]
    formal = [e for e in with_notes if e["type"] == "release"]
    pre = [e for e in with_notes if e["type"] == "prerelease"]
    created = [e for e in events if e["type"] == "created"]
    for group in (formal, pre, created):
        if group:
            return group[0]
    return None


def decode_readme(body):
    try:
        return base64.b64decode(body.get("content", "")).decode("utf-8", errors="replace")
    except (ValueError, AttributeError, TypeError):
        return None


def assess(cand, checks, start, end, config):
    """Return (status, chosen_event, all_events, note) for a candidate."""
    if cand["manually_excluded"]:
        return "manually_excluded", None, [], "人工排除"
    rel, readme = checks.get(("releases", cand["id"])), checks.get(("readme", cand["id"]))
    if rel is None or rel["outcome"] == "skipped":
        return "not_checked", None, [], "超出检查名额或预算"
    if rel["outcome"] == "failed":
        return "check_failed", None, [], rel.get("error")
    events = release_events(rel["body"], start, end)
    new_repo = in_window(parse_ts(cand["created_at"]), start, end)
    readme_missing = new_repo and (readme is None or readme["outcome"] == "skipped")
    readme_text = decode_readme(readme["body"]) if readme and readme["outcome"] == "ok" else None
    created = created_event(cand, readme_text, start, end, config["thresholds"]["readme_min_chars"])
    if created:
        events.append(created)
    chosen = choose_event(events)
    if chosen:
        return "qualified", chosen, events, ""
    if new_repo and readme and readme["outcome"] == "failed":
        return "check_failed", None, events, "readme请求失败"
    if readme_missing:
        return "not_checked", None, events, "新建仓库的readme未获取（超出名额或预算）"
    note = "窗口内发布无说明" if events else "窗口内无正式发布、预发布或新建"
    return "checked_no_event", None, events, note


# ---------- fetching a new period ----------

def refresh(root, config, http_get=None, sleep=time.sleep, now=None, token=None):
    as_of = now or utc_now()
    start = as_of - timedelta(days=config["window_days"])
    run_id = as_of.strftime("%Y%m%dT%H%M%SZ")
    run_dir = os.path.join(root, "data", "runs", run_id)
    write_json(os.path.join(run_dir, "config_used.json"), config)
    manifest = {"schema_version": SCHEMA_VERSION, "run_id": run_id, "as_of": iso(as_of),
                "window_start": iso(start), "window_end": iso(as_of),
                "config_version": config["config_version"],
                "config_sha256": sha256_bytes(json.dumps(config, sort_keys=True).encode()),
                "run_status": "running", "started_at": iso(utc_now()), "finished_at": None,
                "requests": []}
    f = Fetcher(run_dir, manifest, config, token=token, http_get=http_get, sleep=sleep)
    hits = run_searches(f, config, start, token, sleep)
    cands = build_candidates(hits, config)
    picks, queues = allocate_main(cands, config)
    for key in queues:
        for rid in picks[key]:
            check_candidate(f, cands[rid], config, start)
    recheck(f, cands, picks, queues, config, start, as_of)
    manifest["run_status"] = run_status(manifest, f)
    manifest["http_calls"] = f.count
    manifest["stopped"] = f.stopped
    manifest["finished_at"] = iso(utc_now())
    write_json(os.path.join(run_dir, "manifest.json"), manifest)
    failed = [r for r in manifest["requests"] if r["outcome"] in ("failed", "skipped")]
    write_json(os.path.join(run_dir, "run_log.json"), {
        "run_id": run_id, "run_status": manifest["run_status"], "http_calls": f.count,
        "retries": f.retries, "stopped": f.stopped, "rate_limit_reset": manifest.get("rate_limit_reset"),
        "problems": [{"seq": r["seq"], "purpose": r["purpose"], "repo": r["repo"], "error": r["error"]} for r in failed]})
    return run_id, manifest["run_status"]


def run_searches(f, config, start, token, sleep):
    interval = config["search"]["interval_sec_with_token" if token else "interval_sec"]
    hits, first = [], True
    for cat in config["categories"]:
        for kind in ("s1", "s2"):
            if not first:
                sleep(interval)
            first = False
            per_page = config["search"][f"{kind}_per_page"]
            url = search_url(cat["topic"], kind, start.strftime("%Y-%m-%d"), per_page)
            data = f.get(url, "search", category=cat["key"], kind=kind)
            for rank, item in enumerate((data or {}).get("items", [])):
                hits.append((cat["key"], kind, rank, item))
    return hits


def check_candidate(f, cand, config, start):
    repo = cand["name"]
    per_page = config["search"].get("releases_per_page", 20)
    f.get(f"{API}/repos/{repo}/releases?per_page={per_page}", "releases", category=cand["category"], repo=cand["id"])
    new_repo = parse_ts(cand["created_at"]) is not None and parse_ts(cand["created_at"]) >= start
    readme_used = sum(1 for r in f.manifest["requests"] if r["purpose"] == "readme")
    if new_repo and readme_used < config["quota"]["readme_cap"]:
        f.get(f"{API}/repos/{repo}/readme", "readme", category=cand["category"], repo=cand["id"])


def recheck(f, cands, picks, queues, config, start, end):
    checks = checks_from_manifest(f.manifest, f.run_dir)
    for key, queue in queues.items():
        qualified = [rid for rid in picks[key]
                     if assess(cands[rid], checks, start, end, config)[0] == "qualified"]
        rest = [rid for rid in queue if rid not in picks[key]]
        if not qualified and rest:
            for rid in rest[: config["quota"]["recheck_per_category"]]:
                check_candidate(f, cands[rid], config, start)


def run_status(manifest, fetcher):
    reqs = manifest["requests"]
    searches_ok = [r for r in reqs if r["purpose"] == "search" and r["outcome"] == "ok"]
    if not searches_ok:
        return "failed"
    if any(r["outcome"] not in ("ok", "not_found") for r in reqs) or fetcher.stopped:
        return "partial"
    return "complete"


# ---------- building outputs from a saved period ----------

def load_run(root, run_id):
    run_dir = os.path.join(root, "data", "runs", run_id)
    manifest = read_json(os.path.join(run_dir, "manifest.json"))
    config = read_json(os.path.join(run_dir, "config_used.json"))
    problems = []
    for rec in manifest["requests"]:
        if rec["outcome"] != "ok":
            continue
        path = os.path.join(run_dir, rec["raw_file"])
        if not os.path.exists(path):
            problems.append(f"缺少原始响应 {rec['raw_file']}")
            continue
        with open(path, "rb") as fh:
            if sha256_bytes(fh.read()) != rec["raw_sha256"]:
                problems.append(f"校验值不符 {rec['raw_file']}")
    if problems:
        raise InputError("; ".join(problems))
    return run_dir, manifest, config


def checks_from_manifest(manifest, run_dir):
    checks = {}
    for rec in manifest["requests"]:
        if rec["purpose"] in ("releases", "readme"):
            entry = dict(rec)
            if rec["outcome"] == "ok":
                entry["body"] = read_json(os.path.join(run_dir, rec["raw_file"]))["body"]
            checks[(rec["purpose"], rec["repo"])] = entry
    return checks


def search_hits_from_manifest(manifest, run_dir):
    hits = []
    for rec in manifest["requests"]:
        if rec["purpose"] == "search" and rec["outcome"] == "ok":
            body = read_json(os.path.join(run_dir, rec["raw_file"]))["body"]
            hits += [(rec["category"], rec["kind"], i, item, rec["raw_file"])
                     for i, item in enumerate(body.get("items", []))]
    return hits


def search_scope(manifest, run_dir):
    """One row per search request: how many repos GitHub matched versus how many we received."""
    rows = []
    for rec in manifest["requests"]:
        if rec["purpose"] != "search":
            continue
        query = urllib.parse.parse_qs(urllib.parse.urlparse(rec["url"]).query)
        row = {"category": rec["category"], "kind": rec["kind"], "query": query.get("q", [""])[0],
               "sort": query.get("sort", [""])[0], "outcome": rec["outcome"], "total_count": None,
               "returned": 0, "incomplete_results": None, "raw_file": rec.get("raw_file")}
        if rec["outcome"] == "ok":
            body = read_json(os.path.join(run_dir, rec["raw_file"]))["body"]
            row.update(total_count=body.get("total_count"), returned=len(body.get("items", [])),
                       incomplete_results=body.get("incomplete_results"))
        row["truncated"] = row["total_count"] is not None and row["total_count"] > row["returned"]
        rows.append(row)
    return rows


def releases_truncated(check, start):
    """True when the releases page was full and even its oldest entry is inside the window."""
    if not check or check.get("outcome") != "ok":
        return False
    query = urllib.parse.parse_qs(urllib.parse.urlparse(check["url"]).query)
    per_page = int(query.get("per_page", ["30"])[0])
    body = check["body"] or []
    dates = [parse_ts(r.get("published_at") or r.get("created_at")) for r in body]
    dates = [d for d in dates if d is not None]
    return len(body) >= per_page and bool(dates) and min(dates) >= start


def build_brief(root, run_id, mode, selection, annotations, context=None, previous=None):
    run_dir, manifest, config = load_run(root, run_id)
    start, end = parse_ts(manifest["window_start"]), parse_ts(manifest["window_end"])
    cands = build_candidates(search_hits_from_manifest(manifest, run_dir), config)
    checks = checks_from_manifest(manifest, run_dir)
    reserved = config["quota"].get("s2_reserved", 1)
    queues = {c["key"]: [x["id"] for x in category_queue(cands, c["key"], reserved)[0]] for c in config["categories"]}
    assessed = {}
    for rid, cand in cands.items():
        status, chosen, events, note = assess(cand, checks, start, end, config)
        rank = queues[cand["category"]].index(rid) if rid in queues[cand["category"]] else None
        raw = {p: checks[(p, rid)].get("raw_file") for p in ("releases", "readme") if (p, rid) in checks}
        raw["search"] = min(cand["hits"], key=lambda h: h["rank"])["raw_file"]
        raw = {k: f"data/runs/{run_id}/{v}" if v else None for k, v in raw.items()}
        assessed[rid] = {"status": status, "chosen": chosen, "events": events, "note": note, "check_rank": rank,
                         "releases_truncated": releases_truncated(checks.get(("releases", rid)), start), "raw": raw}
    scope = {"searches": search_scope(manifest, run_dir), "raw_dir": f"data/runs/{run_id}/raw"}
    return assemble(manifest, config, cands, assessed, selection, annotations, mode, iso(utc_now()),
                    context=context or {}, scope=scope, previous=previous)


def load_inputs(root):
    return (read_json(os.path.join(root, "selection.json"), default={"decisions": []}),
            read_json(os.path.join(root, "annotations.json"), default={"items": [], "observations": []}),
            read_json(os.path.join(root, "context.json"), default={}))


def snapshot_dir(root, run_id):
    return os.path.join(root, "data", "runs", run_id, "snapshot")


def load_snapshot(root, run_id):
    """Brief of an earlier published period, or None. Used only to list what left the current period."""
    if not run_id:
        return None
    path = os.path.join(snapshot_dir(root, run_id), "brief.json")
    return read_json(path) if os.path.exists(path) else None


def write_all(files):
    """Write every output to a temp file first, then swap them in, so a failure leaves old outputs intact."""
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path + ".tmp", "w", encoding="utf-8") as fh:
            fh.write(content)
    for path in files:
        os.replace(path + ".tmp", path)


def build_outputs(root, run_id, mode, out_dir=None, previous_run=None):
    selection, annotations, context = load_inputs(root)
    previous = load_snapshot(root, previous_run) if previous_run and previous_run != run_id else None
    brief = build_brief(root, run_id, mode, selection, annotations, context, previous)
    brief = {**brief, "diff": compute_diff(previous, brief)}
    report = render_report(brief)
    brief_text = json.dumps(brief, ensure_ascii=False, indent=2) + "\n"
    if out_dir:
        write_all({os.path.join(out_dir, "brief.json"): brief_text, os.path.join(out_dir, "report.md"): report})
        return brief
    snap = snapshot_dir(root, run_id)
    write_all({os.path.join(root, "data", "brief.json"): brief_text,
               os.path.join(root, "report.md"): report,
               os.path.join(root, "site", "data.js"): render_data_js(brief, report),
               os.path.join(root, "site", "index.html"): render_site_index(brief),
               os.path.join(root, "data", "diff.json"): json.dumps(brief["diff"], ensure_ascii=False, indent=2) + "\n",
               os.path.join(snap, "brief.json"): brief_text,
               os.path.join(snap, "report.md"): report})
    return brief


def current_pointer(root):
    return read_json(os.path.join(root, "data", "current.json"), default={})


def current_run(root):
    return current_pointer(root).get("run_id")


def set_current(root, run_id, previous_run=None):
    write_json(os.path.join(root, "data", "current.json"), {"run_id": run_id, "previous_run_id": previous_run})


# ---------- command line ----------

def publish(root, run_id, status):
    """Apply the current-period pointer rules and build outputs. Returns an exit code."""
    previous = current_run(root)
    if status == "failed":
        print("没有任何搜索成功，未生成输出；已有快照保持不变。详见 manifest.json", file=sys.stderr)
        return EXIT_FAILED
    if status == "partial" and previous:
        print(f"部分结果，未替换当前快照 {previous}。确认采用请运行 --accept-partial {run_id}")
        return EXIT_PARTIAL
    build_outputs(root, run_id, "refresh", previous_run=previous)
    set_current(root, run_id, previous)
    print(f"已生成 report.md、data/brief.json、site/（当前期 {run_id}；上一期快照 {previous or '无'} 保留）")
    return EXIT_OK if status == "complete" else EXIT_PARTIAL


def cmd_refresh(root):
    config = read_json(os.path.join(root, "config.json"))
    run_id, status = refresh(root, config, token=os.environ.get("GITHUB_TOKEN"))
    print(f"run {run_id}: {status}")
    return publish(root, run_id, status)


def cmd_offline(root, run_id):
    target = run_id or current_run(root)
    if not target:
        print("没有当前期，请先运行 --refresh", file=sys.stderr)
        return EXIT_FAILED
    pointer = current_pointer(root)
    out_dir = None
    if run_id and run_id != pointer.get("run_id"):
        out_dir = os.path.join(root, "data", "runs", run_id, "rebuild")
    build_outputs(root, target, "offline", out_dir, previous_run=pointer.get("previous_run_id"))
    print(f"离线重建完成：{target}" + (f"（输出到 {out_dir}）" if out_dir else ""))
    return EXIT_OK


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--refresh", action="store_true")
    g.add_argument("--offline", action="store_true")
    g.add_argument("--accept-partial", metavar="RUN_ID")
    p.add_argument("--run", metavar="RUN_ID")
    args = p.parse_args(argv)
    try:
        if args.refresh:
            return cmd_refresh(ROOT)
        if args.offline:
            return cmd_offline(ROOT, args.run)
        _, manifest, _ = load_run(ROOT, args.accept_partial)
        if manifest["run_status"] != "partial":
            print(f"只能采用partial期，该期状态为 {manifest['run_status']}", file=sys.stderr)
            return EXIT_CONFIG
        previous = current_run(ROOT)
        build_outputs(ROOT, args.accept_partial, "offline", previous_run=previous)
        set_current(ROOT, args.accept_partial, previous)
        print(f"已采用 {args.accept_partial} 为当前期")
        return EXIT_OK
    except InputError as e:
        print(f"离线输入缺失或损坏: {e}", file=sys.stderr)
        return EXIT_FAILED
    except (KeyError, ValueError) as e:
        print(f"配置或数据格式错误: {e}", file=sys.stderr)
        return EXIT_CONFIG


if __name__ == "__main__":
    sys.exit(main())
