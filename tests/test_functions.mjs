// Cloudflare Pages Functions for the one-click update, tested with a fake GitHub API. Run: node tests/test_functions.mjs
import assert from "node:assert/strict";
import { onRequestPost as refresh } from "../functions/api/refresh.js";
import { onRequestGet as status } from "../functions/api/status.js";

const env = { GITHUB_TOKEN: "test-token", GITHUB_REPO: "o/r" };
const minutesAgo = (m) => new Date(Date.now() - m * 60000).toISOString();

function fakeGitHub({ runs = [], dispatchStatus = 204, current = { run_id: "R2" } } = {}) {
  const calls = [];
  globalThis.fetch = async (url, init = {}) => {
    calls.push({ url, method: init.method || "GET" });
    if (url.includes("/dispatches")) return new Response(null, { status: dispatchStatus });
    if (url.includes("/runs")) return Response.json({ workflow_runs: runs });
    if (url.includes("/contents/data/current.json")) return new Response(JSON.stringify(current));
    return new Response("not found", { status: 404 });
  };
  return calls;
}

const post = (origin = "https://aigc-signal.pages.dev") =>
  new Request("https://aigc-signal.pages.dev/api/refresh", { method: "POST", headers: { Origin: origin } });

async function body(res) { return { status: res.status, json: await res.json() }; }

const tests = {
  "dispatches when idle": async () => {
    const calls = fakeGitHub({ runs: [{ status: "completed", created_at: minutesAgo(30) }] });
    const r = await body(await refresh({ request: post(), env }));
    assert.equal(r.status, 202);
    assert.ok(r.json.requested_at);
    assert.ok(calls.some((c) => c.url.endsWith("/actions/workflows/refresh.yml/dispatches") && c.method === "POST"));
  },
  "cooldown within 10 minutes": async () => {
    const calls = fakeGitHub({ runs: [{ status: "completed", created_at: minutesAgo(3) }] });
    const r = await body(await refresh({ request: post(), env }));
    assert.equal(r.status, 429);
    assert.ok(!calls.some((c) => c.url.includes("/dispatches")));
  },
  "running run is reported, not duplicated": async () => {
    fakeGitHub({ runs: [{ status: "in_progress", created_at: minutesAgo(1) }] });
    const r = await body(await refresh({ request: post(), env }));
    assert.equal(r.status, 409);
    assert.equal(r.json.running, true);
  },
  "cross-site POST rejected": async () => {
    fakeGitHub();
    assert.equal((await refresh({ request: post("https://evil.example"), env })).status, 403);
  },
  "missing token is a clear 503": async () => {
    fakeGitHub();
    assert.equal((await refresh({ request: post(), env: {} })).status, 503);
  },
  "status waits, then reports the new run id": async () => {
    const since = new Date().toISOString();
    fakeGitHub({ runs: [{ status: "completed", conclusion: "success", created_at: minutesAgo(30) }] });
    let r = await body(await status({ request: new Request(`https://x/api/status?since=${since}`), env }));
    assert.equal(r.json.state, "waiting");
    fakeGitHub({ runs: [{ status: "completed", conclusion: "success", created_at: new Date().toISOString(), html_url: "u" }] });
    r = await body(await status({ request: new Request(`https://x/api/status?since=${since}`), env }));
    assert.equal(r.json.state, "completed");
    assert.equal(r.json.latest_run_id, "R2");
  },
};

let failed = 0;
for (const [name, fn] of Object.entries(tests)) {
  try { await fn(); console.log("ok  ", name); } catch (e) { failed += 1; console.log("FAIL", name, e.message); }
}
process.exit(failed ? 1 : 0);
