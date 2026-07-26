# 明白金 FinFair｜金融产品“公平说明书”Agent

> 不替用户做决定，只把金融产品中重要、容易被忽略的事情讲明白。

**明白金是一款金融产品购买前信息核验 Agent：它将宣传材料与正式说明书逐项对照，把收益、本金、期限、费用和风险翻译成普通用户能理解的说明，并为每个结论提供可追溯证据。**

在线体验：[https://finfair-agent.streamlit.app/](https://finfair-agent.streamlit.app/)

当前课程 MVP 的首要用户是普通金融消费者，交付的是一条可运行、可演示的购买前核验闭环。金融机构营销材料一致性初审属于后续 B2B 延伸方向，不是当前已经交付或验证的能力。

用户可上传带有可复制文字的金融产品 PDF，并同时粘贴宣传文案；系统提取关键字段、检查两类材料的信息差异，并输出带页码和原文证据的“公平说明书”。

项目仓库是课程要求中的可运行交付物；商业计划书 PPT 见 [docs/商业计划书.pptx](./docs/商业计划书.pptx)，Demo 介绍视频见 [demo/FinFair介绍视频.mp4](./demo/FinFair介绍视频.mp4)。

规范文档入口：

- [产品需求文档](./docs/prd.md)
- [技术与交互设计](./docs/design.md)
- [验收与证据清单](./docs/checklist.md)
- [最终项目报告（持续更新）](./report/final-report.md)

## 1. 为什么做这个项目

金融产品正式文件通常篇幅长、术语多，而宣传材料倾向突出收益和便利性。普通用户真正关心的“是否保本、最坏会怎样、何时能退出、需要付什么费用”，可能分散在不同页面。

已有监管材料和研究支持以下设计原则：

- 披露应当可理解、完整、及时，并优先呈现关键信息；
- 个人投资者偏好摘要式、分层式披露；
- 通俗表达有助于理解金融条款，但披露本身不能消除行为偏差和利益冲突；
- 金融 AI 的结论需要解释、证据和不确定性提示；
- 工具应解释产品而非替用户做适当性判断或购买决定。

因此，报告采用“30 秒看懂 → 通俗解释 → 页码原文”的分层结构，并把宣传材料检查与正式说明书核验结合起来。

项目限制：现有研究只能支持“问题存在”和“设计原则有依据”，不能证明本项目的使用意愿、付费意愿、用户转化率或机构采购需求。由于课程项目时间有限且缺少足够的现成证据，本项目不对这些商业结果作结论。

## 2. 当前成果与项目状态

当前状态：**已公开部署的课程 MVP，核心 Demo 闭环已完成。**

| 模块 | 当前状态 | 说明 |
| --- | --- | --- |
| PDF 解析 | 已完成 | 按页解析含可复制文字的 PDF |
| 核心字段提取 | 已完成 | 本金、收益表述、期限、赎回、费用、风险等 |
| 宣传材料逐项对照 | 已完成 | 主结果直接展示宣传说法、正式结论、核验状态、优先级和页码证据 |
| 分析覆盖披露 | 已完成 | 展示解析页数、提取字符、空白页、Agent 接收字符及截断状态 |
| 证据追溯 | 已完成 | 关键结果附原文和页码 |
| 规则模式 | 已完成 | 不配置 API 也能完成稳定演示 |
| 双阶段 Agent | 已完成 | 同一模型配置依次承担分析与核验角色，再由程序执行引用门控 |
| 多模型接口 | 已完成 | 千问、DeepSeek、Kimi、Grok、Gemini、OpenAI、Claude |
| 报告导出 | 已完成 | Markdown、JSON、Word、PDF |
| 自动化测试 | 已完成 | 已覆盖规则、宣传对照、双 Agent、引用门控和接口安全等场景 |
| 标准答案基准集 | 已完成 | 12个团队模拟案例，保存公式、分母、逐案例结果和失败明细 |
| 响应式课堂界面 | 已完成 | 桌面与375px手机端无页面横向溢出，核心宣传对照优先展示 |
| OCR | 未实现 | 暂不支持纯扫描件和图片 |
| 多产品横向比较 | 未实现 | 当前一次分析一个产品 |
| 正式适当性评估 | 明确不做 | 不收集客户画像，不生成购买建议 |
| 使用意愿与商业结果 | 项目限制 | 缺少足够证据，不宣称已验证付费、转化或机构采购需求 |

内置模拟案例的预期结果为：解析 4 页 PDF、提取 8 个核心字段，并识别 6 项宣传材料问题。详细测试过程见 [`测试报告.md`](./测试报告.md)。

规则模式基准集包含12个团队模拟案例。当前结果及完整分母见 [`report/benchmark-results.json`](./report/benchmark-results.json)。其中的100%只代表当前代码满足这12个预设样例，不代表真实金融产品准确率。

## 3. 核心产品流程

```text
选择内置案例或上传产品说明书
        ↓
输入宣传文案（可选）
        ↓
规则引擎提取确定性字段并执行公平性检查
        ↓
可选：大模型语义分析 Agent 提出候选洞察
        ↓
第二阶段证据核验 Agent 复核
        ↓
程序确认逐字引文真实存在于指定页
        ↓
披露规则与 Agent 实际覆盖范围
        ↓
展示分层结果并导出 Markdown / JSON / Word / PDF
```

它不是一个简单的“PDF 聊天机器人”。系统会围绕明确任务执行提取、比较、核验和报告生成；大模型只补充规则难以覆盖的复杂语义，确定性事实仍优先由规则引擎处理。

当前分析阶段和核验阶段使用同一份厂商、模型和协议配置，按固定顺序各调用一次。这里的“双阶段”指职责分离，不代表两个完全独立的模型，也不存在两个 Agent 无限互聊。

### 防幻觉与降级策略

只有同时通过以下检查的新增语义洞察才会展示：

1. 分析 Agent 给出结论、页码和逐字引文；
2. 核验 Agent 判定原文支持结论；
3. 程序在指定页面找到该引文；
4. API 失败或结果不合格时，自动保留规则模式结果。

这一设计降低幻觉进入报告的概率，但不能保证零错误，最终仍需人工核对正式文件。

## 4. 快速开始

### 环境要求

- Python 3.10 或更高版本
- Windows、macOS 或 Linux
- 如启用语义增强，需要对应厂商的 API Key

### 安装与启动

```powershell
git clone https://github.com/XiAn-07/FinFair.git
cd FinFair
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

macOS / Linux 激活环境时使用：

```bash
source .venv/bin/activate
```

Windows 用户也可在项目目录运行：

```powershell
.\启动应用.ps1
```

### 最快 Demo

1. 保持左侧“使用内置教学案例”开启；
2. 暂不开启大模型增强；
3. 点击“开始生成公平说明书”；
4. 先查看首页结果区的“宣传材料与正式说明书逐项对照”，再查看摘要、风险和页码证据；
5. 下载任一格式报告。

规则模式无需 API，可以用于课堂稳定演示。

### 使用自己的材料

关闭“使用内置教学案例”，上传带有可复制文字的 PDF。上传前必须删除姓名、身份证号、银行卡号、账户信息、交易流水等真实或敏感数据。纯扫描件目前无法解析。

## 5. 可选大模型增强

在侧栏开启“启用大模型语义增强”，选择厂商，填写或确认 Base URL、模型名称与 API Key，勾选数据发送提示，然后点击“确认并保存 API”。页面出现“API 已保存（当前会话）”后配置才会生效。

| 厂商 | 官方 Base URL | 页面默认模型 | 协议 |
| --- | --- | --- | --- |
| 通义千问（阿里云百炼·国内） | `https://dashscope.aliyun.com/compatible-mode/v1` | `qwen3.7-plus` | OpenAI 兼容 |
| DeepSeek | `https://api.deepseek.com` | `deepseek-v4-flash` | OpenAI 兼容 |
| Kimi（月之暗面·国内） | `https://api.moonshot.cn/v1` | `kimi-k2.6` | OpenAI 兼容 |
| Grok（xAI） | `https://api.x.ai/v1` | `grok-4.5` | OpenAI 兼容 |
| Gemini（Google AI） | `https://generativelanguage.googleapis.com/v1beta/openai` | `gemini-3.6-flash` | OpenAI 兼容 |
| OpenAI | `https://api.openai.com/v1` | `gpt-5-mini` | Chat Completions |
| Claude（Anthropic） | `https://api.anthropic.com/v1` | `claude-sonnet-5` | 原生 Messages API |

页面还支持自定义 OpenAI 兼容接口和自定义 Anthropic 原生接口。模型 ID、区域可用性和账号权限可能变化，应以厂商控制台为准。

API Key 只保存在当前 Streamlit 会话，不写入仓库或下载报告。启用增强后，PDF 提取文字与宣传文案会发送给所选服务商；请阅读对应服务商的数据处理条款，并且不要上传真实客户材料。

## 6. 项目结构

```text
FinFair/
├── app.py                         # Streamlit 页面与完整交互流程
├── finfair/
│   ├── __init__.py                # 对外模块接口
│   ├── core.py                    # PDF 解析、规则提取、宣传检查、Markdown
│   ├── llm_agent.py               # 多厂商调用、双 Agent 与证据校验
│   └── report_export.py           # Word、PDF 报告生成
├── sample_data/
│   ├── 模拟理财产品说明书.pdf       # 教学模拟材料
│   ├── 人工标准答案.json            # 基准答案
│   └── build_sample_pdf.py        # 样例生成脚本
├── tests/
│   ├── test_core.py               # 规则与核心闭环测试
│   └── test_llm_agent.py          # Agent、引用门控和协议测试
├── requirements.txt
├── 启动应用.ps1
├── 测试报告.md
└── 项目制作方案.md
```

本地生成的 `test*.md`、`test*.docx`、`test*.pdf`、缓存、密钥和临时文件已通过 `.gitignore` 排除，不应提交到 GitHub。

## 7. 测试与复现

运行全部自动化测试：

```powershell
pytest tests -q
```

测试覆盖：

- 标准案例的字段提取与宣传问题识别；
- 信息缺失时显示待确认，不自行补全；
- 宣传文案与正式文件冲突；
- 双 Agent 调用及 JSON 结构处理；
- 虚构引文拦截和页码逐字引用校验；
- 非 HTTPS、本机和内网接口拒绝；
- Claude 原生 Messages API 请求与解析。

人工基准答案位于 [`sample_data/人工标准答案.json`](./sample_data/人工标准答案.json)。模型接口测试使用模拟响应，不消耗真实 API 额度。

## 8. 风险边界与负责任使用

| 风险 | 当前控制 | 剩余边界 |
| --- | --- | --- |
| 金融误导 | 不预测收益、不做产品推荐，展示原文证据 | 规则和模型仍可能误读复杂条款 |
| 大模型幻觉 | 双 Agent 核验 + 程序逐字引用门控 | 无法保证所有遗漏和错误均被发现 |
| 适当性越界 | 不收集风险承受能力，不输出“适合买/不适合买” | 不能代替持牌机构的适当性流程 |
| 隐私与数据 | 密钥仅存当前会话，提示用户去标识化 | 启用 API 后文本会发送给第三方模型厂商 |
| 文档解析 | 保留页码、缺失内容标记待确认 | 表格、特殊排版和扫描件可能解析失败 |
| 宣传判断 | 按有限规则提示疑点 | 不等同于监管认定或法律结论 |

本项目仅用于课程教学、产品原型与信息辅助，不构成投资建议、收益承诺、法律意见、合规审查或正式适当性评估。不要依据本工具单独作出交易决定；最终应以金融机构正式文件、监管要求和专业人员人工复核为准。

## 9. 课程交付对应关系

| 课程要求 | 本项目对应成果 |
| --- | --- |
| GitHub 项目库 | 本仓库：代码、测试、说明与模拟数据（两名成员协作，2 个 PR 已合并） |
| 商业计划书 / 路演 PPT | [docs/商业计划书.pptx](./docs/商业计划书.pptx)（12 页，含产品定位、市场、技术与商业假设） |
| Demo 视频 | [demo/FinFair介绍视频.mp4](./demo/FinFair介绍视频.mp4)（产品演示） |
| 创业团队视角 | 明确用户痛点、差异化、商业设想和现阶段项目限制 |
| 需求与前景判断 | 使用研究与监管材料支持问题，不虚构市场验证 |
| 用户触达与转化思考 | 以购买前解释工具为 B2C 入口，B2B 营销材料初审为后续方向 |
| 可用性与先进性 | 无 API 可用、混合 Agent 增强、多层证据门控、多格式导出 |
| 团队合作 | 两位成员协作：XiAn-07 负责核心工程（规则引擎、双 Agent、测试与部署），rachelmeize-ui 负责商业计划书、演示视频与课程交付；PR [#1](https://github.com/XiAn-07/FinFair/pull/1)、[#2](https://github.com/XiAn-07/FinFair/pull/2) 已合并，仓库贡献记录可见两名贡献者 |

本项目不声称“市场上没有类似产品”。差异化在于把金融文件解释、宣传材料对比、最不利情形提示和页码证据组合到中国金融消费者购买前场景。

## 10. 参考与致谢

### 研究与监管材料

- [SEC：Report of the Task Force on Disclosure Simplification](https://www.sec.gov/news/studies/smpl.htm)
- [SEC：Plain English Disclosure](https://www.sec.gov/rules-regulations/1998/01/plain-english-disclosure)
- [SEC：Study Regarding Financial Literacy Among Investors](https://www.sec.gov/file/917-financial-literacy-study-part1pdf)
- [OECD：Consumer Finance Risk Monitor 2026](https://www.oecd.org/en/publications/consumer-finance-risk-monitor-2026_61f7dbe0-en/full-report/conduct-related-risks_3038e5f7.html)
- [Ben David 等：Explainable AI and Adoption of Financial Algorithmic Advisors](https://arxiv.org/abs/2101.02555)
- [国家金融监督管理总局：《金融机构产品适当性管理办法》](https://www.nfra.gov.cn/cn/view/pages/ItemDetail.html?docId=1217123&itemId=917)

### API 官方文档

- [阿里云百炼 Base URL](https://help.aliyun.com/en/model-studio/base-url)
- [DeepSeek API](https://api-docs.deepseek.com/)
- [Kimi API](https://platform.kimi.com/docs/api/overview)
- [xAI API](https://docs.x.ai/)
- [Gemini OpenAI compatibility](https://ai.google.dev/gemini-api/docs/openai)
- [OpenAI API](https://platform.openai.com/docs/api-reference)
- [Anthropic Messages API](https://platform.claude.com/docs/en/api/messages/create)

### 类似产品与开源思路

项目调研参考了 SEC/FINRA 面向投资者的解释工具、FinanceBench，以及公开的 PDF 问答与证据检索项目。参考仅用于理解功能边界与工程思路；本项目未复制商业产品的代码、商标、文案或视觉资产。

#### 同类方案结构化对比

| 维度 | 明白金 FinFair | SEC / FINRA 投资者解释工具 | FinanceBench | 通用 PDF 问答 / 证据检索 |
| --- | --- | --- | --- | --- |
| 目标用户 | 中国金融消费者（购买前） | 美国投资者（教育） | 研究者 / 评测基准 | 通用读者 |
| 宣传材料 vs 正式文件逐项对照 | ✅ 核心功能 | ❌ | ❌（仅问答） | ❌ |
| 页码 + 原文证据追溯 | ✅ | 部分 | ✅（研究场景） | 视实现而定 |
| 最不利情形提示 | ✅ | 部分 | ❌ | ❌ |
| 中国金融消费者购买前场景聚焦 | ✅ | ❌（美国语境） | ❌ | ❌ |
| 可运行部署 | ✅ Streamlit Cloud | 监管网站 | 数据集 / 脚本 | 各异 |

差异化在于把上述能力组合到中国金融消费者购买前场景；这一组合是否构成长期壁垒仍需市场验证，当前阶段仅作为课程 MVP 的能力定位说明。

感谢 Streamlit、pdfplumber、python-docx、ReportLab、pytest 及其开源社区。第三方名称和商标归各自权利人所有。

## 11. 后续路线

1. 完成 1—2 名外部同学的最小可用性测试并如实记录；
2. 增加 OCR 与复杂表格解析；
3. 扩展更多金融产品与多产品对比；
4. 建立更大的人工标注测试集并量化准确率、召回率和证据正确率；
5. 商业计划书 PPT、Demo 视频和团队分工披露（已完成，见第 9 节）；
6. 在真实部署前补充用户协议、数据保留策略、密钥代理与安全审计。

---

课程教学项目，当前未提供开源许可证；在许可证补充前，仓库公开不等于授权复制、修改或再分发。
