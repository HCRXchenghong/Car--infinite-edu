"""Generate review tables from archived vendor pin data, not from guessed pad numbers.

Run with Python 3.11+. This is a documentation checker, NOT an electrical/CAD sign-off.
"""
from pathlib import Path
import csv
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / '数据'
DATA.mkdir(exist_ok=True)
APP = ['# 数据附录与空白记录', '', '自动生成，来源为本包工具与存档 ST 引脚数据库。网络分配是工程建议；H 项不得投板。GPIO 复用信号存在性已校验，AF 数字、电气能力及真实 CAD 尚未验证。', '']
checks = []

def write_csv(name, headers, rows):
    with (DATA / name).open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)

def table(title, headers, rows):
    APP.extend(['## ' + title, '', '| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |'])
    for row in rows:
        APP.append('| ' + ' | '.join(str(x).replace('|', '/') for x in row) + ' |')
    APP.append('')

def assignments(board):
    d = {}
    def put(pin, net, signal='GPIO', direction='输出', default='外部下拉，安全门控', note='', irq=None):
        assert pin not in d, (board, pin, 'duplicate assignment')
        d[pin] = dict(net=net, signal=signal, direction=direction, default=default, note=note, irq=irq)
    # Dedicated debug pins: never borrow for load control.
    put('PA13', 'SWDIO', 'SYS_JTMS-SWDIO', '双向', '保留调试', 'VTREF 仅采样')
    put('PA14', 'SWCLK', 'SYS_JTCK-SWCLK', '输入', '保留调试')
    put('PB3', 'SWO', 'SYS_JTDO-SWO', '输出', '可选测试点')
    for pin, net, sig, direction in [('PD0','CAN1_RX','FDCAN1_RX','输入'), ('PD1','CAN1_TX','FDCAN1_TX','输出'),
                                      ('PB12','CAN2_RX','FDCAN2_RX','输入'), ('PB13','CAN2_TX','FDCAN2_TX','输出')]:
        put(pin, net, sig, direction, 'TX 10k 上拉；RX 由收发器驱动')
    put('PC10', 'DEBUG_TX', 'UART4_TX', '输出', '仅壳内测试')
    put('PC11', 'DEBUG_RX', 'UART4_RX', '输入', '10k 上拉')
    if board == 'VCU':
        put('PA8', 'CAN3_RX', 'FDCAN3_RX', '输入', '收发器驱动')
        put('PA15', 'CAN3_TX', 'FDCAN3_TX', '输出', '10k 上拉', '禁用完整 JTAG，保留 SWD')
        for pin, sig, direction in [('PA5','SPI1_SCK','输出'),('PA6','SPI1_MISO','输入'),('PA7','SPI1_MOSI','输出')]:
            put(pin, 'MAX_' + sig.split('_')[1], sig, direction, '总线初始空闲；CS 高')
        for i, label in enumerate('ABC'):
            put('PE'+str(2+i), 'MAX_CS_'+label, default='10k 上拉')
            put('PE'+str(7+i), 'MAX_IRQ_'+label, direction='输入', default='10k 上拉', note='开漏低有效', irq=7+i)
            put(['PE5','PE6','PF2'][i], 'MAX_RST_'+label, default='10k 下拉，低复位')
        put('PD5','BMS_TX','USART2_TX','输出','经匹配物理层','BMS 电平/隔离 H')
        put('PD6','BMS_RX','USART2_RX','输入','经匹配物理层','BMS 电平/隔离 H')
        for pin, sig, direction in [('PE12','SPI4_SCK','输出'),('PE13','SPI4_MISO','输入'),('PE14','SPI4_MOSI','输出')]:
            put(pin, 'RF_'+sig.split('_')[1], sig, direction, '模块接口 H')
        put('PE11','RF_CS',default='10k 上拉',note='具体模块 H')
        put('PC4','RF_IRQ',direction='输入',default='按模块偏置 H',irq=4)
        put('PC5','RF_RESET',direction='开漏请求',default='按模块复位 H')
        for pin, net, sig in [('PC0','VIN_ADC','ADC1_IN6'),('PC1','SENSOR5V_ADC','ADC1_IN7'),('PC2','LOGIC3V3_ADC','ADC1_IN8')]:
            put(pin,net,sig,'模拟输入','分压/滤波/限幅','ADC 电气 H')
        put('PC3','ESTOP_OK',direction='输入',default='断线为无效',note='调理后；独立硬件通路',irq=3)
        put('PC6','WD_HEARTBEAT',default='下拉；停止翻转视为故障')
        put('PC7','ARM_REQ',default='10k 下拉；新边沿武装')
        put('PC8','HW_PERMIT_SENSE',direction='输入',default='低为禁止',note='轮询，不占 EXTI8')
        for pin, net in [('PD8','DRIVE_A_FAULT'),('PD9','DRIVE_A_READY'),('PD11','DRIVE_B_FAULT'),('PD12','DRIVE_B_READY'),('PF3','STEER_SAFE_FEEDBACK'),('PG3','REARM_SENSE'),('PG4','POWER_HEALTH')]:
            put(pin,net,direction='输入',default='调理后，断线安全',note='轮询；外部电平 H')
        for pin, net in [('PD10','DRIVE_A_RESET_REQ'),('PD13','DRIVE_B_RESET_REQ'),('PD14','DRIVE_A_ENABLE_REQ'),('PD15','DRIVE_B_ENABLE_REQ'),('PF4','STEER_PERMIT_REQ'),('PG0','DRIVE_A_STOP_REQ'),('PG1','DRIVE_B_STOP_REQ')]:
            put(pin,net,default='外部门控，禁能优先',note='真实驱动器电平 H')
        for pin, label in zip(['PB0','PB1','PB2'],'ABC'):
            put(pin,'SENS_EN_'+label,default='10k 下拉，输出关闭')
        for pin, label in zip(['PB14','PB15','PC9'],'ABC'):
            put(pin,'SENS_FAULT_'+label,direction='输入',default='上拉，开漏线与条件核验',note='轮询')
        for pin, num in zip(['PA9','PA10','PB10'],[1,2,3]):
            put(pin,f'CAN{num}_STB',default='10k 上拉，待机')
        put('PB11','LED_STATUS',default='串阻 LED，默认灭')
    else:
        for pin, num in [('PC6',1),('PC7',2)]: put(pin,f'CAN{num}_STB',default='10k 上拉，待机')
        put('PC12','CAN1_WAKE_RXD',direction='输入',default='10k 上拉；RXD 扇出',note='经 0Ω 从 U301.4 接入；独立 EXTI12',irq=12)
        for pin, net, sig, direction in [('PA9','MODEM_TX','USART1_TX','输出'),('PA10','MODEM_RX','USART1_RX','输入'),('PB10','EXT_UART_TX','USART3_TX','输出'),('PB11','EXT_UART_RX','USART3_RX','输入')]:
            put(pin,net,sig,direction,'经电平转换/物理层 H')
        put('PA11','MODEM_CTS','USART1_CTS','输入','经电平转换 H','可选流控，与模块 RTS 对接')
        put('PA12','MODEM_RTS','USART1_RTS','输出','经电平转换 H','可选流控，与模块 CTS 对接')
        put('PC8','SHT_SCL','I2C3_SCL','开漏','4.7k 上拉起始值')
        put('PC9','SHT_SDA','I2C3_SDA','开漏','4.7k 上拉起始值')
        for i in range(8): put('PE'+str(i+2),'K'+str(i+1)+'_REQ',default='下拉；门控后驱动',note='K2 散热例外路径' if i==1 else '急停切断')
        for pin, net in [('PA6','ACT_IN1_REQ'),('PA7','ACT_IN2_REQ'),('PC0','ACT_EN_REQ'),('PC2','ACT_D2_REQ')]:
            put(pin,net,default='缓冲后 2.2k 下拉',note='掉电 Ioff/反灌待核验')
        put('PC1','ACT_D1_REQ',default='高禁止，芯片侧上拉',note='与 EN/D2 独立默认禁止')
        put('PC4','ACT_SF',direction='输入',default='15k 上拉',note='开漏；禁止时也可低',irq=4)
        for pin,net,sig in [('PA0','VIN_ADC','ADC1_IN1'),('PA1','K1_ADC','ADC1_IN2'),('PA2','ACT_FB_ADC','ADC1_IN3'),('PA3','LOCK_I_ADC','ADC1_IN4')]:
            put(pin,net,sig,'模拟输入','限幅/滤波，范围待核验')
        for pin,net,irq in [('PC5','LOCK_SENSE',5),('PB0','ESTOP_OK',0),('PB1','WAKE_LOGIC',1),('PB2','MODEM_RI',2)]:
            put(pin,net,direction='输入',default='调理后本地电平',note='禁止直接接外部 12V',irq=irq)
        for pin,net in [('PD8','MODEM_PWRKEY_REQ'),('PD9','MODEM_RESET_REQ')]:
            put(pin,net,direction='开漏请求',default='模块时序/电平 H')
        put('PD10','MODEM_STATUS',direction='输入',default='电平转换 H')
        put('PD11','WD_HEARTBEAT',default='下拉；停止翻转故障')
        put('PD12','ARM_REQ',default='10k 下拉，新边沿武装')
        put('PD13','HW_PERMIT_SENSE',direction='输入',default='低为禁止，轮询')
        put('PD14','LOCK_EN_REQ',default='下拉，硬件许可门控')
        put('PD15','LOCK_FAULT',direction='输入',default='匹配高边型号 H')
        put('PE10','SHT_ALERT_1',direction='输入',default='按器件上拉 H',note='可不装，轮询')
        put('PE11','SHT_ALERT_2',direction='输入',default='按器件上拉 H',note='可不装，轮询')
        put('PE12','SHT_RESET_REQ',direction='开漏请求',default='按具体器件 H')
        put('PE13','LED_STATUS',default='串阻 LED，默认灭')
    return d

