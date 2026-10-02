"""Compare this period's brief with the previous published snapshot.

The result is embedded in brief.json as `diff` and also written to data/diff.json. The dashboard uses it
to mark rows in the update list ("新增", "新版本") and to list projects that left this period.
"""

REASON_OUT_OF_WINDOW = "事件超出30天窗口"
REASON_NOT_SELECTED = "本期未通过精选条件"


def _event_brief(event):
    return {"event_id": event["event_id"], "tag": event.get("tag"), "type": event.get("type"),
            "published_at": event.get("published_at")}


def _project_status(project, previous_by_id):
    old = previous_by_id.get(project["id"])
    if old is None:
        return {"status": "new", "to": _event_brief(project["event"])}
    if old["event"]["event_id"] != project["event"]["event_id"]:
        return {"status": "version", "from": _event_brief(old["event"]), "to": _event_brief(project["event"])}
    return {"status": "same"}


def _removed(previous_projects, current_ids, window_start):
    rows = []
    for p in previous_projects:
        if p["id"] in current_ids:
            continue
        published = p["event"].get("published_at") or ""
        reason = REASON_OUT_OF_WINDOW if published and published < window_start else REASON_NOT_SELECTED
        rows.append({"id": p["id"], "name": p["name"], "tag": p["event"].get("tag"),
                     "published_at": published, "reason": reason})
    return rows


def compute_diff(previous, current):
    """previous may be None (first period). Returns a JSON-serialisable dict; inputs are not modified."""
    meta = current["meta"]
    if not previous:
        return {"from_run": None, "to_run": meta["run_id"], "has_previous": False, "projects": {},
                "removed": [], "pending_new": [],
                "summary": {"new": 0, "version": 0, "removed": 0, "pending_new": 0, "changed": 0}}
    previous_by_id = {p["id"]: p for p in previous.get("projects", [])}
    projects = {p["id"]: _project_status(p, previous_by_id) for p in current.get("projects", [])}
    removed = _removed(previous.get("projects", []), set(projects), meta["window_start"])
    previous_pending = {x["id"] for x in previous.get("pending", [])}
    pending_new = [x["name"] for x in current.get("pending", []) if x["id"] not in previous_pending]
    counts = {k: sum(1 for v in projects.values() if v["status"] == k) for k in ("new", "version")}
    summary = {"new": counts["new"], "version": counts["version"], "removed": len(removed),
               "pending_new": len(pending_new)}
    summary["changed"] = summary["new"] + summary["version"] + summary["removed"]
    return {"from_run": previous["meta"]["run_id"], "to_run": meta["run_id"], "has_previous": True,
            "projects": projects, "removed": removed, "pending_new": pending_new, "summary": summary}
