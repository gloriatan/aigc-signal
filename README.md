# Signal · AIGC开源动态简报

用 GitHub 公开 API 抓取近30天 AIGC 开源项目的版本发布与新建仓库，经过核查后生成结构化简报。读者是同花顺 AI创新／出海产品团队的产品、算法与增长人员。

压缩包内的数据快照：`20261002T093816Z`，事件窗口 2026-09-02 09:38:16 UTC 至 2026-10-02 09:38:16 UTC（含起点不含终点）。本期正式精选 5 项，另有 3 项待核查、4 项经核查排除。

## 线上版本

- 看板：https://aigc-signal.pages.dev （每周二、五北京时间 09:00 自动更新；页面顶部「一键更新」可手动触发）
- 代码与运行记录：https://github.com/gloriatan/aigc-signal （Actions 页可查看每次抓取、测试与部署的日志）
- 压缩包是某一期的离线快照，线上版会继续逐期更新，并与上一期对比标出变化。部署细节见 `DEPLOY.md`。

## 对照题目

| 题目要求 | 本作品 |
|---|---|
| 借助 AI 编写脚本 | 代码、解读与建议由 AI 起草，过程与人工决定记录在 `AI_USAGE.md` |
| 调用第三方 API | GitHub REST API；每次请求的原始响应落盘并记录哈希（`data/runs/`） |
| 近30天 AIGC 前沿项目（技术或产品） | UTC 30天窗口；四个 AIGC topic；按发布、预发布、新建仓库判定事件 |
| 总结为结构化简报 | `report.md`：本期判断、项目更新、团队下一步、待核查与排除、数据与方法 |
| 自动化 Python 脚本，能抓取并生成 Markdown | `python3 collect.py --refresh`；线上由 GitHub Actions 定时运行 |
| 或趋势看板网页 | `site/index.html`（离线可开）与线上看板；逐期对比形成趋势记录 |
| 打包为一个压缩包，30MB 以内 | 本压缩包 |

## 打开哪个文件

双击 `site/index.html`，不联网、不安装。首页是一句本期判断和更新目录，点一行看详情，“查看依据”定位到原文摘录。右上角“导出 Markdown”一键下载完整简报。

`report.md` 是同一份数据生成的 Markdown 简报（原题要求的报告），内容与看板一致。看板脚本加载失败时，页面会直接显示完整简报正文。

## 运行

需要 Python 3.9 及以上，只用标准库，无需安装依赖。命令都在本目录下执行。

```sh
python3 collect.py --refresh                 # 联网：调用 GitHub API 抓取新一期，生成全部输出
python3 collect.py --offline                 # 不联网：用随包的原始响应重建当前期
python3 collect.py --offline --run <run_id>  # 重建历史期，输出到 data/runs/<run_id>/rebuild/
python3 collect.py --accept-partial <run_id> # 手动采用一个“部分成功”的期
python3 -m unittest discover -s tests        # 运行测试（不联网，约1秒）
```

可选：设置环境变量 `GITHUB_TOKEN` 提高 GitHub 限额（未设置也能运行，本期即未使用令牌）。令牌只从环境变量读取，不写入任何文件。

退出码：0 成功；1 部分成功；2 失败或离线输入缺失；3 参数或配置错误。

刷新的保护规则：
- 全部搜索失败：不生成输出，上一期报告保持不变。
- 部分成功且已有上一期：不替换当前期，需手动 `--accept-partial`。首次运行时直接采用，报告顶部标明缺口。
- 每次发布都在 `data/runs/<run_id>/snapshot/` 留存当期的 brief 和 Markdown，上一期快照不会被覆盖（`20261001T210300Z` 的快照是原提交版本的输出原样）。
- 离线重建只读本地原始响应，并校验每个文件的 SHA-256，缺失或被改动就报错退出。

## 一键更新与对比上期

线上版每周二、五自动更新，也可以点顶部「一键更新」手动更新。每次更新都和上一期快照对比：项目更新列表标出“新增”“新版本”，移出的项目单独列出原因，标题下方给出汇总，可切换“只看变化”。对比结果同时写在 `data/diff.json`。部署方式见 `DEPLOY.md`。

