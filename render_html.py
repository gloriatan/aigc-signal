"""Render the dashboard shell site/index.html.

The shell embeds the full report as plain HTML (#fallback): if app.js fails,
the brief is still readable. Same reading order as render.py's Markdown:
title + one-line judgment -> index (with sorting rationale) -> projects
(default layer visible; secondary layers in native <details>) -> signals ->
one action recommendation (parameters in <details>) -> pending/changes/
exclusions -> background (<details>) -> data & method.
"""
from html import escape

from render import (KIND_LABEL, PLAN_FIELDS, REVIEW_LABEL, SOURCE_TYPE, TYPE_LABEL, background_map,
                    caps, dep_names, event_line, label_of, project_title)


def e(text):
    return escape(str(text if text is not None else ""))


def a(url, text):
    return f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(text)}</a>'


def ul(items):
    return "<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>" if items else ""


def html_details(summary, inner):
    """A secondary layer rendered as a native collapsed disclosure."""
    return f"<details><summary>{e(summary)}</summary>{inner}</details>"


def ref_links(item, brief, pid):
    out = [f'<a href="#ev-{pid}-{x}">依据 {e(x)}</a>' for x in item.get("evidence", [])]
    bmap = background_map(brief)
    out += [f'<a href="#bg-{e(b)}">背景：{e(bmap[b]["title"])}</a>' for b in item.get("background", []) if b in bmap]
    return f' <span class="meta">（{"；".join(out)}）</span>' if out else ""


def dates_html(brief):
    m = brief["meta"]
    events = sorted(p["event"]["published_at"][:10] for p in brief["projects"])
    rows = [("事件窗口", f"{m['window_start']} 至 {m['window_end']}（UTC，含起点不含终点）"),
            ("精选事件日期", f"{events[0]} 至 {events[-1]}" if events else "本期无"),
            ("数据抓取时间", f"{m['as_of']}（期次 {m['run_id']}，状态 {m['run_status']}）"),
            ("报告生成时间", f"{m['generated_at']}（{'离线重建' if m['mode'] == 'offline' else '联网刷新'}）")]
    if m.get("background_accessed_at"):
        rows.append(("背景资料查阅日期", "、".join(m["background_accessed_at"]) + "（可早于30天窗口，不属于开源事件）"))
    return ul([f'<span class="label">{e(k)}：</span>{e(v)}' for k, v in rows])


def head_html(brief):
    m, j = brief["meta"], brief.get("period_judgment")
    out = ["<h1>近 30 天 AIGC 开源更新看板</h1>"]
    if j and j["status"] == "valid":
        out.append(f'<p class="judgment"><span class="label">本期判断</span><br>{e(j["text"])}</p>')
    else:
        out.append('<p class="judgment">本期判断待复核：其依据的项目解读已变化或不在本期。</p>')
    if m["run_status"] == "partial":
        failed = [c["label"] for c in brief["coverage"] if c["search_failed"]]
        checks = sum(c["check_failed"] for c in brief["coverage"])
        out.append(f'<p class="judgment limit">覆盖缺口：搜索失败的分类：{e("、".join(failed) or "无")}；'
                   f'检查失败 {checks} 个。以下结论只基于成功获取的部分。</p>')
    return "".join(out) + html_details("时间与抓取信息", dates_html(brief))


def index_html(brief):
    out = ['<h2 id="index">项目更新</h2>']
    if brief.get("priority_basis"):
        out.append(html_details("为什么这样排序", f'<p class="meta sort-basis">{e(brief["priority_basis"])}</p>'))
    if not brief["projects"]:
        return out[0] + "<p>本期没有经核查的正式精选。有事件的项目见“待核查”。</p>"
    rows = "".join(f'<tr><td>{i}</td><td><a href="#p-{i}">{e(project_title(p))}</a></td><td>{e(p["name"])}</td>'
                   f'<td>{e(event_line(p["event"]))}</td><td>{e(caps(brief, p))}</td></tr>'
                   for i, p in enumerate(brief["projects"], 1))
    out.append('<div class="table-wrap"><table class="idx"><thead><tr><th>#</th><th>任务/场景：具体变化</th><th>项目</th>'
               f'<th>事件</th><th>能力标签</th></tr></thead><tbody>{rows}</tbody></table></div>')
    n = len(brief["pending"])
    out.append(f'<p class="meta">另有 {n} 个有事件的项目在“待核查”，未计入精选。</p>' if n else
               '<p class="meta">本期没有待核查项目。</p>')
    return "".join(out)


