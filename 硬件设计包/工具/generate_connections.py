"""Known-core-device pad ledger and point-to-point drafting checklist.

This expands only archived/verified pin definitions. Unknown vendor modules and
protection/safety ICs remain H; this is not a fabricated complete CAD netlist.
"""
from pathlib import Path
import csv
import json
import hashlib

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'数据'
rows=[]; passive=[]; groups=[]; interfaces=[]
def write(name,headers,body):
    with (DATA/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f); w.writerow(headers); w.writerows(body)
def pin(board,ref,pad,name,net,dest,state):
    rows.append([board,ref,str(pad),name,net,dest,state,''])
def component(board,ref,value,p1,p2,note):
    passive.append([board,ref,value,p1,p2,note,''])
def mcu(board,net):
    with (DATA/(board+'_MCU全引脚.csv')).open(encoding='utf-8-sig',newline='') as f:
        found=[r for r in csv.DictReader(f) if r['网络名']==net]
    assert len(found)==1,(board,net,len(found))
    row=found[0]
    return f'U101.{row["实体脚"]} ({row["引脚名"]})'

for board in ['VCU','BCM']:
    for ref,vin,vout,bottom in [('U201','12V_PROT','5V_LOGIC','2.49k'),('U202','5V_LOGIC','3V3_LOGIC','4.32k'),('U203','12V_PROT','5V_SENSOR_RAW' if board=='VCU' else '4V0_MODEM','2.49k' if board=='VCU' else '3.32k')]:
        n=ref[1:]; fb='FB_'+ref
        groups.append([board,ref,'TPSM53603RDAR','B3QFN RDA-15',vin+' → '+vout,'S03'])
        for pad in range(1,16):
            if pad in [1,14]: name,net,dest,state='VIN',vin,'输入陶瓷电容正端；保护后电源','连线 V；输入/瞬态 H'
            elif pad==2: name,net,dest,state='EN',vin,'直接接本单元 VIN','不得悬空；UVLO 另核'
            elif pad in [3,10,11]: name,net,dest,state='NC','GND','按资料建议接 PGND','不是 DNC'
            elif pad in [4,5]: name,net,dest,state='DNC','DNC_'+ref+'_'+str(pad),'独立焊盘；无铜线/无过孔/不互连','禁止接地'
            elif pad==6: name,net,dest,state='PGOOD','TP_PG_'+ref,'仅高阻测试点；不接 MCU/上拉','默认不用；时序限制 VIN+0.3V'
            elif pad in [7,8]: name,net,dest,state='VOUT',vout,'输出电容正端及负载','两脚均接'
            elif pad==9: name,net,dest,state='FB',fb,'R'+n+'1.2 与 R'+n+'2.1','安静采样点'
            elif pad==12: name,net,dest,state='AGND','GND','反馈下阻与本地 PGND 汇合','同网，局部单点布局'
            elif pad==13: name,net,dest,state='V5V','NC_'+ref+'_V5V','不连接负载','内部 LDO，不当系统 5V'
            else: name,net,dest,state='PGND','GND','功率底焊盘/输入输出电容负端','必须焊接与散热'
            pin(board,ref,pad,name,net,dest,state)
        component(board,'R'+n+'1','10.0k / 0.1%',vout,fb,'反馈上阻')
        component(board,'R'+n+'2',bottom+' / 0.1%',fb,'GND','反馈下阻，靠 AGND')
        for idx in [1,2]: component(board,'C'+n+str(idx),'GRM32ER71H106KA12L / 10µF 50V',vin,'GND','资料推荐；偏压/容量复核')
        component(board,'C'+n+'3','100nF / 50V',vin,'GND','近 VIN；MPN/封装 H')
        component(board,'C'+n+'4','47µF / 50V 非陶瓷',vin,'GND','储能预留；ESR/MPN H')
        for idx in [5,6]: component(board,'C'+n+str(idx),'GRM32ER71A476KE15L / 47µF 10V',vout,'GND','有效电容必须达表 7-1')
        component(board,'C'+n+'7','100nF / 10V',vout,'GND','近输出；MPN/封装 H')
    for bus in range(1,4 if board=='VCU' else 3):
        ref=f'U{300+bus}'; n=ref[1:]; tx=f'CAN{bus}_TX'; txphy=tx+'D_PHY'; rx=f'CAN{bus}_RX'; stb=f'CAN{bus}_STB'
        groups.append([board,ref,'TCAN1044AVDRQ1','SOIC-8 D',f'CAN{bus}','S04'])
        defs=[('TXD',txphy,'经 R'+n+'1 到 '+mcu(board,tx)),('GND','GND','逻辑地'),('VCC','5V_LOGIC','100nF + 1µF 去耦'),('RXD',rx,mcu(board,rx)),('VIO','3V3_LOGIC','100nF 去耦'),('CANL',f'CAN{bus}_L_PHY','经所选接口保护/CMC 到 L'),('CANH',f'CAN{bus}_H_PHY','经所选接口保护/CMC 到 H'),('STB',stb,mcu(board,stb))]
        for pad,(name,net,dest) in enumerate(defs,1): pin(board,ref,pad,name,net,dest,'S04 脚位 V；保护/布线待验证')
        component(board,'R'+n+'1','33Ω',tx,txphy,'源端串阻起始值')
        component(board,'R'+n+'2','10k',txphy,'3V3_LOGIC','TXD 上拉，空闲隐性')
        component(board,'R'+n+'3','10k',stb,'3V3_LOGIC','STB 上拉，默认待机')
        component(board,'C'+n+'1','100nF / 10V','5V_LOGIC','GND','VCC 近端')
        component(board,'C'+n+'2','1µF / 10V','5V_LOGIC','GND','VCC 储能')
        component(board,'C'+n+'3','100nF / 10V','3V3_LOGIC','GND','VIO 近端')
        component(board,'R'+n+'4','120Ω / 1% / 0.5W，默认 DNP',f'CAN{bus}_H_BUS',f'CAN{bus}_L_BUS','全总线只装两端')
        interfaces.append([board,f'CAN{bus} TX',mcu(board,tx),'R'+n+'1 → '+ref+'.1',tx+' / '+txphy,'____'])
        interfaces.append([board,f'CAN{bus} RX',ref+'.4',mcu(board,rx),rx,'____'])
    if board=='BCM':
        component(board,'R3015','0Ω','CAN1_RX','CAN1_WAKE_RXD','只扇出到输入 PC12；不接推挽输出')
        component(board,'R3016','10k','CAN1_WAKE_RXD','3V3_LOGIC','掉电 RXD 高阻时偏置')
        interfaces.append(['BCM','CAN1 独立唤醒','U301.4 / CAN1_RX','R3015 → '+mcu('BCM','CAN1_WAKE_RXD'),'EXTI12；不抢急停 EXTI0','____'])

