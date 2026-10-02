# 部署与一键更新

线上地址：https://aigc-signal.pages.dev （根路径跳转到 `/site/`）

线上链路：看板「一键更新」→ Cloudflare Pages Function `/api/refresh` → GitHub Actions `refresh-data` 运行 `collect.py --refresh` → 新数据提交回仓库 → 同一工作流用 wrangler 部署到 Cloudflare Pages → 页面检测到新一期后自动刷新，项目更新列表标出与上一期的差异。

定时：每周二、周五 01:00 UTC（北京时间 09:00）自动运行一次。手动更新有 10 分钟冷却，同一时间只跑一个任务。

## 组成

| 文件 | 作用 |
|---|---|
| `.github/workflows/refresh.yml` | 定时与手动触发；先跑测试，再抓取、重建，提交 `data/`、`report.md`、`site/`，最后部署 |
| `.github/workflows/deploy.yml` | 代码推送到 main 后部署 |
| `functions/api/refresh.js` | POST：检查冷却与运行中任务，触发 workflow |
| `functions/api/status.js` | GET：返回本次任务进度，完成后返回仓库里 `data/current.json` 的期次 |
| `diff.py` | 当期与上一期快照对比，写入 `brief.json` 的 `diff` 字段和 `data/diff.json` |
| `_redirects` | 站点根路径跳转到 `/site/` |

失败保护沿用脚本原有规则：全部失败不提交新数据；部分成功且已有上一期时不替换当前期。页面只在新一期真正部署后才刷新。

## 一次性配置

Pages 项目 `aigc-signal` 用 wrangler 直接上传方式创建（不连 Git），仓库变量 `CLOUDFLARE_ACCOUNT_ID` 已设置。还需要两个令牌，由账号本人创建并在终端提示里粘贴：

1. **按钮触发更新用的 GitHub 令牌**：GitHub → Settings → Developer settings → Fine-grained tokens → Generate new token。Repository access 只选 `aigc-signal`；权限 Actions: Read and write、Contents: Read-only。然后运行：
   ```sh
   npx wrangler pages secret put GITHUB_TOKEN --project-name aigc-signal
   ```
2. **Actions 自动部署用的 Cloudflare 令牌**：Cloudflare → My Profile → API Tokens → Create Token → Custom token，权限 Account / Cloudflare Pages / Edit。然后运行：
   ```sh
   gh secret set CLOUDFLARE_API_TOKEN -R gloriatan/aigc-signal
   ```

配好后重新部署一次（`npx wrangler pages deploy . --project-name aigc-signal --branch main`，或在 GitHub Actions 里手动运行 deploy-pages），Pages 的新密钥在下一次部署时生效。

没配 Cloudflare 令牌时，Actions 照常抓取和提交，只跳过部署；没配 GitHub 令牌时，按钮会提示“更新服务未配置 GITHUB_TOKEN”，数据不变。

可选 Pages 变量：`GITHUB_REPO`（默认 `gloriatan/aigc-signal`）、`GITHUB_BRANCH`（默认 `main`）、`WORKFLOW_FILE`（默认 `refresh.yml`）。

## 本地

```sh
python3 collect.py --refresh                     # 本地联网更新
python3 -m unittest discover -s tests            # Python 测试
node tests/test_functions.mjs                    # 两个 Pages Function 的测试（模拟 GitHub）
npx wrangler pages dev . --port 8788             # 本地预览站点和函数（未配令牌时按钮会提示）
```

双击打开 `site/index.html` 时没有后端，「一键更新」会提示改用 `python3 collect.py --refresh`。