for board, filename, count, expected_can in [('VCU','STM32G474Q_B-C-E_Tx.xml',128,3),('BCM','STM32G491V_C-E_Tx.xml',100,2)]:
    root = ET.parse(ROOT/'资料'/filename).getroot()
    pins = [p for p in root if p.tag.rsplit('}',1)[-1]=='Pin']
    assert len(pins)==count
    assert {int(p.attrib['Position']) for p in pins} == set(range(1,count+1))
    ips = [p.attrib.get('InstanceName','') for p in root if p.tag.rsplit('}',1)[-1]=='IP']
    assert len([x for x in ips if x.startswith('FDCAN')])==expected_can
    assigned=assignments(board)
    seen=set(); irqs=set(); rows=[]
    for p in sorted(pins,key=lambda p:int(p.attrib['Position'])):
        name=p.attrib['Name']; base=name.split('-')[0]; pos=int(p.attrib['Position'])
        available={s.attrib.get('Name') for s in p if s.tag.endswith('Signal')}
        if base in assigned:
            a=assigned[base]; seen.add(base)
            assert a['signal'] in available, (board,name,a['signal'])
            if a['irq'] is not None:
                assert a['irq'] not in irqs, (board,'EXTI collision',a['irq'])
                assert int(base[2:])==a['irq']
                irqs.add(a['irq'])
            function = a['signal'] if a['signal']!='GPIO' else a['direction']
            if a['irq'] is not None: function += '/EXTI'+str(a['irq'])
            rows.append([pos,name,a['net'],function,a['default'],a['note'] or 'D 分配；复用信号已核验'])
        elif name=='VDD': rows.append([pos,name,'3V3_LOGIC','供电','100nF/脚','V 脚位；D 去耦'])
        elif name in ['VSS','VSSA']: rows.append([pos,name,'GND','地','低阻回流','V 脚位'])
        elif name=='VDDA': rows.append([pos,name,'VDDA_3V3','模拟供电','100nF+1µF','D；时序 H'])
        elif name=='VBAT': rows.append([pos,name,'3V3_LOGIC','备份域电源','100nF','无后备电池基线'])
        elif name.startswith('VREF'):
            if board=='VCU': rows.append([pos,name,'HOLD_VERIFY_REF','禁止冻结','不根据 XML 猜接法','H：43/44 实体定义须查数据手册'])
            else: rows.append([pos,name,'VREF_VDDA_PROPOSED','模拟参考','提议接 VDDA/去耦','H：电气手册与缓冲设置'])
        elif 'NRST' in name: rows.append([pos,name,'NRST','复位','10k 上拉+100nF','监督开漏；保留复位功能'])
        elif 'BOOT0' in name: rows.append([pos,name,'BOOT0','启动','10k 下拉','启动选项 H'])
        elif 'OSC32' in name: rows.append([pos,name,'LSE_DNP','可选 RTC','不用时 NC','无默认 32k 晶体'])
        elif 'OSC_' in name: rows.append([pos,name,'HSE_'+('IN' if 'OSC_IN' in name else 'OUT'),'主时钟','晶体/CL/ESR 待选','H：CAN 时钟精度'])
        else: rows.append([pos,name,'NC_RESERVED','未用 GPIO','NC，初始化模拟态','不外接，不临时挪用'])
    assert seen==set(assigned),(board,'unmatched',set(assigned)-seen)
    headers=['实体脚','引脚名','网络名','功能/方向','外部默认/处理','备注']
    write_csv(board+'_MCU全引脚.csv',headers,rows)
    table(board+' MCU 全引脚（实体脚号，不是连接器腔号）',headers,rows)
    checks.append(f'{board}: {count} 个唯一实体脚完整；{len(assigned)} 个 GPIO 分配的功能存在；{len(irqs)} 条 EXTI 无冲突；{expected_can} 路 FDCAN 实例确认。')

