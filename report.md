# 近 30 天 AIGC 开源更新看板

> 本期判断待复核：其依据的项目解读已变化或不在本期。

- 事件窗口：2026-09-13T07:19:03Z 至 2026-10-13T07:19:03Z（UTC，含起点不含尾）
- 精选事件日期：2026-09-13 至 2026-09-17
- 数据抓取时间：2026-10-13T07:19:03Z（期次 20261013T071903Z，状态 complete）
- 报告生成时间：2026-10-13T07:19:41Z（联网刷新）
- 商业背景资料查阅日期：2026-10-02（可早于30天窗口，不属于开源事件）

## 本期更新目录

_按“与出海创作流程的相关度 × 能否离线、低成本验证”排序：前两项共同支撑末尾行动建议，故标“先看”；第 3 项只借鉴流程；第 4 项仅在自部署特定两个模型时相关；第 5 项数字为项目方数据，仅作复测线索。不按 Stars 多少排序，也不把五项归为同一趋势。_

| # | 任务/场景：具体变化 | 项目 | 事件 | 能力标签 |
|---|---|---|---|---|
| 1 | 短视频配音：坏音频当场中止，不再产出缺旁白成片 | harry0703/MoneyPrinterTurbo | 正式发布 v1.3.7，2026-09-13 | 视频、语音 |
| 2 | 自部署视频模型：加载时可融合 LoRA 风格插件 | mudler/LocalAI | 正式发布 v4.10.0，2026-09-17 | 视频 |

另有 7 个有事件的项目在“待核查”，未计入精选。

## 项目更新

### 1. 短视频配音：坏音频当场中止，不再产出缺旁白成片

