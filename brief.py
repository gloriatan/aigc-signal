"""Assemble brief.json from assessed candidates, the editorial ledger, annotations and context."""
import re

from editorial import decide

LICENSE_CLASSES = {
    "permissive": ({"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "Unlicense", "0BSD"},
                   "宽松许可：可商用，需保留版权与许可声明"),
    "network_copyleft": ({"AGPL-3.0"},
                         "AGPL-3.0：可商用；修改后以网络服务提供时需按AGPL公开对应源码，不等于禁止商用"),
    "copyleft": ({"GPL-2.0", "GPL-3.0", "LGPL-2.1", "LGPL-3.0", "MPL-2.0"},
                 "copyleft许可：可商用；分发衍生作品需按同许可开源（LGPL/MPL范围较窄）"),
    "noncommercial": ({"CC-BY-NC-4.0", "CC-BY-NC-SA-4.0"}, "非商用许可：禁止商用，需另行授权"),
}
UNKNOWN_NOTE = "许可待核实（GitHub未识别或未声明），不得视为可商用"
WEIGHTS_NOTE = "模型权重与服务条款未核查"
STATUSES = ["qualified", "checked_no_event", "manually_excluded", "not_checked", "check_failed"]
ANNOTATION_FIELDS = ["purpose", "scene", "update_title", "key_change", "useful_for", "key_limits", "facts",
                     "change_type", "change", "target_task", "hypothesis", "team_value", "tech",
                     "experiment", "limitations"]
CONTEXT_PAD = 140


def license_info(spdx):
    for cls, (ids, note) in LICENSE_CLASSES.items():
        if spdx in ids:
            return {"spdx_id": spdx, "class": cls, "adoption_note": f"{note}。{WEIGHTS_NOTE}"}
    return {"spdx_id": spdx, "class": "unknown", "adoption_note": f"{UNKNOWN_NOTE}。{WEIGHTS_NOTE}"}


def clean_excerpt(text, limit):
    """Plain-text excerpt: drop HTML tags, markdown images and link targets."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    return text[:limit]


def collapse(text):
    return re.sub(r"\s+", " ", text or "").strip()


def public_event(event, th):
    if not event:
        return None
    text = event["source_text"]
    plain = len(re.sub(r"\s+", "", re.sub(r"https?://\S+", "", text)))
    return {k: event[k] for k in ("event_id", "type", "tag", "published_at", "url", "prerelease", "source_sha256")} | {
        "excerpt": clean_excerpt(text, th["excerpt_chars"]),
        "short_notes": event["type"] != "created" and plain < th["short_notes_chars"]}


# ---------- statistics ----------

def coverage(manifest, config, cands, assessed):
    rows = []
    for cat in config["categories"]:
        search = {r["kind"]: r["outcome"] for r in manifest["requests"]
                  if r["purpose"] == "search" and r["category"] == cat["key"]}
        row = {"category": cat["key"], "label": cat["label"],
               "search_status": {"s1": search.get("s1", "missing"), "s2": search.get("s2", "missing")},
               "candidates": 0} | {s: 0 for s in STATUSES}
        for rid, cand in cands.items():
            if cand["category"] == cat["key"]:
                row["candidates"] += 1
                row[assessed[rid]["status"]] += 1
        row["search_failed"] = any(v != "ok" for v in row["search_status"].values())
        rows.append(row)
    return rows


def category_gaps(coverage_rows, projects, layers, cands):
    """One sentence per search category that has no selected project, built from the counts."""
    picked = {p["category"] for p in projects}
    gaps = []
    for row in coverage_rows:
        if row["category"] in picked:
            continue
        cat = row["category"]
        pending = sum(1 for x in layers["pending"] if cands[x["id"]]["category"] == cat)
        excluded = sum(1 for x in layers["excluded"] if cands[x["id"]]["category"] == cat)
        checked = row["qualified"] + row["checked_no_event"] + row["check_failed"]
        parts = [f"检查{checked}个", f"{row['checked_no_event']}个窗口内无正式发布、预发布或新建"]
        if pending:
            parts.append(f"{pending}个有事件但待核查")
        if excluded:
            parts.append(f"{excluded}个有事件但经核查排除")
        if row["check_failed"]:
            parts.append(f"{row['check_failed']}个检查失败")
        related = [p["name"] for p in projects if cat in p["capabilities"]]
        text = f"检索分类“{row['label']}”下本期无正式精选：" + "，".join(parts) + f"，另有{row['not_checked']}个未检查。"
        text += (f"按能力标签，有{len(related)}个精选项目涉及{row['label']}：{'、'.join(related)}。" if related
                 else f"按能力标签，本期也没有精选项目涉及{row['label']}。")
        gaps.append({"category": cat, "label": row["label"], "related": related, "text": text})
    return gaps


# ---------- annotations and evidence ----------

def locate(quote, text):
    """Find a quote in the source (whitespace-insensitive). Returns surrounding context or None."""
    hay, needle = collapse(text), collapse(quote)
    i = hay.find(needle) if needle else -1
    if i < 0:
        return None
    a, b = max(0, i - CONTEXT_PAD), min(len(hay), i + len(needle) + CONTEXT_PAD)
    return {"before": ("…" if a > 0 else "") + hay[a:i],
            "after": hay[i + len(needle):b] + ("…" if b < len(hay) else "")}


def resolve_evidence(items, sources):
    """Attach context and raw-file pointers to each quote. Returns (resolved, missing_ids)."""
    resolved, missing = [], []
    for ev in items or []:
        field = ev.get("field", "source_text")
        src = sources.get(field)
        found = locate(ev.get("quote"), src["text"]) if src else None
        if not found:
            missing.append(ev.get("id"))
            continue
        resolved.append({"id": ev["id"], "quote": collapse(ev["quote"]), "field": field,
                         "field_label": src["label"], "url": src["url"], "raw_file": src["raw_file"]} | found)
    return resolved, missing


def match_annotation(annotations, rid, event, sources=None):
    """Annotation bound to repo + event + tag + source hash, with every quoted fact still present."""
    items = [a for a in annotations.get("items", [])
             if (a.get("repo") or "").lower() == rid and str(a.get("event_id")) == event["event_id"]]
    if not items:
        return {"status": "missing", "reason": "本事件尚无对应解读，以下只列原文事实与来源，待分析"}
    a = items[0]
    if a.get("tag") != event["tag"] or a.get("source_sha256") != event["source_sha256"]:
        return {"status": "needs_review", "reason": "来源说明已变化，旧解读不再展示，待重新分析"}
    evidence, missing = resolve_evidence(a.get("evidence"), sources or {})
    if missing:
        return {"status": "needs_review", "reason": "解读引用的原文在当前来源中找不到：" + "、".join(map(str, missing))}
    out = {"status": "valid", "review_status": a.get("review_status", "ai_draft"),
           "reviewed_at": a.get("reviewed_at"), "evidence": evidence}
    if out["review_status"] == "user_reviewed" and not out["reviewed_at"]:
        out["review_status"] = "ai_draft"
    return out | {k: a.get(k) for k in ANNOTATION_FIELDS}


def event_sources(cand, event, raw):
    raw_event = raw.get("readme") if event["type"] == "created" else raw.get("releases")
    return {"source_text": {"text": event["source_text"], "url": event["url"], "raw_file": raw_event,
                            "label": "README" if event["type"] == "created" else "版本说明"},
            "description": {"text": cand["description"], "url": cand["repo_url"], "raw_file": raw.get("search"),
                            "label": "仓库简介"}}


def capabilities(decision, cand, config):
    """Editor-tagged capability labels for this event; falls back to the search category."""
    keys = [c["key"] for c in config["categories"]]
    tags = [t for t in (decision.get("capabilities") or []) if t in keys]
    return tags or [cand["category"]]


def make_project(entry, cands, assessed, annotations, config):
    rid, event, decision = entry["id"], entry["event"], entry["decision"]
    cand, th, a = cands[rid], config["thresholds"], assessed[rid]
    sources = event_sources(cand, event, a["raw"])
    return {"id": rid, "name": cand["name"], "repo_url": cand["repo_url"], "category": cand["category"],
            "also_in": cand["also_in"], "description": cand["description"],
            "stars_snapshot": cand["stars_snapshot"], "license": license_info(cand["license_spdx"]),
            "event": public_event(event, th) | {"raw_file": sources["source_text"]["raw_file"]},
            "other_events": [public_event(e, th) for e in a["events"] if e["event_id"] != event["event_id"]],
            "newer_unreviewed": [public_event(e, th) for e in entry["newer_unreviewed"]],
            "releases_truncated": a["releases_truncated"],
            "selection_reason": decision.get("reason"), "decided_by": decision.get("decided_by"),
            "decided_in_run": decision.get("decided_in_run"), "checks": decision.get("checks"),
            "capabilities": capabilities(decision, cand, config),
            "annotation": match_annotation(annotations, rid, event, sources)}


def bound(entry, valid_keys, background_ids, body_fields):
    """Analysis that depends on projects/background: valid only while every dependency is valid."""
    deps = [(d[0].lower(), str(d[1])) for d in entry.get("depends_on", [])]
    bg = entry.get("background", [])
    ok = bool(deps or bg) and all(d in valid_keys for d in deps) and all(b in background_ids for b in bg)
    out = {"title": entry.get("title"), "kind": entry.get("kind"), "depends_on": [list(d) for d in deps],
           "background": bg, "status": "valid" if ok else "needs_review",
           "review_status": entry.get("review_status", "ai_draft") if ok else None}
    if ok:
        out |= {k: entry.get(k) for k in body_fields if k in entry}
    return out


def observations(annotations, projects, background_ids=()):
    valid_keys = {(p["id"], p["event"]["event_id"]) for p in projects if p["annotation"]["status"] == "valid"}
    out = []
    for o in annotations.get("observations", []):
        entry = bound(o, valid_keys, set(background_ids), ["body"])
        entry["scope"] = "单项目观察" if len(entry["depends_on"]) == 1 else "跨项目信号"
        out.append(entry)
    return out


def analysis(annotations, context, projects):
    """Period judgment and team plan, each degraded to needs_review when its evidence lapses."""
    valid_keys = {(p["id"], p["event"]["event_id"]) for p in projects if p["annotation"]["status"] == "valid"}
    bg_ids = {b["id"] for b in context.get("background", [])}
    judgment = annotations.get("period_judgment")
    plan = annotations.get("team_plan", {})
    plan_fields = ["short", "why", "target_users", "hypothesis", "control", "variable", "controls",
                   "primary_metric", "quality_cost", "roles", "prerequisites", "sample", "decision",
                   "limits", "condition", "reason", "mode"]
    return {
        "period_judgment": bound(judgment, valid_keys, bg_ids, ["text"]) if judgment else None,
        "team_plan": {k: [bound(x, valid_keys, bg_ids, plan_fields) for x in plan.get(k, [])]
                      for k in ("priority", "conditional", "deferred")},
        "priority_basis": plan.get("priority_basis"),
    }


# ---------- lists for the reader ----------

def candidate_rows(cands, assessed):
    rows = []
    for rid, c in sorted(cands.items(), key=lambda kv: (kv[1]["category"], assessed[kv[0]]["check_rank"] or 0)):
        a = assessed[rid]
        rows.append({"id": rid, "name": c["name"], "repo_url": c["repo_url"], "category": c["category"],
                     "also_in": c["also_in"], "hits": c["hits"], "review_flag": c["review_flag"],
                     "status": a["status"], "note": a["note"], "stars_snapshot": c["stars_snapshot"],
                     "created_at": c["created_at"], "exclusion_lapsed": c.get("exclusion_lapsed", False),
                     "releases_truncated": a["releases_truncated"],
                     "license": license_info(c["license_spdx"]), "description": c["description"]})
    return rows


def layer_rows(rows, cands, th, extra):
    out = []
    for x in rows:
        c = cands[x["id"]]
        out.append({"id": x["id"], "name": c["name"], "repo_url": c["repo_url"], "category": c["category"],
                    "description": c["description"], "stars_snapshot": c["stars_snapshot"],
                    "review_flag": c["review_flag"], "event": public_event(x["event"], th)} | extra(x))
    return out


def changes_since(previous, projects, window_start):
    if not previous:
        return None
    now_ids = {p["id"] for p in projects}
    removed = []
    for p in previous.get("projects", []):
        if p["id"] in now_ids:
            continue
        date = p["event"]["published_at"]
        why = (f"事件日期 {date[:10]} 已早于本期窗口起点 {window_start[:10]}" if date < window_start
               else "本期未通过精选条件（见待核查、排除或不再适用的核查记录）")
        removed.append({"id": p["id"], "name": p["name"], "tag": p["event"]["tag"], "reason": why})
    prev_ids = {p["id"] for p in previous.get("projects", [])}
    return {"previous_run_id": previous["meta"]["run_id"], "removed": removed,
            "added": [p["name"] for p in projects if p["id"] not in prev_ids]}


def assemble(manifest, config, cands, assessed, selection, annotations, mode, generated_at,
             context=None, scope=None, previous=None):
    context, th = context or {}, config["thresholds"]
    layers = decide(cands, assessed, selection, th["shortlist_max"])
    projects = [make_project(x, cands, assessed, annotations, config) for x in layers["selected"]]
    errors = [{"seq": r["seq"], "purpose": r["purpose"], "repo": r["repo"], "category": r["category"],
               "error": r["error"]} for r in manifest["requests"] if r["outcome"] != "ok"]
    cov = coverage(manifest, config, cands, assessed)
    bg = context.get("background", [])
    return {
        "meta": {"schema_version": manifest["schema_version"], "run_id": manifest["run_id"],
                 "as_of": manifest["as_of"], "window_start": manifest["window_start"],
                 "window_end": manifest["window_end"], "generated_at": generated_at, "mode": mode,
                 "run_status": manifest["run_status"], "config_version": manifest["config_version"],
                 "request_count": manifest.get("http_calls", sum(r.get("attempts", 1) for r in manifest["requests"]
                                                                 if r["outcome"] != "skipped")),
                 "selection_status": "editorial", "errors": errors,
                 "background_accessed_at": sorted({b.get("accessed_at") for b in bg if b.get("accessed_at")}),
                 "categories": [{"key": c["key"], "label": c["label"], "topic": c["topic"]}
                                for c in config["categories"]],
                 "quota": config["quota"], "thresholds": th, "search_config": config["search"]},
        "coverage": cov,
        "scope": scope or {},
        "category_gaps": category_gaps(cov, projects, layers, cands),
        "candidates": candidate_rows(cands, assessed),
        "manual_exclusions": [e | {"lapsed": cands.get(e["repo"].lower(), {}).get("exclusion_lapsed", False)}
                              for e in config["manual_exclusions"]],
        "projects": projects,
        "pending": layer_rows(layers["pending"], cands, th, lambda x: {"reasons": x["reasons"]}),
        "excluded": layer_rows(layers["excluded"], cands, th, lambda x: {
            "scope": x["decision"].get("scope"), "reason_code": x["decision"].get("reason_code"),
            "reason": x["decision"].get("reason"), "evidence_url": x["decision"].get("evidence_url"),
            "decided_in_run": x["decision"].get("decided_in_run")}),
        "dropped_decisions": layers["dropped"],
        "changes_since_previous": changes_since(previous, projects, manifest["window_start"]),
        "observations": observations(annotations, projects, [b["id"] for b in bg]),
        "background": bg,
    } | analysis(annotations, context, projects)
