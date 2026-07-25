from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "模拟理财产品说明书.pdf"
FONT_REGULAR = Path(r"C:\Windows\Fonts\msyh.ttc")
FONT_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")

pdfmetrics.registerFont(TTFont("YaHei", str(FONT_REGULAR), subfontIndex=0))
pdfmetrics.registerFont(TTFont("YaHeiBold", str(FONT_BOLD), subfontIndex=0))

NAVY = colors.HexColor("#102A43")
BLUE = colors.HexColor("#1769AA")
LIGHT_BLUE = colors.HexColor("#EAF4FB")
LIGHT_GRAY = colors.HexColor("#F3F5F7")
DARK_GRAY = colors.HexColor("#3E4C59")
RED = colors.HexColor("#B42318")
GOLD = colors.HexColor("#B7791F")


def footer(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(colors.HexColor("#D9E2EC"))
    canvas.line(18 * mm, 14 * mm, width - 18 * mm, 14 * mm)
    canvas.setFont("YaHei", 7.5)
    canvas.setFillColor(colors.HexColor("#52606D"))
    canvas.drawString(18 * mm, 9 * mm, "教学模拟文件｜明川理财有限责任公司（虚构）")
    canvas.drawRightString(width - 18 * mm, 9 * mm, f"第 {doc.page} 页 / 共 4 页")
    canvas.restoreState()


doc = BaseDocTemplate(
    str(OUTPUT),
    pagesize=A4,
    rightMargin=18 * mm,
    leftMargin=18 * mm,
    topMargin=16 * mm,
    bottomMargin=19 * mm,
    title="明享稳健180天固定期限净值型理财产品说明书（教学模拟）",
    author="金融产品公平说明书Agent课程项目组",
    subject="教学模拟金融产品说明书",
)
frame = Frame(
    doc.leftMargin,
    doc.bottomMargin,
    doc.width,
    doc.height,
    id="normal",
)
doc.addPageTemplates(PageTemplate(id="main", frames=frame, onPage=footer))

styles = getSampleStyleSheet()
title = ParagraphStyle(
    "TitleCN",
    parent=styles["Title"],
    fontName="YaHeiBold",
    fontSize=21,
    leading=30,
    textColor=NAVY,
    alignment=TA_CENTER,
    spaceAfter=7 * mm,
)
subtitle = ParagraphStyle(
    "SubtitleCN",
    parent=styles["Normal"],
    fontName="YaHei",
    fontSize=10,
    leading=16,
    textColor=DARK_GRAY,
    alignment=TA_CENTER,
    spaceAfter=3 * mm,
)
h1 = ParagraphStyle(
    "H1CN",
    parent=styles["Heading1"],
    fontName="YaHeiBold",
    fontSize=15,
    leading=22,
    textColor=NAVY,
    spaceBefore=3 * mm,
    spaceAfter=3 * mm,
)
h2 = ParagraphStyle(
    "H2CN",
    parent=styles["Heading2"],
    fontName="YaHeiBold",
    fontSize=11.5,
    leading=18,
    textColor=BLUE,
    spaceBefore=2 * mm,
    spaceAfter=2 * mm,
)
h3 = ParagraphStyle(
    "H3CN",
    parent=styles["Heading3"],
    fontName="YaHeiBold",
    fontSize=9.5,
    leading=15,
    textColor=NAVY,
    spaceBefore=1.5 * mm,
    spaceAfter=1 * mm,
)
body = ParagraphStyle(
    "BodyCN",
    parent=styles["BodyText"],
    fontName="YaHei",
    fontSize=8.6,
    leading=14.2,
    textColor=colors.HexColor("#243B53"),
    alignment=TA_LEFT,
    spaceAfter=2.2 * mm,
)
small = ParagraphStyle(
    "SmallCN",
    parent=body,
    fontSize=7.5,
    leading=12,
    textColor=DARK_GRAY,
)
callout = ParagraphStyle(
    "CalloutCN",
    parent=body,
    fontName="YaHeiBold",
    fontSize=9,
    leading=15,
    textColor=RED,
    borderColor=colors.HexColor("#FDA29B"),
    borderWidth=0.8,
    borderPadding=7,
    backColor=colors.HexColor("#FFF1F0"),
    spaceBefore=2 * mm,
    spaceAfter=3 * mm,
)
note = ParagraphStyle(
    "NoteCN",
    parent=body,
    fontSize=8,
    leading=13,
    textColor=GOLD,
    borderColor=colors.HexColor("#F6D68A"),
    borderWidth=0.7,
    borderPadding=6,
    backColor=colors.HexColor("#FFF8E6"),
    spaceBefore=2 * mm,
    spaceAfter=3 * mm,
)


def P(text, style=body):
    return Paragraph(text, style)


def section(title_text, items):
    return KeepTogether([P(title_text, h2), *items])


def info_table(rows, widths=(43 * mm, 118 * mm)):
    data = [[P(str(a), small), P(str(b), small)] for a, b in rows]
    table = Table(data, colWidths=list(widths), repeatRows=0, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "YaHei"),
                ("BACKGROUND", (0, 0), (0, -1), LIGHT_BLUE),
                ("TEXTCOLOR", (0, 0), (0, -1), NAVY),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#BCCCDC")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


story = []

# Page 1
story += [
    Spacer(1, 10 * mm),
    P("教学模拟｜非真实金融产品", subtitle),
    P("明享稳健180天固定期限<br/>净值型理财产品说明书", title),
    P("模拟发行机构：明川理财有限责任公司", subtitle),
    P("产品代码：MXSJ-180-01　｜　文件版本：V1.0　｜　日期：2026年7月25日", subtitle),
    Spacer(1, 4 * mm),
    P(
        "重要提示：本产品为非保本浮动收益型净值型理财产品，不保证本金和收益。"
        "投资者的本金可能因市场变动、资产信用状况变化、流动性不足以及其他风险因素发生损失。",
        callout,
    ),
    P(
        "业绩比较基准仅用于投资管理和业绩评价，不代表未来表现，不是预期收益率，"
        "也不构成对产品收益的承诺或保证。",
        note,
    ),
    P("第一部分　产品基本信息", h1),
    P("一、重要提示", h2),
    P(
        "投资者应当认真阅读本说明书、风险揭示书及相关销售文件，根据自身投资目的、投资经验、"
        "财务状况、风险承受能力和流动性需求，独立、审慎作出决定。"
    ),
    P("二、产品要素", h2),
    info_table(
        [
            ("产品名称", "明享稳健180天固定期限净值型理财产品"),
            ("产品代码", "MXSJ-180-01"),
            ("产品类型", "固定期限、非保本浮动收益型、净值型"),
            ("产品风险等级", "R3（中风险，教学模拟分级）"),
            ("适合投资者", "经销售机构评估为风险承受能力不低于稳健型的投资者"),
            ("产品期限", "180天"),
            ("币种", "人民币"),
            ("认购起点", "1元人民币，以1元的整数倍递增"),
            ("募集期", "2026年8月1日至2026年8月3日"),
            ("产品成立日", "2026年8月4日"),
            ("产品到期日", "2027年1月31日，如遇非工作日顺延"),
            ("业绩比较基准", "3.20%（年化）"),
            ("收益分配", "产品到期后根据实际净值和持有份额计算"),
        ]
    ),
    PageBreak(),
]

# Page 2
story += [
    P("第二部分　认购、期限、赎回与费用", h1),
    P("三、认购与确认", h2),
    P(
        "投资者在募集期内提交认购申请。管理人有权根据募集情况提前结束或延长募集期，"
        "但应当按照约定渠道进行信息披露。"
    ),
    P(
        "认购份额按照产品成立日单位净值1.0000元计算。募集期内认购资金按照销售机构规则处理，"
        "募集期利息是否计入投资份额以销售机构公告为准。"
    ),
    P("四、产品期限与退出", h2),
    P(
        "本产品期限为180天。产品存续期内原则上不开放投资者主动申购或赎回，"
        "投资者不能因临时资金需要而提前取回投资本金。",
        callout,
    ),
    P(
        "发生法律法规、监管要求、市场异常、底层资产无法及时变现或本说明书约定的其他特殊情形时，"
        "管理人可以根据产品实际情况暂停估值、延迟兑付或提前终止产品，并按照约定进行信息披露。"
    ),
    P(
        "产品到期后，管理人将在完成资产变现和费用扣除后，将投资者应得资金划转至销售机构。"
        "实际到账时间可能受到非工作日、资产变现和支付系统处理等因素影响。"
    ),
    P("五、产品费用", h2),
    P("本产品可能收取以下费用，费用从产品财产中计提："),
    info_table(
        [
            ("固定管理费", "0.30%/年｜按前一日产品净资产每日计提"),
            ("托管费", "0.03%/年｜按前一日产品净资产每日计提"),
            ("销售服务费", "0.10%/年｜按前一日产品净资产每日计提"),
        ]
    ),
    Spacer(1, 3 * mm),
    P(
        "上述费用将影响投资者最终获得的实际收益。产品运作中依法产生的交易费用、税费等，"
        "按照实际发生额从产品财产中支付。",
        note,
    ),
    P("六、收益计算说明", h2),
    P("产品实际收益取决于产品净值变化，计算示意为："),
    P("<b>投资者到期金额 = 到期确认份额 × 到期单位净值</b>", note),
    P(
        "上述公式仅用于说明计算逻辑，不代表投资者一定能够获得正收益。业绩比较基准3.20%（年化）"
        "不是到期收益率，实际收益可能高于、低于该基准，也可能为负。"
    ),
    PageBreak(),
]

# Page 3
story += [
    P("第三部分　投资范围、估值与风险", h1),
    P("七、投资范围", h2),
    P(
        "本产品募集资金主要投资于现金、银行存款、同业存单、货币市场工具、债券、资产支持证券"
        "以及符合监管要求的其他固定收益类资产。"
    ),
    P(
        "产品可根据市场情况在约定范围内调整资产配置。底层资产的市场价格、信用状况和流动性变化"
        "会影响产品净值。"
    ),
    P("八、估值", h2),
    P(
        "产品采用净值化管理。管理人根据适用的会计准则和估值规则计算产品单位净值。"
        "因市场价格缺失、交易不活跃或其他特殊情况，估值结果可能与资产实际变现价值存在差异。"
    ),
    P("九、主要风险", h2),
    P("1. 本金及收益风险", h3),
    P("本产品不保证本金和收益。产品净值下跌时，投资者可能损失部分或全部本金。"),
    P("2. 市场风险", h3),
    P("利率、债券价格、信用利差以及宏观经济环境变化可能导致资产价格波动，从而影响产品净值。"),
    P("3. 信用风险", h3),
    P("融资主体、债券发行人或交易对手未能按约定履行义务时，产品可能遭受损失。"),
    P("4. 流动性风险", h3),
    P(
        "当市场成交不足、底层资产难以及时变现或发生集中兑付需求时，产品可能面临资产无法及时处置、"
        "延迟兑付或提前终止等情况。"
    ),
    P("5. 估值风险", h3),
    P("在缺乏活跃市场报价时，估值模型、参数和假设可能影响产品净值。"),
    P("6. 信息传递风险", h3),
    P("投资者未及时查询相关公告，可能无法及时了解产品净值、重大事项或到期安排。"),
    P("7. 政策与不可抗力风险", h3),
    P("法律法规、监管政策、税收政策变化或不可抗力事件可能影响产品正常运作。"),
    P("十、最不利情形", h2),
    P(
        "在市场大幅波动、底层资产违约或资产无法及时变现等极端情况下，产品净值可能明显下降，"
        "投资者可能损失部分或全部本金，资金到账时间也可能晚于原计划日期。",
        callout,
    ),
    P(
        "本说明书未对最大损失金额作出限定，投资者不应根据业绩比较基准推断本金安全或最低收益。"
    ),
    PageBreak(),
]

# Page 4
story += [
    P("第四部分　信息披露、适当性与其他事项", h1),
    P("十一、信息披露", h2),
    P(
        "管理人通过官方网站、销售机构或双方约定的其他渠道披露产品净值、定期报告、重大事项和到期公告。"
        "投资者应当主动查询相关信息。"
    ),
    P("十二、投资者适当性", h2),
    P(
        "本产品教学模拟风险等级为R3。产品风险等级不等于对本金安全或收益结果的保证。"
        "销售机构应当按照适用要求了解投资者情况并开展风险承受能力评估。"
    ),
    P(
        "本说明书中的适合投资者描述仅为产品属性说明，不能替代销售机构正式适当性评估，"
        "也不能作为某一投资者适合购买本产品的结论。",
        note,
    ),
    P("十三、投诉与咨询", h2),
    P("教学模拟客服电话：400-000-0000。该号码仅为版式示例，不提供真实服务。"),
    P("十四、特别声明", h2),
    P(
        "本文件由课程项目团队制作，仅用于测试金融产品信息提取、通俗解释、材料一致性检查和原文引用功能。"
        "文件中的机构、产品、日期、费率和条款均为教学模拟，不对应真实金融产品。",
        callout,
    ),
    Spacer(1, 14 * mm),
    P("用户核对清单", h2),
    info_table(
        [
            ("本金", "是否明确理解产品不保证本金和收益？"),
            ("收益", "是否明确3.20%是业绩比较基准而不是承诺收益？"),
            ("流动性", "是否能够接受180天内原则上不能提前赎回？"),
            ("费用", "是否了解管理费、托管费、销售服务费和其他可能费用？"),
            ("风险", "是否阅读并理解市场、信用、流动性和估值等风险？"),
            ("信息", "是否知道在哪里查询产品净值和重大事项公告？"),
        ]
    ),
    Spacer(1, 8 * mm),
    P("不替你做决定，只把重要的事讲明白。", title),
]

doc.build(story)
print(OUTPUT)

