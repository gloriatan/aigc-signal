"""Render brief.json into Markdown and the site's embedded data file.

Reading order (shared with render_html.py's no-script fallback):
title + one-line judgment -> update index (with sorting rationale) -> projects
(default layer: change / audience / boundaries; secondary layers in <details>)
-> cross-project signals -> one action recommendation (parameters in <details>)
-> pending/changes/exclusions -> background (<details>) -> data & method.
"""
import json

TYPE_LABEL = {"release": "正式发布", "prerelease": "预发布", "created": "窗口内新建仓库"}
STATUS_LABEL = {"qualified": "窗口内有事件", "checked_no_event": "检查后无合格事件",
                "manually_excluded": "人工排除", "not_checked": "未检查（超出名额或预算）",
                "check_failed": "检查请求失败"}
REVIEW_LABEL = {"ai_draft": "AI草稿，未经本人审阅", "user_reviewed": "已经本人审阅"}
KIND_LABEL = {"s1": "近期有推送（按Stars）", "s2": "窗口内新建（按Stars）"}
SOURCE_TYPE = {"official": "官方", "third_party": "第三方辅助线索"}
NETWORK_NOTE = ("本简报是截至抓取时间的数据快照，可离线查看。刷新数据和打开原始来源需要能访问GitHub。"
                "刷新失败时保留原快照，原快照时间不会更新。本期只覆盖所列四个topic的检索结果，不代表全部开源动态。")


def label_of(brief, key):
    return next((c["label"] for c in brief["meta"]["categories"] if c["key"] == key), key)


def caps(brief, p):
    return "、".join(label_of(brief, c) for c in p.get("capabilities") or [])


def event_line(e):
    tag = f" {e['tag']}" if e["tag"] else ""
    return f"{TYPE_LABEL[e['type']]}{tag}，{e['published_at'][:10]}"


def project_title(p):
    a = p["annotation"]
    if a["status"] == "valid" and a.get("update_title"):
        return a["update_title"]
    return f"待分析：{p['name']} {event_line(p['event'])}"


def background_map(brief):
    return {b["id"]: b for b in brief.get("background", [])}


def refs(item, brief):
    parts = [f"依据 {x}" for x in item.get("evidence", [])]
    bmap = background_map(brief)
    parts += [f"背景：{bmap[b]['title']}" for b in item.get("background", []) if b in bmap]
    return f"（{'；'.join(parts)}）" if parts else ""


def details(summary, body_lines):
    """A secondary layer rendered as a collapsed disclosure in Markdown."""
    return ["<details>", f"<summary>{summary}</summary>", ""] + body_lines + ["", "</details>", ""]


def dates_lines(brief):
    m = brief["meta"]
    events = sorted(p["event"]["published_at"][:10] for p in brief["projects"])
    lines = [f"- 事件窗口：{m['window_start']} 至 {m['window_end']}（UTC，含起点不含尾）",
             f"- 精选事件日期：{events[0]} 至 {events[-1]}" if events else "- 精选事件日期：本期无",
             f"- 数据抓取时间：{m['as_of']}（期次 {m['run_id']}，状态 {m['run_status']}）",
             f"- 报告生成时间：{m['generated_at']}（{'离线重建' if m['mode'] == 'offline' else '联网刷新'}）"]
    if m.get("background_accessed_at"):
        lines.append(f"- 商业背景资料查阅日期：{'、'.join(m['background_accessed_at'])}（可早于30天窗口，不属于开源事件）")
    return lines


def header(brief):
    m = brief["meta"]
    j = brief.get("period_judgment")
    lines = ["# 近 30 天 AIGC 开源更新看板", ""]
    if j and j["status"] == "valid":
        lines += [f"> **本期判断**：{j['text']}", ""]
    else:
        lines += ["> 本期判断待复核：其依据的项目解读已变化或不在本期。", ""]
    lines += dates_lines(brief) + [""]
    if m["run_status"] == "partial":
        failed = [c["label"] for c in brief["coverage"] if c["search_failed"]]
        checks = sum(c["check_failed"] for c in brief["coverage"])
        lines += [f"> 覆盖缺口：搜索失败的分类：{'、'.join(failed) or '无'}；检查失败 {checks} 个。以下结论只基于成功获取的部分。", ""]
    return lines


