// POST /api/refresh — start the "refresh-data" GitHub Actions workflow for the one-click update button.
// Secrets/vars (Cloudflare Pages → Settings → Variables): GITHUB_TOKEN (secret, fine-grained token with
// Actions: read & write on the repo), optional GITHUB_REPO, GITHUB_BRANCH, WORKFLOW_FILE.

const COOLDOWN_MS = 10 * 60 * 1000;

function json(body, status) {
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

function github(cfg, path, init = {}) {
  return fetch("https://api.github.com" + path, {
    ...init,
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${cfg.token}`,
      "User-Agent": "aigc-signal-pages",
      "X-GitHub-Api-Version": "2022-11-28",
      ...(init.headers || {}),
    },
  });
}

function sameOrigin(request) {
  const origin = request.headers.get("Origin");
  if (!origin) return true;
  try {
    return new URL(origin).host === new URL(request.url).host;
  } catch {
    return false;
  }
}

export async function onRequestPost({ request, env }) {
  const cfg = config(env);
  if (!cfg.token) return json({ ok: false, message: "更新服务未配置 GITHUB_TOKEN。" }, 503);
  if (!sameOrigin(request)) return json({ ok: false, message: "拒绝跨站请求。" }, 403);

  const runsRes = await github(cfg, `/repos/${cfg.repo}/actions/workflows/${cfg.workflow}/runs?per_page=1`);
  if (!runsRes.ok) return json({ ok: false, message: `无法读取更新任务状态（GitHub HTTP ${runsRes.status}）。` }, 502);
  const latest = ((await runsRes.json()).workflow_runs || [])[0];
  if (latest && latest.status !== "completed") {
    return json({ ok: false, running: true, requested_at: latest.created_at, message: "已有更新任务在运行。" }, 409);
  }
  if (latest) {
    const age = Date.now() - Date.parse(latest.created_at);
    if (age < COOLDOWN_MS) {
      const minutes = Math.ceil((COOLDOWN_MS - age) / 60000);
      return json({ ok: false, retry_after_min: minutes, message: `距上次更新不足 10 分钟，请约 ${minutes} 分钟后再试。` }, 429);
    }
  }

  const requestedAt = new Date().toISOString();
  const dispatch = await github(cfg, `/repos/${cfg.repo}/actions/workflows/${cfg.workflow}/dispatches`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ ref: cfg.ref }),
  });
  if (dispatch.status !== 204) {
    return json({ ok: false, message: `触发更新失败（GitHub HTTP ${dispatch.status}）。` }, 502);
  }
  return json({ ok: true, requested_at: requestedAt }, 202);
}

export function onRequestGet() {
  return json({ ok: false, message: "请用 POST 调用。" }, 405);
}
