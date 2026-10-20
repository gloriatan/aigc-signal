# 近 30 天 AIGC 开源更新看板

> 本期判断待复核：其依据的项目解读已变化或不在本期。

- 事件窗口：2026-09-20T05:38:31Z 至 2026-10-20T05:38:31Z（UTC，含起点不含尾）
- 精选事件日期：2026-09-23 至 2026-09-23
- 数据抓取时间：2026-10-20T05:38:31Z（期次 20261020T053831Z，状态 complete）
- 报告生成时间：2026-10-20T05:38:58Z（联网刷新）
- 商业背景资料查阅日期：2026-10-02（可早于30天窗口，不属于开源事件）

## 本期更新目录

_按“与出海创作流程的相关度 × 能否离线、低成本验证”排序：前两项共同支撑末尾行动建议，故标“先看”；第 3 项只借鉴流程；第 4 项仅在自部署特定两个模型时相关；第 5 项数字为项目方数据，仅作复测线索。不按 Stars 多少排序，也不把五项归为同一趋势。_

| # | 任务/场景：具体变化 | 项目 | 事件 | 能力标签 |
|---|---|---|---|---|
| 1 | 长篇有声书：中断或断电后，已渲染章节不用重做 | debpalash/VoiceStudio | 正式发布 v0.5.6，2026-09-23 | 语音 |

另有 11 个有事件的项目在“待核查”，未计入精选。

## 项目更新

### 1. 长篇有声书：中断或断电后，已渲染章节不用重做