max_defs={1:('SPI/I2C','3V3_LOGIC','选择 SPI'),2:('LDOEN','3V3_LOGIC','启用内部 1.8V LDO'),3:('MISO','MAX_MISO','共用 SPI1'),4:('SCLK','MAX_SCK_PHY','经 R4101 接 MCU MAX_SCK'),6:('MOSI','MAX_MOSI_PHY','经 R4102 接 MCU MAX_MOSI'),9:('VL','3V3_LOGIC','100nF 到 DGND'),10:('DGND','GND','地'),43:('VEXT','3V3_LOGIC','100nF 到 DGND'),46:('AGND','GND','必须独立接地，不只靠 EP'),47:('VA','3V3_LOGIC','100nF 到 AGND')}
component('VCU','R4101','33Ω，允许 SI 验证后调整','MAX_SCK','MAX_SCK_PHY','靠 MCU 源端；三颗下游共享')
component('VCU','R4102','33Ω，允许 SI 验证后调整','MAX_MOSI','MAX_MOSI_PHY','靠 MCU 源端；三颗下游共享')
for net,pad,via in [('MAX_SCK',4,'R4101'),('MAX_MOSI',6,'R4102'),('MAX_MISO',3,'直连')]:
    interfaces.append(['VCU',net,mcu('VCU',net),f'{via} → U401/U402/U403.{pad}',net+'；三片共用','____'])