conn=[]
def slot(net,direction,peer,return_note):
    conn.append([f'B{len(conn)+1:02d}','H：厂家腔号未确认',net,direction,peer,return_note])
for suffix in 'ABCD': slot('12V_IN_'+suffix,'输入','12V 配电正极','等规格并联')
for suffix in 'ABCD': slot('PWR_RETURN_'+suffix,'功率回流','12V 配电地','不借信号地')
for i in range(1,9): slot('K'+str(i)+'_OUT','输出','负载'+str(i)+'正极','负载负线回外部汇流排')
for net,direction,peer,ret in [
 ('LOCK_PWR_OUT','输出','锁正极','LOCK_RETURN'),('LOCK_RETURN','回流','锁负极','板内 PGND'),
 ('ACT_OUT1','双向功率','推杆线1','与 OUT2 成对，不接地'),('ACT_OUT2','双向功率','推杆线2','与 OUT1 成对，不接地'),
 ('CAN1_H','双向','主干 H','与 L 双绞'),('CAN1_L','双向','主干 L','与 H 双绞'),('CAN1_REF','参考','主干参考地','非负载回流'),
 ('CAN2_H','双向','扩展 H','与 L 双绞'),('CAN2_L','双向','扩展 L','与 H 双绞'),('CAN2_REF','参考','扩展参考地','非负载回流'),
 ('BCM_TX','输出','对端 RX','电平 H'),('BCM_RX','输入','对端 TX','电平 H'),('UART_REF','参考','对端参考地','非负载回流'),
 ('WAKE_IN','输入','12V 唤醒请求','调理；与系统参考地同域'),('ESTOP_SENSE','检测','独立辅助 NC','ESTOP_RETURN'),('ESTOP_RETURN','检测回流','独立辅助 NC','不加载 VCU 主链'),
 ('LOCK_SENSE','检测','SM60E 白线1','反馈电气 H；限流辨识'),('LOCK_SENSE_RETURN','检测回流','SM60E 白线2','非锁功率负线'),('RESERVED','不接','空腔堵头','禁止私接电源')]: slot(net,direction,peer,ret)
