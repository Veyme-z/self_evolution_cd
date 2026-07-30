# 荒野应急通信流程档案

**版本**：v1.1  
**数据格式**：JSON（UTF-8）  
**执行方式**：离线整理流程记录，不调用 HTTP API

---

## 1. 档案说明

每道任务都包含相同的 6 个操作步骤，但旧档案中的步骤顺序已经丢失。下列步骤按档案编号排列，**排列位置不代表正确执行顺序**。

Agent 需要根据每个步骤的前置状态、完成状态和数据依赖，在 C-1 中推导出唯一流程。C-2、C-3 继续使用相同流程。

---

## 2. 无序步骤卡

### 档案 P-17：log

```text
REQUIRES=ack_ready
PRODUCES=done
```

用途：把发射回执登记到总台，产生完成凭证。该步骤需要使用此前产生的 ACK。

### 档案 P-04：tune

```text
REQUIRES=seed_ready
PRODUCES=tuned
```

用途：根据型号公式和频率种子写入工作频率。

### 档案 P-21：auth

```text
REQUIRES=tuned
PRODUCES=authorized
```

用途：取得当前任务的授权码。

### 档案 P-02：power

```text
REQUIRES=idle
PRODUCES=powered
```

用途：使用设备型号和型号额定电压启动设备。

### 档案 P-13：transmit

```text
REQUIRES=authorized
PRODUCES=ack_ready
```

用途：使用授权码和任务坐标发送定位记录，产生 ACK。

### 档案 P-09：seed

```text
REQUIRES=powered
PRODUCES=seed_ready
```

用途：读取当前任务的频率种子。

---

## 3. 字段残卷

完整记录会使用以下字段名，但残卷没有保存它们在步骤中的排列位置：

```text
model
voltage
freq_seed
freq
code
coord
ack
done_code
```

整理原则：

- 发给某步骤的数据放在 `request`；
- 某步骤产生的数据放在 `response`；
- 每个步骤对象必须包含 `step`；
- 顶层必须包含 `task`、`execution` 和 `submission`；
- `execution` 中必须包含全部 6 个步骤，每步恰好一次；
- 不得添加残卷之外的业务字段。

步骤对象通用形式：

```json
{
  "step": "<步骤名>",
  "request": {"<输入字段>": "<值>"},
  "response": {"<输出字段>": "<值>"}
}
```

如果某个步骤只有输入或只有输出，则只保留对应的 `request` 或 `response`。

---

## 4. 数据传递约束

1. 频率种子来自当前任务运行记录；
2. 工作频率根据当前型号手册计算；
3. auth 产生的授权码必须传递给需要它的后续步骤；
4. transmit 产生的 ACK 必须传递给需要它的后续步骤；
5. log 产生的完成凭证必须作为最终提交值；
6. 任务坐标必须逐字使用当前运行记录中的值。

---

## 5. 参数格式线索

旧系统留下了以下拒绝记录：

| 被拒绝的值 | 错误原因 |
|---|---|
| `"12V"` | 数值字段中包含单位 |
| `"168.0"` | 数值字段被写成字符串 |
| `168` | 频率没有保留要求的小数位 |
| `168.00` | 频率小数位过多 |
| `"[N31.2, E121.5]"` | 坐标包含方括号和多余空格 |
| 使用 ACK 作为最终提交 | 提交的不是完成凭证 |

本组频率计算结果均可精确表示为 1 位小数，不需要四舍五入。

---

## 6. 判题反馈

提交错误时，判题器只返回错误类别或首个错误步骤，不返回正确内容：

```text
E_SCHEMA
E_SEQUENCE position=N
E_POWER
E_SEED
E_FREQUENCY
E_PRECISION
E_AUTH
E_TRANSMIT
E_LOG
E_SUBMISSION
```
