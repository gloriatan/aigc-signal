"""Editorial layer: turn a ledger of human/AI review decisions into this period's shortlist.

A repo with an in-window event is only "qualified" (an automatic state). It reaches the formal
shortlist only through a matching `select` decision whose checks all pass. Everything else with
an event goes to the pending-review list, with the reason. Decisions are keyed by repo + event +
source hash, not by run id, so a valid judgement survives a new period and a stale one does not.
"""

REQUIRED_CHECKS = ("aigc_relevant", "substantive_change", "source_ok")


def _repo(d):
    return (d.get("repo") or "").lower()


def _event_label(event):
    return event.get("tag") or event["event_id"]


def _select_problem(decision, event):
    """Why a select decision cannot be used for this event, or None when it is usable."""
    if event is None:
        return f"已核查的事件 {decision.get('tag') or decision.get('event_id')} 不在本期窗口内"
    if decision.get("source_sha256") and decision["source_sha256"] != event["source_sha256"]:
        return f"{_event_label(event)} 的来源说明已变化，原核查不再适用"
    checks = decision.get("checks") or {}
    missing = [k for k in REQUIRED_CHECKS if checks.get(k) is not True]
    if missing:
        return "核查未全部通过：" + "、".join(missing)
    if not decision.get("reason"):
        return "缺少入选理由"
    return None


def _exclusion_for(decisions, cand, chosen):
    """Return (exclusion, note). note explains an exclusion that no longer applies."""
    notes = []
    for d in decisions:
        if d.get("scope") == "repo":
            pinned = (d.get("fingerprint") or {}).get("description_sha256")
            if pinned and pinned != cand["description_sha256"]:
                notes.append("此前按仓库整体排除，但仓库描述已变化，需重新核查")
                continue
            return d, None
        if d.get("scope") == "event":
            if chosen and str(d.get("event_id")) == chosen["event_id"]:
                if d.get("source_sha256") and d["source_sha256"] != chosen["source_sha256"]:
                    notes.append(f"此前排除的 {_event_label(chosen)} 来源说明已变化，需重新核查")
                    continue
                return d, None
            notes.append(f"此前排除的是 {d.get('tag') or d.get('event_id')}，本期最新事件 "
                         f"{_event_label(chosen) if chosen else '未知'} 尚未核查")
    return None, "；".join(notes) or None


def decide(cands, assessed, ledger, max_items):
    """Split qualified repos into selected / pending / excluded. Pure function."""
    decisions = ledger.get("decisions", [])
    selects, excludes = {}, {}
    for d in decisions:
        target = selects if d.get("decision") == "select" else excludes if d.get("decision") == "exclude" else None
        if target is not None:
            target.setdefault(_repo(d), []).append(d)

    order = [_repo(d) for d in decisions if d.get("decision") == "select"]
    qualified = [rid for rid, a in assessed.items() if a["status"] == "qualified"]
    qualified.sort(key=lambda rid: (order.index(rid) if rid in order else len(order),
                                    cands[rid]["category"], assessed[rid]["check_rank"] or 0))
    selected, pending, excluded = [], [], []
    for rid in qualified:
        a = assessed[rid]
        events = {e["event_id"]: e for e in a["events"]}
        problems, pick = [], None
        for d in selects.get(rid, []):
            event = events.get(str(d.get("event_id")))
            problem = _select_problem(d, event)
            if problem:
                problems.append(problem)
            elif pick is None or event["published_at"] > pick[1]["published_at"]:
                pick = (d, event)
        if pick and len(selected) >= max_items:
            problems.append(f"超过本期 {max_items} 项上限")
            pick = None
        if pick:
            d, event = pick
            reviewed = {str(x.get("event_id")) for x in selects.get(rid, []) + excludes.get(rid, [])}
            newer = [e for e in a["events"] if e["published_at"] > event["published_at"]
                     and e["event_id"] not in reviewed]
            selected.append({"id": rid, "event": event, "decision": d, "newer_unreviewed": newer})
            continue
        exclusion, lapse_note = _exclusion_for(excludes.get(rid, []), cands[rid], a["chosen"])
        if exclusion:
            excluded.append({"id": rid, "event": a["chosen"], "decision": exclusion})
            continue
        reasons = problems + ([lapse_note] if lapse_note else [])
        pending.append({"id": rid, "event": a["chosen"],
                        "reasons": reasons or ["尚无核查记录：窗口内有事件不等于值得推荐，需人工核查"]})

    dropped = []
    for rid, ds in selects.items():
        if rid in {s["id"] for s in selected} or rid in {p["id"] for p in pending}:
            continue
        status = assessed.get(rid, {}).get("status")
        why = {None: "本期检索结果中未出现该仓库", "checked_no_event": "本期检查后窗口内无合格事件",
               "not_checked": "本期未检查（超出名额或预算）", "check_failed": "本期检查请求失败",
               "manually_excluded": "本期被人工排除"}.get(status, "本期不符合精选条件")
        for d in ds:
            dropped.append({"id": rid, "tag": d.get("tag"), "event_id": str(d.get("event_id")), "reason": why})
    return {"selected": selected, "pending": pending, "excluded": excluded, "dropped": dropped}
