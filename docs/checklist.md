# 明白金 FinFair 验收与证据清单

> 版本：V1.0
> 规则：只有完成操作并保存证据后才能标记为 `[x]`。`[ ]` 表示未验证，不代表功能一定有问题。
> 状态日期：2026-07-25

| 状态 | 检查项 | 操作方法 | 预期结果 | 证据路径 | 复测结果 |
| --- | --- | --- | --- | --- | --- |
| [x] | AC-01 应用可加载 | 使用 Streamlit AppTest 运行 `app.py` | 页面运行且无异常对象 | 本轮终端测试；`app.py` | 通过 |
| [x] | AC-01 内置案例进入规则分析 | 运行核心测试中的 Demo 案例 | 生成非空分析结果 | `tests/test_core.py::test_demo_case`、`测试报告.md` | 既有完整环境记录为通过；当前终端缺少 `pdfplumber`，提交前还需复测 |
| [x] | AC-02 页码与引文对应 | 对照模拟 PDF 和人工标准答案 | 关键引文可在对应页找到 | `sample_data/人工标准答案.json`、`tests/test_core.py`、`测试报告.md` | 既有完整环境记录为通过 |
| [x] | AC-03 缺失字段不补造 | 运行最小缺字段测试 | 缺失项标记待确认 | `tests/test_core.py::test_missing_fields_are_marked_for_review` | 通过 |
| [x] | AC-04 冲突宣传被提示 | 运行冲突宣传测试 | 输出宣传风险提示 | `tests/test_core.py::test_conflicting_marketing_copy_is_flagged` | 通过 |
| [x] | AC-04 一致宣传被标记支持 | 运行完整披露样例 | 六个核验项目均为 `supported` | `tests/test_core.py::test_consistent_marketing_is_marked_supported` | 通过 |
| [x] | AC-04 遗漏与冲突分开 | 运行“年化收益、灵活取用”样例 | 本金和费用为未披露，收益和赎回为冲突 | `tests/test_core.py::test_omission_and_conflict_are_distinct` | 通过 |
| [x] | AC-04 正式证据不足 | 使用信息不足的正式材料 | 状态为无法判断且证据位置为未定位 | `tests/test_core.py::test_formal_document_missing_evidence_is_unclear` | 通过 |
| [x] | AC-04 未输入宣传材料 | 使用空宣传文案 | 明确提示未执行宣传对照，不误报“没有问题” | `tests/test_core.py::test_no_marketing_input_has_distinct_state` | 通过 |
| [x] | AC-05 非原文引文被拦截 | 运行引用门控测试 | 不在指定页的引文不被接收 | `tests/test_llm_agent.py` | 通过 |
| [x] | AC-06 无 API 可使用规则模式 | 不保存 API，运行内置案例 | 不调用模型也可生成规则结果 | `app.py`、`finfair/core.py`、`测试报告.md` | 既有完整环境记录为通过；仍需最终页面录屏 |
| [x] | AC-07 仓库无真实密钥 | 搜索常见密钥格式并检查 Git 状态 | 无真实 Key 被跟踪 | `.gitignore`、`.env.example` | 当前结构符合；提交前必须再次扫描 |
| [x] | AC-08 四种报告可下载 | 页面检查四个下载入口，并用完整依赖环境生成四种文件 | 四个文件非空且内容对应同一次分析 | `screenshots/rule-mode.png`、`tests/test_core.py::test_four_report_formats_include_same_comparison_status` | 浏览器显示4个入口，四格式生成与内容测试通过 |
| [x] | AC-09 金融边界可见 | 查看首页、侧栏和报告免责声明 | 明确不构成投资建议 | `app.py`、`README.md` | 通过文本检查 |
| [x] | AC-10 普通文档覆盖统计 | 分析含文字和空白页的页面列表 | 页数、字符数、空白页数正确 | `tests/test_core.py::test_document_coverage_counts_empty_pages` | 通过 |
| [x] | AC-10 全空文档拒绝 | 模拟两页均无法提取文字 | 明确拒绝并提示扫描件需要 OCR | `tests/test_core.py::test_all_empty_pdf_is_rejected` | 通过 |
| [x] | AC-10 长文 Agent 截断 | 构造超过 45,000 字符的文本 | 接收字符为 45,000 且截断为真 | `tests/test_llm_agent.py::test_document_text_reports_truncation` | 通过 |
| [x] | AC-10 API 失败保留覆盖数据 | 模拟模型请求失败 | 规则页数、字符数和空白页信息不丢失 | `tests/test_llm_agent.py::test_agent_failure_preserves_rule_coverage` | 通过 |
| [x] | AC-11 双阶段职责与停止条件 | 模拟两个固定模型响应 | 分析、核验各调用一次，程序门控后停止 | `tests/test_llm_agent.py::test_two_agent_calls_and_exact_quote_gate` | 通过 |
| [x] | AC-11 无候选时正常停止 | 分析 Agent 返回空候选 | 核验阶段完成后停止，不进入循环 | `tests/test_llm_agent.py::test_no_candidates_still_runs_fixed_verification_stage` | 通过 |
| [x] | AC-11 虚构引用程序拦截 | 核验阶段误判虚构引文为支持 | 程序门控仍拦截并记录原因 | `tests/test_llm_agent.py::test_two_agent_calls_and_exact_quote_gate` | 通过 |
| [x] | AC-12 基准集规模与来源 | 检查数据集结构 | 12个案例均有类别、来源和标准答案 | `tests/test_benchmark.py::test_benchmark_has_required_case_structure` | 通过 |
| [x] | AC-12 参数化案例复现 | 运行基准参数化测试 | 每个案例单独运行并保留失败原因 | `tests/test_benchmark.py::test_benchmark_case` | 12例通过 |
| [x] | AC-12 指标与分母 | 运行完整评测 | 输出字段、证据、查准、召回、拒答及安全指标的公式和分母 | `report/benchmark-results.json` | 通过 |
| [x] | AC-12 失败不被删除 | 检查评测脚本和机器结果 | 所有案例进入 `case_results`，失败时返回非零退出码 | `scripts/run_benchmark.py` | 通过代码与结构检查 |
| [x] | AC-13 桌面端布局 | 在1440px宽度运行内置案例 | 无明显遮挡、截断或页面横向溢出 | `screenshots/rule-mode.png` | `scrollWidth = innerWidth = 1440` |
| [x] | AC-13 手机端布局 | 在375px宽度运行内置案例 | 可选择入口、分析并查看核心结果 | `screenshots/mobile.png`、`screenshots/marketing-contrast.png` | `scrollWidth = innerWidth = 375` |
| [ ] | 混合 Agent 实际调用 | 使用测试 Key 分析模拟材料 | 显示模型、接受数、拦截数且规则结果保留 | `screenshots/hybrid-agent.png` | 待最终 Demo 环境复测 |
| [x] | AC-13 宣传对照截图 | 用模拟宣传文案运行 | 宣传说法、正式证据和文字状态可见 | `screenshots/marketing-contrast.png` | 通过 |
| [x] | AC-13 动态HTML安全 | 注入 `<script>` 与事件属性作为证据文字 | 使用原生安全元素渲染，不进入可执行HTML | `tests/test_ui.py::test_untrusted_evidence_uses_native_safe_rendering` | 通过 |
| [ ] | 在线部署 | 打开公开地址并运行内置案例 | 免费公开地址可访问且核心流程可用 | `screenshots/deployed-site.png` | 尚未部署 |
| [ ] | 最终课程核对 | 对照提交要求检查仓库、PPT、视频 | PPT ≤5 分钟，Demo 视频 ≤2 分钟，链接有效 | `screenshots/checklist.png` | 待最终交付阶段 |

## 复测命令

在已安装 `requirements.txt` 的环境中运行：

```powershell
$env:PYTHONPATH = (Get-Location).Path
python -m pytest -q
python -m py_compile app.py
```

预期：全部测试通过且编译无错误。若失败，应记录失败用例、环境、原因、修复文件和复测结果，不得只写“测试通过”。
