# 部署与一键更新

线上链路：看板「一键更新」→ Cloudflare Pages Function `/api/refresh` → GitHub Actions `refresh-data` 运行 `collect.py --refresh` → 新数据提交回仓库 → Cloudflare Pages 自动重新部署 → 页面检测到新一期后自动刷新，项目更新列表标出与上一期的差异。

定时：每周二、周五 01:00 UTC（北京时间 09:00）自动运行一次。手动更新有 10 分钟冷却，同一时间只跑一个任务。

## 组成

| 文件 | 作用 |
|---|---|
| `.github/workflows/refresh.yml` | 定时与手动触发；先跑测试，再抓取、重建，最后提交 `data/`、`report.md`、`site/` |
| `functions/api/refresh.js` | POST：检查冷却与运行中任务，触发 workflow |
| `functions/api/status.js` | GET：返回本次任务进度，完成后返回仓库里 `data/current.json` 的期次 |
| `diff.py` | 当期与上一期快照对比，写入 `brief.json` 的 `diff` 字段和 `data/diff.json` |
| `_redirects` | 站点根路径跳转到 `/site/` |

失败保护沿用脚本原有规则：全部失败不提交新数据；部分成功且已有上一期时不替换当前期。页面只在新一期真正部署后才刷新。

## 一次性配置

1. **Cloudflare Pages 连接仓库**：Workers & Pages → Create → Pages → Connect to Git → 选 `gloriatan/aigc-signal`。
   - Framework preset：None；Build command：留空；Build output directory：`/`
   - 生产分支：`main`
2. **GitHub 令牌**（给按钮触发 Actions 用）：GitHub → Settings → Developer settings → Fine-grained tokens → 只选 `aigc-signal` 仓库，权限 Actions: Read and write、Contents: Read-only。
3. **把令牌存进 Cloudflare**：Pages 项目 → Settings → Variables and Secrets → 添加 Secret `GITHUB_TOKEN`（Production）。保存后在 Deployments 里重新部署一次。

可选变量：`GITHUB_REPO`（默认 `gloriatan/aigc-signal`）、`GITHUB_BRANCH`（默认 `main`）、`WORKFLOW_FILE`（默认 `refresh.yml`）。

Actions 抓取用的是 GitHub 自动提供的 `GITHUB_TOKEN`，不需要另配。

## 本地

```sh
python3 collect.py --refresh                     # 本地联网更新
python3 -m unittest discover -s tests            # Python 测试
node tests/test_functions.mjs                    # 两个 Pages Function 的测试（模拟 GitHub）
npx wrangler pages dev . --port 8788             # 本地预览站点和函数（未配令牌时按钮会提示）
```

双击打开 `site/index.html` 时没有后端，「一键更新」会提示改用 `python3 collect.py --refresh`。
