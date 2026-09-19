# 工程输入与验证模板

硬件实施已增加 [HW-R1 设计包](硬件设计包/00_使用说明与放行边界.md)。MCU 分配和 35P 逻辑接口以该包生成的数据为单一来源，避免在下方空白模板再维护一套冲突版本；本模板继续用于整车需求、真实功率/协议和审批输入。

本文件用于把 [完整审查报告](PROJECT_AUDIT.md) 中的放行要求转成可填写、可评审、可追溯的工程记录。每张表都应包含版本、负责人、评审人和证据文件链接；没有测量值时填写 `TBD`，不得填猜测值。

## 1. 系统需求基线

| 项目 | 目标值 | 容差/边界 | 验证方法 | 状态 |
|---|---:|---|---|---|
| 整车质量/最大载荷 | TBD | TBD | 称重 | OPEN |
| 最大纵向/横向速度 | TBD | TBD | 封闭场地测试 | OPEN |
| 最大角速度 | TBD | TBD | 封闭场地测试 | OPEN |
| 最大坡度/侧坡 | TBD | TBD | 坡道测试 | OPEN |
| 急停停止距离 | TBD | 按速度/载荷分档 | 实车测量 | OPEN |
| 工作温度/湿度 | TBD | TBD | 温箱/环境测试 | OPEN |
| 连续工作时间 | TBD | TBD | 热稳态测试 | OPEN |
| 防护目标 | TBD | 明确是否仅防泼溅 | 整机测试 | OPEN |

## 2. 功率预算

| 负载 | 电压 | 稳态电流 | 启动/堵转峰值 | 峰值持续时间 | 占空比 | 最坏同时组合 | 支路保护 | 线径/端子 | 实测证据 |
|---|---:|---:|---:|---:|---:|---|---|---|---|
| BCM K1 上位机域 | 12V | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| BCM K2 风扇 | 12V | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| BCM K3～K8 | 12V | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| SM60E 电磁锁 DC12V 候选 | 12V | 0.092A 资料值 | 待测 | 待测 | 持续通电允许 | 常关/急停关 | 独立支路 | 板外 | 双白反馈电气/机械含义待测 |
| 推杆 | 12V | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| EG800Z 电源输入侧 | 12V | TBD | TBD | TBD | TBD | 常电 | TBD | 板内 | TBD |
| VCU 逻辑 | 12V | TBD | TBD | TBD | 100% | 常电 | TBD | 板内 | TBD |
| VCU 5V_SENSOR 分组 | 5V | TBD | TBD | TBD | TBD | TBD | eFuse/限流高边 | TBD | TBD |
| DM-J10010L-2EC ×4 转向 | 24～48V | DC 母线值待测；23.5A 是额定相电流 | DC 母线峰值待测；95A 是峰值相电流 | TBD | 按转向工况 | 四轴同时转向/堵转边界 | 每支路独立熔断+受控接触器 | XT30/线径待厂家确认 | S10/S16 + 台架波形 |

校核结果至少包含：外部 DCDC 余量、连接器每针降额、并联针电流均衡、PCB 压降/温升、支路保护动作和最坏环境温度。

## 3. MCU Pinmap

| 逻辑信号 | MCU 引脚 | 复用功能 | 方向 | 上电默认态 | 外部上拉/下拉 | 安全相关 | DMA/IRQ | 测试点 | 评审结论 |
|---|---|---|---|---|---|---|---|---|---|
| `SAFETY_ENABLE` | TBD | GPIO | OUT | 禁能 | 硬件禁能偏置 | 是 | - | 是 | OPEN |
| `ESTOP_ACTIVE` | TBD | GPIO/EXTI | IN | 急停 | TBD | 是 | IRQ | 是 | OPEN |
| `FDCAN1_TX/RX` | TBD | FDCAN1 | I/O | recessive | 按收发器 | 是 | IRQ | 是 | OPEN |
| `MAX14830_A_CS/IRQ` | TBD | SPI/GPIO | I/O | 未选中 | CS 上拉/IRQ 上拉 | 否 | DMA/IRQ | 是 | OPEN |

Pinmap 放行时同时附上时钟树、DMA 通道表、中断优先级表和封装引脚图标注。

## 4. CAN 网络与报文

### 4.1 物理网络

