"""Landscape A4 shop-floor drafting ledger: all rows, no condensed templates."""
from pathlib import Path
import argparse
import csv
import hashlib
import html
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, LongTable, TableStyle
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'打印版'
args=argparse.ArgumentParser()
args.add_argument('--font',default='/System/Library/Fonts/Supplemental/Arial Unicode.ttf')
options=args.parse_args()
pdfmetrics.registerFont(TTFont('CN',options.font))
W,H=landscape(A4); M=14*mm; width=W-2*M
teal=colors.HexColor('#186C73'); navy=colors.HexColor('#143342')
cell=ParagraphStyle('cell',fontName='CN',fontSize=8,leading=11,wordWrap='CJK',textColor=navy)
head=ParagraphStyle('head',parent=cell,textColor=colors.white)
body=ParagraphStyle('body',parent=cell,fontSize=10,leading=17,spaceAfter=7)
title=ParagraphStyle('title',parent=body,fontSize=19,leading=27,textColor=teal,spaceAfter=12)
story=[]; sections=[]
def p(s,style=cell): return Paragraph(html.escape(str(s)).replace('\n','<br/>'),style)
def read(name):
    with (ROOT/'数据'/name).open(encoding='utf-8-sig',newline='') as f: return list(csv.reader(f))
def page(canvas,doc):
    canvas.saveState(); canvas.setFont('CN',7)
    canvas.setFillColor(navy)
    canvas.drawString(M,H-9*mm,'四轮四转底盘 · 完整逐焊盘/逐端连接作业册 | HW-R1')
    canvas.drawRightString(W-M,H-9*mm,'2026-09-19')
    canvas.drawString(M,8*mm,'设计输入版；非真实 CAD 网表；所有 H 待确认项关闭前不得投板。空白勾选不代表已检验。')
    canvas.drawRightString(W-M,8*mm,str(doc.page)); canvas.restoreState()
def section(label,note,headers,rows,weights):
    if story: story.append(PageBreak())
    story.extend([p(label,title),p(note,body)])
    assert len(headers)==len(weights)
    table=LongTable([[p(x,head) for x in headers]]+[[p(x) for x in row] for row in rows],colWidths=[width*w for w in weights],repeatRows=1,hAlign='LEFT')
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),teal),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F0F5F6')]),('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#C9D8DD')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4)]))
    story.extend([table,Spacer(1,10),p('CAD/线束版本：________  绘图/装配人：________  独立复核：________  日期：________',body)])
    sections.append({'title':label,'rows':len(rows)})

story.extend([Spacer(1,12*mm),p('完整逐焊盘 / 逐端连接作业册',title),p('HW-R1 | VCU + BCM | 横向 A4 打印',body),
 p('配合主手册使用。本册完整展开数据 CSV，不压缩重复芯片实例：228 个 MCU 脚、310 个其它核心芯片焊盘/EP、142 条参考外围连接、24 条关键对端关系、35P 逻辑接口、DM-J10010L-2EC 四轴配置/标定表与检验记录。',body),
 p('字段“实体脚/焊盘”仅针对已确认芯片封装；BCM B01～B35 是逻辑槽位，不是连接器厂家腔号。EP 必须与受控 footprint 的实际焊盘号映射。',body),
 p('这里仍不包含未选定模块、安全/保护器件的全部连接。H 项保持未确认，不能据此宣称全板 CAD 已完成、物料可直接下单或硬件保证无误。',body),
 p('使用方法：按板/位号定位 → 核实物脚号 → 在 CAD 逐网追到对端 → 检查电平/默认态/时序 → 绘图人勾选 → 独立复核签字。主手册 09 章列出 H01～H16 的关闭条件。',body),
 p('不要在一张表上混合 VCU 与 BCM 的 U401：VCU U401 是 MAX14830；BCM U401 是 MC33926PNBR2。',body),
 p('项目：________    原理图版本：________    线束版本：________\n领取人：________    复核人：________    日期：________',body)])