def signals_html(brief):
    out = ['<h2 id="signals">几项更新共同说明什么</h2>',
           "<p>以下信号只说明本期少量项目里的共同点，不外推为行业趋势。</p>"]
    for o in brief["observations"]:
        n = len(o.get("depends_on") or [])
        if o["status"] == "valid":
            out.append(f'<h3>{e(o["title"])} <span class="tag">{e(o["scope"])} · 基于 {n} 个项目</span></h3>'
                       f'<p>{e(o["body"])}</p><p class="meta">依据项目：{e(dep_names(brief, o))}</p>')
        else:
            out.append(f"<h3>{e(o['title'])}</h3><p>该信号依赖的证据已变化或不在本期，待复核。</p>")
    return "".join(out)


def evidence_html(ev, pid):
    return (f'<li id="ev-{pid}-{e(ev["id"])}"><span class="label">[{e(ev["id"])}]</span> '
            f'<blockquote><span class="ctx">{e(ev["before"])}</span><mark>{e(ev["quote"])}</mark>'
            f'<span class="ctx">{e(ev["after"])}</span></blockquote>'
            f'<span class="meta">{e(ev["field_label"])} · {a(ev["url"], "原文链接")} · 原始响应 <code>{e(ev["raw_file"])}</code></span></li>')