- 项目：[debpalash/VoiceStudio](https://github.com/debpalash/VoiceStudio) — 本地运行的开源配音工具：声音克隆、视频配音、转写和有声书制作。
- 事件：正式发布 v0.5.6，2026-09-23，[来源](https://github.com/debpalash/VoiceStudio/releases/tag/v0.5.6)
- 能力标签：语音

**本次变化**

v0.5.6 起，断电或数据目录迁移后，已渲染的有声书章节仍可复用，续传点不再被清空（依据 v2）。同版本修复了 8GB 显卡长章节渲染中途超时的问题，超时章节在当前片段结束后释放 GPU（依据 v1）。

**谁值得关注**

需要连续渲染大量章节的有声书、长配音创作者；做长任务类功能的产品——可参考“留住已完成部分、只补剩余部分”的恢复设计。

**关键边界**

- 指定硬件：超时修复针对 8GB 显卡上的长章节，不代表所有硬件都不再超时（v1）
- 许可：AGPL-3.0：修改后以网络服务提供需公开对应源码，只适合借鉴机制
- 安装包：未签名或仅临时签名、未经 Apple 公证（v6）
- 未经实测：未给出提速或降显存数据
<details>
<summary>具体改动（5 项）</summary>

- 8GB 显卡上长有声书章节不再在渲染中超时；超时章节在当前片段结束后释放 GPU。（依据 v1）
- 数据目录迁移或断电后，已渲染章节仍可复用，续传点不再被清空。（依据 v2）
- Claude Code、Cursor、Codex CLI 和 OpenAI Agents SDK 可按给出的配置接入。（依据 v3）
- 可替换已保存克隆的参考音频；OmniVoice 支持超过 20 秒的参考。（依据 v4）
- 新增用保存的声音应答 Twilio 来电，默认关闭。（依据 v5）

</details>

<details>
<summary>技术与采用条件</summary>

- Electron 桌面应用（Windows、macOS、Linux），AGPL-3.0。安装包未签名或仅临时签名，未经 Apple 公证。声音克隆需确认授权与合规。
- 许可：AGPL-3.0。AGPL-3.0：可商用；修改后以网络服务提供时需按AGPL公开对应源码，不等于禁止商用。模型权重与服务条款未核查
- 限制与未知：项目方没有给出提速或降显存数据；“已渲染章节可保留”不等于正在生成的每一秒都能恢复。安装包未签名、未经 Apple 公证。许可证为 AGPL-3.0：可以商用，但修改后通过网络提供服务，需要公开对应源码。克隆声音还要确认授权与合规。
- 窗口内其他事件：正式发布 v0.5.5，2026-09-22、正式发布 v0.5.4，2026-09-21

</details>

<details>
<summary>对团队的启发</summary>

- 适合的用户任务：做长篇配音或有声书的人，通常要让电脑连续渲染很多章节。麻烦在于：跑到一半超时、断电或软件退出，前面等了很久的内容可能白做。
- 方式：借鉴机制；接入代码受 AGPL 约束
- 改善哪个步骤：长任务中断后的恢复：已完成的部分不必重做。
- 可能影响的指标：中断后需要重新生成的时长；长任务完成率。
- 公开事实：该版本保留断电或迁移前已渲染的章节，并修复长章节超时。（依据 v1；依据 v2）
- 公开事实：DreamFace 的积分用于AI生成，已使用的积分不退。（背景：DreamFace 订阅与积分政策）
- 公开事实：岗位写明关注完成率。（背景：同花顺官方校园招聘：AI Native出海产品经理（AI创新集群，杭州））
- 分析推断：长视频或长配音任务中断后如果只需补做剩余部分，用户等待更短；在按积分计费的产品里，重复生成也可能意味着额外消耗。
- 待验证：生成失败时是否返还积分，政策页没有说明；DreamFace 是否有长任务中断问题未知。
- 产品假设：这次更新的价值主要在稳定性：长章节少超时、已完成章节能保留，创作者就少一点从头再来的等待。它不是显存优化，也没有承诺所有电脑都不再超时；是否真能减少损失，要在自己的设备和任务长度上验证。
- 最小验证建议（拟议，未执行）：在8GB显卡的测试环境里，用同一本10章有声书对照上一版本。测试中分别模拟进程退出、任务中断和数据目录迁移：记录超时次数、完成章数、恢复后需要重渲染的时长、整本完成率。不要求在真实工作设备上硬断电。

</details>

<details>
<summary>原始依据（6 条）</summary>

- [v1] “Long audiobook chapters on 8 GB GPUs no longer time out while still rendering, and a timed-out chapter stops using the GPU after its current chunk (#2287)” — 版本说明，[原文](https://github.com/debpalash/VoiceStudio/releases/tag/v0.5.6)，原始响应 `data/runs/20261020T053831Z/raw/0022.json`
- [v2] “Rendered audiobook chapters stay reusable after the data folder moves, and a power-off no longer empties the resume point or tears chapter audio (#2279)” — 版本说明，[原文](https://github.com/debpalash/VoiceStudio/releases/tag/v0.5.6)，原始响应 `data/runs/20261020T053831Z/raw/0022.json`
- [v3] “Claude Code, Cursor, Codex CLI and the OpenAI Agents SDK connect to VoiceStudio with working setup (#2289, #2290)” — 版本说明，[原文](https://github.com/debpalash/VoiceStudio/releases/tag/v0.5.6)，原始响应 `data/runs/20261020T053831Z/raw/0022.json`
- [v4] “Replace a saved clone's reference sample, and clone from references longer than 20 s on OmniVoice (#2282, #2281)” — 版本说明，[原文](https://github.com/debpalash/VoiceStudio/releases/tag/v0.5.6)，原始响应 `data/runs/20261020T053831Z/raw/0022.json`
- [v5] “Answer Twilio phone calls with a greeting in a saved voice; off by default” — 版本说明，[原文](https://github.com/debpalash/VoiceStudio/releases/tag/v0.5.6)，原始响应 `data/runs/20261020T053831Z/raw/0022.json`
- [v6] “Electron installers are unsigned or ad-hoc signed and are not Apple-notarized.” — 版本说明，[原文](https://github.com/debpalash/VoiceStudio/releases/tag/v0.5.6)，原始响应 `data/runs/20261020T053831Z/raw/0022.json`

</details>

选择理由：本地语音克隆与有声书工具，本版修复长任务超时并保留断电前进度，同时开放Agent接入，可对照岗位关注的完成率（AI（Claude）核查起草，待本人确认，核查于期次 20261001T210300Z）。解读审阅状态：AI草稿，未经本人审阅。

## 跨项目信号

以下信号只说明本期少量项目里的共同点，不外推为行业趋势。

### 出错后，别让前面的工作白做

该信号依赖的证据已变化或不在本期，待复核。

### 创作能力，开始能被 AI 助手直接调用

该信号依赖的证据已变化或不在本期，待复核。

### 更快、更省显存、更稳定，不是一回事

该信号依赖的证据已变化或不在本期，待复核。

## 行动建议

优先建议待复核：其依据的项目解读已变化或不在本期。

<details>
<summary>有条件实验（2 项）</summary>

#### 结构化排版流程 vs 直接提示词（海报、封面类功能）

依据已变化或不在本期，待复核。

#### 自部署视频模型的 LoRA 风格试验

依据已变化或不在本期，待复核。


</details>

<details>
<summary>暂缓清单（3 项）</summary>

#### 按项目方测速数字做选型或成本判断

依据已变化或不在本期，待复核。

#### 暂缓：直接接入 VoiceStudio 做声音克隆

- 理由：AGPL-3.0 下以网络服务提供修改版需公开对应源码；克隆声音需要授权与合规审查；安装包未签名。可借鉴“保留已完成部分”的机制，不急于接入代码。
- 依据：debpalash/VoiceStudio

#### 暂缓：把“推出 API”当作新建议

- 理由：DreamFace 已有 DreamAPI 并按 Credits 计费，这不是新方向。
- 依据：DreamAPI（DreamFace API）页面


</details>

以上建议均未执行；阈值、样本量和周期是建议值，需先建立基线。

## 待核查

窗口内有事件、但没有有效核查记录的项目。只列原文事实与来源，未做分析，也不计入精选。

- [harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo)：正式发布 v1.3.8，2026-10-03，[来源](https://github.com/harry0703/MoneyPrinterTurbo/releases/tag/v1.3.8)。原因：已核查的事件 v1.3.7 不在本期窗口内。简介：利用 AI 大模型和自动化工作流，根据主题或关键词一键生成高清短视频。Generate HD short videos from a topic or keyword with an automated AI workflow.
- [mudler/LocalAI](https://github.com/mudler/LocalAI)：正式发布 v4.11.0，2026-10-02，[来源](https://github.com/mudler/LocalAI/releases/tag/v4.11.0)。原因：已核查的事件 v4.10.0 不在本期窗口内。简介：LocalAI is the open-source AI engine. Run any model - LLMs, vision, voice, image, video - on any hardware. No GPU required.
- [unslothai/unsloth](https://github.com/unslothai/unsloth)：正式发布 v0.1.909-beta，2026-10-19，[来源](https://github.com/unslothai/unsloth/releases/tag/v0.1.909-beta)。原因：v0.1.902-beta 的来源说明已变化，原核查不再适用。简介：Local UI to run and train LLMs and diffusion models. Supports GGUF, MLX, Qwen3.8, DeepSeek-V4, MiniMax-H3, Gemma 4, FLUX and more.
- [TimoteoAltobrando/ai-video-skill](https://github.com/TimoteoAltobrando/ai-video-skill)：窗口内新建仓库，2026-10-05，[来源](https://github.com/TimoteoAltobrando/ai-video-skill)。原因：尚无核查记录：窗口内有事件不等于值得推荐，需人工核查。简介：Make and edit videos with Claude Opus 5.5: a Claude Code skill for product films, ads, talking heads, explainers, montages and Reels/TikTok/Shorts, with Remotion, AI images and animation, ElevenLabs music and ffmpeg.
- [Antoine-Thomas/hermes-skills-showcase](https://github.com/Antoine-Thomas/hermes-skills-showcase)：窗口内新建仓库，2026-10-10，[来源](https://github.com/Antoine-Thomas/hermes-skills-showcase)。原因：尚无核查记录：窗口内有事件不等于值得推荐，需人工核查。简介：Showcase of Hermes Agent skills for AI video automation, free-model routing and Windows optimization. Full version on Agensi.io.
- [OpenMOSS/MOSS-Image](https://github.com/OpenMOSS/MOSS-Image)：窗口内新建仓库，2026-10-16，[来源](https://github.com/OpenMOSS/MOSS-Image)。原因：尚无核查记录：窗口内有事件不等于值得推荐，需人工核查。简介：Official repository for MOSS-Image, a 5B-parameter base DiT model with high-quality text rendering, layout generation, and efficient fine-tuning.
- [SnowSky1/universal-imagegen-agent](https://github.com/SnowSky1/universal-imagegen-agent)：正式发布 v0.1.2，2026-10-11，[来源](https://github.com/SnowSky1/universal-imagegen-agent/releases/tag/v0.1.2)。原因：尚无核查记录：窗口内有事件不等于值得推荐，需人工核查。简介：把 Codex imagegen 的工作流与提示词库带到任意智能体；支持 npm/pnpm 一键安装、配套 skill、独立 API 与 Qwen-Image 兼容网关。
- [lemomo-ai/lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar)：正式发布 thanks，2026-10-12，[来源](https://github.com/lemomo-ai/lemo-opuscar/releases/tag/thanks)。原因：此前排除的是 web，本期最新事件 thanks 尚未核查。简介：Claude Code skill for short films with no video model: 51 film styles, each a style prompt plus a demo film made entirely in code by Claude Opus 5.5 (incl. OPUSCAR 98 and the new Evidence Films). By Lemomo. · Opus5.5 x 51 种影片风格：风格提示词 + 纯代码样片 + 导演与技术指南（新增「实证影像」）
- [vincentsch/explainroo](https://github.com/vincentsch/explainroo)：正式发布 v0.4.0，2026-10-15，[来源](https://github.com/vincentsch/explainroo/releases/tag/v0.4.0)。原因：尚无核查记录：窗口内有事件不等于值得推荐，需人工核查。简介：Explainer videos and product demos made by your AI agent. Free and open source: a local voice (Kokoro), word timing (Whisper) and a canvas renderer turn a script into a narrated MP4.
- [sitor-ai/frametell](https://github.com/sitor-ai/frametell)：正式发布 v0.7.1，2026-10-16，[来源](https://github.com/sitor-ai/frametell/releases/tag/v0.7.1)。原因：尚无核查记录：窗口内有事件不等于值得推荐，需人工核查。简介：Frametell: turn your ideas and material into vivid explainer videos with an AI director agent. Local-first, any model.
- [Rylaispirit/cinematic-video-prompt-skill](https://github.com/Rylaispirit/cinematic-video-prompt-skill)：窗口内新建仓库，2026-09-20，[来源](https://github.com/Rylaispirit/cinematic-video-prompt-skill)。原因：尚无核查记录：窗口内有事件不等于值得推荐，需人工核查。简介：AI video prompt cheat sheet & Claude Skill: cinematic camera angles, camera movement, lighting, composition, color grading for Veo 3, Kling, Sora, Runway, Midjourney. 700+ terms with Vietnamese explanations.

## 移出与变化

- 对比上一期快照 20261016T052230Z：新增 无。
- 移出 mudler/LocalAI（v4.10.0）：事件日期 2026-09-17 已早于本期窗口起点 2026-09-20
- 已有核查记录但本期不适用：op7418/guizang-yingzao-skill created:1354705170，本期检索结果中未出现该仓库

## 排除记录

- 检查前排除 apimart-api-ai-Aggregator/seedance-2.0-api：仓库是商业API转售方的价格与调用示例页，正文含推广链接，没有可核查的开源实现（https://github.com/apimart-api-ai-Aggregator/seedance-2.0-api；生效；仓库简介变化时自动失效，重新进入检查）

<details>
<summary>商业背景资料（5 条）</summary>

背景资料只用于判断与目标团队的关系。区分：公开事实（页面写明）、分析推断、待验证假设。

- **同花顺官方校园招聘：AI Native出海产品经理（AI创新集群，杭州）**（官方，查阅 2026-10-02）：岗位面向全球创作者，写明快速做MVP并在Reddit/Discord验证、关注生成等待（“用户等不了那0.8秒”）、完成率与留存。 边界：招聘要求说明团队关注点，不能证明产品当前存在某个问题；列表页需在浏览器中加载，岗位详情页可直接阅读。 https://campus.10jqka.com.cn/mobile/job/detail?id=2198
- **DreamFace 头像视频（Avatar Video）产品页**（官方，查阅 2026-10-02）：产品把照片、脚本或音频转成口播头像视频，提供网页、iOS、Android 入口，页面列出多种语言。 边界：作为相关产品参照，不认定该岗位负责其全部业务；未披露内部流程、失败率或成本。 https://www.dreamfaceapp.com/ai-tools/avatar-video
- **DreamAPI（DreamFace API）页面**（官方，查阅 2026-10-02）：已提供 Lip Sync、DreamAct、AI Voice 等 API，按任务复杂度消耗 Credits。 边界：说明产品已有API和积分计费，因此“推出API”不是新建议；未披露调用量或收入。 https://www.dreamfaceapp.com/tools/dreamface-api
- **DreamFace 订阅与积分政策**（官方，查阅 2026-10-02）：积分包用于AI生成功能，已使用的积分不退；生成、处理、导出等操作会消耗平台资源。 边界：政策不说明生成失败时是否返还积分，本作品不对此作推断。 https://dreamfaceapp.com/subscriptionPolicy.html
- **牛客网：同花顺 Java 开发实习（已关闭）**（第三方辅助线索，查阅 2026-10-02）：第三方页面把同花顺岗位与 Dreamface 的稳定性优化、架构工作联系在一起，只作为同花顺与 DreamFace 关联的辅助线索。 边界：第三方转载、岗位已关闭；页面中的规模描述不作为事实引用，也不据此推断技术栈。 https://www.nowcoder.com/jobs/detail/390262

</details>

## 数据与方法

### 覆盖统计（按检索分类）

| 检索分类 | 搜索 | 候选 | 窗口内有事件 | 检查后无合格事件 | 人工排除 | 未检查 | 检查失败 |
|---|---|---|---|---|---|---|---|
| 视频 | 成功 | 30 | 2 | 2 | 0 | 26 | 0 |
| 图像 | 成功 | 27 | 4 | 0 | 0 | 23 | 0 |
| 语音 | 成功 | 27 | 4 | 0 | 0 | 23 | 0 |
| 数字人 | 成功 | 26 | 2 | 2 | 0 | 22 | 0 |

检索到的候选 110 个 → 窗口内有事件 12 个 → 正式精选 1 个、待核查 11 个、经核查排除 0 个。

- 检索分类“视频”下本期无正式精选：检查4个，2个窗口内无正式发布、预发布或新建，2个有事件但待核查，另有26个未检查。按能力标签，本期也没有精选项目涉及视频。
- 检索分类“图像”下本期无正式精选：检查4个，0个窗口内无正式发布、预发布或新建，4个有事件但待核查，另有23个未检查。按能力标签，本期也没有精选项目涉及图像。
- 检索分类“数字人”下本期无正式精选：检查4个，2个窗口内无正式发布、预发布或新建，2个有事件但待核查，另有22个未检查。按能力标签，本期也没有精选项目涉及数字人。

### 各项目抓取时累计 Stars（一次观测，不代表增长）

| 项目 | Stars | 许可 |
|---|---|---|
| debpalash/VoiceStudio | 77850 | AGPL-3.0 |

### 检索范围与截断

| 分类 | 检索 | GitHub匹配总数 | 实际取回 | 是否截断 |
|---|---|---|---|---|
| 视频 | 近期有推送（按Stars） | 651 | 20 | 是 |
| 视频 | 窗口内新建（按Stars） | 296 | 10 | 是 |
| 图像 | 近期有推送（按Stars） | 4410 | 20 | 是 |
| 图像 | 窗口内新建（按Stars） | 3167 | 10 | 是 |
| 语音 | 近期有推送（按Stars） | 3173 | 20 | 是 |
| 语音 | 窗口内新建（按Stars） | 1450 | 10 | 是 |
| 数字人 | 近期有推送（按Stars） | 77 | 20 | 是 |
| 数字人 | 窗口内新建（按Stars） | 38 | 10 | 是 |

每条检索只取Stars最高的前20或10个，排名之后的仓库没有进入候选；候选中还有 94 个因名额未检查（名单见 data/brief.json 的 candidates）。
- 失败或跳过的请求：0 个。

### 方法

- 数据源：GitHub REST API（单一来源，未使用模型）。分类：视频（topic:text-to-video）、图像（topic:image-generation）、语音（topic:text-to-speech）、数字人（topic:talking-head）。
- 每类两次检索：近期有推送的仓库按Stars排序（偏向成熟项目），窗口内新建的仓库按Stars排序（照顾新项目）；均排除fork与归档。
- 每类检查4个候选，其中2个名额留给窗口内新建的仓库；空缺轮转补位；某类无合格事件时补检1个。请求上限48次，本期实际32次。
- 事件：窗口内最新的正式发布优先，其次预发布，再次窗口内新建仓库（README不少于300字）。草稿忽略，只有提交活动不算事件。
- 关键词（awesome、list、prompts、paper等，按整词匹配）只降低检查顺序并提示复核，不阻止新建仓库事件识别，也不直接排除。
- “窗口内有事件”是自动状态。进入正式精选必须有核查记录：AIGC相关、实质变化、来源可查三项为真，并写明理由；没有记录的有事件项目进入待核查，不会被默认规则补进精选。
- 解读按“仓库+事件ID+版本号+来源哈希”绑定，引用原文须逐字可查；不满足时旧解读不显示，只列事实与来源。
- Stars为抓取时累计值，只有一次观测，不表示增长。许可只说明代码许可，模型权重与服务条款未核查。
- 网络说明：本简报是截至抓取时间的数据快照，可离线查看。刷新数据和打开原始来源需要能访问GitHub。刷新失败时保留原快照，原快照时间不会更新。本期只覆盖所列四个topic的检索结果，不代表全部开源动态。

## AI参与说明

抓取、去重、窗口判断、统计与排版由脚本完成，运行时不调用模型。项目解读、本期判断、跨项目信号与团队建议由AI在制作阶段起草，每条都绑定依据，审阅状态见各项；详见 AI_USAGE.md。
