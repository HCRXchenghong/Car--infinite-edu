"""Read-only checks of generated content; emits a separate QA report."""
from pathlib import Path
import csv
import hashlib
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parent
def read_csv(name):
    with (ROOT/'数据'/name).open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def normalize(s): return re.sub(r'\s+','',unicodedata.normalize('NFKC',s))
pdf=ROOT/'打印版/四轮四转底盘_硬件实施与检验手册_HW-R1.pdf'
reader=PdfReader(str(pdf)); texts=[p.extract_text() or '' for p in reader.pages]
full=normalize('\n'.join(texts))
checks=[]
for board,count in [('VCU',128),('BCM',100)]:
    rows=read_csv(board+'_MCU全引脚.csv')
    assert len(rows)==count
    assert {int(r['实体脚']) for r in rows}==set(range(1,count+1))
    for row in rows:
        assert normalize(row['网络名']) in full,(board,row['网络名'],'missing in PDF')
        assert normalize(row['引脚名']) in full,(board,row['引脚名'],'missing in PDF')
    checks.append(f'{board}: 全部 {count} 脚、引脚名及分配网络均进入 PDF。')
conn=read_csv('BCM_35P逻辑分配_非厂家腔号.csv')
assert len(conn)==35 and len({r['逻辑槽位'] for r in conn})==35
assert all(r['厂家腔号'].startswith('H') for r in conn)
for r in conn: assert normalize(r['网络']) in full,r
sources=read_csv('资料来源与SHA256.csv')
for src in sources:
    assert hashlib.sha256((ROOT/'资料'/src['文件']).read_bytes()).hexdigest()==src['SHA256'],src['文件']
checks.append(f'35P 逻辑分配完整，厂家腔号未伪装成已确认；{len(sources)} 份存档资料 SHA256 匹配。')
ledger=read_csv('已核验芯片_全焊盘连接.csv')
assert len(ledger)==310
assert len({(r['板'],r['器件'],r['焊盘']) for r in ledger})==310
assert len({(r['板'],r['器件']) for r in ledger})==15
assert all(not r['人工勾选'] for r in ledger)
parts=read_csv('已核验芯片_实例表.csv')
for r in parts:
    assert normalize(r['型号']) in full,r['型号']
    assert normalize(r['封装']) in full,r['封装']
peripherals=read_csv('参考单元_外围逐端连接.csv')
assert len(peripherals)==142
assert len({(r['板'],r['位号']) for r in peripherals})==len(peripherals)
hb=[r for r in parts if r['板']=='BCM' and r['位号']=='U401'][0]
assert 'PQFN32' in hb['封装'] and 'MC33926PNBR2'==hb['型号']
for r in ledger:
    if r['脚名']=='PGOOD': assert '不接' in r['连接去向/处理']
checks.append('15 颗核心芯片 310 条焊盘记录完整唯一；142 条参考外围位号唯一；PQFN 与 PGOOD 修正已进入导出。')
for filename,expected in [('STM32G474Q_B-C-E_Tx.xml','d9c52b4725451407ec54c877732ffd71bde67cee'),('STM32G491V_C-E_Tx.xml','a04f9a00c77e25860360e857e4470f1ec9209114')]:
    content=(ROOT/'资料'/filename).read_bytes()
    blob=hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest()
    assert blob==expected,(filename,blob)
checks.append('两份 MCU XML 的 Git blob SHA1 与官方 API 固定版本匹配。')
for term in ['MSSD-100EMA_2EC_N','暂不支持 CANopen','SM60E','92mA','双白','DM-J10010L-2EC','默认 1Mbps','ERR<<4 会发生位重叠']:
    assert normalize(term) in full,('new supplier evidence missing in PDF',term)
checks.append('MSSD 自定义经典 CAN、SM60E 反馈边界及 DM-J10010L-2EC 经典 CAN/协议矛盾已进入 PDF。')
workbook=PdfReader(str(ROOT/'打印版/逐焊盘与外围连接_完整作业册_HW-R1.pdf'))
work_text=normalize('\n'.join(p.extract_text() or '' for p in workbook.pages))
for r in ledger:
    assert normalize(r['网络']) in work_text,(r['板'],r['器件'],r['网络'])
for r in peripherals:
    for field in ['位号','端1网络','端2网络']:
        assert normalize(r[field]) in work_text,(r['板'],r['位号'],field)
checks.append(f'横向完整作业册 {len(workbook.pages)} 页；310 条焊盘的网络、142 条外围位号及两端网络全部进入打印内容。')
tests=read_csv('检验记录.csv')
assert len(tests)==26
assert all(not r['结论'] and not r['实测值'] for r in tests)
checks.append('26 项测试记录未填实测值/结论，没有虚构合格记录。')
bad_links=[]
for p in REPO.rglob('*.md'):
    if any(x in p.parts for x in ['.git','.codex','.agents']): continue
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        target=target.strip('<>').split('#')[0]
        if not target or re.match(r'^[a-zA-Z]+:',target): continue
        if not (p.parent/target).exists(): bad_links.append([str(p.relative_to(REPO)),target])
assert not bad_links,bad_links
checks.append('仓库 Markdown 中本地文件链接全部可解析。')
docx=ROOT/'打印版/四轮四转底盘_硬件实施与检验手册_HW-R1.docx'
with zipfile.ZipFile(docx) as z:
    assert z.testzip() is None
    for name in ['word/document.xml','word/styles.xml','word/header1.xml','word/footer1.xml']:
        ET.fromstring(z.read(name))
checks.append('DOCX ZIP 完整、正文/样式/页眉/页脚 XML 可解析；未宣称 Word 排版已实机验证。')
assert all('不得直接投板' in t for t in texts)
checks.append(f'PDF {len(reader.pages)} 页全部有设计输入/禁止投板状态提示。')
review=(ROOT/'打印版/版面抽检记录.md').read_text(encoding='utf-8')
for artifact in [pdf,ROOT/'打印版/逐焊盘与外围连接_完整作业册_HW-R1.pdf',docx]:
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() in review,(artifact.name,'review hash is stale')
checks.append('版面抽检记录存在，其 3 个文件摘要与当前 PDF/DOCX 一致；不代替人工重检。')
report={'status':'PASSED_DOCUMENT_CHECKS_ONLY','checks':checks,'visual_review':'另见版面抽检记录.md；不等于硬件验证','hardware_tests_executed':0,'unresolved_inputs':'H01～H16，见 09_待确认输入与资料.md'}
(ROOT/'打印版/内容校验.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
for index,txt in enumerate(texts,1):
    lines=[x for x in txt.splitlines() if x.strip()]
    print(f'PAGE {index:02d}: '+' / '.join(lines[4:7])[:150])