def project_html(brief, i, p):
    ev, an = p["event"], p["annotation"]
    head = (f'<section class="project" id="p-{i}"><h3>{i}. {e(project_title(p))}</h3>'
            f'<p class="meta">{a(p["repo_url"], p["name"])} · {e(event_line(ev))} · {a(ev["url"], "来源")} · '
            f'能力标签：{e(caps(brief, p))}</p>')
    if an["status"] != "valid":
        return head + (f'<p><span class="tag limit">待分析</span>{e(an["reason"])}</p><p>{e(p["description"])}</p>'
                       f'<h4>原文摘录（规则截取，非AI分析）</h4><blockquote>{e(ev["excerpt"])}</blockquote>'
                       f'<p class="meta">选择理由：{e(p["selection_reason"])}</p></section>')
    # Keep the exact annotation text; move supporting material into disclosures.
    lead, sep, rest = an["key_change"].partition("。")
    primary_labels = {
        "harry0703/moneyprinterturbo": ["未经实测"],
        "debpalash/voicestudio": [],
        "op7418/guizang-yingzao-skill": ["未经实测"],
        "mudler/localai": ["指定模型", "范围有限"],
        "unslothai/unsloth": ["指定硬件"],
    }.get(p["id"])
    primary = [x for x in an["key_limits"] if primary_labels is None or x["label"] in primary_labels]
    secondary = [x for x in an["key_limits"] if primary_labels is not None and x["label"] not in primary_labels]
    def limits(items):
        return ul([f'<b>{e(x["label"])}：</b>{e(x["text"])}' for x in items])
    default = (f'<h4 class="l1-h">本次变化</h4><p>{e(lead + sep)}</p>'
               + (html_details("这次还更新了什么", f"<p>{e(rest)}</p>") if rest else "")
               + limits(primary)
               + html_details("项目用途与适用人群", f'<p>{e(an["purpose"])}</p><p>{e(an["useful_for"])}</p>')
               + (html_details(f"使用前还要确认什么（{len(secondary)} 项）", limits(secondary)) if secondary else ""))
    # secondary layers
    facts = html_details(f"具体改动（{len(an['facts'])} 项）",
                         ul([e(f["text"]) + ref_links(f, brief, i) for f in an["facts"]]))
    tech = [e(an["tech"]), f'许可：{e(p["license"]["spdx_id"] or "未声明")}。{e(p["license"]["adoption_note"])}',
            f'限制与未知：{e(an["limitations"])}']
    if p["other_events"]:
        tech.append("窗口内其他事件：" + e("、".join(event_line(x) for x in p["other_events"])))
    if p["newer_unreviewed"]:
        tech.append("窗口内有更新的事件尚未核查：" + e("、".join(event_line(x) for x in p["newer_unreviewed"])))
    if p["releases_truncated"]:
        tech.append("发布列表达到单页上限，窗口内更早的发布可能未取全。")
    tech_html = html_details("技术与使用条件", ul(tech))
    tv = an["team_value"]
    team_items = [f'<span class="label">适合的用户任务：</span>{e(an["target_task"])}',
                  f'<span class="label">方式：</span>{e(tv["mode"])}',
                  f'<span class="label">改善哪个步骤：</span>{e(tv["step"])}',
                  f'<span class="label">可能影响的指标：</span>{e(tv["metric"])}']
    team_items += [f'<span class="label">公开事实：</span>{e(f["text"])}{ref_links(f, brief, i)}' for f in tv["facts"]]
    team_items += [f'<span class="label">分析推断：</span>{e(tv["inference"])}',
                   f'<span class="label">待验证：</span>{e(tv["unverified"])}',
                   f'<span class="label">产品假设：</span>{e(an["hypothesis"])}',
                   f'<span class="label">最小验证建议（拟议，未执行）：</span>{e(an["experiment"])}']
    team_html = html_details("对团队的启发", ul(team_items))
    evidence = html_details(f"原始依据（{len(an['evidence'])} 条）",
                            '<ul class="ev-list">' + "".join(evidence_html(x, i) for x in an["evidence"]) + "</ul>")
    foot = (f'<p class="meta">选择理由：{e(p["selection_reason"])}（{e(p["decided_by"])}，核查于期次 {e(p["decided_in_run"])}）。'
            f'解读审阅状态：{e(REVIEW_LABEL.get(an["review_status"]))}。</p></section>')
    return head + default + facts + tech_html + team_html + evidence + foot


def plan_item_html(brief, x):
    if x["status"] != "valid":
        return f"<h3>{e(x['title'])}</h3><p>依据已变化或不在本期，待复核。</p>"
    items = ([f'<span class="label">方式：</span>{e(x["mode"])}'] if x.get("mode") else [])
    items += [f'<span class="label">{e(label)}：</span>{e(x[k])}' for k, label in PLAN_FIELDS if x.get(k)]
    d = x.get("decision")
    if d:
        items += [f'<span class="label">继续：</span>{e(d["continue"])}', f'<span class="label">调整：</span>{e(d["adjust"])}',
                  f'<span class="label">停止：</span>{e(d["stop"])}']
    bmap = background_map(brief)
    basis = [n for n in dep_names(brief, x).split("、") if n != "无"] + [bmap[b]["title"] for b in x.get("background", []) if b in bmap]
    items.append(f'<span class="label">依据：</span>{e("、".join(basis))}')
    return f'<h3><span class="tag">{e(x["kind"])}</span>{e(x["title"])}</h3>{ul(items)}'