def index_section(brief):
    lines = ["## 本期更新目录", ""]
    if brief.get("priority_basis"):
        lines += [f"_{brief['priority_basis']}_", ""]
    if not brief["projects"]:
        return lines + ["本期没有经核查的正式精选。有事件的项目见“待核查”。", ""]
    lines += ["| # | 任务/场景：具体变化 | 项目 | 事件 | 能力标签 |", "|---|---|---|---|---|"]
    for i, p in enumerate(brief["projects"], 1):
        lines.append(f"| {i} | {project_title(p)} | {p['name']} | {event_line(p['event'])} | {caps(brief, p)} |")
    pending = len(brief["pending"])
    lines += ["", f"另有 {pending} 个有事件的项目在“待核查”，未计入精选。" if pending else "本期没有待核查项目。", ""]
    return lines


# ---------- project blocks ----------

def team_value_lines(brief, tv):
    lines = [f"- 方式：{tv['mode']}", f"- 改善哪个步骤：{tv['step']}", f"- 可能影响的指标：{tv['metric']}"]
    for f in tv.get("facts", []):
        lines.append(f"- 公开事实：{f['text']}{refs(f, brief)}")
    lines += [f"- 分析推断：{tv['inference']}", f"- 待验证：{tv['unverified']}"]
    return lines


def project_block(brief, i, p):
    e, a = p["event"], p["annotation"]
    lines = [f"### {i}. {project_title(p)}", "",
             f"- 项目：[{p['name']}]({p['repo_url']})" + (f" — {a['purpose']}" if a["status"] == "valid"
                                                         else f" — {p['description']}"),
             f"- 事件：{event_line(e)}，[来源]({e['url']})",
             f"- 能力标签：{caps(brief, p)}"]
    if a["status"] != "valid":
        return lines + [f"- 解读状态：待分析。{a['reason']}",
                        f"- 原文摘录（规则截取，非AI分析）：{e['excerpt'].replace(chr(10), ' ')[:400]}",
                        f"- 选择理由：{p['selection_reason']}", ""]
    # default layer: change / audience / boundaries
    lines += ["", "**本次变化**", "", a["key_change"], "",
              "**谁值得关注**", "", a["useful_for"], "",
              "**关键边界**", ""]
    lines += [f"- {x['label']}：{x['text']}" for x in a["key_limits"]]
    # secondary layers
    lines += details(f"具体改动（{len(a['facts'])} 项）",
                     [f"- {f['text']}{refs(f, brief)}" for f in a["facts"]])
    tech_lines = [f"- {a['tech']}",
                  f"- 许可：{p['license']['spdx_id'] or '未声明'}。{p['license']['adoption_note']}",
                  f"- 限制与未知：{a['limitations']}"]
    if p["other_events"]:
        tech_lines.append("- 窗口内其他事件：" + "、".join(event_line(x) for x in p["other_events"]))
    if p["newer_unreviewed"]:
        tech_lines.append("- 窗口内有更新的事件尚未核查：" + "、".join(event_line(x) for x in p["newer_unreviewed"]))
    if p["releases_truncated"]:
        tech_lines.append("- 发布列表达到单页上限，窗口内更早的发布可能未取全。")
    lines += details("技术与采用条件", tech_lines)
    insp_lines = [f"- 适合的用户任务：{a['target_task']}"] + team_value_lines(brief, a["team_value"])
    insp_lines += [f"- 产品假设：{a['hypothesis']}",
                   f"- 最小验证建议（拟议，未执行）：{a['experiment']}"]
    lines += details("对团队的启发", insp_lines)
    ev_lines = [f"- [{ev['id']}] “{ev['quote']}” — {ev['field_label']}，[原文]({ev['url']})，"
                f"原始响应 `{ev['raw_file']}`" for ev in a["evidence"]]
    lines += details(f"原始依据（{len(a['evidence'])} 条）", ev_lines)
    lines += [f"选择理由：{p['selection_reason']}（{p['decided_by']}，核查于期次 {p['decided_in_run']}）。"
              f"解读审阅状态：{REVIEW_LABEL.get(a['review_status'])}。", ""]
    return lines


