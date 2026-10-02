# 近 30 天 AIGC 开源更新看板

> **本期判断**：本期 5 项更新里，3 项在做同一件事：生成出错后少返工。

- 事件窗口：2026-09-02T02:29:21Z 至 2026-10-02T02:29:21Z（UTC，含起点不含尾）
- 精选事件日期：2026-09-02 至 2026-10-01
- 数据抓取时间：2026-10-02T02:29:21Z（期次 20261002T022921Z，状态 complete）
- 报告生成时间：2026-10-02T08:45:28Z（离线重建）
- 商业背景资料查阅日期：2026-10-02（可早于30天窗口，不属于开源事件）

## 本期更新目录

_按“与出海创作流程的相关度 × 能否离线、低成本验证”排序：前两项共同支撑末尾行动建议，故标“先看”；第 3 项只借鉴流程；第 4 项仅在自部署特定两个模型时相关；第 5 项数字为项目方数据，仅作复测线索。不按 Stars 多少排序，也不把五项归为同一趋势。_

| # | 任务/场景：具体变化 | 项目 | 事件 | 能力标签 |
|---|---|---|---|---|
| 1 | 短视频配音：坏音频当场中止，不再产出缺旁白成片 | harry0703/MoneyPrinterTurbo | 正式发布 v1.3.7，2026-09-13 | 视频、语音 |
| 2 | 长篇有声书：中断或断电后，已渲染章节不用重做 | debpalash/VoiceStudio | 正式发布 v0.5.6，2026-09-23 | 语音 |
| 3 | 照片转海报：新技能把出图流程写成固定四步 | op7418/guizang-yingzao-skill | 窗口内新建仓库，2026-09-02 | 图像 |
| 4 | 自部署视频模型：加载时可融合 LoRA 风格插件 | mudler/LocalAI | 正式发布 v4.10.0，2026-09-17 | 视频 |
| 5 | 本地生图：最高快 3.6 倍（项目方指定显卡） | unslothai/unsloth | 正式发布 v0.1.902-beta，2026-10-01 | 图像 |

另有 3 个有事件的项目在“待核查”，未计入精选。

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
- 窗口内其他事件：正式发布 v1.3.6，2026-09-02

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