def action_html(brief):
    plan = brief["team_plan"]
    out = ['<h2 id="action">下一步试什么</h2>']
    priority = plan.get("priority") or []
    if priority and priority[0]["status"] == "valid" and priority[0].get("short"):
        x = priority[0]
        lead, sep, rest = x["short"].partition("。")
        out.append(f"<p>{e(lead + sep)}</p>")
        if rest:
            out.append(html_details("为什么建议试，哪些还不确定", f"<p>{e(rest)}</p>"))
        out.append(html_details("怎么试，怎样判断结果", plan_item_html(brief, x)))
    else:
        out.append("<p>优先建议待复核：其依据的项目解读已变化或不在本期。</p>")
    conditional = plan.get("conditional") or []
    if conditional:
        inner = "".join(plan_item_html(brief, x) for x in conditional)
        out.append(html_details(f"有条件实验（{len(conditional)} 项）", inner))
    deferred = plan.get("deferred") or []
    if deferred:
        inner = "".join(plan_item_html(brief, x) for x in deferred)
        out.append(html_details(f"暂缓清单（{len(deferred)} 项）", inner))
    out.append('<p class="meta">以上建议均未执行；阈值、样本量和周期是建议值，需先建立基线。</p>')
    return "".join(out)


def review_html(brief):
    out = ['<h2 id="pending">其他项目为什么没选入</h2><p>窗口内有事件、但没有有效核查记录的项目。只列原文事实与来源，未做分析，也不计入精选。</p>']
    rows = []
    for x in brief["pending"]:
        flag = f'；复核提示：{e(", ".join(x["review_flag"]))}' if x["review_flag"] else ""
        rows.append(f'{a(x["repo_url"], x["name"])}：{e(event_line(x["event"]))}，{a(x["event"]["url"], "来源")}。'
                    f'原因：{e("；".join(x["reasons"]))}。简介：{e(x["description"] or "无")}{flag}')
    out.append(ul(rows) or "<p>无</p>")
    out.append('<h2 id="changes">与上一期相比</h2>')
    ch, rows = brief.get("changes_since_previous"), []
    if ch:
        rows.append(f"对比上一期快照 {e(ch['previous_run_id'])}：新增 {e('、'.join(ch['added']) or '无')}。")
        rows += [f"移出 {e(r['name'])}（{e(r['tag'] or '新建')}）：{e(r['reason'])}" for r in ch["removed"]]
    rows += [f"已有核查记录但本期不适用：{e(d['id'])} {e(d['tag'] or d['event_id'])}，{e(d['reason'])}"
             for d in brief.get("dropped_decisions", [])]
    out.append(ul(rows) or "<p>无上一期快照可对比；没有失效的核查记录。</p>")
    out.append('<h2 id="excluded">不纳入的理由</h2>')
    rows = [f'{e(x["name"])}：{e(x["reason"])}。适用范围：'
            f'{"仓库整体，简介变化即失效" if x["scope"] == "repo" else "仅该事件，出现新事件或说明变化即失效"}。'
            f'{a(x["evidence_url"], "证据")}' for x in brief["excluded"]]
    rows += [f'检查前排除 {e(m["repo"])}：{e(m["explanation"])}（{"已失效，本期重新检查" if m["lapsed"] else "生效"}；'
             f'{e(m.get("recheck_when", ""))}）{a(m["evidence_url"], "证据")}' for m in brief["manual_exclusions"]]
    out.append(ul(rows) or "<p>无</p>")
    return "".join(out)


def background_html(brief):
    bg = brief.get("background", [])
    rows = [f'<span id="bg-{e(b["id"])}" class="label">{e(b["title"])}</span> '
            f'<span class="tag">{e(SOURCE_TYPE.get(b["type"], b["type"]))}</span><span class="tag">查阅 {e(b["accessed_at"])}</span><br>'
            f'{e(b["supports"])}<br><span class="meta">边界：{e(b["limits"])}</span> {a(b["url"], "页面")}'
            for b in bg]
    inner = ('<p>背景资料只用于判断与目标团队的关系。区分公开事实（页面写明）、分析推断与待验证假设。</p>' + ul(rows))
    return html_details(f"这些更新与团队有什么关系（{len(bg)} 条）", inner).replace("<details>", '<details id="background">', 1)