def projects_section(brief):
    lines = ["## 项目更新", ""]
    if not brief["projects"]:
        return lines + ["本期没有经核查的正式精选。", ""]
    for i, p in enumerate(brief["projects"], 1):
        lines += project_block(brief, i, p)
    return lines


def dep_names(brief, entry):
    names = {p["id"]: p["name"] for p in brief["projects"]}
    return "、".join(names.get(d[0], d[0]) for d in entry["depends_on"]) or "无"


def signals_section(brief):
    lines = ["## 跨项目信号", "", "以下信号只说明本期少量项目里的共同点，不外推为行业趋势。", ""]
    for o in brief["observations"]:
        n = len(o.get("depends_on") or [])
        if o["status"] == "valid":
            lines += [f"### {o['title']}（{o['scope']} · 基于 {n} 个项目）", "", o["body"], "",
                      f"依据项目：{dep_names(brief, o)}", ""]
        else:
            lines += [f"### {o['title']}", "", "该信号依赖的证据已变化或不在本期，待复核。", ""]
    return lines


# ---------- action recommendation ----------

PLAN_FIELDS = [("why", "为什么先做"), ("target_users", "目标用户"), ("hypothesis", "假设"),
               ("control", "对照流程"), ("variable", "主要变量"), ("controls", "控制条件"),
               ("primary_metric", "主指标"), ("quality_cost", "质量与成本约束"), ("roles", "所需角色"),
               ("prerequisites", "前提"), ("sample", "样本与周期"), ("condition", "前提条件"),
               ("reason", "理由"), ("limits", "限制")]


def plan_item_lines(brief, x):
    """One plan item as a list of markdown lines (used inside disclosures)."""
    if x["status"] != "valid":
        return [f"#### {x['title']}", "", "依据已变化或不在本期，待复核。", ""]
    lines = [f"#### {x['kind']}：{x['title']}", ""]
    if x.get("mode"):
        lines.append(f"- 方式：{x['mode']}")
    lines += [f"- {label}：{x[k]}" for k, label in PLAN_FIELDS if x.get(k)]
    d = x.get("decision")
    if d:
        lines += [f"- 继续：{d['continue']}", f"- 调整：{d['adjust']}", f"- 停止：{d['stop']}"]
    bmap = background_map(brief)
    basis = [n for n in dep_names(brief, x).split("、") if n != "无"]
    basis += [bmap[b]["title"] for b in x.get("background", []) if b in bmap]
    return lines + [f"- 依据：{'、'.join(basis)}", ""]


def action_section(brief):
    plan = brief["team_plan"]
    lines = ["## 行动建议", ""]
    priority = plan.get("priority") or []
    if priority and priority[0]["status"] == "valid" and priority[0].get("short"):
        x = priority[0]
        lines += [x["short"], ""]
        lines += details("展开实验参数", plan_item_lines(brief, x))
    else:
        lines += ["优先建议待复核：其依据的项目解读已变化或不在本期。", ""]
    conditional = plan.get("conditional") or []
    cond_lines = [ln for x in conditional for ln in plan_item_lines(brief, x)]
    if cond_lines:
        lines += details(f"有条件实验（{len(conditional)} 项）", cond_lines)
    deferred = plan.get("deferred") or []
    deferred_lines = [ln for x in deferred for ln in plan_item_lines(brief, x)]
    if deferred_lines:
        lines += details(f"暂缓清单（{len(deferred)} 项）", deferred_lines)
    lines += ["以上建议均未执行；阈值、样本量和周期是建议值，需先建立基线。", ""]
    return lines