for group,label in enumerate('ABC'):
    ref=f'U{401+group}'; n=ref[1:]
    groups.append(['VCU',ref,'MAX14830ETM+','TQFN48+EP / T4877+3','四个 UART / '+label,'S01'])
    for pad in list(range(1,49))+['EP']:
        if pad in max_defs:
            name,net,dest=max_defs[pad]
            if net=='MAX_MISO': dest=mcu('VCU',net)+'，SPI1 共享'
        elif pad in [5,7,8]:
            name={5:'CS',7:'IRQ',8:'RST'}[pad]; net='MAX_'+name+'_'+label; dest=mcu('VCU',net)
        elif pad==44: name,net,dest='XOUT',ref+'_XOUT','Y'+n+'.2，外部负载电容 DNP'
        elif pad==45: name,net,dest='XIN',ref+'_XIN','Y'+n+'.1，外部负载电容 DNP'
        elif pad==48: name,net,dest='V18',ref+'_V18','1µF 到地；不接 3V3/外部负载'
        elif pad=='EP': name,net,dest='EP','GND','接 AGND；焊盘编号按受控 footprint 核对'
        else:
            channel=(pad-11)//8; offset=(pad-11)%8
            if offset<4:
                name='GPIO'+str(channel*4+offset); net=f'NC_{ref}_{name}'; dest='未用，保留内部弱下拉，配置输入；不硬接地'
            else:
                name=['RTS','CTS','RX','TX'][offset-4]+str(channel)
                sensor_index=group*4+channel
                device=f'USONIC_{sensor_index+1}' if sensor_index<8 else f'TOF_{sensor_index-7}'
                if offset==4: net=f'NC_{ref}_{name}'; dest='输出未用，NC；不接电源/地'
                elif offset==5: net=f'{ref}_{name}'; dest='经独立 10k 到地；不启用流控'
                elif offset==6: net=device+'_TO_VCU_3V3'; dest=device+' 电平前端逻辑输出；外设侧 H'
                else: net='VCU_TO_'+device+'_3V3'; dest=device+' 电平前端逻辑输入；外设侧 H'
        pin('VCU',ref,pad,name,net,dest,'S01 脚位 V；外设前端 H')
    component('VCU','R'+n+'1','10k','MAX_CS_'+label,'3V3_LOGIC','片选上拉')
    component('VCU','R'+n+'2','10k','MAX_IRQ_'+label,'3V3_LOGIC','开漏上拉')
    component('VCU','R'+n+'3','10k','MAX_RST_'+label,'GND','默认复位')
    for channel in range(4): component('VCU','R'+n+str(channel+4),'10k',f'{ref}_CTS{channel}','GND','流控禁用基线')
    for idx,name in enumerate(['VL','VEXT','VA'],1): component('VCU','C'+n+str(idx),'100nF / 10V','3V3_LOGIC','GND','靠 '+ref+'.'+{'VL':'9','VEXT':'43','VA':'47'}[name])
    component('VCU','C'+n+'4','1µF / 6.3V',ref+'_V18','GND','近 48 脚，不装到 3V3')
    component('VCU','Y'+n,'1.8432MHz 晶体 / CL、ESR H',ref+'_XIN',ref+'_XOUT','内部各 16pF；实际晶体待核验')
    for sig in ['CS','IRQ','RST']:
        pad={'CS':5,'IRQ':7,'RST':8}[sig]; net='MAX_'+sig+'_'+label
        interfaces.append(['VCU',net,mcu('VCU',net),ref+'.'+str(pad),net,'____'])