- 项目：[harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) — 开源短视频生成工具：输入主题或关键词，自动写脚本、配音、配字幕和素材，生成短视频。
- 事件：正式发布 v1.3.7，2026-09-13，[来源](https://github.com/harry0703/MoneyPrinterTurbo/releases/tag/v1.3.7)
- 能力标签：视频、语音

**本次变化**

v1.3.7 起，配音阶段检测到无效音频会直接中止生成，不再继续产出缺旁白的成片（依据 m3）。同版本支持在脚本里写 [pause: 2s] 插入停顿、字幕时间轴同步调整，并新增逐词字幕（依据 m1、m2）。

**谁值得关注**

从脚本直接生成带旁白短视频的创作者；以及做“先配音、后画面”口播类功能的产品和技术——可参考“渲染画面之前先拦坏音频”的做法。是否减少返工需自行验证。

**关键边界**

- 指定服务：停顿标记仅支持 Edge TTS（Azure TTS V1），单次停顿 0.1–10 秒（m4）
- 字幕条件：逐词字幕取决于语音服务是否提供词级时间，不提供时退化为短语或整句（m5）
- 未经实测：项目方未给出返工减少或成功率数据
<details>
<summary>具体改动（6 项）</summary>

- 脚本停顿：用 [停顿: 2s] 或 [pause: 2s] 插入静音，配音与字幕时间轴同步调整。（依据 m1）
- 新增逐词字幕和弹跳出现动画；逐词效果依赖语音服务提供词级时间。（依据 m2；依据 m5）
- 无效语音片段会中止生成，不再静默输出缺旁白的成片。（依据 m3）
- 新增 Kokoro、VoxCPM 配音服务；新增预设背景音乐与试听。（依据 m7；依据 m9）
- 中断写入留下的临时文件会被清理。（依据 m8）
- 胜算云（Shengsuan Cloud）视频生成显示报价、要求确认费用，并按旁白时长推荐素材数量。（依据 m6）

</details>

<details>
<summary>技术与采用条件</summary>

- Python 项目，MIT 许可。停顿标记仅支持 Edge TTS，单次停顿 0.1–10 秒；Kokoro 需要另行运行兼容服务；胜算云报价确认只适用于这一家。
- 许可：MIT。宽松许可：可商用，需保留版权与许可声明。模型权重与服务条款未核查
- 限制与未知：项目方没有给出返工减少或成功率数据；停顿标记只适用于 Edge TTS，逐词字幕效果取决于语音服务是否提供时间信息；Shengsuan Cloud 报价确认只覆盖这一家。以上效果未实测。
- 窗口内其他事件：正式发布 v1.3.8，2026-10-03
- 窗口内有更新的事件尚未核查：正式发布 v1.3.8，2026-10-03

</details>

<details>
<summary>对团队的启发</summary>

- 适合的用户任务：做短视频的人，从脚本走到成片时，要处理配音停顿、字幕出现的时间、背景音乐和素材。这个版本主要减少配音和字幕对不上的问题。
- 方式：借鉴机制，不必接入仓库
- 改善哪个步骤：脚本 → 配音 → 成片：在渲染画面之前确认配音节奏和音频是否有效。
- 可能影响的指标：每条合格视频的生成次数；旁白残缺的成片比例。
- 公开事实：该版本让无效语音中止生成，并支持停顿标记与字幕同步。（依据 m1；依据 m3）
- 公开事实：DreamFace 头像视频把照片、脚本或音频转成口播视频。（背景：DreamFace 头像视频（Avatar Video）产品页）
- 分析推断：口播视频同样先有配音再出画面。坏音频如果在画面渲染前被拦下，用户可能少等一轮、少重做一次。
- 待验证：DreamFace 现有流程是否已有类似校验、当前残缺率和重生成率都未知；停顿标记只在一种语音服务上可用。
- 产品假设：如果配音能在指定位置停、字幕按词出现，创作者可能少做几次“生成完才发现节奏不对”的返工。坏音频直接停下，也能避免一条缺旁白的视频继续走后面的素材和剪辑流程。但 Shengsuan Cloud 的报价确认只是让成本提前可见，不等于降低成本，而且只适用于这一家。
- 最小验证建议（拟议，未执行）：同一 v1.3.7、同一批10个主题脚本、同一 TTS 声音和素材源：A组不加停顿标记，B组在相同位置加 [pause: 2s]。记录旁白和字幕错位次数、为修节奏重新生成的次数、第一条可用成片耗时。无效语音中止生成另测：在相同输入和服务中注入同一段坏音频，统计有多少次还会产出旁白残缺的视频。成本确认不放进这组实验。

</details>

<details>
<summary>原始依据（9 条）</summary>

- [m1] “新增 Azure TTS V1（Edge TTS）脚本停顿支持：使用 `[停顿: 2s]` 或 `[pause: 2s]` 插入静音，并同步调整配音与字幕时间轴。” — 版本说明，[原文](https://github.com/harry0703/MoneyPrinterTurbo/releases/tag/v1.3.7)，原始响应 `data/runs/20261013T071903Z/raw/0021.json`
- [m2] “新增逐词字幕和弹跳出现动画，WebUI 可分别选择字幕显示模式与动画效果。” — 版本说明，[原文](https://github.com/harry0703/MoneyPrinterTurbo/releases/tag/v1.3.7)，原始响应 `data/runs/20261013T071903Z/raw/0021.json`
- [m3] “无效语音片段会中止生成，避免静默输出缺失旁白的成片。” — 版本说明，[原文](https://github.com/harry0703/MoneyPrinterTurbo/releases/tag/v1.3.7)，原始响应 `data/runs/20261013T071903Z/raw/0021.json`
- [m4] “Script pause tags are supported only with Azure TTS V1 (Edge TTS), with individual pauses from **0.1 to 10 seconds**.” — 版本说明，[原文](https://github.com/harry0703/MoneyPrinterTurbo/releases/tag/v1.3.7)，原始响应 `data/runs/20261013T071903Z/raw/0021.json`
- [m5] “Word-by-word timing works best with Azure TTS V1 (Edge TTS) or Whisper; providers without word-level timestamps may display phrases or whole sentences instead.” — 版本说明，[原文](https://github.com/harry0703/MoneyPrinterTurbo/releases/tag/v1.3.7)，原始响应 `data/runs/20261013T071903Z/raw/0021.json`
- [m6] “优化胜算云视频生成流程，支持读取当前账号可用模型、获取报价和确认费用，并根据旁白时长推荐素材数量。” — 版本说明，[原文](https://github.com/harry0703/MoneyPrinterTurbo/releases/tag/v1.3.7)，原始响应 `data/runs/20261013T071903Z/raw/0021.json`
- [m7] “新增 Kokoro 和 VoxCPM 配音服务。” — 版本说明，[原文](https://github.com/harry0703/MoneyPrinterTurbo/releases/tag/v1.3.7)，原始响应 `data/runs/20261013T071903Z/raw/0021.json`
- [m8] “Extended material cache cleanup to reclaim temporary files left behind by interrupted writes.” — 版本说明，[原文](https://github.com/harry0703/MoneyPrinterTurbo/releases/tag/v1.3.7)，原始响应 `data/runs/20261013T071903Z/raw/0021.json`
- [m9] “新增预设背景音乐选择与浏览器内试听，生成视频前即可确认配乐效果。” — 版本说明，[原文](https://github.com/harry0703/MoneyPrinterTurbo/releases/tag/v1.3.7)，原始响应 `data/runs/20261013T071903Z/raw/0021.json`

</details>

选择理由：短视频一键生成工具，本版改动落在配音停顿、逐词字幕和生成出错时的处理上，最贴近创作者成片流程（AI（Claude）核查起草，待本人确认，核查于期次 20261001T210300Z）。解读审阅状态：AI草稿，未经本人审阅。

### 2. 自部署视频模型：加载时可融合 LoRA 风格插件

- 项目：[mudler/LocalAI](https://github.com/mudler/LocalAI) — 开源的本地 AI 推理引擎，可在自有硬件上运行文本、图像、语音、视频等模型。
- 事件：正式发布 v4.10.0，2026-09-17，[来源](https://github.com/mudler/LocalAI/releases/tag/v4.10.0)
- 能力标签：视频

**本次变化**

v4.10.0 起，vllm-cpp 视频引擎在模型加载时即可把 LoRA 融合进权重，LTX2.5 与 MiniMax-H3 走同一路径（依据 l1）。LoRA 在加载后固定生效，本版不支持按单次请求切换（依据 l4）。

**谁值得关注**

自部署视频生成服务、需要试验特定风格的技术团队；仅当使用 LTX2.5 或 MiniMax-H3 时相关。按请求切换风格的需求此版不覆盖。

**关键边界**

- 指定模型：LoRA 融合只覆盖 LTX2.5 与 MiniMax-H3（l1）
- 范围有限：不支持按请求切换 LoRA，运行时激活不在本版（l4）
- 测速范围：benchmark 只测文本模型，得不到视频速度或首帧时间（l2、l3）
- 未经实测：LoRA 对画质和生成耗时的影响未说明
<details>
<summary>具体改动（4 项）</summary>

- vllm-cpp 视频引擎在加载时把 LoRA 融合进模型权重，LTX2.5 与 MiniMax-H3 走同一路径。（依据 l1）
- LoRA 在加载时固定生效，不支持按单次请求切换。（依据 l4）
- 新增 local-ai benchmark 命令，测量文本模型端到端延迟与吞吐；不测首个 token 时间。（依据 l2；依据 l3）
- 新增集群运维面板和统一凭据文件；修复 4 个 CVE。（依据 l6；依据 l7；依据 l5）

</details>

<details>
<summary>技术与采用条件</summary>

- Go 项目，MIT 许可；需要 vllm-cpp 视频后端与对应模型权重；LoRA 在加载时固定，按请求激活不在本版范围内。
- 许可：MIT。宽松许可：可商用，需保留版权与许可声明。模型权重与服务条款未核查
- 限制与未知：新增 benchmark 只覆盖文本模型，不能直接得到视频生成速度或首帧等待；LoRA 对画质和速度的影响未说明；自部署能否降低成本没有验证。
- 窗口内其他事件：正式发布 v4.11.0，2026-10-02
- 窗口内有更新的事件尚未核查：正式发布 v4.11.0，2026-10-02

</details>

<details>
<summary>对团队的启发</summary>

- 适合的用户任务：需要自己部署 AI 生成服务的小团队，想在本地视频模型上加入特定风格，同时了解服务的响应速度。
- 方式：仅在团队自部署视频模型时相关
- 改善哪个步骤：定制风格：把一种风格加进视频模型并上线试用。
- 可能影响的指标：新风格从准备到可试用的搭建时间；风格一致性评分。
- 公开事实：该版本支持视频模型加载时融合 LoRA，但不能按请求切换。（依据 l1；依据 l4）
- 公开事实：DreamFace 已对外提供 API 并按 Credits 计费。（背景：DreamAPI（DreamFace API）页面）
- 分析推断：如果团队用 LTX2.5 或 MiniMax-H3 自部署，这一改动可能缩短风格试验的搭建工作；按请求切换风格的需求仍要另行实现。
- 待验证：团队是否使用这两种模型、是否自部署未知；生成耗时与画质影响未验证。
- 产品假设：视频模型在加载阶段就能融合 LoRA，团队可以更快试验特定风格，不必另外搭一套推理脚本。LoRA 不只能做风格，风格只是这次测试场景。能否真正减少搭建工作、会不会增加生成耗时，都还需要验证。
- 最小验证建议（拟议，未执行）：同一台 GPU、同一 LocalAI v4.10.0、同一 LTX2.5 基础模型、同一组20条提示词和随机种子：A组不加载 LoRA，B组在加载时融合同一个 LoRA。记录模型加载耗时、5秒视频生成耗时、失败率，并由3名评审盲评风格一致性。不与手动搭建脚本比较，否则部署方式和推理实现都会变。

</details>

<details>
<summary>原始依据（7 条）</summary>

- [l1] “`lora_adapters` and `lora_scales` are now consumed by the vllm-cpp video engine, fusing LoRA deltas into DiT weights at engine load. Works for both LTX2.5 and MiniMax-H3 through one generic path.” — 版本说明，[原文](https://github.com/mudler/LocalAI/releases/tag/v4.10.0)，原始响应 `data/runs/20261013T071903Z/raw/0016.json`
- [l2] “measures end-to-end latency and throughput against configured text models.” — 版本说明，[原文](https://github.com/mudler/LocalAI/releases/tag/v4.10.0)，原始响应 `data/runs/20261013T071903Z/raw/0016.json`
- [l3] “The command does not measure decode-only speed or time to first token” — 版本说明，[原文](https://github.com/mudler/LocalAI/releases/tag/v4.10.0)，原始响应 `data/runs/20261013T071903Z/raw/0016.json`
- [l4] “Adapters are always loaded; there is no per-request activation in this path.” — 版本说明，[原文](https://github.com/mudler/LocalAI/releases/tag/v4.10.0)，原始响应 `data/runs/20261013T071903Z/raw/0016.json`
- [l5] “Four CVEs were patched” — 版本说明，[原文](https://github.com/mudler/LocalAI/releases/tag/v4.10.0)，原始响应 `data/runs/20261013T071903Z/raw/0016.json`
- [l6] “A fleet operations dashboard replaces the flat node list with cluster-wide health, capacity, running models, and bulk lifecycle actions.” — 版本说明，[原文](https://github.com/mudler/LocalAI/releases/tag/v4.10.0)，原始响应 `data/runs/20261013T071903Z/raw/0016.json`
- [l7] “A credentials file lets one `credentials.yaml` authenticate OCI registries, galleries and direct downloads without scattering tokens across environment variables.” — 版本说明，[原文](https://github.com/mudler/LocalAI/releases/tag/v4.10.0)，原始响应 `data/runs/20261013T071903Z/raw/0016.json`

</details>

选择理由：本地多模态推理引擎，本版为视频引擎加载LoRA、提供延迟与吞吐测量，关系到自部署生成服务的门槛（AI（Claude）核查起草，待本人确认，核查于期次 20261001T210300Z）。解读审阅状态：AI草稿，未经本人审阅。

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

#### 有条件实验：自部署视频模型的 LoRA 风格试验

- 方式：仅自部署时相关
- 假设：加载时融合 LoRA 能缩短新风格的搭建时间。
- 主指标：新风格从准备到可试用的耗时；同时记录生成耗时与失败率。
- 前提条件：只有团队在 LTX2.5 或 MiniMax-H3 上自部署视频生成时才做；否则不投入。
- 限制：LoRA 不能按请求切换；对画质和速度的影响未说明。
- 依据：mudler/LocalAI、DreamAPI（DreamFace API）页面


</details>

<details>
<summary>暂缓清单（3 项）</summary>

#### 按项目方测速数字做选型或成本判断

依据已变化或不在本期，待复核。

#### 直接接入 VoiceStudio 做声音克隆

依据已变化或不在本期，待复核。

#### 暂缓：把“推出 API”当作新建议

- 理由：DreamFace 已有 DreamAPI 并按 Credits 计费，这不是新方向。
- 依据：DreamAPI（DreamFace API）页面


</details>

以上建议均未执行；阈值、样本量和周期是建议值，需先建立基线。

## 待核查

窗口内有事件、但没有有效核查记录的项目。只列原文事实与来源，未做分析，也不计入精选。

- [unslothai/unsloth](https://github.com/unslothai/unsloth)：正式发布 v0.1.906-beta，2026-10-12，[来源](https://github.com/unslothai/unsloth/releases/tag/v0.1.906-beta)。原因：v0.1.902-beta 的来源说明已变化，原核查不再适用。简介：Local UI to run and train LLMs and diffusion models. Supports GGUF, MLX, Qwen3.8, DeepSeek-V4, MiniMax-H3, Gemma 4, FLUX and more.
- [TimoteoAltobrando/ai-video-skill](https://github.com/TimoteoAltobrando/ai-video-skill)：窗口内新建仓库，2026-10-05，[来源](https://github.com/TimoteoAltobrando/ai-video-skill)。原因：尚无核查记录：窗口内有事件不等于值得推荐，需人工核查。简介：Make and edit videos with Claude Opus 5.5: a Claude Code skill for product films, ads, talking heads, explainers, montages and Reels/TikTok/Shorts, with Remotion, AI images and animation, ElevenLabs music and ffmpeg.
- [hiroki-abe-58/ComfyUI-LeapTalk](https://github.com/hiroki-abe-58/ComfyUI-LeapTalk)：预发布 v0.2.0，2026-10-03，[来源](https://github.com/hiroki-abe-58/ComfyUI-LeapTalk/releases/tag/v0.2.0)。原因：尚无核查记录：窗口内有事件不等于值得推荐，需人工核查。简介：Unofficial ComfyUI integration of LeapTalk: turn a portrait and speech into a talking video locally (official weights and 1-step recipe, separate runtime)
- [Arekejoker/qwen21-nsfw-pose-skill](https://github.com/Arekejoker/qwen21-nsfw-pose-skill)：正式发布 v1.0.0，2026-10-13，[来源](https://github.com/Arekejoker/qwen21-nsfw-pose-skill/releases/tag/v1.0.0)。原因：尚无核查记录：窗口内有事件不等于值得推荐，需人工核查。简介：Qwen-Image 2.1 NSFW/姿势出图 skill：作者级提示词配方 + NSFW LoRA + 136 姿势 VNCCS 人偶控制；适用 Claude Code / Codex / Cursor / OpenClaw
- [lemomo-ai/lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar)：正式发布 thanks，2026-10-12，[来源](https://github.com/lemomo-ai/lemo-opuscar/releases/tag/thanks)。原因：此前排除的是 web，本期最新事件 thanks 尚未核查。简介：Claude Code skill for short films with no video model: 43 film styles, each a style prompt plus a demo film made entirely in code by Claude Opus 5.5 (incl. OPUSCAR 98). By Lemomo. · Opus5.5 x 43 种影片风格：风格提示词 + 纯代码样片 + 导演与技术指南
- [leemysw/yovoice](https://github.com/leemysw/yovoice)：正式发布 v0.2.0，2026-10-12，[来源](https://github.com/leemysw/yovoice/releases/tag/v0.2.0)。原因：尚无核查记录：窗口内有事件不等于值得推荐，需人工核查。简介：Open-source local AI audio & music studio for macOS & Windows. Voice cloning, songs with lyrics, and multi-track scores — 100% offline, zero API fees.
- [Rylaispirit/cinematic-video-prompt-skill](https://github.com/Rylaispirit/cinematic-video-prompt-skill)：窗口内新建仓库，2026-09-20，[来源](https://github.com/Rylaispirit/cinematic-video-prompt-skill)。原因：尚无核查记录：窗口内有事件不等于值得推荐，需人工核查。简介：AI video prompt cheat sheet & Claude Skill: cinematic camera angles, camera movement, lighting, composition, color grading for Veo 3, Kling, Sora, Runway, Midjourney. 700+ terms with Vietnamese explanations.

## 移出与变化

- 对比上一期快照 20261009T070556Z：新增 无。
- 移出 unslothai/unsloth（v0.1.902-beta）：本期未通过精选条件（见待核查、排除或不再适用的核查记录）
- 已有核查记录但本期不适用：debpalash/voicestudio v0.5.6，本期未检查（超出名额或预算）
- 已有核查记录但本期不适用：op7418/guizang-yingzao-skill created:1354705170，本期检索结果中未出现该仓库

## 排除记录

- apimart-API-Gateway/grok-image-api：未通过“来源可查/开源实现”核查：README是商业API聚合方的按图计价与调用示例（含推广短链），与已排除的seedance系列同一模式，没有可核查的开源实现。适用范围：仓库整体，简介变化即失效。证据：https://github.com/apimart-API-Gateway/grok-image-api
- apimart-api-ai-Aggregator/seedance-2.5-api：未通过“来源可查/开源实现”核查：与已人工排除的seedance-2.0-api同为商业API转售示例页，含推广链接。适用范围：仓库整体，简介变化即失效。证据：https://github.com/apimart-api-ai-Aggregator/seedance-2.5-api
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
| 视频 | 成功 | 30 | 2 | 2 | 1 | 25 | 0 |
| 图像 | 成功 | 28 | 4 | 0 | 0 | 24 | 0 |
| 语音 | 成功 | 27 | 3 | 1 | 0 | 23 | 0 |
| 数字人 | 成功 | 28 | 2 | 2 | 0 | 24 | 0 |

检索到的候选 113 个 → 窗口内有事件 11 个 → 正式精选 2 个、待核查 7 个、经核查排除 2 个。

- 检索分类“视频”下本期无正式精选：检查4个，2个窗口内无正式发布、预发布或新建，1个有事件但待核查，1个有事件但经核查排除，另有25个未检查。按能力标签，有2个精选项目涉及视频：harry0703/MoneyPrinterTurbo、mudler/LocalAI。
- 检索分类“数字人”下本期无正式精选：检查4个，2个窗口内无正式发布、预发布或新建，2个有事件但待核查，另有24个未检查。按能力标签，本期也没有精选项目涉及数字人。

### 各项目抓取时累计 Stars（一次观测，不代表增长）

| 项目 | Stars | 许可 |
|---|---|---|
| harry0703/MoneyPrinterTurbo | 130374 | MIT |
| mudler/LocalAI | 49504 | MIT |

### 检索范围与截断

| 分类 | 检索 | GitHub匹配总数 | 实际取回 | 是否截断 |
|---|---|---|---|---|
| 视频 | 近期有推送（按Stars） | 586 | 20 | 是 |
| 视频 | 窗口内新建（按Stars） | 259 | 10 | 是 |
| 图像 | 近期有推送（按Stars） | 2026 | 20 | 是 |
| 图像 | 窗口内新建（按Stars） | 877 | 10 | 是 |
| 语音 | 近期有推送（按Stars） | 2755 | 20 | 是 |
| 语音 | 窗口内新建（按Stars） | 1151 | 10 | 是 |
| 数字人 | 近期有推送（按Stars） | 71 | 20 | 是 |
| 数字人 | 窗口内新建（按Stars） | 30 | 10 | 是 |

每条检索只取Stars最高的前20或10个，排名之后的仓库没有进入候选；候选中还有 96 个因名额未检查（名单见 data/brief.json 的 candidates）。
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