# ---------- review / background / method ----------

def review_section(brief):
    lines = ["## 待核查", "", "窗口内有事件、但没有有效核查记录的项目。只列原文事实与来源，未做分析，也不计入精选。", ""]
    for x in brief["pending"]:
        e = x["event"]
        lines.append(f"- [{x['name']}]({x['repo_url']})：{event_line(e)}，[来源]({e['url']})。原因：{'；'.join(x['reasons'])}。"
                     f"简介：{x['description'] or '无'}" + (f"。复核提示：{', '.join(x['review_flag'])}" if x["review_flag"] else ""))
    if not brief["pending"]:
        lines.append("- 无")
    lines += ["", "## 移出与变化", ""]
    ch = brief.get("changes_since_previous")
    if ch:
        lines.append(f"- 对比上一期快照 {ch['previous_run_id']}：新增 {'、'.join(ch['added']) or '无'}。")
        lines += [f"- 移出 {r['name']}（{r['tag'] or '新建'}）：{r['reason']}" for r in ch["removed"]]
    for d in brief.get("dropped_decisions", []):
        lines.append(f"- 已有核查记录但本期不适用：{d['id']} {d['tag'] or d['event_id']}，{d['reason']}")
    if not ch and not brief.get("dropped_decisions"):
        lines.append("- 无上一期快照可对比；没有失效的核查记录。")
    lines += ["", "## 排除记录", ""]
    for x in brief["excluded"]:
        scope = "仓库整体，简介变化即失效" if x["scope"] == "repo" else "仅该事件，出现新事件或说明变化即失效"
        lines.append(f"- {x['name']}：{x['reason']}。适用范围：{scope}。证据：{x['evidence_url']}")
    for e in brief["manual_exclusions"]:
        state = "已失效，本期重新检查" if e["lapsed"] else "生效"
        lines.append(f"- 检查前排除 {e['repo']}：{e['explanation']}（{e['evidence_url']}；{state}；{e.get('recheck_when', '')}）")
    return lines + [""]


def background_section(brief):
    bg = brief.get("background", [])
    body = ["背景资料只用于判断与目标团队的关系。区分：公开事实（页面写明）、分析推断、待验证假设。", ""]
    for b in bg:
        body.append(f"- **{b['title']}**（{SOURCE_TYPE.get(b['type'], b['type'])}，查阅 {b['accessed_at']}）："
                    f"{b['supports']} 边界：{b['limits']} {b['url']}")
    return details(f"商业背景资料（{len(bg)} 条）", body)