groups.append(['BCM','U401','MC33926PNBR2','PQFN32+EP / 98ARL10579D','推杆 H 桥','S02'])
hb={1:('IN2','ACT_IN2_HW','经掉电安全缓冲/门控，来自 ACT_IN2_REQ'),2:('IN1','ACT_IN1_HW','经掉电安全缓冲/门控，来自 ACT_IN1_REQ'),3:('SLEW','GND','慢边沿'),7:('INV','GND','不反相'),8:('FB','ACT_FB_RAW','150Ω 取样及滤波；4.7k 后为 ACT_FB_ADC'),10:('EN','ACT_EN_HW','硬件许可与 EN 请求门控，2.2k 下拉'),16:('D2','ACT_D2_HW','硬件禁止低；2.2k 下拉'),21:('SF','ACT_SF','15k 上拉，接 '+mcu('BCM','ACT_SF')),26:('D1','ACT_D1_HW','默认高禁止；缓冲/反灌 H'),32:('CCP','ACT_CCP','33nF 到 12V_ACT，不接地')}
for pad in list(range(1,33))+['EP']:
    if pad in hb: name,net,dest=hb[pad]
    elif pad in [4,6,11,31]: name,net,dest='VPWR','12V_ACT','同接 F_ACT 之后；多脚全连'
    elif pad in [5,'EP']: name,net,dest='AGND','GND','低阻接 PGND；EP 须焊接'
    elif pad in [9,17,25]: name,net,dest='NC',f'NC_U401_{pad}','不连接'
    elif pad in [12,13,14,15]: name,net,dest='OUT1','ACT_OUT1','四脚全连 → BCM B19 逻辑位；物理腔号 H'
    elif pad in [18,19,20,22,23,24]: name,net,dest='PGND','GND','六脚全连，功率回流'
    elif pad in [27,28,29,30]: name,net,dest='OUT2','ACT_OUT2','四脚全连 → BCM B20 逻辑位；物理腔号 H'
    else: raise AssertionError(pad)
    pin('BCM','U401',pad,name,net,dest,'S02 脚位 V；外围/安全 H')
for ref,value,a,b,note in [
 ('R4011','150Ω / 1% / 0.25W','ACT_FB_RAW','GND','电流取样，不可遗漏'),
 ('R4012','15k','ACT_SF','3V3_LOGIC','SF 上拉，不能改 4.7k'),
 ('R4013','4.7k','ACT_FB_RAW','ACT_FB_ADC','ADC 串阻起始值；钳位电路仍 H'),
 ('R4014','2.2k','ACT_IN1_HW','GND','抵抗内部拉流'),('R4015','2.2k','ACT_IN2_HW','GND','抵抗内部拉流'),
 ('R4016','2.2k','ACT_EN_HW','GND','默认睡眠'),('R4017','2.2k','ACT_D2_HW','GND','默认禁止'),
 ('R4018','2.2k','ACT_D1_HW','3V3_LOGIC','高禁止；掉电反灌须核验'),
 ('C4011','33nF / 50V','ACT_CCP','12V_ACT','电荷泵，不接地'),('C4012','1nF / 10V','ACT_FB_RAW','GND','FB 滤波起始值'),
 ('C4013','100nF / 50V','12V_ACT','GND','近桥去耦'),('C4014','10µF / 50V','12V_ACT','GND','陶瓷去耦'),('C4015','470µF / 35V 低 ESR','12V_ACT','GND','再生/浪涌/纹波 H')]: component('BCM',ref,value,a,b,note)
interfaces.append(['BCM','ACT FB','U401.8 → R4011/R4013/限幅 H',mcu('BCM','ACT_FB_ADC'),'ACT_FB_ADC','____'])

for board,ref,part,package,role,source in groups:
    found=[r for r in rows if r[0]==board and r[1]==ref]
    expected=set(map(str,range(1,16))) if part.startswith('TPSM') else set(map(str,range(1,9))) if part.startswith('TCAN') else set(map(str,range(1,49)))|{'EP'} if part.startswith('MAX') else set(map(str,range(1,33)))|{'EP'}
    assert len(found)==len(expected)
    assert {r[2] for r in found}==expected,(board,ref)
assert len(rows)==310 and len(groups)==15
assert len({tuple(r[:3]) for r in rows})==len(rows)
assert len({tuple(r[:2]) for r in passive})==len(passive),'Duplicate peripheral designator'
write('已核验芯片_全焊盘连接.csv',['板','器件','焊盘','脚名','网络','连接去向/处理','状态','人工勾选'],rows)
write('参考单元_外围逐端连接.csv',['板','位号','值/候选','端1网络','端2网络','说明','人工勾选'],passive)
write('已核验芯片_实例表.csv',['板','位号','型号','封装','作用','来源'],groups)
write('MCU到关键芯片_点对点复核.csv',['板','信号','起点','终点','网络/条件','人工勾选'],interfaces)