for board in ['VCU','BCM']:
    data=read(board+'_MCU全引脚.csv')
    section(board+' MCU 全部实体脚', '逐脚分配以官方 XML 检查功能存在；电气/AF 数字/时钟及 G474 43/44 脚仍按 H 关闭。',data[0]+['勾选'],[r+['____'] for r in data[1:]],[.045,.13,.22,.16,.20,.195,.05])
ledger=read('已核验芯片_全焊盘连接.csv')
for board in ['VCU','BCM']:
    subset=[r for r in ledger[1:] if r[0]==board]
    section(board+' 核心芯片逐焊盘连接（完整实例）','芯片功能据存档资料核验；连接方案仍需 CAD/电气复核。每一电源、地、多输出脚单独检查。',ledger[0][1:],[r[1:-1]+['____'] for r in subset],[.06,.04,.075,.225,.33,.22,.05])
outer=read('参考单元_外围逐端连接.csv')
for board in ['VCU','BCM']:
    subset=[r for r in outer[1:] if r[0]==board]
    section(board+' 参考外围器件两端连接','只覆盖已定义参考单元，不是全板生产 BOM；电阻/陶瓷电容无极性，电解需核正负极。',outer[0][1:],[r[1:-1]+['____'] for r in subset],[.08,.265,.18,.18,.245,.05])
point=read('MCU到关键芯片_点对点复核.csv')
section('MCU 到关键芯片的对端检查','串阻两侧不能用同名标签短接；请求信号与经过硬件许可门控的 HW 输出不是同一网。',point[0],point[1:],[.05,.17,.25,.25,.23,.05])
dmframes=read('DM_J10010L_CAN帧与字节序.csv')
section('DM-J10010L-2EC CAN 帧与字节序','厂家 V1.1 手册的可实现输入；D0 位宽、使能/失能、TIMEOUT 等冲突/缺项未关闭，不得当作已联调协议。',dmframes[0],dmframes[1:],[.14,.13,.07,.34,.32])
dmids=read('DM_J10010L_四轴身份配置记录.csv')
section('DM-J10010L-2EC 四轴身份配置','一次只连接一台未配置电机；写入、存储、重启、读回后才接公共 CAN2。ESC_ID 和 MST_ID 都必须唯一。',dmids[0],dmids[1:],[.10,.10,.07,.07,.10,.09,.10,.15,.22])
dmlimits=read('DM_J10010L_四轴限制与标定记录.csv')
section('DM-J10010L-2EC 四轴限制与标定','PMAX/VMAX/TMAX、TIMEOUT 单位、零位、方向、机械/软件限位和终端位置必须逐台实测签认。',dmlimits[0],dmlimits[1:],[.09,.07,.07,.07,.15,.09,.07,.16,.09,.14])
conn=read('BCM_35P逻辑分配_非厂家腔号.csv')
section('BCM 35P 逻辑接口——非厂家腔号','必须取得厂图并按插合面/出线面核验后另出物理腔号图；当前不得直接压接生产线束。',conn[0]+['勾选'],[r+['____'] for r in conn[1:]],[.06,.14,.23,.10,.20,.22,.05])
tests=read('检验记录.csv')
section('26 项试验记录（填写实测，不自动合格）','程序及限值来源见主手册 08 章；本册仅记录摘要，波形/温升/数据需独立附件。',tests[0],[r[:2]+['________________']*6 for r in tests[1:]],[.05,.19,.17,.12,.15,.12,.075,.125])

path=OUT/'逐焊盘与外围连接_完整作业册_HW-R1.pdf'
doc=SimpleDocTemplate(str(path),pagesize=landscape(A4),leftMargin=M,rightMargin=M,topMargin=16*mm,bottomMargin=16*mm,title='完整逐焊盘与外围连接作业册 HW-R1',author='项目硬件设计资料')
doc.build(story,onFirstPage=page,onLaterPages=page)
r=PdfReader(str(path)); text='\n'.join(p.extract_text() or '' for p in r.pages)
for term in ['HOLD_VERIFY_REF','MC33926','R4101','ACT_CCP','T26','B35','MAX_RST_C']:
    assert term in text,term
report={'status':'WORKBOOK_EXPORTED_NOT_HARDWARE_VALIDATION','pages':len(r.pages),'sections':sections,'file':path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
(OUT/'作业册导出检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