def method_section(brief):
    m, q, sc = brief["meta"], brief["meta"]["quota"], brief["meta"]["search_config"]
    lines = ["## 数据与方法", "", "### 覆盖统计（按检索分类）", "",
             "| 检索分类 | 搜索 | 候选 | 窗口内有事件 | 检查后无合格事件 | 人工排除 | 未检查 | 检查失败 |",
             "|---|---|---|---|---|---|---|---|"]
    for c in brief["coverage"]:
        lines.append(f"| {c['label']} | {'失败' if c['search_failed'] else '成功'} | {c['candidates']} | {c['qualified']} | "
                     f"{c['checked_no_event']} | {c['manually_excluded']} | {c['not_checked']} | {c['check_failed']} |")
    layers = (f"检索到的候选 {len(brief['candidates'])} 个 → 窗口内有事件 {sum(c['qualified'] for c in brief['coverage'])} 个 → "
              f"正式精选 {len(brief['projects'])} 个、待核查 {len(brief['pending'])} 个、经核查排除 {len(brief['excluded'])} 个。")
    lines += ["", layers, ""] + [f"- {g['text']}" for g in brief.get("category_gaps", [])]
    lines += ["", "### 各项目抓取时累计 Stars（一次观测，不代表增长）", "",
              "| 项目 | Stars | 许可 |", "|---|---|---|"]
    for p in brief["projects"]:
        lines.append(f"| {p['name']} | {p['stars_snapshot']} | {p['license']['spdx_id'] or '未声明'} |")
    lines += ["", "### 检索范围与截断", "", "| 分类 | 检索 | GitHub匹配总数 | 实际取回 | 是否截断 |",
              "|---|---|---|---|---|"]
    for s in brief["scope"].get("searches", []):
        total = s["total_count"] if s["total_count"] is not None else "失败"
        lines.append(f"| {label_of(brief, s['category'])} | {KIND_LABEL.get(s['kind'], s['kind'])} | {total} | {s['returned']} | {'是' if s['truncated'] else '否'} |")
    unchecked = sum(c["not_checked"] for c in brief["coverage"])
    lines += ["", f"每条检索只取Stars最高的前{sc['s1_per_page']}或{sc['s2_per_page']}个，排名之后的仓库没有进入候选；"
              f"候选中还有 {unchecked} 个因名额未检查（名单见 data/brief.json 的 candidates）。"]
    errors = m["errors"]
    lines.append(f"- 失败或跳过的请求：{len(errors)} 个" + ("。" if not errors else "：" + "；".join(
        f"#{e['seq']} {e['purpose']} {e['repo'] or e['category']} {e['error']}" for e in errors)))
    topics = "、".join(f"{c['label']}（topic:{c['topic']}）" for c in m["categories"])
    lines += ["", "### 方法", "",
              f"- 数据源：GitHub REST API（单一来源，未使用模型）。分类：{topics}。",
              "- 每类两次检索：近期有推送的仓库按Stars排序（偏向成熟项目），窗口内新建的仓库按Stars排序（照顾新项目）；均排除fork与归档。",
              f"- 每类检查{q['per_category']}个候选，其中{q.get('s2_reserved', 1)}个名额留给窗口内新建的仓库；空缺轮转补位；"
              f"某类无合格事件时补检{q['recheck_per_category']}个。请求上限{q['request_cap']}次，本期实际{m['request_count']}次。",
              f"- 事件：窗口内最新的正式发布优先，其次预发布，再次窗口内新建仓库（README不少于{m['thresholds']['readme_min_chars']}字）。草稿忽略，只有提交活动不算事件。",
              "- 关键词（awesome、list、prompts、paper等，按整词匹配）只降低检查顺序并提示复核，不阻止新建仓库事件识别，也不直接排除。",
              "- “窗口内有事件”是自动状态。进入正式精选必须有核查记录：AIGC相关、实质变化、来源可查三项为真，并写明理由；"
              "没有记录的有事件项目进入待核查，不会被默认规则补进精选。",
              "- 解读按“仓库+事件ID+版本号+来源哈希”绑定，引用原文须逐字可查；不满足时旧解读不显示，只列事实与来源。",
              "- Stars为抓取时累计值，只有一次观测，不表示增长。许可只说明代码许可，模型权重与服务条款未核查。",
              f"- 网络说明：{NETWORK_NOTE}", "",
              "## AI参与说明", "",
              "抓取、去重、窗口判断、统计与排版由脚本完成，运行时不调用模型。项目解读、本期判断、跨项目信号与团队建议由AI在制作阶段起草，"
              "每条都绑定依据，审阅状态见各项；详见 AI_USAGE.md。", ""]
    return lines


def render_report(brief):
    lines = (header(brief) + index_section(brief) + projects_section(brief) + signals_section(brief)
             + action_section(brief) + review_section(brief) + background_section(brief) + method_section(brief))
    return "\n".join(lines)


def render_data_js(brief, report):
    payload = json.dumps({"brief": brief, "report": report}, ensure_ascii=False)
    payload = payload.replace("</", "<\\/")  # keep "</script>" inside strings from closing a script tag
    return "window.SIGNAL_DATA = " + payload + ";\n"