def method_html(brief):
    m, q, sc = brief["meta"], brief["meta"]["quota"], brief["meta"]["search_config"]
    cov = "".join(f'<tr><td>{e(c["label"])}</td><td>{"失败" if c["search_failed"] else "成功"}</td><td>{c["candidates"]}</td>'
                  f'<td>{c["qualified"]}</td><td>{c["checked_no_event"]}</td><td>{c["manually_excluded"]}</td>'
                  f'<td>{c["not_checked"]}</td><td>{c["check_failed"]}</td></tr>' for c in brief["coverage"])
    stars = "".join(f'<tr><td>{e(p["name"])}</td><td>{e(p["stars_snapshot"])}</td><td>{e(p["license"]["spdx_id"] or "未声明")}</td></tr>'
                    for p in brief["projects"])
    scope = "".join(f'<tr><td>{e(label_of(brief, s["category"]))}</td><td>{e(KIND_LABEL.get(s["kind"], s["kind"]))}</td>'
                    f'<td>{e(s["total_count"] if s["total_count"] is not None else "失败")}</td><td>{s["returned"]}</td>'
                    f'<td>{"是" if s["truncated"] else "否"}</td></tr>' for s in brief["scope"].get("searches", []))
    errors = m["errors"]
    unchecked = sum(c["not_checked"] for c in brief["coverage"])
    layers = (f"检索到的候选 {len(brief['candidates'])} 个 → 窗口内有事件 {sum(c['qualified'] for c in brief['coverage'])} 个 → "
              f"正式精选 {len(brief['projects'])} 个、待核查 {len(brief['pending'])} 个、经核查排除 {len(brief['excluded'])} 个。")
    topics = "、".join(f"{c['label']}（topic:{c['topic']}）" for c in m["categories"])
    method = [f"数据源：GitHub REST API（单一来源，未使用模型）。分类：{topics}。",
              "每类两次检索：近期有推送的仓库按Stars排序（偏向成熟项目），窗口内新建的仓库按Stars排序（照顾新项目）；均排除fork与归档。",
              f"每类检查{q['per_category']}个候选，其中{q.get('s2_reserved', 1)}个名额留给窗口内新建的仓库；空缺轮转补位；某类无合格事件时补检"
              f"{q['recheck_per_category']}个。请求上限{q['request_cap']}次，本期实际{m['request_count']}次。",
              f"事件：窗口内最新的正式发布优先，其次预发布，再次窗口内新建仓库（README不少于{m['thresholds']['readme_min_chars']}字）。草稿忽略，只有提交活动不算事件。",
              "关键词（awesome、list、prompts、paper等，按整词匹配）只降低检查顺序并提示复核，不阻止新建仓库事件识别，也不直接排除。",
              "“窗口内有事件”是自动状态。进入正式精选必须有核查记录（三项核查为真并写明理由）；没有记录的有事件项目进入待核查，不会被默认规则补进精选。",
              "解读按“仓库+事件ID+版本号+来源哈希”绑定，引用原文须逐字可查；不满足时旧解读不显示，只列事实与来源。",
              "Stars为抓取时累计值，只有一次观测，不表示增长。许可只说明代码许可，模型权重与服务条款未核查。"]
    err = "无" if not errors else "；".join(f"#{x['seq']} {x['purpose']} {x['repo'] or x['category']} {x['error']}" for x in errors)
    return ('<h2 id="method">数据怎么来的</h2><h3>覆盖统计（按检索分类）</h3><div class="table-wrap"><table><thead><tr>'
            '<th>检索分类</th><th>搜索</th><th>候选</th><th>窗口内有事件</th><th>检查后无合格事件</th><th>人工排除</th><th>未检查</th>'
            f'<th>检查失败</th></tr></thead><tbody>{cov}</tbody></table></div><p>{e(layers)}</p>'
            + ul([e(g["text"]) for g in brief.get("category_gaps", [])]) +
            '<h3>各项目抓取时累计 Stars（一次观测，不代表增长）</h3>'
            f'<div class="table-wrap"><table><thead><tr><th>项目</th><th>Stars</th><th>许可</th></tr></thead><tbody>{stars}</tbody></table></div>'
            '<h3>检索范围与截断</h3><div class="table-wrap"><table><thead><tr><th>分类</th><th>检索</th><th>GitHub匹配总数</th>'
            f'<th>实际取回</th><th>是否截断</th></tr></thead><tbody>{scope}</tbody></table></div>'
            f'<p>每条检索只取Stars最高的前{sc["s1_per_page"]}或{sc["s2_per_page"]}个，排名之后的仓库没有进入候选；候选中还有 {unchecked} 个因名额未检查'
            f'（名单见 data/brief.json 的 candidates）。失败或跳过的请求：{e(err)}。</p>'
            '<h3>方法</h3>' + ul([e(x) for x in method]) +
            '<h2 id="ai">AI参与说明</h2><p>抓取、去重、窗口判断、统计与排版由脚本完成，运行时不调用模型。项目解读、本期判断、几项更新共同说明什么与团队建议'
            '由AI在制作阶段起草，每条都绑定依据，审阅状态见各项；详见 AI_USAGE.md。</p>')


