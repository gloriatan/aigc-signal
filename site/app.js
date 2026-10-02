/* Signal dashboard: update directory + reading panel, built from window.SIGNAL_DATA (site/data.js).
   If anything here throws, the full report embedded in index.html (#fallback) is shown instead. */
(function () {
  "use strict";

  var html = document.documentElement;
  var DATA = window.SIGNAL_DATA;

  function fail(err) {
    html.className = "nojs";
    if (window.console && err) console.error(err);
  }
  if (!DATA || !DATA.brief) { fail(new Error("缺少 data.js，请运行 python3 collect.py --offline")); return; }

  var brief = DATA.brief;
  var meta = brief.meta;
  var WIDE = window.matchMedia ? window.matchMedia("(min-width: 960px)") : { matches: true };
  var REDUCE = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : { matches: false };

  var TYPE = { release: "正式发布", prerelease: "预发布", created: "窗口内新建仓库" };
  var TASK = { video: "视频", image: "图片", speech: "配音", avatar: "数字人" };
  var REVIEW = { ai_draft: "AI草稿，未经本人审阅", user_reviewed: "已经本人审阅" };
  var KIND = { s1: "近期有推送（按Stars）", s2: "窗口内新建（按Stars）" };
  var SRC = { official: "官方", third_party: "第三方辅助线索" };

  var state = { task: "all", query: "", selected: null, open: {}, changedOnly: false };
  var DIFF = brief.diff || null;
  var anims = {};

  // ---------- helpers ----------
  function el(tag, attrs, kids) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      var v = attrs[k];
      if (v === null || v === undefined || v === false) return;
      if (k === "text") n.textContent = v;
      else if (k === "class") n.className = v;
      else if (k.slice(0, 2) === "on") n.addEventListener(k.slice(2), v);
      else n.setAttribute(k, v === true ? "" : v);
    });
    (kids || []).forEach(function (c) {
      if (c === null || c === undefined || c === false) return;
      n.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    });
    return n;
  }
  function $(id) { return document.getElementById(id); }
  function safeUrl(u) {
    try { var x = new URL(u); return /^https?:$/.test(x.protocol) ? x.href : null; } catch (e) { return null; }
  }
  function link(u, text) {
    var h = safeUrl(u);
    return h ? el("a", { href: h, target: "_blank", rel: "noopener noreferrer", text: text }) : el("span", { text: text });
  }
  function day(iso) { return iso ? iso.slice(0, 10) : ""; }
  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function eventLine(e) { return TYPE[e.type] + (e.tag ? " " + e.tag : "") + " · " + day(e.published_at); }
  function short(name) { return name.split("/").pop(); }
  function catLabel(k) {
    var c = meta.categories.filter(function (x) { return x.key === k; })[0];
    return c ? c.label : k;
  }
  function caps(p) { return p.capabilities || [p.category]; }
  function valid(p) { return p.annotation.status === "valid"; }
  function title(p) {
    return valid(p) && p.annotation.update_title ? p.annotation.update_title : "待分析：" + p.name + " " + eventLine(p.event);
  }
  function bgById(id) { return (brief.background || []).filter(function (b) { return b.id === id; })[0]; }
  function projectById(id) { return brief.projects.filter(function (p) { return p.id === id; })[0]; }
  function sum(key) { return brief.coverage.reduce(function (n, c) { return n + c[key]; }, 0); }

  // Short opacity/transform animation; any running one on the same key is cancelled first.
  function animate(key, node, frames, ms) {
    if (anims[key]) { try { anims[key].cancel(); } catch (e) { /* ignore */ } anims[key] = null; }
    if (REDUCE.matches || !node || !node.animate) return;
    anims[key] = node.animate(frames, { duration: ms || 200, easing: "cubic-bezier(0.2, 0.7, 0.2, 1)" });
  }
  function fadeIn(key, node) {
    animate(key, node, [{ opacity: 0, transform: "translateY(6px)" }, { opacity: 1, transform: "none" }], 200);
  }

  // ---------- top bar ----------
  function renderTop() {
    $("snapshot").textContent = "数据截止 " + day(meta.as_of).replace(/-/g, ".") +
      (meta.run_status === "partial" ? " · 部分成功，有覆盖缺口" : "");
    var toggle = $("theme");
    toggle.addEventListener("click", function () {
      var dark = html.getAttribute("data-theme") !== "dark";
      html.setAttribute("data-theme", dark ? "dark" : "light");
      toggle.setAttribute("aria-pressed", String(dark));
      toggle.textContent = dark ? "浅色" : "深色";
    });
    setupUpdate();
    $("dl-md").addEventListener("click", function () {
      download(DATA.report, "AIGC_Signal_" + meta.run_id + ".md", "text/markdown", "report.md");
    });
    var m = document.querySelector('a[href="#method"]');
    if (m) m.setAttribute("href", "#s-method");
  }

  function toast(text) { $("toast").textContent = text; }

  function download(content, name, type, fallbackPath) {
    if (!content) { toast("本页没有内嵌该文件，请直接打开提交包中的 " + fallbackPath + "。"); return; }
    try {
      var url = URL.createObjectURL(new Blob([content], { type: type + ";charset=utf-8" }));
      var a = el("a", { href: url, download: name });
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
      toast("已向浏览器发出下载请求：" + name + "。是否保存成功请以浏览器下载列表为准；也可直接打开提交包中的 " +
        fallbackPath + "。");
    } catch (e) {
      toast("此环境无法发起下载，请直接打开提交包中的 " + fallbackPath + "。");
    }
  }

  // ---------- judgment ----------
  function renderJudgment(root) {
    var j = brief.period_judgment;
    var n = brief.projects.length;
    var box = el("section", { class: "hero", id: "s-judgment", "aria-labelledby": "hero-title" });
    box.appendChild(el("h1", { id: "hero-title", text: "近 30 天 AIGC 开源更新看板" }));
    var card = el("div", { class: "judgment glass" });
    if (j && j.status === "valid") {
      card.appendChild(el("p", { class: "eyebrow" }, [el("span", { class: "pill pill-accent", text: "本期判断" })]));
      card.appendChild(el("p", { class: "judgment-text", text: j.text }));
      card.appendChild(el("details", { class: "quiet-disclosure judgment-sources" }, [el("summary", { text: "判断依据" }), el("p", { class: "judgment-deps" }, j.depends_on.map(function (d) {
        var p = projectById(d[0]);
        return p ? el("button", { class: "chip-btn", type: "button", text: short(p.name),
          onclick: function () { select(p.id, { scroll: true, focusPanel: false }); } }) : null;
      }))]));
    } else {
      card.appendChild(el("p", { class: "judgment-text", text: "本期判断待复核：其依据的项目解读已变化或不在本期。请直接查看下方更新目录。" }));
    }
    if (meta.run_status === "partial") {
      card.appendChild(el("p", { class: "limit", text: "本期数据部分成功：结论只基于成功获取的部分，缺口见“数据怎么来的”。" }));
    }
    box.appendChild(card);
    root.appendChild(box);
  }

  // ---------- directory ----------
  function tasks() {
    return meta.categories.filter(function (c) {
      return brief.projects.some(function (p) { return caps(p).indexOf(c.key) !== -1; });
    });
  }
  function diffOf(p) { return (DIFF && DIFF.projects && DIFF.projects[p.id]) || { status: "same" }; }
  function runDay(runId) { return runId ? runId.slice(0, 4) + "-" + runId.slice(4, 6) + "-" + runId.slice(6, 8) : ""; }
  function diffTag(p) {
    var d = diffOf(p);
    if (d.status === "new") return el("span", { class: "diff-tag", text: "新增" });
    if (d.status === "version") {
      return el("span", { class: "diff-tag", text: "新版本 " + (d.from.tag || day(d.from.published_at)) + " → " + (d.to.tag || day(d.to.published_at)) });
    }
    return null;
  }
  function diffSummaryText() {
    if (!DIFF) return "";
    if (!DIFF.has_previous) return "首期数据，暂无可对比的上一期";
    var s = DIFF.summary;
    var head = "较上期（" + runDay(DIFF.from_run) + "）：";
    var parts = [];
    if (s.new) parts.push("+" + s.new + " 新增");
    if (s.version) parts.push(s.version + " 新版本");
    if (s.removed) parts.push(s.removed + " 移出");
    var text = head + (parts.length ? parts.join(" · ") : "精选无变化");
    if (s.pending_new) text += " · " + s.pending_new + " 个新项目进入待核实";
    return text;
  }
  function matches(p) {
    if (state.changedOnly && diffOf(p).status === "same") return false;
    if (state.task !== "all" && caps(p).indexOf(state.task) === -1) return false;
    if (!state.query) return true;
    var a = p.annotation;
    var text = [p.name, p.description, title(p), a.key_change, a.useful_for, a.scene,
      (a.facts || []).map(function (f) { return f.text; }).join(" ")].join(" ").toLowerCase();
    return text.indexOf(state.query) !== -1;
  }

  function renderDirectory(root) {
    var wrap = el("section", { class: "updates", id: "updates", "aria-label": "本期更新" });
    var left = el("div", { class: "dir glass" });
    left.appendChild(el("div", { class: "dir-head" }, [
      el("div", {}, [el("p", { class: "dir-kicker", text: "UPDATES" }), el("h2", { text: "项目更新" })]),
      el("p", { class: "count", id: "count", "aria-live": "polite" })]));

    var filters = el("div", { class: "filters", role: "group", "aria-label": "按任务筛选" });
    [{ key: "all", label: "全部" }].concat(tasks()).forEach(function (c) {
      var n = c.key === "all" ? brief.projects.length
        : brief.projects.filter(function (p) { return caps(p).indexOf(c.key) !== -1; }).length;
      filters.appendChild(el("button", { class: "filter", type: "button", "data-key": c.key,
        "aria-pressed": String(state.task === c.key),
        onclick: function () { state.task = c.key; refreshList(); } },
        [c.key === "all" ? c.label : (TASK[c.key] || c.label), el("span", { class: "n", text: String(n) })]));
    });
    var search = el("input", { class: "search", type: "search", placeholder: "搜索任务、场景或项目", "aria-label": "搜索更新" });
    search.addEventListener("input", function () { state.query = search.value.trim().toLowerCase(); refreshList(); });
    if (DIFF) left.appendChild(el("p", { class: "diff-summary", id: "diff-summary", text: diffSummaryText() }));
    var changedChip = DIFF && DIFF.summary && DIFF.summary.changed
      ? el("button", { class: "chip-btn diff-only", type: "button", id: "diff-only", "aria-pressed": "false",
        text: "只看变化 " + DIFF.summary.changed,
        onclick: function () {
          state.changedOnly = !state.changedOnly;
          changedChip.setAttribute("aria-pressed", String(state.changedOnly));
          refreshList();
        } })
      : null;
    left.appendChild(el("div", { class: "toolbar" }, [filters, search, changedChip]));
    var list = el("ul", { class: "dir-list", id: "dir-list" });
    list.addEventListener("keydown", onListKey);
    left.appendChild(list);
    var foot = [];
    if (brief.pending.length) foot.push(el("a", { href: "#s-pending", text: "另有 " + brief.pending.length + " 个项目有更新，尚未核实" }));
    if (brief.changes_since_previous && brief.changes_since_previous.removed.length) {
      foot.push(" · ", el("a", { href: "#s-pending", text: brief.changes_since_previous.removed.length + " 个项目已移出本期" }));
    }
    if (foot.length) left.appendChild(el("p", { class: "dir-foot" }, foot));
    if (brief.priority_basis) left.appendChild(el("details", { class: "quiet-disclosure sorting" }, [
      el("summary", { text: "为什么这样排序" }), el("p", { class: "sort-basis", text: brief.priority_basis })]));
    wrap.appendChild(left);
    wrap.appendChild(el("div", { class: "reader-slot", id: "reader-slot" }));
    root.appendChild(wrap);
  }

  function refreshList() {
    Array.prototype.forEach.call(document.querySelectorAll(".filter"), function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-key") === state.task));
    });
    var list = $("dir-list");
    var reader = $("reader");
    if (reader && reader.parentNode === list) list.removeChild(reader);
    list.textContent = "";
    var shown = brief.projects.filter(matches);
    shown.forEach(function (p) {
      var i = brief.projects.indexOf(p);
      var row = el("button", { class: "row" + (i < 2 ? " row-priority" : ""), type: "button", id: "row-" + i, "data-id": p.id,
        "aria-expanded": String(state.selected === p.id), "aria-controls": "reader",
        "aria-label": pad(i + 1) + " " + (diffTag(p) ? diffTag(p).textContent + "：" : "") + title(p) + "。" + short(p.name) + "，" + eventLine(p.event),
        onclick: function () { state.selected === p.id ? close() : select(p.id, { focusPanel: false }); } }, [
        el("span", { class: "row-num", text: pad(i + 1) }),
        el("span", { class: "row-title" }, (i < 2 ? [el("span", { class: "priority-tag", text: "先看" })] : [])
          .concat([diffTag(p), title(p)])),
        el("span", { class: "row-meta" }, [
          el("span", { text: short(p.name) }), "·", el("span", { text: day(p.event.published_at) }),
          el("span", { class: "pill", text: caps(p).map(function (k) { return TASK[k] || catLabel(k); }).join(" / ") }),
          valid(p) ? null : el("span", { class: "pill", text: "待分析" })])]);
      list.appendChild(el("li", {}, [row]));
    });
    if (DIFF && DIFF.removed && DIFF.removed.length && state.task === "all" && !state.query) {
      DIFF.removed.forEach(function (r) {
        list.appendChild(el("li", { class: "row-removed" }, [
          el("span", { class: "diff-tag diff-tag-out", text: "已移出" }),
          el("span", { text: short(r.name) + (r.tag ? " " + r.tag : "") + (r.published_at ? " · " + day(r.published_at) : "") }),
          el("span", { class: "muted", text: "· " + r.reason })]));
      });
    }
    if (!shown.length && !(state.changedOnly && DIFF && DIFF.removed && DIFF.removed.length)) {
      list.appendChild(el("li", { class: "empty" }, ["没有符合条件的更新。",
        el("button", { class: "chip-btn", type: "button", text: "清除筛选", onclick: function () {
          state.task = "all"; state.query = ""; state.changedOnly = false; document.querySelector(".search").value = "";
          var chip = $("diff-only"); if (chip) chip.setAttribute("aria-pressed", "false");
          refreshList();
        } })]));
    }
    var label = state.task === "all" ? "" : "（" + (TASK[state.task] || catLabel(state.task)) + "）";
    $("count").textContent = "显示 " + shown.length + " / " + brief.projects.length + " 项" + label;
    var stillShown = shown.some(function (p) { return p.id === state.selected; });
    if (state.selected && !stillShown) { state.selected = null; state.open = {}; }

    placeReader(false);
  }

  function onListKey(ev) {
    if (ev.key !== "ArrowDown" && ev.key !== "ArrowUp") return;
    var rows = Array.prototype.slice.call(document.querySelectorAll(".row"));
    var i = rows.indexOf(document.activeElement);
    if (i === -1) return;
    ev.preventDefault();
    var next = rows[Math.max(0, Math.min(rows.length - 1, i + (ev.key === "ArrowDown" ? 1 : -1)))];
    next.focus();
  }

  // ---------- reading panel ----------
  function select(id, opts) {
    opts = opts || {};
    if (state.task !== "all" || state.query) {
      var p = projectById(id);
      if (p && !matches(p)) { state.task = "all"; state.query = ""; document.querySelector(".search").value = ""; refreshList(); }
    }
    var changed = state.selected !== id;
    state.selected = id;
    if (changed) state.open = { audience: true };
    placeReader(changed);
    var row = document.querySelector('.row[data-id="' + id + '"]');
    if (opts.scroll && row) row.scrollIntoView({ block: "nearest", behavior: REDUCE.matches ? "auto" : "smooth" });
    if (changed && !opts.scroll) {
      var panel = $("reader");
      if (panel) panel.scrollIntoView({ block: "nearest", behavior: REDUCE.matches ? "auto" : "smooth" });
    }
    if (opts.focusPanel) { var h = $("reader-title"); if (h) h.focus(); }
  }

  function close() {
    var id = state.selected;
    state.selected = null;
    state.open = {};
    placeReader(false);
    var row = document.querySelector('.row[data-id="' + id + '"]');
    if (row) row.focus();
  }

  function placeReader(animateIn) {
    Array.prototype.forEach.call(document.querySelectorAll(".row"), function (r) {
      r.setAttribute("aria-expanded", String(r.getAttribute("data-id") === state.selected));
    });
    var old = $("reader");
    if (old) old.remove();
    var p = state.selected && projectById(state.selected);
    var slot = $("reader-slot");
    slot.hidden = !p;
    if (!p) return;
    var panel = renderReader(p);
    slot.appendChild(panel);
    if (animateIn) fadeIn("reader", panel);
  }

  function evButton(p, evId, label) {
    return el("button", { class: "ev-link", type: "button", text: label || "查看依据 " + evId,
      "aria-label": "查看依据 " + evId + "：定位到原文摘录",
      onclick: function () { locate(p, evId); } });
  }
  function evButtons(p, ids) {
    return (ids || []).map(function (id) { return evButton(p, id); });
  }
  function bgLinks(ids) {
    return (ids || []).map(function (id) {
      var b = bgById(id);
      return b ? el("a", { href: "#bg-" + id, class: "ev-link", text: "背景：" + b.title.split("：")[0] }) : null;
    });
  }

  function splitLead(text) {
    var end = text.indexOf("。");
    return end < 0 ? [text, ""] : [text.slice(0, end + 1), text.slice(end + 1)];
  }
  function primaryBoundaryLabels(id) {
    var labels = {
      "harry0703/moneyprinterturbo": ["未经实测"],
      "debpalash/voicestudio": [],
      "op7418/guizang-yingzao-skill": ["未经实测"],
      "mudler/localai": ["指定模型", "范围有限"],
      "unslothai/unsloth": ["指定硬件"]
    };
    return Object.prototype.hasOwnProperty.call(labels, id) ? labels[id] : null;
  }

  function renderReader(p) {
    var a = p.annotation;
    var i = brief.projects.indexOf(p);
    var panel = el("article", { class: "reader glass", id: "reader", "aria-labelledby": "reader-title" });
    panel.appendChild(el("div", { class: "reader-top" }, [
      el("h3", { id: "reader-title", tabindex: "-1" }, [el("span", { class: "muted", text: pad(i + 1) + " / " + pad(brief.projects.length) + "  " }), title(p)]),
      el("button", { class: "close", type: "button", text: "关闭", "aria-label": "关闭详情，回到目录", onclick: close })]));
    panel.appendChild(el("p", { class: "reader-meta" }, [link(p.repo_url, p.name), " · ", eventLine(p.event), " · ",
      link(p.event.url, "官方来源")]));
    panel.addEventListener("keydown", function (ev) { if (ev.key === "Escape") close(); });

    if (!valid(p)) {
      panel.appendChild(el("div", { class: "layer1" }, [
        el("div", { class: "l1-item" }, [el("h4", { text: "解读状态：待分析" }), el("p", { text: a.reason })]),
        el("div", { class: "l1-item" }, [el("h4", { text: "仓库简介" }), el("p", { text: p.description || "无" })]),
        el("div", { class: "l1-item" }, [el("h4", { text: "原文摘录（规则截取，非AI分析）" }), el("p", { class: "small", text: p.event.excerpt })])]));
      return panel;
    }
    var refMatch = /依据\s*([a-z]\d+)/.exec(a.key_change);
    var parts = splitLead(a.key_change);
    var labels = primaryBoundaryLabels(p.id);
    var primaryLimits = a.key_limits.filter(function (x) { return labels === null || labels.indexOf(x.label) !== -1; });
    var secondaryLimits = a.key_limits.filter(function (x) { return labels !== null && labels.indexOf(x.label) === -1; });
    var changeNodes = [el("p", { class: "change-lead", text: parts[0] })];
    if (parts[1]) changeNodes.push(el("details", { class: "quiet-disclosure" }, [
      el("summary", { text: "这次还更新了什么" }), el("p", { text: parts[1] })]));
    if (refMatch) changeNodes.push(el("p", { class: "direct-evidence" }, evButtons(p, [refMatch[1]])));
    panel.appendChild(el("div", { class: "layer1" }, [
      el("div", { class: "l1-item primary-change" }, changeNodes),
      primaryLimits.length ? el("ul", { class: "essential-limits" }, primaryLimits.map(function (x) {
        return el("li", {}, [el("b", { text: x.label + "：" }), x.text]);
      })) : null,
      secondaryLimits.length ? el("details", { class: "quiet-disclosure" }, [
        el("summary", { text: "使用前还要确认什么（" + secondaryLimits.length + " 项）" }),
        el("ul", { class: "secondary-limits" }, secondaryLimits.map(function (x) {
          return el("li", {}, [el("b", { text: x.label + "：" }), x.text]);
        }))]) : null]));

    var more = el("div", { class: "more topic-reader" });
    var topicNav = el("div", { class: "topic-nav", role: "group", "aria-label": "选择阅读主题，每次显示一个" });
    var topicContent = el("div", { class: "topic-content" });
    var sections = [
      { key: "audience", label: "适合谁", body: function (p) { return [el("p", { text: p.annotation.useful_for })]; } },
      { key: "facts", label: "具体改动", body: factsBody },
      { key: "tech", label: "使用条件", body: techBody },
      { key: "team", label: "团队能用在哪", body: teamBody },
      { key: "evidence", label: "证据", body: evidenceBody }];
    sections.forEach(function (s) {
      var bodyId = "acc-" + s.key;
      var open = !!state.open[s.key];
      var btn = el("button", { class: "acc-btn", type: "button", id: "btn-" + s.key, "aria-expanded": String(open),
        "aria-controls": bodyId, text: s.label, onclick: function () { toggle(s.key); } });
      var body = el("div", { class: "acc-body", id: bodyId, role: "region", "aria-labelledby": "btn-" + s.key, hidden: !open },
        s.body(p));
      topicNav.appendChild(btn);
      topicContent.appendChild(body);
    });
    more.appendChild(topicNav);
    more.appendChild(topicContent);
    panel.appendChild(more);
    panel.appendChild(el("details", { class: "quiet-disclosure review-note" }, [
      el("summary", { text: "为什么选入，谁审阅过" }),
      el("p", { class: "reader-foot", text: "入选理由：" + p.selection_reason + "（" + (p.decided_by || "") +
        "）。解读：" + (REVIEW[a.review_status] || a.review_status) + "。" })]));
    return panel;
  }

  function toggle(key, forceOpen) {
    var btn = $("btn-" + key);
    var body = $("acc-" + key);
    if (!btn || !body) return;
    var open = forceOpen || btn.getAttribute("aria-expanded") !== "true";
    Array.prototype.forEach.call(document.querySelectorAll(".acc-btn"), function (b) {
      b.setAttribute("aria-expanded", "false");
      var region = $(b.getAttribute("aria-controls"));
      if (region) region.hidden = true;
    });
    state.open = {};
    state.open[key] = open;
    btn.setAttribute("aria-expanded", String(open));
    body.hidden = !open;
    if (open) fadeIn("acc-" + key, body);
  }

  function locate(p, evId) {
    toggle("evidence", true);
    Array.prototype.forEach.call(document.querySelectorAll(".ev-located"), function (n) { n.classList.remove("ev-located"); });
    var item = $("ev-" + evId);
    if (!item) return;
    var orig = item.querySelector("details.ev-original");
    if (orig) orig.open = true;
    item.classList.add("ev-located");
    item.scrollIntoView({ block: "nearest", behavior: REDUCE.matches ? "auto" : "smooth" });
    item.focus({ preventScroll: true });
    animate("flash", item.querySelector(".flash"), [{ opacity: 0 }, { opacity: 1, offset: 0.25 }, { opacity: 0 }], 900);
  }

  function factsBody(p) {
    return [el("ul", {}, p.annotation.facts.map(function (f) {
      return el("li", {}, [f.text, " "].concat(evButtons(p, f.evidence)));
    }))];
  }

  function teamBody(p) {
    var a = p.annotation, tv = a.team_value;
    var facts = tv.facts.map(function (f) {
      return el("li", {}, [el("span", { class: "tagline tag-fact", text: "公开事实" }), f.text, " "]
        .concat(evButtons(p, f.evidence)).concat(bgLinks(f.background)));
    });
    return [
      el("dl", { class: "kv" }, [
        el("dt", { text: "方式" }), el("dd", { text: tv.mode }),
        el("dt", { text: "改善哪个步骤" }), el("dd", { text: tv.step }),
        el("dt", { text: "可能影响的指标" }), el("dd", { text: tv.metric }),
        el("dt", { text: "适合的用户任务" }), el("dd", { text: a.target_task })]),
      el("ul", {}, facts.concat([
        el("li", {}, [el("span", { class: "tagline tag-infer", text: "分析推断" }), tv.inference]),
        el("li", {}, [el("span", { class: "tagline tag-infer", text: "产品假设" }), a.hypothesis]),
        el("li", {}, [el("span", { class: "tagline tag-test", text: "待验证" }), tv.unverified])])),
      el("p", {}, [el("span", { class: "tagline tag-test", text: "最小验证建议（拟议，未执行）" }), a.experiment])];
  }

  function techBody(p) {
    var a = p.annotation;
    var items = [el("li", { text: a.tech }),
      el("li", { text: "许可：" + (p.license.spdx_id || "未声明") + "。" + p.license.adoption_note }),
      el("li", { text: "限制与未知：" + a.limitations })];
    if (p.other_events.length) items.push(el("li", { text: "窗口内其他事件：" + p.other_events.map(eventLine).join("、") }));
    if (p.newer_unreviewed.length) items.push(el("li", { text: "窗口内有更新的事件尚未核查：" + p.newer_unreviewed.map(eventLine).join("、") }));
    if (p.releases_truncated) items.push(el("li", { text: "发布列表达到单页上限，窗口内更早的发布可能未取全。" }));
    return [el("ul", {}, items)];
  }

  // Map each evidence id to the Chinese line(s) that cite it, so the default
  // view shows what the evidence is used for instead of the raw quote.
  function buildEvMap(p) {
    var a = p.annotation, map = {}, re = /（(?:依据\s*)?([a-z]\d+(?:、[a-z]\d+)*)）/g;
    function add(ids, cn) { ids.forEach(function (id) { (map[id] = map[id] || []).push(cn); }); }
    [a.key_change].concat(a.facts.map(function (f) { return f.text; }))
      .concat(a.key_limits.map(function (x) { return x.label + "：" + x.text; }))
      .forEach(function (cn) {
        re.lastIndex = 0;
        var hit;
        while ((hit = re.exec(cn))) {
          add(hit[1].split("、"), cn.replace(/（(?:依据\s*)?[a-z\d、]+）/g, ""));
        }
      });
    return map;
  }

  function evidenceBody(p) {
    var map = buildEvMap(p);
    return [el("ul", {}, p.annotation.evidence.map(function (ev) {
      var cn = map[ev.id] && map[ev.id].length ? map[ev.id][0] : ev.field_label;
      var orig = el("details", { class: "ev-original" }, [
        el("summary", { text: "查看原文" }),
        el("span", { class: "ev-head" }, [el("b", { text: ev.id }), el("span", { text: ev.field_label }),
          el("span", { class: "ev-badge", text: "已定位到此处" })]),
        el("p", { class: "ev-quote" }, [el("span", { class: "ctx", text: ev.before }), el("mark", { text: ev.quote }),
          el("span", { class: "ctx", text: ev.after })]),
        el("p", { class: "ev-src" }, [link(ev.url, "打开原文"), " · 原始响应 ", el("code", { text: ev.raw_file })])]);
      return el("li", { class: "ev", id: "ev-" + ev.id, tabindex: "-1" }, [
        el("span", { class: "flash", "aria-hidden": "true" }),
        el("p", { class: "ev-line" }, [el("span", { class: "ev-id-badge", text: ev.id }),
          el("span", { class: "ev-cn", text: cn })]),
        orig]);
    }))];
  }

  // ---------- sections below ----------
  function section(id, heading, lead, kids) {
    return el("section", { class: "section", id: id, "aria-labelledby": id + "-h" },
      [el("h2", { id: id + "-h", text: heading }), lead ? el("p", { class: "section-lead", text: lead }) : null].concat(kids));
  }
  function depChips(entry) {
    return el("p", { class: "judgment-deps" }, ["依据："].concat(entry.depends_on.map(function (d) {
      var p = projectById(d[0]);
      return p ? el("button", { class: "chip-btn", type: "button", text: short(p.name),
        onclick: function () { select(p.id, { scroll: true }); $("updates").scrollIntoView({ block: "start" }); } }) : null;
    })).concat(bgLinks(entry.background)));
  }

  function renderSignals(root) {
    var rows = brief.observations.map(function (o, i) {
      var validSignal = o.status === "valid";
      var content = el("div", { class: "signal-content", id: "signal-content-" + i, hidden: true },
        validSignal ? [el("p", { text: o.body }), depChips(o)] :
          [el("p", { class: "muted", text: "依据已变化或不在本期，待复核。" })]);
      var button = el("button", { class: "signal-trigger", type: "button", "aria-expanded": "false",
        "aria-controls": "signal-content-" + i, onclick: function () {
          var open = button.getAttribute("aria-expanded") !== "true";
          Array.prototype.forEach.call(document.querySelectorAll(".signal-trigger"), function (b) {
            b.setAttribute("aria-expanded", "false"); $(b.getAttribute("aria-controls")).hidden = true;
          });
          button.setAttribute("aria-expanded", String(open)); content.hidden = !open;
          if (open) fadeIn("signal", content);
        } }, [el("span", { class: "signal-num", text: pad(i + 1) }),
          el("span", { class: "signal-title", text: o.title }),
          el("span", { class: "signal-scope", text: validSignal ? o.scope + " · " + (o.depends_on || []).length + " 个项目" : "待复核" })]);
      return el("article", { class: "signal-row" }, [button, content]);
    });
    root.appendChild(section("s-signals", "几项更新共同说明什么", "只说明本期少量样本里的共同点，不外推为行业趋势。",
      [el("div", { class: "signal-map glass" }, rows)]));
  }

  var PLAN_FIELD_LABELS = [["why", "为什么先做"], ["target_users", "目标用户"], ["hypothesis", "假设"],
    ["control", "对照流程"], ["variable", "主要变量"], ["controls", "控制条件"], ["primary_metric", "主指标"],
    ["quality_cost", "质量与成本约束"], ["roles", "所需角色"], ["prerequisites", "前提"], ["sample", "样本与周期"],
    ["condition", "前提条件"], ["reason", "理由"], ["limits", "限制"]];

  function planItem(x) {
    if (x.status !== "valid") {
      return el("article", { class: "plan-item" }, [el("h3", { text: x.title }),
        el("p", { class: "muted", text: "依据已变化或不在本期，待复核。" })]);
    }
    var kids = [el("h3", {}, [el("span", { class: "pill", text: x.kind + (x.mode ? " · " + x.mode : "") }), x.title])];
    kids.push(el("dl", { class: "plan-grid" }, PLAN_FIELD_LABELS.filter(function (f) { return x[f[0]]; })
      .map(function (f) { return el("div", {}, [el("dt", { text: f[1] }), el("dd", { text: x[f[0]] })]); })));
    if (x.decision) kids.push(el("div", { class: "decision" },
      [["continue", "继续"], ["adjust", "调整"], ["stop", "停止"]].map(function (d) {
        return el("div", {}, [el("b", { text: d[1] }), x.decision[d[0]]]);
      })));
    kids.push(depChips(x));
    return el("article", { class: "plan-item" }, kids);
  }

  function renderPlan(root) {
    var plan = brief.team_plan, kids = [];
    var priority = plan.priority || [];
    if (priority.length && priority[0].status === "valid" && priority[0].short) {
      var x = priority[0];
      var actionParts = splitLead(x.short);
      kids.push(el("p", { class: "action-short", text: actionParts[0] }));
      if (actionParts[1]) kids.push(el("details", { class: "quiet-disclosure action-basis" }, [
        el("summary", { text: "为什么建议试，哪些还不确定" }), el("p", { text: actionParts[1] })]));
      kids.push(el("details", { class: "more-box" }, [el("summary", { text: "怎么试，怎样判断结果" }), planItem(x)]));
    } else {
      kids.push(el("p", { class: "muted", text: "优先建议待复核：其依据的项目解读已变化或不在本期。" }));
    }
    var cond = plan.conditional || [];
    if (cond.length) kids.push(el("details", { class: "more-box" },
      [el("summary", { text: "有条件实验（" + cond.length + " 项）" })].concat(cond.map(planItem))));
    var deferred = plan.deferred || [];
    if (deferred.length) kids.push(el("details", { class: "more-box" },
      [el("summary", { text: "暂缓清单（" + deferred.length + " 项）" })].concat(deferred.map(planItem))));
    kids.push(el("p", { class: "muted small", text: "以上建议均未执行；阈值、样本量和周期是建议值，需先建立基线。" }));
    root.appendChild(section("s-plan", "下一步试什么", null, kids));
  }

  function renderReview(root) {
    var kids = [];
    var pend = brief.pending.map(function (x) {
      return el("li", {}, [link(x.repo_url, x.name), "：" + eventLine(x.event) + "。", link(x.event.url, "来源"),
        el("br"), el("span", { class: "muted small", text: "原因：" + x.reasons.join("；") + "。简介：" + (x.description || "无") +
          (x.review_flag.length ? "。复核提示：" + x.review_flag.join(", ") : "") })]);
    });
    kids.push(el("h3", { class: "small muted", text: "有更新，尚未核实（" + brief.pending.length + "）" }),
      pend.length ? el("ul", { class: "list" }, pend) : el("p", { class: "muted small", text: "本期没有待核查项目。" }));
    var ch = brief.changes_since_previous;
    var changes = [];
    if (ch) {
      changes.push(el("li", { text: "对比上一期快照 " + ch.previous_run_id + "：新增 " + (ch.added.join("、") || "无") + "。" }));
      ch.removed.forEach(function (r) { changes.push(el("li", { text: "移出 " + r.name + "（" + (r.tag || "新建") + "）：" + r.reason })); });
    }
    (brief.dropped_decisions || []).forEach(function (d) {
      changes.push(el("li", { text: "已有核查记录但本期不适用：" + d.id + " " + (d.tag || d.event_id) + "，" + d.reason }));
    });
    kids.push(el("h3", { class: "small muted", text: "与上一期相比" }),
      changes.length ? el("ul", { class: "list" }, changes) : el("p", { class: "muted small", text: "无上一期快照可对比；没有失效的核查记录。" }));
    var exc = brief.excluded.map(function (x) {
      return el("li", {}, [el("b", { text: x.name + "：" }), x.reason + "。适用范围：" +
        (x.scope === "repo" ? "仓库整体，简介变化即失效。" : "仅该事件，出现新事件或说明变化即失效。"), link(x.evidence_url, "证据")]);
    }).concat(brief.manual_exclusions.map(function (m) {
      return el("li", {}, [el("b", { text: "检查前排除 " + m.repo + "：" }), m.explanation + "（" + (m.lapsed ? "已失效，本期重新检查" : "生效") +
        "；" + (m.recheck_when || "") + "）", link(m.evidence_url, "证据")]);
    }));
    kids.push(el("h3", { class: "small muted", text: "不纳入的理由" }), exc.length ? el("ul", { class: "list" }, exc) : el("p", { class: "muted small", text: "无" }));
    root.appendChild(section("s-pending", "其他项目为什么没选入", "“窗口内有事件”是自动状态，不等于值得推荐。这里的项目未经分析，不计入精选。", [
      el("details", { class: "more-box" }, [el("summary", { text: "查看其他项目和未入选原因" })].concat(kids))]));
  }

  function renderBackground(root) {
    var items = (brief.background || []).map(function (b) {
      return el("li", { id: "bg-" + b.id }, [el("b", { text: b.title }), " ",
        el("span", { class: "pill", text: SRC[b.type] || b.type }), " ", el("span", { class: "pill", text: "查阅 " + b.accessed_at }),
        el("br"), b.supports, el("br"), el("span", { class: "muted small", text: "边界：" + b.limits + " " }), link(b.url, "页面")]);
    });
    var box = el("details", { class: "more-box" },
      [el("summary", { text: "展开背景资料（" + (brief.background || []).length + " 条）" }),
       el("p", { class: "muted small", text: "区分公开事实（页面写明）、分析推断与待验证假设。" }),
       el("ul", { class: "list" }, items)]);
    root.appendChild(section("s-background", "这些更新与团队有什么关系", "可早于30天窗口，只用于判断与目标团队的关系。", [box]));
  }

  function renderMethod(root) {
    var events = brief.projects.map(function (p) { return day(p.event.published_at); }).sort();
    var dates = [["事件窗口", meta.window_start + " 至 " + meta.window_end + "（UTC，含起点不含终点）"],
      ["精选事件日期", events.length ? events[0] + " 至 " + events[events.length - 1] : "本期无"],
      ["数据抓取时间", meta.as_of + "（期次 " + meta.run_id + "，状态 " + meta.run_status + "）"],
      ["报告生成时间", meta.generated_at + "（" + (meta.mode === "offline" ? "离线重建" : "联网刷新") + "）"]];
    if (meta.background_accessed_at && meta.background_accessed_at.length) dates.push(["背景资料查阅日期", meta.background_accessed_at.join("、")]);
    var total = brief.candidates.length;
    var steps = [["检索到的候选", total], ["实际检查", total - sum("not_checked") - sum("manually_excluded")],
      ["窗口内有事件", sum("qualified")], ["正式精选", brief.projects.length], ["待核查", brief.pending.length]];
    var funnel = el("div", { class: "funnel", role: "img", "aria-label": steps.map(function (s) { return s[0] + " " + s[1]; }).join("，") },
      steps.map(function (s) {
        return el("div", { class: "bar-row", "aria-hidden": "true" }, [el("span", { text: s[0] }),
          el("span", { class: "bar-track" }, [el("span", { class: "bar", style: "display:block;width:" + (total ? Math.max(2, 100 * s[1] / total) : 0) + "%" })]),
          el("span", { class: "bar-n", text: String(s[1]) })]);
      }));
    var cov = el("div", { class: "table-wrap" }, [el("table", {}, [el("thead", {}, [el("tr", {}, ["检索分类", "候选", "有事件", "无合格事件", "人工排除", "未检查", "检查失败"].map(function (h, i) {
      return el("th", { class: i ? "num" : null, text: h }); }))]), el("tbody", {}, brief.coverage.map(function (c) {
      return el("tr", {}, [el("td", { text: c.label + (c.search_failed ? "（搜索失败）" : "") })].concat(
        [c.candidates, c.qualified, c.checked_no_event, c.manually_excluded, c.not_checked, c.check_failed].map(function (n) {
          return el("td", { class: "num", text: String(n) }); })));
    }))])]);
    var scope = el("div", { class: "table-wrap" }, [el("table", {}, [el("thead", {}, [el("tr", {}, ["分类", "检索", "GitHub匹配总数", "实际取回", "截断"].map(function (h, i) {
      return el("th", { class: i > 1 ? "num" : null, text: h }); }))]), el("tbody", {}, (brief.scope.searches || []).map(function (s) {
      return el("tr", {}, [el("td", { text: catLabel(s.category) }), el("td", { text: KIND[s.kind] || s.kind }),
        el("td", { class: "num", text: s.total_count === null ? "失败" : String(s.total_count) }), el("td", { class: "num", text: String(s.returned) }),
        el("td", { class: "num", text: s.truncated ? "是" : "否" })]);
    }))])]);
    var q = meta.quota;
    var notes = el("ul", { class: "list small" }, [
      "数据源：GitHub REST API，单一来源；运行时不调用模型。",
      "每类两次检索：近期有推送的仓库按Stars排序（偏向成熟项目），窗口内新建的仓库按Stars排序（照顾新项目）。每条只取前 " +
        meta.search_config.s1_per_page + " 或 " + meta.search_config.s2_per_page + " 个，排名之后的仓库没有进入候选。",
      "每类检查 " + q.per_category + " 个候选，其中 " + (q.s2_reserved || 1) + " 个名额留给窗口内新建的仓库；请求上限 " + q.request_cap +
        " 次，本期实际 " + meta.request_count + " 次；候选中 " + sum("not_checked") + " 个未检查。",
      "关键词（awesome、prompts、paper等，整词匹配）只降低检查顺序并提示复核，不阻止识别新建仓库，也不直接排除。",
      "进入正式精选必须有核查记录；没有记录的有事件项目进入待核查，不会被默认规则补进精选。",
      "失败或跳过的请求：" + (meta.errors.length ? meta.errors.map(function (e) { return "#" + e.seq + " " + e.purpose + " " + (e.repo || e.category) + " " + e.error; }).join("；") : "无") + "。",
      "Stars 是抓取时累计值，只有一次观测，不表示增长。"].map(function (t) { return el("li", { text: t }); }));
    var stars = el("div", { class: "table-wrap" }, [el("table", {}, [el("thead", {}, [el("tr", {},
      ["项目", "Stars", "许可"].map(function (h) { return el("th", { text: h }); }))]),
      el("tbody", {}, brief.projects.map(function (p) {
        return el("tr", {}, [el("td", { text: p.name }), el("td", { class: "num", text: String(p.stars_snapshot) }),
          el("td", { text: p.license.spdx_id || "未声明" })]);
      }))])]);
    var kids = [el("details", { class: "more-box" }, [el("summary", { text: "时间与抓取信息" }),
      el("dl", { class: "dates" }, [].concat.apply([], dates.map(function (d) { return [el("dt", { text: d[0] }), el("dd", { text: d[1] })]; })))]),
      funnel, el("details", { class: "more-box" }, [el("summary", { text: "覆盖统计、检索截断与方法" }),
        el("h3", { class: "small muted", text: "覆盖统计（按检索分类）" }), cov,
        el("ul", { class: "list small" }, (brief.category_gaps || []).map(function (g) { return el("li", { text: g.text }); })),
        el("h3", { class: "small muted", text: "各项目抓取时累计 Stars（一次观测，不代表增长）" }), stars,
        el("h3", { class: "small muted", text: "检索范围与截断" }), scope, notes])];
    var s = section("s-method", "数据怎么来的", null, kids);
    root.appendChild(s);
    if (!REDUCE.matches && "IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (entries) {
        if (entries[0].isIntersecting) { funnel.classList.add("play"); io.disconnect(); }
      });
      io.observe(funnel);
    }
  }

  // ---------- one-click update ----------
  // The page asks /api/refresh (Cloudflare Pages Function) to start the GitHub Actions workflow, then polls
  // /api/status until the run finishes and the redeployed site serves the new period.
  var POLL_MS = 8000;
  var TIMEOUT_MS = 12 * 60 * 1000;
  var UPDATED_KEY = "signal-updated-run";

  function setBusy(btn, text) {
    btn.disabled = !!text;
    btn.setAttribute("aria-busy", String(!!text));
    btn.textContent = text || "一键更新";
  }
  function getJSON(url, opts) {
    var o = opts || {};
    o.cache = "no-store";
    o.headers = { Accept: "application/json" };
    return fetch(url, o).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (body) { return { status: r.status, body: body }; });
    });
  }
  function setupUpdate() {
    var btn = $("refresh");
    if (!btn) return;
    btn.addEventListener("click", function () {
      if (location.protocol === "file:") {
        toast("本地打开的页面不能联网更新：请在项目目录运行 python3 collect.py --refresh，或打开线上看板使用一键更新。");
        return;
      }
      startUpdate(btn);
    });
    var done = null;
    try { done = sessionStorage.getItem(UPDATED_KEY); sessionStorage.removeItem(UPDATED_KEY); } catch (e) { done = null; }
    if (done && done === meta.run_id) toast("已更新到最新一期（" + runDay(meta.run_id) + "）。" + diffSummaryText() + "。");
  }
  function startUpdate(btn) {
    setBusy(btn, "提交中…");
    getJSON("/api/refresh", { method: "POST" }).then(function (res) {
      var b = res.body || {};
      if (res.status === 202 || (res.status === 409 && b.running)) {
        toast(res.status === 202 ? "已提交更新：正在抓取 GitHub 数据，通常需要 2–3 分钟，期间可继续阅读。"
          : "已有更新任务在运行，正在跟踪它的进度。");
        pollRun(btn, b.requested_at, Date.now());
        return;
      }
      setBusy(btn, null);
      toast((b.message || "更新请求失败（HTTP " + res.status + "）") + " 当前数据未改变。");
    }).catch(function () {
      setBusy(btn, null);
      toast("无法连接更新服务（本页需部署在 Cloudflare Pages 上才能一键更新）。当前数据未改变。");
    });
  }
  function pollRun(btn, since, started) {
    function later() { setTimeout(function () { pollRun(btn, since, started); }, POLL_MS); }
    if (Date.now() - started > TIMEOUT_MS) {
      setBusy(btn, null);
      toast("更新超过 12 分钟仍未完成，请稍后刷新页面查看。当前数据未改变。");
      return;
    }
    getJSON("/api/status?since=" + encodeURIComponent(since || "")).then(function (res) {
      var s = res.body || {};
      if (s.state === "completed" && s.conclusion === "success") {
        if (!s.latest_run_id || s.latest_run_id === meta.run_id) {
          setBusy(btn, null);
          toast("抓取已完成，但本次没有产生可替换的新一期（可能部分请求失败）。当前数据未改变，详情见 GitHub Actions 日志。");
          return;
        }
        setBusy(btn, "部署中…");
        waitDeploy(btn, s.latest_run_id, started);
        return;
      }
      if (s.state === "completed") {
        setBusy(btn, null);
        toast("更新任务未成功（" + (s.conclusion || "未知") + "）。当前数据未改变。");
        return;
      }
      setBusy(btn, "抓取中…");
      later();
    }).catch(later);
  }
  function waitDeploy(btn, runId, started) {
    if (Date.now() - started > TIMEOUT_MS) {
      setBusy(btn, null);
      toast("新数据已生成（" + runDay(runId) + "），网站仍在部署，请稍后刷新页面。");
      return;
    }
    getJSON("../data/current.json?t=" + Date.now()).then(function (res) {
      if (res.body && res.body.run_id === runId) {
        try { sessionStorage.setItem(UPDATED_KEY, runId); } catch (e) { /* toast after reload is optional */ }
        location.reload();
        return;
      }
      setTimeout(function () { waitDeploy(btn, runId, started); }, POLL_MS);
    }).catch(function () { setTimeout(function () { waitDeploy(btn, runId, started); }, POLL_MS); });
  }

  // ---------- boot ----------
  function boot() {
    renderTop();
    var app = $("app");
    renderJudgment(app);
    renderDirectory(app);
    renderSignals(app);
    renderPlan(app);
    renderReview(app);
    renderBackground(app);
    renderMethod(app);
    app.appendChild(el("p", { class: "footer" }, ["同一数据源生成的 Markdown 简报：", el("a", { href: "../report.md", text: "report.md" }),
      "。每周二、五自动更新，也可点顶部「一键更新」手动更新。Signal 是作品工作名，与任何公司无隶属关系。"]));
    refreshList();
    app.hidden = false;
    var navLinks = Array.prototype.slice.call(document.querySelectorAll(".section-link"));
    function markSection(id) {
      navLinks.forEach(function (a) {
        if (a.getAttribute("data-section") === id) a.setAttribute("aria-current", "location");
        else a.removeAttribute("aria-current");
      });
    }
    navLinks.forEach(function (a) {
      a.setAttribute("href", "#" + a.getAttribute("data-section"));
      a.addEventListener("click", function () { markSection(a.getAttribute("data-section")); });
    });
    if ("IntersectionObserver" in window) {
      var navObserver = new IntersectionObserver(function (entries) {
        var visible = entries.filter(function (e) { return e.isIntersecting; });
        if (visible.length) markSection(visible[0].target.getAttribute("id"));
      }, { rootMargin: "-80px 0px -55% 0px", threshold: 0 });
      navLinks.forEach(function (a) { var target = $(a.getAttribute("data-section")); if (target) navObserver.observe(target); });
    }
    app.addEventListener("toggle", function (ev) {
      if (ev.target.tagName !== "DETAILS" || !ev.target.open) return;
      Array.prototype.forEach.call(ev.target.children, function (n, i) {
        if (n.tagName !== "SUMMARY") fadeIn("disclosure-" + i, n);
      });
    }, true);
    var fb = $("fallback");
    if (fb) fb.remove();
    var onWidth = function () { placeReader(false); };
    if (WIDE.addEventListener) WIDE.addEventListener("change", onWidth);
    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape" && state.selected && !WIDE.matches) close();
    });
  }

  try { boot(); } catch (err) {
    var app = $("app");
    if (app) app.hidden = true;
    fail(err);
  }
})();