## 每期怎么出精选

脚本只判断“窗口内有没有事件”，不判断值不值得推荐。进入正式精选要在 `selection.json` 里有核查记录：

- `decision: "select"`：绑定仓库、事件ID和来源哈希，三项核查（AIGC相关、实质变化、来源可查）都为 true，并写明理由。
- `decision: "exclude"`：写明理由和证据。`scope: "event"` 只对该事件生效，出现新事件或说明改动就回到待核查；`scope: "repo"` 在仓库简介哈希不变时生效，简介变了就回到待核查。
- 没有记录的有事件项目一律进入“待核查”，只列事实和来源，不会被默认规则补进精选。

记录按事件而不是按期次绑定，所以上一期的有效判断在新一期仍然适用。事件移出窗口或来源变化后，记录自动失效，报告的“移出与变化”会写明原因。

项目解读在 `annotations.json`，按“仓库 + 事件ID + 版本号 + 来源哈希”绑定。每条解读里的 `evidence.quote` 必须逐字出现在当前来源中，否则整条解读降为“待复核”，页面只显示原文摘录。本期判断、跨项目信号和团队建议都声明了依赖的项目和背景资料，依赖失效时同样降级。商业背景资料在 `context.json`，写明查阅日期和能支持的表述。

## 方法要点

- 数据源只有 GitHub REST API，四个 topic：`text-to-video`、`image-generation`、`text-to-speech`、`talking-head`。运行时不调用任何模型。
- 每个 topic 检索两次：近期有推送的仓库按 Stars 取前20，窗口内新建的仓库按 Stars 取前10。每类检查4个候选，其中2个名额留给新建仓库，请求上限48次（本期32次）。
- 事件优先级：窗口内最新的正式发布 > 预发布 > 窗口内新建仓库（README不少于300字）。草稿和单纯提交不算事件。
- awesome、prompts、paper 等关键词按整词匹配，只降低检查顺序并提示复核，不阻止新建仓库事件，也不直接排除。

## 已知限制

- 覆盖面小：GitHub 对每条检索匹配到24至2368个仓库，本工具只取 Stars 排名靠前的10或20个；候选中还有 92 个因名额未检查。报告“检索范围与截断”表列出了每条检索的匹配总数和实际取回数。
- 按 Stars 排序偏向成熟项目，靠“新建仓库”检索和预留名额部分弥补，但仍会漏掉 topic 标注不全或排名靠后的项目。
- Stars 只有一次观测，不能说明增长。
- 项目解读、本期判断和团队建议由 AI 起草，标为“AI草稿，未经本人审阅”。新出现的待核查项目没有分析。
- 拟议实验都没有执行；样本量、周期、阈值是建议值。
- 商业背景资料按 2026-10-02 查阅时的页面内容引用，页面以后可能变化。

## 文件

```text
collect.py        抓取、窗口判断、去重、请求预算、失败保护、离线重建、命令入口
editorial.py      核查记录 → 正式精选 / 待核查 / 排除 / 失效记录
diff.py           当期与上一期对比（新增、新版本、移出、新进入待核查）
functions/        Cloudflare Pages Functions：/api/refresh 触发更新，/api/status 查询进度
.github/          GitHub Actions：每周二、五定时更新，也接受一键更新触发
brief.py          组装 brief.json：覆盖统计、解读与证据匹配、依赖校验
render.py         生成 report.md 与 site/data.js
render_html.py    生成 site/index.html（含脚本失败时显示的完整简报）
config.json       topic、检索参数、名额、阈值、检查前排除清单
selection.json    核查记录（入选与排除，带理由、证据、适用范围）
annotations.json  项目解读、证据摘录、本期判断、跨项目信号、团队下一步
context.json      商业背景资料与查阅日期
report.md         当前期 Markdown 简报（生成文件）
data/             current.json 指针、brief.json、各期 manifest、原始响应和快照
site/             看板：index.html、style.css、app.js、data.js
tests/            测试，HTTP 全部为合成数据
AI_USAGE.md       AI 使用记录
ACCEPTANCE.md     本次验收记录
```

Signal 是作品工作名，与任何公司无隶属关系。
