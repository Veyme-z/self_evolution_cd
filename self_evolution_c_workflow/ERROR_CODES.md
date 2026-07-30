# 流程记录判题错误码

| 错误码 | 含义 |
|---|---|
| `E_MISSING` | 未找到当前题答案文件 |
| `E_JSON` | 答案不是合法 JSON |
| `E_SCHEMA` | 顶层结构、步骤字段或嵌套形式不正确 |
| `E_SEQUENCE position=N` | 第 N 个步骤不符合流程依赖 |
| `E_POWER` | 型号、电压或 power 字段错误 |
| `E_VOLTAGE_PRECISION` | 电压不是规定的小数形式 |
| `E_SEED` | 频率种子字段或值错误 |
| `E_FREQUENCY` | 频率字段类型、公式或值错误 |
| `E_PRECISION` | 频率没有恰好保留 1 位小数 |
| `E_AUTH` | 授权记录错误 |
| `E_TRANSMIT` | 授权码、坐标或 ACK 传递错误 |
| `E_LOG` | ACK 或完成凭证传递错误 |
| `E_SUBMISSION` | 最终提交值错误 |

判题器不会在错误响应中返回正确步骤、正确字段值或标准答案。
