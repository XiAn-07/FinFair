# 明白金 FinFair

> 不替你做决定，只把重要的事讲明白。

明白金是一个课程教学MVP。用户上传金融产品说明书并粘贴宣传文案后，系统提取本金保障、业绩比较基准、期限、赎回条件、费用和主要风险，检查宣传材料与正式文件的差异，并为关键结论提供页码和原文证据。

## 当前版本

当前版本采用“可审计规则引擎 + 可选双逻辑Agent”。不配置API时仍可稳定运行；
用户也可以在页面中自行接入OpenAI兼容接口，由语义分析Agent和证据核验Agent各调用一次。

已实现：

- PDF按页解析；
- 核心金融字段提取；
- 风险与最不利情形说明；
- 宣传材料一致性检查；
- 页码和原文引用；
- 购买前问题清单；
- Markdown、JSON、Word和PDF下载；
- 内置教学模拟案例。
- 用户自行配置API、Base URL和模型名称；
- 大模型失败自动降级为规则模式；
- 模型结论经过证据核验Agent和程序化逐字引用双重校验。

暂未实现：

- 扫描件OCR；
- 多产品比较；
- 大模型语义增强；
- 正式适当性评估；
- 投资推荐。

## 运行方法

```powershell
pip install -r requirements.txt
streamlit run app.py
```

浏览器打开Streamlit显示的本地地址，保留“使用内置教学案例”，点击“开始生成公平说明书”即可完成Demo。

Windows也可以在项目目录中右键运行：

```text
启动应用.ps1
```

## Demo流程

```text
上传/选择模拟说明书
→ 输入模拟宣传文案
→ 解析4页PDF
→ 提取核心字段
→ 检查宣传材料
→ 查看页码证据
→ 下载报告
```

## 可选大模型增强

在左侧打开“启用大模型语义增强”，填写：

- OpenAI兼容接口的 Base URL；
- 模型名称；
- API Key；
- 数据发送确认。

填写完成后必须点击“确认并保存 API”。页面显示“API 已保存（当前会话）”后，
Agent 才会使用该配置。密钥只保存在当前 Streamlit 会话中，可以随时点击清除；
应用服务重启后需要重新填写。

DeepSeek 当前官方预设为：

```text
Base URL: https://api.deepseek.com
Model: deepseek-v4-flash
```

API Key只存在于当前Streamlit会话，不写入项目文件或下载报告。PDF提取文字和宣传文案
会发送到用户选择的模型服务商，因此不得上传真实客户资料或其他敏感信息。

混合Agent流程：

```text
规则引擎提取确定性事实
→ 语义分析Agent提出候选洞察
→ 证据核验Agent独立审查
→ 程序检查逐字引文是否真实存在于对应页
→ 仅展示通过双重核验的内容
```

## 测试

```powershell
pytest tests/test_core.py
```

人工标准答案位于：

```text
sample_data/人工标准答案.json
```

## 项目结构

```text
.
├── app.py
├── finfair/
│   ├── __init__.py
│   └── core.py
├── sample_data/
├── tests/
├── requirements.txt
└── 项目制作方案.md
```

## 风险边界

- 仅用于教学模拟和信息辅助；
- 不构成投资建议、法律意见或正式适当性评估；
- 不预测收益；
- 不建议购买或拒绝购买具体产品；
- 请勿上传身份证、银行卡号、账户流水等真实敏感信息；
- 最终判断应以金融机构正式文件和人工核对为准。

## 参考与致谢

项目在功能和工程思路上参考了公开产品与开源项目，包括Explain Documents、BeforeYouPay、FINRA Fund Analyzer、FinanceBench和LLM-powered PDF Chatbot。项目没有复制商业产品的代码、文案、商标或视觉素材。使用任何开源代码前应再次核对其许可证并保留必要声明。