| 总线 | 节点 | 拓扑/顺序 | 总长 | 最大 stub | 仲裁/数据速率 | 终端位置 | 参考地/屏蔽 | 收发器 |
|---|---|---|---:|---:|---|---|---|---|
| CAN1_MAIN | 上位机/BCM/VCU | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| CAN2_STEER | VCU/4×DM-J10010L-2EC | 线性/菊链，节点顺序待线束冻结 | TBD | TBD | 经典 CAN 1Mbps | VCU + 最远端电机；中间节点关闭拨码4 | 电机仅2线 CAN；非隔离地/共模 H | TCAN1044AV-Q1 + 电机内置收发器 |
| CAN3_DRIVE | VCU/MSSD A/B | 线性/菊链，最终冻结 | TBD | TBD | 经典 CAN 500kbps 默认 | 仅两个物理端 | 参考地/屏蔽待定义 | TCAN1044AV-Q1 + MSSD 内置收发器 |

### 4.2 报文定义

| 报文名 | ID | FD/经典 | DLC | 周期 | 超时 | 发送者 | 接收者 | 序号 | CRC | 失效默认态 |
|---|---:|---|---:|---:|---:|---|---|---|---|---|
| ChassisCommand | TBD | FD | TBD | TBD | TBD | 当前控制源 | VCU | 是 | 是 | 目标清零/停车 |
| VCUStatus | TBD | FD | TBD | TBD | TBD | VCU | 上位机/BCM | 是 | 是 | 状态未知 |
| BCMCommand | TBD | FD | TBD | TBD | TBD | 上位机/VCU | BCM | 是 | 是 | 输出安全默认 |
| SteerPositionVelocity | `0x100+ESC_ID` | 经典 | 8 | 初始 10ms，实测冻结 | TBD | VCU | 单台 DM-J10010L | 无 | 无 | 停发后依 TIMEOUT 失能；TIMEOUT 单位/默认 H |
| SteerFeedback | 每台唯一 `MST_ID` | 经典 | 8 | 厂家触发规则/实测 | TBD | 单台 DM-J10010L | VCU | 无 | 无 | 状态非使能、重复 ID 或超时即退出正常闭环 |

每个信号还必须定义字节序、位位置、单位、比例、偏移、物理范围、无效值、滚动计数器、版本兼容和启动阶段行为。

## 5. UART/传感器接口

| 设备 | 电平 | 供电 | 波特率 | 最大线长 | 物理层 | 校验 | 超时 | 保护 | 断线/异常策略 |
|---|---|---|---:|---:|---|---|---:|---|---|
| BMS | TBD | TBD | TBD | TBD | UART/RS-485/TBD | TBD | TBD | TBD | TBD |
| 超声波型号 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| ToF 型号 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

## 6. 安全验证矩阵

| 故障注入 | 预期硬件动作 | 预期软件状态 | 最大响应时间 | 恢复条件 | 测量方法 | 结果/证据 |
|---|---|---|---:|---|---|---|
| 本地急停断开 | 八轴进入安全态 | `ESTOP_LATCHED` | TBD | 物理恢复+人工复位 | 示波器+整车 | OPEN |
| MCU 卡死 | 外部监督器撤销安全使能 | 复位后保持锁存 | TBD | 自检+人工复位 | 停止心跳 | OPEN |
| CAN1 命令超时 | 目标清零/受控停车 | FAULT/停车 | TBD | 新鲜命令+重新使能 | 断线/报文抑制 | OPEN |
| 无线武装后失联 | 安全停车 | `ESTOP_LATCHED` | TBD | 链路恢复+人工复位 | 屏蔽/断电 | OPEN |
| 无线未武装且离线 | 无影响 | 有线模式继续 | - | - | 遥控器断电 | OPEN |
| 任一转向轴离线 | 禁止继续正常运动 | FAULT | TBD | 故障清除+自检 | 断开节点 | OPEN |
| 任一 5V_SENSOR 短路 | 仅故障分支限流/关闭 | DEGRADED/FAULT | TBD | 排故后重试 | 电子负载短路 | OPEN |
| 推杆终点/堵转 | H 桥停止 | 故障锁存 | TBD | 排故/复位 | 假负载/机械限位 | OPEN |

## 7. 版本放行记录

| 交付物 | 版本/哈希 | 负责人 | 评审人 | 测试报告 | 放行状态 |
|---|---|---|---|---|---|
| VCU 固件 | TBD | TBD | TBD | TBD | OPEN |
| BCM 固件 | TBD | TBD | TBD | TBD | OPEN |
| VCU 原理图/PCB | TBD | TBD | TBD | TBD | OPEN |
| BCM 原理图/PCB | TBD | TBD | TBD | TBD | OPEN |
| 线束图 | TBD | TBD | TBD | TBD | OPEN |
| 参数/标定 | TBD | TBD | TBD | TBD | OPEN |
| 整车测试 | TBD | TBD | TBD | TBD | OPEN |