def report_body(brief):
    projects = "".join(project_html(brief, i, p) for i, p in enumerate(brief["projects"], 1))
    return (head_html(brief) + index_html(brief)
            + '<h2 id="projects">项目更新</h2>' + (projects or "<p>本期没有经核查的正式精选。</p>")
            + signals_html(brief) + action_html(brief) + review_html(brief)
            + background_html(brief) + method_html(brief))


SITE_SHELL = """<!doctype html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>近30天 AIGC 开源更新看板</title>
<meta name="description" content="近30天AIGC开源项目更新、依据与团队验证建议">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='16' fill='%230052D9'/%3E%3Ctext x='32' y='43' font-family='Arial,sans-serif' font-size='34' font-weight='700' text-anchor='middle' fill='%23FFFFFF'%3ES%3C/text%3E%3C/svg%3E">
<script>document.documentElement.className="js";document.documentElement.setAttribute("data-theme","light");</script>
<link rel="stylesheet" href="style.css">
</head>
<body>
<a class="skip" href="#updates">跳到更新目录</a>
<header class="topbar glass">
  <div class="wrap topbar-inner">
    <a class="brand" href="#top"><span class="brand-mark" aria-hidden="true">S</span><span>Signal<span class="brand-sub"> / AIGC开源动态</span></span></a>
    <nav class="section-nav" aria-label="简报阅读顺序与快速定位">
      <a class="section-link" href="#top" data-section="s-judgment" aria-current="location">这期重点</a>
      <a class="section-link" href="#index" data-section="updates">项目更新</a>
      <a class="section-link" href="#signals" data-section="s-signals">共同变化</a>
      <a class="section-link" href="#action" data-section="s-plan">下一步试什么</a>
      <a class="section-link" href="#pending" data-section="s-pending">其他项目</a>
      <a class="section-link" href="#background" data-section="s-background">团队相关</a>
      <a class="section-link" href="#method" data-section="s-method">数据来源</a>
    </nav>
    <nav class="actions" aria-label="页面操作">
      <button class="btn btn-ghost" id="theme" type="button" aria-pressed="false">深色</button>
      <button class="btn btn-ghost" id="refresh" type="button">一键更新</button>
      <button class="btn btn-primary" id="dl-md" type="button">导出 Markdown</button>
      <p class="snapshot" id="snapshot"></p>
    </nav>
  </div>
  <p class="wrap toast" id="toast" role="status" aria-live="polite"></p>
</header>
<main id="top" class="wrap">
  <div id="app" class="app" hidden></div>
  <div id="fallback" class="fallback">
    <p class="fallback-note">交互看板未能加载，以下是完整简报（同一数据源）。Markdown 版见提交包中的 report.md。</p>
    __REPORT_BODY__
  </div>
</main>
<script src="data.js"></script>
<script src="app.js" onerror="document.documentElement.className='nojs'"></script>
</body>
</html>
"""


def render_site_index(brief):
    return SITE_SHELL.replace("__REPORT_BODY__", report_body(brief))