assert len(conn)==35
write_csv('BCM_35P逻辑分配_非厂家腔号.csv',['逻辑槽位','厂家腔号','网络','方向','对端','回流/注意'],conn)
table('BCM 35P 逻辑分配——不可据此直接压接',['槽位','厂家腔号','网络','方向','对端','回流/注意'],conn)
checks.append('BCM: 35 个逻辑槽位唯一且总数为 35；所有厂家物理腔号明确未确认。')

sensors=[]
for index in range(12):
    dev=f'USONIC_{index+1}' if index<8 else f'TOF_{index-7}'
    group=index//4; channel=index%4
    sensors.append([dev, f'U{401+group}', channel, [17,25,33,41][channel], [18,26,34,42][channel], f'U{710+index}', 'H：外设电平/实体腔号'])
write_csv('VCU_传感器映射.csv',['设备','MAX位号','通道','MAX_RX脚','MAX_TX脚','保护位号','状态'],sensors)
table('VCU 十二路传感器映射',['设备','MAX','通道','RX脚','TX脚','保护','状态'],sensors)
checks.append('VCU: 12 个 UART 设备和 12 个独立端口保护位号唯一，三片 MAX 各使用 4 路。')

bom=[]
def part(board,ref,qty,model,role,status): bom.append([board,ref,qty,model,role,status])
for board, mcu in [('VCU','STM32G474QET6 / LQFP128'),('BCM','STM32G491VET6 / LQFP100')]:
    part(board,'U101',1,mcu,'主控','GPIO 脚位 V；电气 H')
    part(board,'U201～U203',3,'TPSM53603RDAR / B3QFN RDA-15','Buck 三组','S03 型号/脚位 V；热/时序 H')
    part(board,'CIN_10U 每单元2只',6,'GRM32ER71H106KA12L，10µF/50V','Buck 输入','S03 推荐；偏压/供货 H')
    part(board,'COUT_47U 每单元2只',6,'GRM32ER71A476KE15L，47µF/10V','Buck 输出','S03 推荐；偏压有效容量 H')
    part(board,'RFB_TOP 每单元1只',3,'10.0k/0.1%','Buck 上反馈','D')
    part(board,'RFB_BOTTOM',3,'VCU:2.49k×2+4.32k；BCM:2.49k/4.32k/3.32k','Buck 下反馈','D；按板区别')
    part(board,'U301～'+('U303' if board=='VCU' else 'U302'),3 if board=='VCU' else 2,'TCAN1044AVDRQ1 / SOIC-8 D','CAN 物理层','S04 型号/脚位 V；供货/系统 H')
    part(board,'CAN_TERM',3 if board=='VCU' else 2,'120Ω/1%/0.5W，默认 DNP','总线终端','按两端拓扑装配')
    part(board,'CAN_TVS',3 if board=='VCU' else 2,'CAN 专用双线保护，MPN 待定','接口瞬态','H：耐压/电容/能量')
    part(board,'F_MAIN/反接/输入TVS','按保护设计','型号未冻结','输入保护','H：DCDC/线束/负载')
    part(board,'HSE/负载电容','1组','晶体频率/CL/ESR 待定','主时钟','H：精度/起振')
    part(board,'SUP/WD/LATCH','1组','监督器/看门狗/复位主导锁存','硬件许可','H：实体脚号与失效状态')