md=['# 关键芯片逐焊盘与逐网勾选清单','','这份清单把已核验芯片展开到实际焊盘。CSV 包含 15 颗非 MCU 核心芯片共 310 条焊盘/EP 记录；加上 MCU 的 228 条为 538 条。未知模块、安全/保护器件和连接器腔号没有被虚构成完整 CAD 网表。各行人工勾选保持空白。','','同一板内位号唯一，两块板允许重复位号。EP 是暴露焊盘标识，CAD 的数字焊盘号必须与实际 footprint 映射，不擅自把 EP 写成 33/49。BCM/VCU 的 U401 是不同器件，不得跨板复制。','']
def tab(title,headers,body):
    md.extend(['## '+title,'','| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |'])
    for row in body: md.append('| '+' | '.join(str(x).replace('|','/') for x in row)+' |')
    md.append('')
tab('1. 实例与实体封装',['板','位号','型号','封装','作用','来源'],groups)
md.extend(['## 2. 全部芯片的逐脚展开方式','','下列模板只打印一次，完整实例已全部展开在数据 CSV，不能因模板合并省接任何芯片。每个电源/地/输出并联脚必须独立在 CAD 中连接。PGOOD 默认不使用；所有 DNC 分别隔离。',''])
for board,ref,title in [('VCU','U201','2.1 TPSM53603RDAR，每单元 15 焊盘'),('VCU','U301','2.2 TCAN1044AVDRQ1，每颗 8 脚'),('VCU','U401','2.3 MAX14830ETM+，每颗 48 脚与 EP'),('BCM','U401','2.4 MC33926PNBR2，32 脚与 EP')]:
    sample=[r for r in rows if r[0]==board and r[1]==ref]
    tab(title,['焊盘','脚名','网络（模板实例）','对端/处理','勾选'],[[r[2],r[3],r[4],r[5],'____'] for r in sample])
tab('3. MCU 到关键芯片的逐网复核',['板','信号','起点','终点','网络/条件','勾选'],interfaces)
md.extend(['## 4. 外围器件逐端连线','','`数据/参考单元_外围逐端连接.csv` 给出全部 '+str(len(passive))+' 条参考外围连接：位号、值、两端网络与条件。它覆盖上述 Buck/CAN/MAX/H 桥的已定义外围，但不包含 MCU 去耦、安全门控、外部保护和未知模块所需的全部物料，不能当最终贴片 BOM。电阻/电容端 1/2 只是无极性件的连接方向；电解的端 1 是正极、端 2 是负极，CAD 实体标号仍须检查。','','MAX MISO 是三片共享；SCLK/MOSI 经源端 R4101/R4102（33Ω 起始值）到独立的 MAX_SCK_PHY/MAX_MOSI_PHY 芯片侧子网，不能用同名网绕过串阻。三片 CS/IRQ/RST 分别独立，不能线与。CAN 可选共模电感/0Ω 替位只能二选一。','','## 5. 每一网的审核动作','','1. 从芯片实体脚出发，沿线检查到目标实体脚；中间存在电阻/缓冲/保护就逐段核对，不能只看同名标签。','2. 核对本地电源、电平、上电高阻、正常运行、外设断电和 MCU 下载四类状态。','3. 多脚电源/地/OUT 逐个勾，不以“已经接了一脚”代表全部。','4. 检查 H 项确实仍显式标记；未知针脚不能为了 ERC 清零而接地。','5. 画图人和独立复核人分开签字，并写 CAD 文件版本；自动校验不能代签。','','绘图人____；复核人____；CAD 版本____；已核行数____；未关闭 H 项____；日期____。',''])
(ROOT/'11_逐网连接勾选清单.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
result={'status':'KNOWN_CORE_PAD_LEDGER_CHECKED_NOT_CAD','core_devices':len(groups),'core_pads_including_ep':len(rows),'mcu_pads':228,'combined_record_count':538,'peripheral_reference_rows':len(passive),'point_to_point_rows':len(interfaces),'unverified':'保护/安全器件、模块、物理腔号及真实 CAD 仍未完成'}
(DATA/'逐焊盘校验.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