- [m1] “新增 Azure TTS V1（Edge TTS）脚本停顿支持：使用 `[停顿: 2s]` 或 `[pause: 2s]` 插入静音，并同步调整配音与字幕时间轴。” — 版本说明，[原文](https://github.com/harry0703/MoneyPrinterTurbo/releases/tag/v1.3.7)，原始响应 `data/runs/20261002T022921Z/raw/0021.json`
- [m2] “新增逐词字幕和弹跳出现动画，WebUI 可分别选择字幕显示模式与动画效果。” — 版本说明，[原文](https://github.com/harry0703/MoneyPrinterTurbo/releases/tag/v1.3.7)，原始响应 `data/runs/20261002T022921Z/raw/0021.json`
- [m3] “无效语音片段会中止生成，避免静默输出缺失旁白的成片。” — 版本说明，[原文](https://github.com/harry0703/MoneyPrinterTurbo/releases/tag/v1.3.7)，原始响应 `data/runs/20261002T022921Z/raw/0021.json`
- [m4] “Script pause tags are supported only with Azure TTS V1 (Edge TTS), with individual pauses from **0.1 to 10 seconds**.” — 版本说明，[原文](https://github.com/harry0703/MoneyPrinterTurbo/releases/tag/v1.3.7)，原始响应 `data/runs/20261002T022921Z/raw/0021.json`
- [m5] “Word-by-word timing works best with Azure TTS V1 (Edge TTS) or Whisper; providers without word-level timestamps may display phrases or whole sentences instead.” — 版本说明，[原文](https://github.com/harry0703/MoneyPrinterTurbo/releases/tag/v1.3.7)，原始响应 `data/runs/20261002T022921Z/raw/0021.json`
- [m6] “优化胜算云视频生成流程，支持读取当前账号可用模型、获取报价和确认费用，并根据旁白时长推荐素材数量。” — 版本说明，[原文](https://github.com/harry0703/MoneyPrinterTurbo/releases/tag/v1.3.7)，原始响应 `data/runs/20261002T022921Z/raw/0021.json`
- [m7] “新增 Kokoro 和 VoxCPM 配音服务。” — 版本说明，[原文](https://github.com/harry0703/MoneyPrinterTurbo/releases/tag/v1.3.7)，原始响应 `data/runs/20261002T022921Z/raw/0021.json`
- [m8] “Extended material cache cleanup to reclaim temporary files left behind by interrupted writes.” — 版本说明，[原文](https://github.com/harry0703/MoneyPrinterTurbo/releases/tag/v1.3.7)，原始响应 `data/runs/20261002T022921Z/raw/0021.json`
- [m9] “新增预设背景音乐选择与浏览器内试听，生成视频前即可确认配乐效果。” — 版本说明，[原文](https://github.com/harry0703/MoneyPrinterTurbo/releases/tag/v1.3.7)，原始响应 `data/runs/20261002T022921Z/raw/0021.json`

</details>

选择理由：短视频一键生成工具，本版改动落在配音停顿、逐词字幕和生成出错时的处理上，最贴近创作者成片流程（AI（Claude）核查起草，待本人确认，核查于期次 20261001T210300Z）。解读审阅状态：AI草稿，未经本人审阅。

### 2. 长篇有声书：中断或断电后，已渲染章节不用重做

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
- 窗口内其他事件：正式发布 v0.5.5，2026-09-22、正式发布 v0.5.4，2026-09-21、正式发布 v0.5.3，2026-09-17、正式发布 v0.5.2，2026-09-10

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

- [v1] “Long audiobook chapters on 8 GB GPUs no longer time out while still rendering, and a timed-out chapter stops using the GPU after its current chunk (#2287)” — 版本说明，[原文](https://github.com/debpalash/VoiceStudio/releases/tag/v0.5.6)，原始响应 `data/runs/20261002T022921Z/raw/0022.json`
- [v2] “Rendered audiobook chapters stay reusable after the data folder moves, and a power-off no longer empties the resume point or tears chapter audio (#2279)” — 版本说明，[原文](https://github.com/debpalash/VoiceStudio/releases/tag/v0.5.6)，原始响应 `data/runs/20261002T022921Z/raw/0022.json`
- [v3] “Claude Code, Cursor, Codex CLI and the OpenAI Agents SDK connect to VoiceStudio with working setup (#2289, #2290)” — 版本说明，[原文](https://github.com/debpalash/VoiceStudio/releases/tag/v0.5.6)，原始响应 `data/runs/20261002T022921Z/raw/0022.json`
- [v4] “Replace a saved clone's reference sample, and clone from references longer than 20 s on OmniVoice (#2282, #2281)” — 版本说明，[原文](https://github.com/debpalash/VoiceStudio/releases/tag/v0.5.6)，原始响应 `data/runs/20261002T022921Z/raw/0022.json`
- [v5] “Answer Twilio phone calls with a greeting in a saved voice; off by default” — 版本说明，[原文](https://github.com/debpalash/VoiceStudio/releases/tag/v0.5.6)，原始响应 `data/runs/20261002T022921Z/raw/0022.json`
- [v6] “Electron installers are unsigned or ad-hoc signed and are not Apple-notarized.” — 版本说明，[原文](https://github.com/debpalash/VoiceStudio/releases/tag/v0.5.6)，原始响应 `data/runs/20261002T022921Z/raw/0022.json`

</details>

选择理由：本地语音克隆与有声书工具，本版修复长任务超时并保留断电前进度，同时开放Agent接入，可对照岗位关注的完成率（AI（Claude）核查起草，待本人确认，核查于期次 20261001T210300Z）。解读审阅状态：AI草稿，未经本人审阅。

### 3. 照片转海报：新技能把出图流程写成固定四步

- 项目：[op7418/guizang-yingzao-skill](https://github.com/op7418/guizang-yingzao-skill) — 给 Claude Code / Codex 用的技能：把建筑、在地文化与旅行照片做成带中文排版的编辑海报。
- 事件：窗口内新建仓库，2026-09-02，[来源](https://github.com/op7418/guizang-yingzao-skill)
- 能力标签：图像

**本次变化**

新仓库把照片转海报写成固定流程：先读照片构图与身份，选一张主导参考，设计中文标题与排版垫图，最后整体重绘（依据 g2）。海报完成后还能继续生成 3×3 视频分镜图和可交给视频模型的提示词（依据 g4）。

**谁值得关注**

把旅行、建筑、在地文化实拍照片做成带文字海报的创作者；做封面、海报类功能的产品——可参考“把一句提示词拆成固定步骤”的流程。能否提高一次出图合格率未验证。

**关键边界**

- 许可：仓库未声明许可，许可核实前只借鉴流程、不接入代码
- 依赖外部模型：使用 GPT Image，调用成本未说明（g1）
- 未经实测：只演示中文排版，英文及其他语种、海外场景未验证
<details>
<summary>具体改动（4 项）</summary>

- 仓库简介：Claude Code / Codex 技能，用 GPT Image 把建筑、在地文化与旅行照片转为艺术指导的编辑海报。（依据 g1）
- 流程：先读照片构图与身份，选一张兼容的主导参考，设计中文展示字和排版垫图，再交给图像模型整体重绘。（依据 g2）
- 保护屋坡、飞檐、匾额等身份特征，不把真实建筑改成另一栋楼。（依据 g3）
- 海报完成后可继续生成 3×3 视频分镜图和视频提示词。（依据 g4）

</details>

<details>
<summary>技术与采用条件</summary>

- 以 npx skills 安装到支持技能与图像生成的 Agent 中；依赖外部图像模型（GPT Image）。仓库未声明许可。
- 许可：未声明。许可待核实（GitHub未识别或未声明），不得视为可商用。模型权重与服务条款未核查
- 限制与未知：依赖外部图像生成模型，调用成本未说明；“Claude Code/Codex 技能”“使用 GPT Image”来自仓库简介，不等同于 README 已证明所有接口兼容。当前证据只支持写“许可待核实”；英文排版和海外创作者场景未实测。

</details>

<details>
<summary>对团队的启发</summary>

- 适合的用户任务：旅行、建筑或在地文化内容创作者，想把实拍照片做成有中文标题和排版的海报，再继续准备短视频素材。
- 方式：借鉴流程设计；许可未核实前不接入代码
- 改善哪个步骤：创作控制：用户从“写一句提示词”变成按固定步骤给出参考和排版。
- 可能影响的指标：首次生成即可发布的比例；修改轮数。
- 公开事实：该技能把读图、选参考、排版垫图写成固定步骤。（依据 g2）
- 公开事实：岗位面向全球创作者。（背景：同花顺官方校园招聘：AI Native出海产品经理（AI创新集群，杭州））
- 分析推断：结构化步骤可能减少“生成—不满意—重写提示词”的循环，这一思路可用于封面或海报类功能。
- 待验证：仓库只演示中文排版，不能证明英文或其他语种的本地化效果；海外创作者是否需要这类流程未验证。
- 产品假设：把“看构图、选参考、做排版垫图”写成固定步骤，可能比直接丢一句提示词更容易得到能用的海报；海报到分镜的衔接，也可能减少图转视频前的准备工作。不过这只是本期样本下的判断，英文排版和其他文化场景还没有验证。
- 最小验证建议（拟议，未执行）：选20张实拍照片，两组使用同一个图像模型、同样尺寸和设置：A组直接写提示词，B组使用该技能。第一轮每张只生成一次，由3名不知道分组的评审判断“可直接发布”的比例。若要比较修改轮数，另做第二轮，并给两组相同的修改时间和轮数上限。

</details>

<details>
<summary>原始依据（4 条）</summary>

- [g1] “Claude Code / Codex skill — transform Chinese architecture, cultural places & travel photos into art-directed editorial posters with GPT Image.” — 仓库简介，[原文](https://github.com/op7418/guizang-yingzao-skill)，原始响应 `data/runs/20261002T022921Z/raw/0004.json`
- [g2] “Yingzao 会先读照片的构图与身份，再选择一张兼容的主导参考，设计中文展示字与图文空间关系，最后把原图、参考与稀疏排版垫图一起交给图像模型完成整体重绘。” — README，[原文](https://github.com/op7418/guizang-yingzao-skill)，原始响应 `data/runs/20261002T022921Z/raw/0018.json`
- [g3] “保护屋坡、飞檐、匾额、轮廓、不对称等身份锚点，不把真实建筑“优化”成另一栋楼。” — README，[原文](https://github.com/op7418/guizang-yingzao-skill)，原始响应 `data/runs/20261002T022921Z/raw/0018.json`
- [g4] “海报完成后，可按你的选择继续制作一张 3×3 视频分镜图和可直接交给视频模型的提示词。” — README，[原文](https://github.com/op7418/guizang-yingzao-skill)，原始响应 `data/runs/20261002T022921Z/raw/0018.json`

</details>

选择理由：窗口内新建的图像生成工作流，把照片转为带中文排版的编辑海报，代表“能力封装成Agent技能”的新形态（AI（Claude）核查起草，待本人确认，核查于期次 20261001T210300Z）。解读审阅状态：AI草稿，未经本人审阅。

### 4. 自部署视频模型：加载时可融合 LoRA 风格插件

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

- [l1] “`lora_adapters` and `lora_scales` are now consumed by the vllm-cpp video engine, fusing LoRA deltas into DiT weights at engine load. Works for both LTX2.5 and MiniMax-H3 through one generic path.” — 版本说明，[原文](https://github.com/mudler/LocalAI/releases/tag/v4.10.0)，原始响应 `data/runs/20261002T022921Z/raw/0016.json`
- [l2] “measures end-to-end latency and throughput against configured text models.” — 版本说明，[原文](https://github.com/mudler/LocalAI/releases/tag/v4.10.0)，原始响应 `data/runs/20261002T022921Z/raw/0016.json`
- [l3] “The command does not measure decode-only speed or time to first token” — 版本说明，[原文](https://github.com/mudler/LocalAI/releases/tag/v4.10.0)，原始响应 `data/runs/20261002T022921Z/raw/0016.json`
- [l4] “Adapters are always loaded; there is no per-request activation in this path.” — 版本说明，[原文](https://github.com/mudler/LocalAI/releases/tag/v4.10.0)，原始响应 `data/runs/20261002T022921Z/raw/0016.json`
- [l5] “Four CVEs were patched” — 版本说明，[原文](https://github.com/mudler/LocalAI/releases/tag/v4.10.0)，原始响应 `data/runs/20261002T022921Z/raw/0016.json`
- [l6] “A fleet operations dashboard replaces the flat node list with cluster-wide health, capacity, running models, and bulk lifecycle actions.” — 版本说明，[原文](https://github.com/mudler/LocalAI/releases/tag/v4.10.0)，原始响应 `data/runs/20261002T022921Z/raw/0016.json`
- [l7] “A credentials file lets one `credentials.yaml` authenticate OCI registries, galleries and direct downloads without scattering tokens across environment variables.” — 版本说明，[原文](https://github.com/mudler/LocalAI/releases/tag/v4.10.0)，原始响应 `data/runs/20261002T022921Z/raw/0016.json`

</details>

选择理由：本地多模态推理引擎，本版为视频引擎加载LoRA、提供延迟与吞吐测量，关系到自部署生成服务的门槛（AI（Claude）核查起草，待本人确认，核查于期次 20261001T210300Z）。解读审阅状态：AI草稿，未经本人审阅。

### 5. 本地生图：最高快 3.6 倍（项目方指定显卡）

- 项目：[unslothai/unsloth](https://github.com/unslothai/unsloth) — 本地运行与训练语言模型和扩散模型的桌面界面与工具库。
- 事件：正式发布 v0.1.902-beta，2026-10-01，[来源](https://github.com/unslothai/unsloth/releases/tag/v0.1.902-beta)
- 能力标签：图像

**本次变化**

项目方报告：Qwen-Image-2.1 在 Radeon 8060S 上生成 1536×1536 图像最高快 3.6 倍（依据 u2）；同版本新增解释加载与生成失败原因的错误提示和“查看日志”按钮（依据 u5）。

**谁值得关注**

在本地显卡跑图像生成、关心出图等待的技术人员，以及做本地生图功能的产品——这些数字可作为复测线索，不建议直接据此选型。

**关键边界**

- 指定硬件：3.6 倍来自 Qwen-Image-2.1 ＋ Radeon 8060S ＋ 1536×1536 的项目方测试，未实测（u2）
- 不同测试：45% 显存下降来自语言模型 LoRA 训练（Qwen3.8-27B-NVFP4、单张 RTX PRO 6000，72.9→40.2GB），不是图像推理（u4、u3）
- 范围：图像提速不能外推到视频；版本名含 beta，但 API 字段标记为非预发布
<details>
<summary>具体改动（4 项）</summary>

- 图像模型在内存调配（offloading）时保持 INT8/FP8：限制 10GiB 显存的 B200 上，Z-Image 用时 2.3 秒（原为 38.4 秒）。（依据 u1）
- Qwen-Image-2.1 在 Radeon 8060S 上生成 1536×1536 图像最高快 3.6 倍。（依据 u2）
- NVFP4 LoRA 训练峰值显存降低 45%：Qwen3.8-27B-NVFP4 在单张 RTX PRO 6000 上从 72.9GB 降到 40.2GB，每步耗时缩短 11%。（依据 u4；依据 u3）
- 新增解释加载与生成失败原因的错误提示和查看日志按钮。（依据 u5）

</details>

<details>
<summary>技术与采用条件</summary>

- Apache-2.0。版本名含 beta，但保存的 API 字段标记为非预发布。性能数字均来自项目方指定的模型、精度与显卡。
- 许可：Apache-2.0。宽松许可：可商用，需保留版权与许可声明。模型权重与服务条款未核查
- 限制与未知：3.6倍来自 Qwen-Image-2.1 与 Radeon 8060S；45%显存来自 Qwen3.8-27B-NVFP4 与单张 RTX PRO 6000，属于语言模型训练。版本名称含 beta，但保存的 API 字段标记为非预发布。所有性能数字均来自项目方指定条件，未在本作品中实测。
- 窗口内其他事件：预发布 v0.1.901-beta，2026-10-01、正式发布 v0.1.900-beta，2026-09-28、正式发布 prebuilt-wheels-cu13，2026-09-27、正式发布 v0.1.815-beta，2026-09-23、正式发布 v0.1.814-beta，2026-09-22、正式发布 v0.1.813-beta，2026-09-22、正式发布 v0.1.812-beta，2026-09-22、正式发布 v0.1.811-beta，2026-09-18、正式发布 v0.1.810-beta，2026-09-17、正式发布 Windows-ARM64，2026-09-16、正式发布 v0.1.808-beta，2026-09-09、正式发布 v0.1.807-beta，2026-09-08、正式发布 v0.1.806-beta，2026-09-02、正式发布 v0.1.805-beta，2026-09-02

</details>

<details>
<summary>对团队的启发</summary>

- 适合的用户任务：在本地显卡上跑图像生成、或用 LoRA 做微调的团队，关心出图等待、显存够不够，以及失败后能不能看懂原因。
- 方式：暂作参考，不据此选型
- 改善哪个步骤：出图等待与训练硬件门槛。
- 可能影响的指标：单张出图耗时；训练峰值显存。
- 公开事实：提速和降显存数字分别来自指定硬件上的图像生成与语言模型训练。（依据 u2；依据 u4）
- 公开事实：岗位关注生成等待。（背景：同花顺官方校园招聘：AI Native出海产品经理（AI创新集群，杭州））
- 分析推断：如果团队在同类硬件上本地生图，可以把这些数字当作复测线索。
- 待验证：图像生成提速不能外推为视频提速；语言模型训练降显存不能写成图像推理降成本；未在本作品中实测。
- 产品假设：这里其实有三类收益：图像生成提速是少等，训练显存下降是降低硬件门槛，错误提示是失败后更容易继续。它们不能互相替代，也不能把项目方机器上的结果直接套到自己的电脑上。
- 最小验证建议（拟议，未执行）：图像生成单独测：固定同一显卡、模型、提示词、随机种子、尺寸和步数，比较升级前后各生成50张1536×1536图的单张耗时与失败率。LoRA训练另测：固定模型、精度、序列长度、批量和硬件，比较升级前后能否跑通、峰值显存和每步耗时。

</details>

<details>
<summary>原始依据（5 条）</summary>

- [u1] “Image models keep INT8 or FP8 when offloading. On a 10 GiB-capped B200, Z-Image takes 2.3 s, not 38.4 s.” — 版本说明，[原文](https://github.com/unslothai/unsloth/releases/tag/v0.1.902-beta)，原始响应 `data/runs/20261002T022921Z/raw/0015.json`
- [u2] “Qwen-Image-2.1 renders 1536x1536 images up to 3.6x faster on a Radeon 8060S.” — 版本说明，[原文](https://github.com/unslothai/unsloth/releases/tag/v0.1.902-beta)，原始响应 `data/runs/20261002T022921Z/raw/0015.json`
- [u3] “peaks at 40.2 GB instead of 72.9 GB on one RTX PRO 6000, with 11% shorter steps.” — 版本说明，[原文](https://github.com/unslothai/unsloth/releases/tag/v0.1.902-beta)，原始响应 `data/runs/20261002T022921Z/raw/0015.json`
- [u4] “NVFP4 LoRA with 45% lower peak memory” — 版本说明，[原文](https://github.com/unslothai/unsloth/releases/tag/v0.1.902-beta)，原始响应 `data/runs/20261002T022921Z/raw/0015.json`
- [u5] “that explain failed loads and generations, with a View logs button” — 版本说明，[原文](https://github.com/unslothai/unsloth/releases/tag/v0.1.902-beta)，原始响应 `data/runs/20261002T022921Z/raw/0015.json`

</details>

选择理由：本地训练与运行界面，本版给出图像生成提速与LoRA训练降显存两类数据，适合说明“速度与资源要分开看”（AI（Claude）核查起草，待本人确认，核查于期次 20261001T210300Z）。解读审阅状态：AI草稿，未经本人审阅。

## 跨项目信号

以下信号只说明本期少量项目里的共同点，不外推为行业趋势。

### 出错后，别让前面的工作白做（跨项目信号 · 基于 3 个项目）

本期三个项目处理的是三种不同的失败：VoiceStudio 尽量保住已经渲染好的章节，MoneyPrinterTurbo 遇到坏音频直接停下，Unsloth 把加载和生成失败的原因讲得更清楚。它们都在减少失败后的损失，但不是同一种“恢复”。验证时也应分开看：需要重做多少、残缺成片有多少、看懂错误后能不能继续。

依据项目：debpalash/VoiceStudio、harry0703/MoneyPrinterTurbo、unslothai/unsloth

### 创作能力，开始能被 AI 助手直接调用（跨项目信号 · 基于 2 个项目）

VoiceStudio 提供了 Claude Code、Cursor、Codex CLI 等接入配置；营造把照片到海报的流程做成 Agent 技能。做原型时，可以先试着把这些现成能力接进来，再看用户是否真的需要。这里只有两个样本，不能说整个行业都已经转向 Agent；配置要求和许可也要单独确认。

依据项目：debpalash/VoiceStudio、op7418/guizang-yingzao-skill

### 更快、更省显存、更稳定，不是一回事（跨项目信号 · 基于 3 个项目）

Unsloth 的3.6倍是图像生成速度，45%是语言模型 LoRA 训练的峰值显存；VoiceStudio 处理的是长章节超时；LocalAI 新增的是文本模型测速工具。选型时要把等待时间、硬件占用和稳定性分开比较，并确认数字来自什么模型、硬件和测试条件。

依据项目：unslothai/unsloth、debpalash/VoiceStudio、mudler/LocalAI

## 行动建议

先验证一项：口播视频渲染前的配音校验。在“脚本 → 配音 → 口型视频”流程中，于口型渲染前加一道配音校验（空白、截断、时长异常时中止并提示），与一次跑完的流程对照，主指标取每条合格视频所需的生成次数。理由：MoneyPrinterTurbo 的坏音频中止（m3）与 VoiceStudio 的已渲染章节保留（v2）都指向“失败后少重复”，头像视频类流程同样先配音、后画面，只借鉴机制即可、不受仓库许可约束。主要未知：现有流程是否已含校验、当前旁白残缺率与重生成次数均无数据，需先确认实际流程并跑一轮基线；若基线残缺率很低（建议低于 2%），可暂缓该实验。

<details>
<summary>展开实验参数</summary>

#### 优先实验：口播视频生成前，先校验配音

- 方式：借鉴机制，不接入仓库
- 为什么先做：MoneyPrinterTurbo 让坏音频中止生成、VoiceStudio 保留已完成章节，两项更新都在减少失败后的重复工作；DreamFace 头像视频同样先有配音再出画面。
- 目标用户：用照片加脚本生成多语言口播视频的海外创作者（以 DreamFace 头像视频类流程为参照）。
- 假设：在口型视频渲染前加一道配音校验，能减少每条合格视频的生成次数，且不明显增加等待。
- 对照流程：待确认：现有流程是否已含配音校验未知，需先确认实际流程，并以实际流程作为对照基线；不能预设“中间不校验”。
- 主要变量：唯一变量：在口型视频渲染前加入配音校验（空白、截断、时长异常时停止并提示用户）。
- 控制条件：两组使用同一批脚本、语种、音色、头像照片、模型版本与参数。
- 主指标：每条合格视频所需的生成次数。
- 质量与成本约束：质量：3 名不知分组的评审盲评旁白完整度与口型同步，不低于对照组。成本：每条合格视频的计算耗时或积分消耗不高于对照组（建议容差 +5%）。等待：单次生成耗时增加不超过 10%（建议值）。
- 所需角色：产品 1 人（流程与判定口径）、算法或工程 1 人（实现校验与记录日志）、评审 3 人。
- 前提：先用现有流程跑一轮基线，统计旁白残缺比例和重生成次数；没有基线不进入对照。需要可复现的离线测试环境。
- 样本与周期：建议 3 个语种 × 40 条脚本，约 1 周（建议值，未经统计功效计算）。
- 限制：离线样片测试不能证明留存或付费转化提升；本建议尚未执行。
- 继续：基线中旁白残缺或重生成明显（建议 ≥5%），实验组每条合格视频的生成次数下降 ≥20%，质量不降。
- 调整：能拦下坏音频但等待增加超过 10%：改为异步校验，或只对长脚本校验。
- 停止：基线残缺率低于 2%（本次样本未显示足够的优先投入价值），或两组没有差异。
- 依据：harry0703/MoneyPrinterTurbo、debpalash/VoiceStudio、DreamFace 头像视频（Avatar Video）产品页、DreamFace 订阅与积分政策、同花顺官方校园招聘：AI Native出海产品经理（AI创新集群，杭州）


</details>

<details>
<summary>有条件实验（2 项）</summary>

#### 有条件实验：结构化排版流程 vs 直接提示词（海报、封面类功能）

- 方式：借鉴流程设计
- 假设：按“读构图 → 选参考 → 排版垫图 → 重绘”的步骤生成，首次即可发布的比例高于直接写提示词。
- 主指标：首次生成即可发布的比例（3 名盲评评审判定）。
- 前提条件：先用英文和一种目标语种各做 10 张样图，确认排版可用；营造仓库许可待核实，在此之前只借鉴流程、不接入代码。
- 限制：中文海报工作流不能直接证明海外本地化效果。
- 依据：op7418/guizang-yingzao-skill、同花顺官方校园招聘：AI Native出海产品经理（AI创新集群，杭州）

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

#### 暂缓：按项目方测速数字做选型或成本判断

- 理由：Unsloth 的 3.6 倍是指定显卡上的图像生成，45% 是语言模型训练显存；LocalAI 新测速只覆盖文本模型。这些都不能外推到视频生成速度或推理成本。
- 依据：unslothai/unsloth、mudler/LocalAI

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

- [jajmangold/not_human](https://github.com/jajmangold/not_human)：窗口内新建仓库，2026-09-24，[来源](https://github.com/jajmangold/not_human)。原因：尚无核查记录：窗口内有事件不等于值得推荐，需人工核查。简介：Experiments toward a real-time, controllable talking human: measurements, failures and working pieces (speech, lip sync, expression control, perception) on Volta-class GPUs
- [leemysw/yovoice](https://github.com/leemysw/yovoice)：正式发布 v0.1.6，2026-10-01，[来源](https://github.com/leemysw/yovoice/releases/tag/v0.1.6)。原因：尚无核查记录：窗口内有事件不等于值得推荐，需人工核查。简介：Open-source voice creation for macOS and Windows. Local TTS, voice cloning, and emotion control — no cloud APIs or per-character fees.
- [Rylaispirit/cinematic-video-prompt-skill](https://github.com/Rylaispirit/cinematic-video-prompt-skill)：窗口内新建仓库，2026-09-20，[来源](https://github.com/Rylaispirit/cinematic-video-prompt-skill)。原因：尚无核查记录：窗口内有事件不等于值得推荐，需人工核查。简介：AI video prompt cheat sheet & Claude Skill: cinematic camera angles, camera movement, lighting, composition, color grading for Veo 3, Kling, Sora, Runway, Midjourney. 700+ terms with Vietnamese explanations.

## 移出与变化

- 对比上一期快照 20261001T210300Z：新增 无。

## 排除记录

- yikang329-droid/kaipai-talking-head-skill：AIGC相关性弱：主要是真人口播素材的剪辑与字幕流程，README较短，未见生成能力的实质说明。适用范围：仅该事件，出现新事件或说明变化即失效。证据：https://github.com/yikang329-droid/kaipai-talking-head-skill
- apimart-API-Gateway/grok-image-api：未通过“来源可查/开源实现”核查：README是商业API聚合方的按图计价与调用示例（含推广短链），与已排除的seedance系列同一模式，没有可核查的开源实现。适用范围：仓库整体，简介变化即失效。证据：https://github.com/apimart-API-Gateway/grok-image-api
- lemomo-ai/lemo-opuscar：未通过“实质变化”核查：窗口内发布为自动滚动发布，说明只有一句；仓库主体是风格提示词与示例片合集。适用范围：仅该事件，出现新事件或说明变化即失效。证据：https://github.com/lemomo-ai/lemo-opuscar/releases
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
| 视频 | 成功 | 28 | 2 | 2 | 1 | 23 | 0 |
| 图像 | 成功 | 27 | 4 | 0 | 0 | 23 | 0 |
| 语音 | 成功 | 27 | 4 | 0 | 0 | 23 | 0 |
| 数字人 | 成功 | 27 | 2 | 2 | 0 | 23 | 0 |

检索到的候选 109 个 → 窗口内有事件 12 个 → 正式精选 5 个、待核查 3 个、经核查排除 4 个。

- 检索分类“视频”下本期无正式精选：检查4个，2个窗口内无正式发布、预发布或新建，1个有事件但待核查，1个有事件但经核查排除，另有23个未检查。按能力标签，有2个精选项目涉及视频：harry0703/MoneyPrinterTurbo、mudler/LocalAI。
- 检索分类“数字人”下本期无正式精选：检查4个，2个窗口内无正式发布、预发布或新建，1个有事件但待核查，1个有事件但经核查排除，另有23个未检查。按能力标签，本期也没有精选项目涉及数字人。

### 各项目抓取时累计 Stars（一次观测，不代表增长）

| 项目 | Stars | 许可 |
|---|---|---|
| harry0703/MoneyPrinterTurbo | 127967 | MIT |
| debpalash/VoiceStudio | 51428 | AGPL-3.0 |
| op7418/guizang-yingzao-skill | 480 | 未声明 |
| mudler/LocalAI | 49365 | MIT |
| unslothai/unsloth | 77122 | Apache-2.0 |

### 检索范围与截断

| 分类 | 检索 | GitHub匹配总数 | 实际取回 | 是否截断 |
|---|---|---|---|---|
| 视频 | 近期有推送（按Stars） | 510 | 20 | 是 |
| 视频 | 窗口内新建（按Stars） | 199 | 10 | 是 |
| 图像 | 近期有推送（按Stars） | 1957 | 20 | 是 |
| 图像 | 窗口内新建（按Stars） | 807 | 10 | 是 |
| 语音 | 近期有推送（按Stars） | 2368 | 20 | 是 |
| 语音 | 窗口内新建（按Stars） | 927 | 10 | 是 |
| 数字人 | 近期有推送（按Stars） | 57 | 20 | 是 |
| 数字人 | 窗口内新建（按Stars） | 24 | 10 | 是 |

每条检索只取Stars最高的前20或10个，排名之后的仓库没有进入候选；候选中还有 92 个因名额未检查（名单见 data/brief.json 的 candidates）。
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