part('VCU','U401～U403',3,'MAX14830ETM+ / TQFN48+EP','12 UART','S01 型号/脚位 V；供货 H')
part('VCU','MAX去耦',9,'100nF（VL/VEXT/VA 各一）','近脚去耦','每芯片 3 只，不含储能')
part('VCU','MAX_V18_C',3,'1µF，靠 V18','内部 LDO 输出','S01 V')
part('VCU','MAX晶体',3,'1.8432MHz；CL/ESR 待定','每芯片独立时钟','频率 D；具体晶体 H')
part('VCU','U501',1,'带 U.FL 的 nRF52840 模块','无线','H：具体型号/脚位')
part('VCU','U710～U721',12,'带限流/关断/故障的 5V 支路器件','端口保护','H：具体型号/限流值')
part('VCU','外部UART物理层',13,'12传感器+BMS，TTL转换/差分/隔离按设备','电平/保护','H：实际设备规格')
part('VCU外部','DRIVE_A/DRIVE_B',2,'MSSD-100EMA_2EC_N','一拖二驱动控制器','S07 电气/尺寸；S08 为自定义经典 CAN，非 CANopen；端子/安全 H')
part('BCM','K1～K8',8,'12V 线圈、经 DC 负载核验的继电器','输出','H：线圈/触点/封装')
part('BCM','Q901～Q908',8,'VGS=3.3V 有保证的 N-MOS','继电器线圈低边','H：MPN/脚位/功耗')
part('BCM','D901～D908',8,'线圈续流二极管或经验证钳位网络','线圈保护','H：电流/释放时间')
part('BCM','F_K1～F_K8',8,'各负载独立 DC 保护','触点前端保护','H：曲线/额定/分断')
part('BCM','U401',1,'MC33926PNBR2 / PQFN32+EP，8×8mm','推杆 H 桥','S02 型号/脚位 V；生命周期/热 H')
part('BCM','CCP',1,'33nF/50V 陶瓷','CCP 到 VPWR','S02 V')
part('BCM','R_FB',1,'150Ω/1%/0.25W','电流反馈','D；范围与 ADC 保护验证')
part('BCM','R_SF',1,'15k','SF 上拉到 3V3','D；低于 0.3mA')
part('BCM','U701',1,'带诊断/感性钳位的智能高边','SM60E 锁驱动','S09 负载候选 12V/92mA；高边 MPN/脚位 H')
part('BCM外部','LOCK_EXT',1,'SM60E DC12V 版本候选','电磁锁','S09：红/黑功率、双白反馈；反馈电气/机械到位含义 H')
part('BCM','U501',1,'EG800Z-GL 完整变体待确认','4G','H：硬件手册/脚位')
part('BCM','U601/U602',2,'SHT31 具体封装变体待确认','温湿度','H：器件手册/脚位')
part('BCM','J_BCM_EXT',1,'K776280WV-35-PTSNB 候选','35P 接口','H：厂家受控图纸/配套端子')
part('两板','其余电阻/电容/缓冲/接口/连接器','依最终 CAD 统计','本表未构成完整贴片物料清单','采购前补齐','H：不得以候选表直接下单')
write_csv('BOM候选与缺项_不可直接采购.csv',['板','位号/组','数量','候选规格','用途','证据/状态'],bom)
table('候选 BOM 与缺项——不是生产采购 BOM',['板','位号/组','数','候选规格','用途','状态'],bom)

