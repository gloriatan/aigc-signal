// GET /api/status?since=<ISO time> — progress of the workflow run started at or after `since`,
// plus the run_id that data/current.json points to on the branch once the run has finished.

const SINCE_TOLERANCE_MS = 60 * 1000;

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}

function config(env) {
  return {
    token: env.GITHUB_TOKEN,
    repo: env.GITHUB_REPO || "gloriatan/aigc-signal",
    ref: env.GITHUB_BRANCH || "main",
    workflow: env.WORKFLOW_FILE || "refresh.yml",
  };
}

function github(cfg, path, accept = "application/vnd.github+json") {
  const headers = { Accept: accept, "User-Agent": "aigc-signal-pages", "X-GitHub-Api-Version": "2022-11-28" };
  if (cfg.token) headers.Authorization = `Bearer ${cfg.token}`;
  return fetch("https://api.github.com" + path, { headers });
}

async function currentRunId(cfg) {
  const res = await github(cfg, `/repos/${cfg.repo}/contents/data/current.json?ref=${encodeURIComponent(cfg.ref)}`,
    "application/vnd.github.raw+json");
  if (!res.ok) return null;
  try {
    return JSON.parse(await res.text()).run_id || null;
  } catch {
    return null;
  }
}

export async function onRequestGet({ request, env }) {
  const cfg = config(env);
  const sinceParam = new URL(request.url).searchParams.get("since");
  const since = sinceParam ? Date.parse(sinceParam) - SINCE_TOLERANCE_MS : 0;

  const runsRes = await github(cfg, `/repos/${cfg.repo}/actions/workflows/${cfg.workflow}/runs?per_page=5`);
  if (!runsRes.ok) return json({ state: "unknown", message: `GitHub HTTP ${runsRes.status}` }, 502);
  const runs = (await runsRes.json()).workflow_runs || [];
  const run = runs.find((r) => Date.parse(r.created_at) >= since);
  if (!run) return json({ state: "waiting" });

  const body = { state: run.status, conclusion: run.conclusion, run_url: run.html_url, started_at: run.created_at };
  if (run.status === "completed") body.latest_run_id = await currentRunId(cfg);
  return json(body);
}