test_titles=['文件与实物一致性','断电电阻与连续性','分阶段首次上电','电源轨与纹波','默认关闭与下载','复位欠压再使能','Buck 负载与热','传感器端口隔离','通信外设反灌','CAN 物理层','MAX/12 UART','BMS/无线','继电器/K1','锁与反馈','推杆方向与限位','推杆带载/堵转/再生','4G 电源维护','SHT 热偏差','急停断线短线','看门狗与锁存','八轴/抱闸/接触器','断地电流路径','同时负载/外壳热','线束机械环境','干扰预检回归','最终放行']
records=[[f'T{i:02d}',title,'','','','','',''] for i,title in enumerate(test_titles,1)]
write_csv('检验记录.csv',['编号','项目','板号/版本/条件','实测值','限值依据','证据编号','结论','测试/复核/日期'],records)
table('首件逐项记录（空白待实测）',['编号','项目','条件/实测','限值/证据','结论','签名/日期'],[[r[0],r[1],'________','________','____','________'] for r in records])

sources=[
 ('S01','MAX14830.pdf','Analog Devices / MAX14830 数据手册','https://www.analog.com/media/en/technical-documentation/data-sheets/MAX14830.pdf','厂家原始 PDF'),
 ('S02','MC33926.pdf','Freescale / MC33926 Rev.10.0，2014-08','https://www.pololu.com/file/0J233/MC33926.pdf','Pololu 镜像的厂家 PDF；PNB/PQFN32；当前生命周期未核验'),
 ('S03','TPSM53603.pdf','TI / SNVSB77B，2021-09 修订','https://www.ti.com/lit/ds/symlink/tpsm53603.pdf','厂家 PDF'),
 ('S04','TCAN1044A-Q1.pdf','TI / SLLSFJ3D，2024-10 修订','https://www.ti.com/lit/ds/symlink/tcan1044a-q1.pdf','含 AV 变体；厂家 PDF'),
 ('S05','STM32G474Q_B-C-E_Tx.xml','ST 官方 MCU 引脚数据库 G474Q','https://api.github.com/repos/STMicroelectronics/STM32_open_pin_data/contents/mcu/STM32G474Q(B-C-E)Tx.xml?ref=master','blob d9c52b4725451407ec54c877732ffd71bde67cee；不是电气数据手册'),
 ('S06','STM32G491V_C-E_Tx.xml','ST 官方 MCU 引脚数据库 G491V','https://api.github.com/repos/STMicroelectronics/STM32_open_pin_data/contents/mcu/STM32G491V(C-E)Tx.xml?ref=master','blob a04f9a00c77e25860360e857e4470f1ec9209114；不是电气数据手册'),
 ('S07','MSSD-100EMA_2EC_N_彩页.pdf','MSEAG MSSD-100EMA_2EC_N 产品彩页','用户提供的商户资料原件','3 页图片型资料；核验输入/输出电流、功能、尺寸与接口分组，不含端子针号和安全手册'),
 ('S08','MSSD-2EC_CAN协议_V1.0.pdf','MSSD-2EC 系列 CAN 通讯协议及寄存器说明书 V1.0','用户提供的商户资料原件','明确为 11 位标准帧的厂家自定义经典 CAN，暂不支持 CANopen；完整寄存器表仍依赖未取得的 RS485 手册'),
 ('S09','SM60E规格书_20260611.pdf','SM60E 电磁锁规格书，图号 SHMi20260611SM60E','用户提供的商户资料原件','图片型机械图；核验 12V/24V 电气、60kg 标称最大吸力、红黑功率和双白反馈；反馈电气类型未定义'),
]
manifest=[]
APP.extend(['## 存档资料索引与 SHA256', '', '资料取得日期：2026-09-19。引用页码指原 PDF 印刷页码，不是本手册页码。下载成功不等于所有参数均已核验；证据范围见每章。', ''])
for sid,filename,title,url,note in sources:
    path=ROOT/'资料'/filename
    assert path.is_file(), filename
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    manifest.append([sid,filename,title,url,digest,note])
    APP.extend([f'### {sid} {title}', '', f'本地文件：资料/{filename}', '', f'来源：{url}', '', f'范围：{note}', '', f'SHA256：{digest}', ''])
write_csv('资料来源与SHA256.csv',['ID','文件','名称','来源URL','SHA256','说明'],manifest)
(ROOT/'10_数据附录.md').write_text('\n'.join(APP)+'\n',encoding='utf-8')
result={'status':'DOCUMENT_DATA_CHECKS_PASSED_NOT_HARDWARE_VALIDATION','checks':checks,'open_items':['MCU 电气手册与 G474 43/44 脚','GPIO AF 数字/时钟/启动','实际 CAD ERC/DRC','连接器厂家腔号','MSSD 端子/RS485 完整寄存器表/安全输入','推杆完整型号与电流/机械参数','SM60E 反馈电气与机械到位含义','安全电路器件和八轴安全路径','4G/无线/传感器/保护完整型号','实物测试全部未执行']}
(DATA/'校验结果.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
