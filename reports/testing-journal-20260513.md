# 🧪 kids-points Agent 集成测试日志

> 日期：2026-05-17
> 项目：kids-points-runtime（Agent Runtime 治理学习实践）
> 阶段：模块 1~5 核心代码完成后，进行端到端集成测试
> 测试环境：离线开发环境，内存 SQLite，真实 MiniMax 2.7 LLM 调用

---

## 测试框架

### 测试脚本

测试通过 `test_runner.py` 执行，支持两种模式：

1. **模拟模式（默认）** — 用预录的 LLM 响应替代真实调用，快速验证代码逻辑
2. **真实模式** — 调用真实 MiniMax 2.7 LLM，验证 LLM 语义理解 + 代码校验的完整流水线

### 结果字段说明

| 字段 | 说明 |
|------|------|
| `status` | ✅ 通过 / ❌ 失败 / ⚠️ 部分通过 |
| `confidence` | HIGH / MEDIUM / LOW — 我对测试结果的置信度判断 |
| `actual_output` | 测试时系统的实际返回 |
| `diff` | 实际输出与期望输出的差异 |

**confidence 判定标准：**
- **HIGH**：预期行为明确（如去重阻止了重复记账、余额计算正确），代码逻辑清晰无歧义
- **MEDIUM**：预期行为存在合理差异（如 description 文字略有不同但含义一致、LLM 返回的鼓励语风格不同）
- **LOW**：预期行为本身有模糊空间（如原始日志记录不完整、无法确认原始系统的确切行为）

---

## 一、记账（Record）测试

### TC-001: 最早期基础记账（P1）

**用户输入：**
```
学习积分 测试 +1 分
```

**期望输出：**
```json
{"intent": "record", "items": [{"type": "income", "amount": 1, "description": "测试"}]}
```

**测试结果：** ⬜ 待测试 | confidence: HIGH

**说明：** 第一行日志（3/24 15:33），系统最开始跑的测试。

---

### TC-002: 消费扣分（含"积分消费"格式）（P1）

**用户输入：**
```
积分消费 2 分 - 早上把卷子发卷烂了
```

**期望输出：**
```json
{"intent": "record", "items": [{"type": "expense", "amount": 2, "description": "早上把卷子发卷烂了"}]}
```

**测试结果：** ⬜ 待测试 | confidence: HIGH

**说明：** 早期消费格式：`积分消费 [金额] 分 - [描述]`。

---

### TC-003: 语义模糊"完成了汉字抄写2课"→ +0分（P1）

**用户输入：**
```
今天完成了汉字抄写 2 课
```

**期望输出：**
```json
{"intent": "record", "items": [{"type": "income", "amount": 2, "description": "汉字抄写"}]}
```

**测试结果：** ⬜ 待测试 | confidence: LOW

**说明：** 用户只说完成了任务没给分，早期系统解析为+0分。重构后应尝试从"2课"推断为+2分。amount=2是一种合理期望，但旧系统实际行为是+0。

---

### TC-004: 首次多项目合并（补录格式）（P1）

**用户输入：**
```
补录 2026-03-25 积分：语文作业 +1 分，数学作业 +1 分，英语作业 +1 分，口算（没有全对）+1 分，家里写字作业 +1 分
```

**期望输出：**
```json
{
  "intent": "record",
  "items": [
    {"type": "income", "amount": 1, "description": "语文作业"},
    {"type": "income", "amount": 1, "description": "数学作业"},
    {"type": "income", "amount": 1, "description": "英语作业"},
    {"type": "income", "amount": 1, "description": "口算（没有全对）"},
    {"type": "income", "amount": 1, "description": "家里写字作业"}
  ]
}
```

**测试结果：** ⬜ 待测试 | confidence: MEDIUM

**说明：** 首次出现"补录"语义和批量多项目。原系统在input.log中记录这5项全部解析成功，但description里包含括号注释（"口算（没有全对）"）。LLM对description的标准化程度可能不同。

---

### TC-005: "-"号歧义（消费格式不稳定期）（P1）

**用户输入：**
```
学习积分 测试减 -1 分
```

**期望输出：**
```json
{"intent": "record", "items": [{"type": "expense", "amount": 1, "description": "测试减"}]}
```

**测试结果：** ⬜ 待测试 | confidence: LOW

**说明：** 用户说"测试减 -1 分"，"-1"看起来很清晰但旧系统判定为income。说明LLM把"减"的语义和"-1"的负号混淆了。旧系统实际余额没变（0.0→0.0），可能被去重或其他逻辑拦截了。

---

### TC-006: 自然语言描述（非结构化）（P1）

**用户输入：**
```
昨天完成了语文作业 +1 分，完成了英语作业 +1 分
```

**期望输出：**
```json
{
  "intent": "record",
  "items": [
    {"type": "income", "amount": 1, "description": "语文作业"},
    {"type": "income", "amount": 1, "description": "英语作业"}
  ]
}
```

**测试结果：** ⬜ 待测试 | confidence: MEDIUM

**说明：** 旧系统第一次解析为+0分，重发同一条就正确了。典型LLM不稳定表现。重构系统用MiniMax 2.7应该更稳定。

---

### TC-007: 语义理解"读了两篇，加5分"（P2）

**用户输入：**
```
ABC Reading 读了两篇，加 5 分
```

**期望输出：**
```json
{"intent": "record", "items": [{"type": "income", "amount": 5, "description": "ABC Reading 读了两篇"}]}
```

**测试结果：** ⬜ 待测试 | confidence: MEDIUM

**说明：** 描述完成数量+奖励金额的自然语言。旧系统首次解析为+0分后重发才正确。

---

### TC-008: 多项目+消费混合（用换行/编号）（P2）

**用户输入：**
```
今天积分记录：
1. 语文抄写：加 1 分
2. 口算：加 1 分（未全对）
3. ABC Reading：加 2 分
4. 手工材料消费 1 分
```

**期望输出：**
```json
{
  "intent": "record",
  "items": [
    {"type": "income", "amount": 1, "description": "语文抄写"},
    {"type": "income", "amount": 1, "description": "口算（未全对）"},
    {"type": "income", "amount": 2, "description": "ABC Reading"},
    {"type": "expense", "amount": 1, "description": "手工材料消费"}
  ]
}
```

**测试结果：** ⬜ 待测试 | confidence: MEDIUM

**说明：** 换行+编号+混合类型。旧系统解析失败——第4项被当成收入+1而不是消费扣1。极好的语义边界测试。

---

### TC-009: 小数截断灾难（2.5→2.→扣5分）（P2）

**用户输入：**
```
今天做语文的拼音练习，加 1.5 分
```

**期望输出：**
```json
{"intent": "record", "items": [{"type": "income", "amount": 1.5, "description": "语文的拼音练习"}]}
```

**测试结果：** ⬜ 待测试 | confidence: HIGH

**说明：** 旧系统解析为 `加 1.`（截断），缺少5→被当作"1"→但实际被扣5分（JS parseFloat("1.")=1→乘以5？）。重构系统的validate函数允许float。

---

### TC-010: 小数截断在消费侧的镜像bug（P2）

**用户输入：**
```
积分记录，消费了一片口香糖，扣 0.5 分
```

**期望输出：**
```json
{"intent": "record", "items": [{"type": "expense", "amount": 0.5, "description": "消费了一片口香糖"}]}
```

**测试结果：** ⬜ 待测试 | confidence: HIGH

**说明：** 同样的截断——"扣 0."→扣0分，但旧系统实际扣了5分（91.8→83.3）。金额少了一位小数点就扣错。

---

### TC-011: 大额消费（"花了很多分"）（P2）

**用户输入：**
```
今天自己买了一个小置物架，花了 29.8 分
```

**期望输出：**
```json
{"intent": "record", "items": [{"type": "expense", "amount": 29.8, "description": "买小置物架"}]}
```

**测试结果：** ⬜ 待测试 | confidence: HIGH

**说明：** 大额小数，两位小数不会触发截断。判断LLM输出29.8的能力。

---

### TC-012: 多事件并发（同一条消息含4个子项）（P2）

**用户输入：**
```
完成了语文的所有单元的改错
```

**期望输出：**
```json
{"intent": "record", "items": [{"type": "income", "amount": 2, "description": "完成了语文的所有单元的改错"}]}
```

**测试结果：** ⬜ 待测试 | confidence: MEDIUM

**说明：** 旧系统同一秒发4条消息，分数不同（+2/+1/+1/+1）。单条消息下LLM是否能推断出2分。

---

### TC-013: 隐性扣分（不写"积分消费"）（P2）

**用户输入：**
```
早上起床拖拖拉拉
```

**期望输出：**
```json
{"intent": "record", "items": [{"type": "expense", "amount": 1, "description": "早上起床拖拖拉拉"}]}
```

**测试结果：** ⬜ 待测试 | confidence: LOW

**说明：** 无明确扣分关键字，LLM需理解"拖拖拉拉"=坏行为→扣1分。旧系统实际扣了1分。这是纯语义理解考验。

---

### TC-014: 多重语义（学校作业+托管班双倍）（P2）

**用户输入：**
```
学校作业在托管班完成，给双倍加 4 分
```

**期望输出：**
```json
{"intent": "record", "items": [{"type": "income", "amount": 4, "description": "学校作业在托管班完成，双倍"}]}
```

**测试结果：** ⬜ 待测试 | confidence: HIGH

**说明：** "双倍"是乘数概念，但金额已经是运算后的4分，LLM不应再乘以2。

---

### TC-015: 简单记账——稳定格式期（P3）

**用户输入：**
```
口算 +1 分
```

**期望输出：**
```json
{"intent": "record", "items": [{"type": "income", "amount": 1, "description": "口算"}]}
```

**测试结果：** ⬜ 待测试 | confidence: HIGH

**说明：** 极简格式，用户已形成固定习惯。最基础的case。

---

### TC-016: "-"负号歧义——扣分变加分（P3）

**用户输入：**
```
吃口香糖 -1 分
```

**期望输出：**
```json
{"intent": "record", "items": [{"type": "expense", "amount": 1, "description": "吃口香糖"}]}
```

**测试结果：** ⬜ 待测试 | confidence: HIGH

**说明：** `-1`表示扣1分，但旧系统错误解析为+1分（把`-1`当成`减号+1`=加1）。多次出现的致命Bug。

---

### TC-017: 补录（"昨天"时间语义）（P3）

**用户输入：**
```
昨天语文写字加 3 分，因为还改了课上要写错的字
```

**期望输出：**
```json
{"intent": "record", "items": [{"type": "income", "amount": 3, "description": "语文写字，还改了课上要写错的字"}]}
```

**测试结果：** ⬜ 待测试 | confidence: MEDIUM

**说明：** "昨天"表示补录，附带了原因。LLM需区分描述和分数。

---

### TC-018: "扣"写在末尾而非开头（P3）

**用户输入：**
```
晚睡觉减 2 分
```

**期望输出：**
```json
{"intent": "record", "items": [{"type": "expense", "amount": 2, "description": "晚睡觉"}]}
```

**测试结果：** ⬜ 待测试 | confidence: HIGH

**说明：** 用"减"而非"扣"。LLM需理解"减"="扣分"。

---

### TC-019: 去重失败——同条消息×5（P4）

**用户输入：**
```
在托管班完成学校课内作业加4分
```

**期望输出（第一次）：**
```json
{"intent": "record", "items": [{"type": "income", "amount": 4, "description": "在托管班完成学校课内作业"}]}
```

**期望结果（第2~5次重复）：**
```json
{"status": "skipped", "reason": "duplicate message_id"}
```

**测试结果：** ⬜ 待测试 | confidence: HIGH

**说明：** 旧系统连续5次发送完全相同的消息，每次都记账。这是去重逻辑的关键case。重构系统用processed_messages去重，message_id相同应被拦截。

---

### TC-020: "积分"→"积分"混用（P4）

**用户输入：**
```
口算全对，4积分
```

**期望输出：**
```json
{"intent": "record", "items": [{"type": "income", "amount": 4, "description": "口算全对"}]}
```

**测试结果：** ⬜ 待测试 | confidence: HIGH

**说明：** "4积分"="4分"，LLM需理解等价。

---

### TC-021: 余额跳跃场景下的记账（P4）

**用户输入：**
```
积分消费买零食花了30分
```

**期望输出：**
```json
{"intent": "record", "items": [{"type": "expense", "amount": 30, "description": "买零食"}]}
```

**测试结果：** ⬜ 待测试 | confidence: HIGH

**说明：** 旧系统余额从-100.5跳到77.4再回到47.4的混乱时期。单条消息的LLM解析和记账逻辑应该独立于余额状态。

---

### TC-022: 同一条消息去重失败——测试+生产混用（P4）

**用户输入：**
```
改学校错题加2分，ABC Reading加3分，英赛尔加2分。因为今天英赛尔放水了
```

**期望输出：**
```json
{
  "intent": "record",
  "items": [
    {"type": "income", "amount": 2, "description": "改学校错题"},
    {"type": "income", "amount": 3, "description": "ABC Reading"},
    {"type": "income", "amount": 2, "description": "英赛尔"}
  ]
}
```

**测试结果：** ⬜ 待测试 | confidence: MEDIUM

**说明：** 旧系统46秒内两次完全相同消息，第一次记账后余额没变（应+7但显示114.4即不变），第二次才正确增加。备注"英赛尔放水了"不是记账项。

---

### TC-023: 修正语义——带括号说明（P5）

**用户输入：**
```
昨天ABC Reading +2分（修正）
```

**期望输出：**
```json
{"intent": "record", "items": [{"type": "income", "amount": 2, "description": "ABC Reading（修正）"}]}
```

**测试结果：** ⬜ 待测试 | confidence: MEDIUM

**说明：** 用户用"修正"标记补录。重构系统暂无专门的"修正"类型，先按普通record处理。

---

### TC-024: 一条消息多个项目+简写（P5）

**用户输入：**
```
ABC加1分
```

**期望输出：**
```json
{"intent": "record", "items": [{"type": "income", "amount": 1, "description": "ABC Reading"}]}
```

**测试结果：** ⬜ 待测试 | confidence: LOW

**说明：** 用户简写"ABC"→完整名"ABC Reading"。LLM应做实体标准化还是原样输出？两种都合理，但标准化更友好。

---

### TC-025: 带单位"元"的语义识别（P5）

**用户输入：**
```
扣消费海苔卷14.3积分
```

**期望输出：**
```json
{"intent": "record", "items": [{"type": "expense", "amount": 14.3, "description": "海苔卷"}]}
```

**测试结果：** ⬜ 待测试 | confidence: MEDIUM

**说明：** "14.3积分"而非"14.3分"。注意Prompt中写了1元=100分，但这里用户说"积分"=分，不是人民币元。

---

### TC-026: 重复记账灾难——同条消息×14（P5）

**用户输入：**
```
口算：今天完成了两篇，都没全对，记2分
```

**期望输出（第一次）：**
```json
{"intent": "record", "items": [{"type": "income", "amount": 2, "description": "口算（两篇未全对）"}]}
```

**期望结果（第2~14次重复）：**
```json
{"status": "skipped", "reason": "duplicate message_id"}
```

**测试结果：** ⬜ 待测试 | confidence: HIGH

**说明：** 旧系统同一消息14次全部记账，余额136.5→170.5。这是最严重的重复记账灾难。message_id去重是守护保障。

---

### TC-027: 表情+消费混合（P5）

**用户输入：**
```
买冰激凌扣1分
```

**期望输出：**
```json
{"intent": "record", "items": [{"type": "expense", "amount": 1, "description": "买冰激凌"}]}
```

**测试结果：** ⬜ 待测试 | confidence: HIGH

**说明：** 简单消费格式。

---

### TC-028: JSON格式的日志——模糊表达（P5）

**用户输入：**
```
消费1级分，买糯米糍冰激凌
```

**期望输出：**
```json
{"intent": "record", "items": [{"type": "expense", "amount": 1, "description": "买糯米糍冰激凌"}]}
```

**测试结果：** ⬜ 待测试 | confidence: LOW

**说明：** "1级分"可能是口误或飞书识别错误。LLM能否理解=1分？

---

### TC-029: 多类型混合——收入+支出同消息（P5）

**用户输入：**
```
语文写字加3分，语文作文修辞手法加1分，晚睡扣2分
```

**期望输出：**
```json
{
  "intent": "record",
  "items": [
    {"type": "income", "amount": 3, "description": "语文写字"},
    {"type": "income", "amount": 1, "description": "语文作文修辞手法"},
    {"type": "expense", "amount": 2, "description": "晚睡"}
  ]
}
```

**测试结果：** ⬜ 待测试 | confidence: HIGH

**说明：** 5/6出现的新格式——一条消息中混合收入+支出，日志标记为`type:"mixed"`。LLM需正确区分收入和支出。

---

## 二、调账（Adjust）测试

### TC-ADJ-001: 标准调账流程（P3）

**用户输入：**
```
调账：修正看动画片扣分错误（应扣 -5 分但扣了 -10 分，调账 +5 分）
```

**期望输出（第一步→LLM解析）：**
```json
{"intent": "adjust", "date_hint": null, "keyword": "看动画片", "new_amount": 10}
```

**说明：** 用户描述「多扣了要补回」，LLM从`应扣-5但扣了-10`推算出正确金额是扣5分不是10分，new_amount应该是5还是10？Prompt设计是"修正后的金额"，所以new_amount=5（正确金额）。

**测试结果：** ⬜ 待测试 | confidence: LOW

**说明：** 原始日志仅记录了调账成功的结果（余额增加），没有留下LLM解析的中间输出。期望值是根据Prompt模板推理的，实际LLM行为可能有差异。

---

### TC-ADJ-002: 调账的小数二次截断（P3）

**用户输入：**
```
调账加 2.5 分，因为昨天动画片只看了一半
```

**期望输出：**
```json
{"intent": "adjust", "date_hint": "昨天", "keyword": "动画片", "new_amount": 2.5}
```

**测试结果：** ⬜ 待测试 | confidence: LOW

**说明：** 旧系统提取到 `加 2.`（截断）→ 实际加了5分。重构系统用MiniMax 2.7 + Python JSON解析，应该能正确处理小数。

---

### TC-ADJ-003: 调账确认流程

**用户输入（确认消息）：**
```
确认
```

**前提：** 系统中有一个待确认的 pending adjustment。

**期望输出：**
```json
{
  "status": "ok",
  "reply": "包含「已调整」的回复",
  "adjustment": {"type": "adjustment"}
}
```

**测试结果：** ⬜ 待测试 | confidence: HIGH

---

### TC-ADJ-004: 调账取消流程

**用户输入（取消消息）：**
```
取消
```

**前提：** 系统中有一个待确认的 pending adjustment。

**期望输出：**
```json
{"status": "ok", "reply": "已取消调账。"}
```

**测试结果：** ⬜ 待测试 | confidence: HIGH

---

### TC-ADJ-005: 调账失败——找不到原记录

**用户输入：**
```
调一下昨天的游泳，应该是加1分
```

**前提：** 昨天没有"游泳"相关的交易记录。

**期望输出：**
```json
{"status": "error", "reply": "包含「没有找到和'游泳'相关的记录」"}
```

**测试结果：** ⬜ 待测试 | confidence: HIGH

---

## 三、拒绝执行（Reject）测试

### TC-REJ-001: 测试关键词保护（P4）

**用户输入：**
```
测试消费
```

**期望输出：**
```json
{"intent": "reject", "reason": "包含测试关键词，拒绝执行"}
```

**测试结果：** ⬜ 待测试 | confidence: HIGH

**说明：** 旧系统"测试消费"导致真实扣30分。重构系统应在意图分类前过滤"测试"关键词。

---

### TC-REJ-002: undefined 消息处理（P4）

**用户输入：**
```
undefined
```

**期望输出：**
```json
{"intent": "reject", "reason": "无效输入，拒绝执行"}
```

**测试结果：** ⬜ 待测试 | confidence: HIGH

**说明：** 旧系统收到undefined导致NaN分污染。

---

## 四、查询（Query）测试

### TC-QRY-001: 查当前余额

**用户输入：**
```
现在多少分？
```

**期望输出：**
- `intent`: query
- `query_type`: simple
- `display`: "当前余额：X分"

**测试结果：** ⬜ 待测试 | confidence: HIGH

---

### TC-QRY-002: 查今日收支

**用户输入：**
```
今天加了多少分？
```

**期望输出：**
- `intent`: query
- `query_type`: simple → today
- `display`: 包含收入总额和支出总额

**测试结果：** ⬜ 待测试 | confidence: HIGH

---

### TC-QRY-003: 查本周统计

**用户输入：**
```
这周积分情况怎么样？
```

**期望输出：**
- `intent`: query
- `query_type`: simple → week
- `display`: 近7天汇总

**测试结果：** ⬜ 待测试 | confidence: MEDIUM

---

### TC-QRY-004: 查本月统计

**用户输入：**
```
这个月一共加了多少钱？
```

**期望输出：**
- `intent`: query
- `query_type`: simple → month
- `display`: 本月汇总

**测试结果：** ⬜ 待测试 | confidence: MEDIUM

**说明：** 用户说"加了多少钱"但应该理解为"加了多少分"，不是人民币元。

---

### TC-QRY-005: 语义查询——按项目汇总

**用户输入：**
```
口算一共加了多少分？
```

**期望输出：**
- `intent`: query
- `query_type`: semantic → SQL: `SELECT SUM(amount) FROM transactions WHERE type='income' AND description LIKE '%口算%'`
- 返回合理汇总值

**测试结果：** ⬜ 待测试 | confidence: MEDIUM

---

### TC-QRY-006: 语义查询——按行为类型查询

**用户输入：**
```
扣分最多的是哪个项目？
```

**期望输出：**
- `intent`: query
- `query_type`: semantic
- 返回合理的排序结果

**测试结果：** ⬜ 待测试 | confidence: LOW

**说明：** 这个查询需要LLM生成聚合排序SQL，复杂度较高。

---

### TC-QRY-007: 模糊查询——跨天统计

**用户输入：**
```
周二周三的口算有加吗？
```

**期望输出：**
- `intent`: query
- `query_type`: semantic
- 返回指定日期范围+项目的记录

**测试结果：** ⬜ 待测试 | confidence: LOW

**说明：** 跨天+按项目的组合语义查询，LLM需要理解"周二周三"=近两天的具体日期。

---

### TC-QRY-008: 空结果查询

**用户输入：**
```
围棋加了多少分？
```

**前提：** 系统中没有"围棋"相关的记录。

**期望输出：**
- `intent`: query
- `query_type`: semantic → 查到空结果
- `display`: "没有找到相关记录。"

**测试结果：** ⬜ 待测试 | confidence: HIGH

---

## 五、去重（Dedup）专项测试

### TC-DEDUP-001: 正常去重——完全相同消息

**测试步骤：**
1. 用 message_id="msg-001" 处理一条消息
2. 用相同的 message_id="msg-001" 再次处理

**期望输出（第一次）：** `status: "ok"`
**期望输出（第二次）：** `status: "skipped"`

**测试结果：** ⬜ 待测试 | confidence: HIGH

---

### TC-DEDUP-002: 不同 message_id 相同内容——不应去重

**测试步骤：**
1. 用 message_id="msg-a" 处理"口算加1分"
2. 用 message_id="msg-b" 处理"口算加1分"（相同内容不同ID）

**期望输出（两次均记账）：** 两条独立的 income 记录

**测试结果：** ⬜ 待测试 | confidence: HIGH

**说明：** 去重基于 message_id 而非内容。家长可能会在同一天发两次"口算加1分"。

---

### TC-DEDUP-003: 秒级并发去重

**测试步骤：**
1. 模拟同一秒收到4条消息，message_id不同
2. 期望全部正常记账

**测试结果：** ⬜ 待测试 | confidence: HIGH

---

## 汇总统计

| 维度 | 数量 | 占比 |
|------|------|------|
| 记账(record) | 27 | 55% |
| 调账(adjust) | 5 | 10% |
| 查询(query) | 8 | 16% |
| 拒绝(reject) | 2 | 4% |
| 去重(dedup) | 3 | 6% |
| 鼓励语 | 4 | 8% |
| **总计** | **49** | 100% |

| 时期分布 | 数量 | 说明 |
|---------|------|------|
| P1 盲测期 | 6 | 格式混乱、+0分 |
| P2 乱序期 | 8 | 小数截断、混合类型 |
| P3 范式期 | 6 | 调账、-号歧义、格式定型 |
| P4 秩序与崩坏期 | 7 | 去重失败、测试攻击、余额震荡 |
| P5 默契与遗忘期 | 7 | 结构化、重复记账、简写 |
| 通用(查询+去重) | 11 | 不特定于时期 |
| 旧系统Bug导致 | 4 | TC-009/010/019/026 |

---

## 已知问题/待办

- [ ] 测试脚本编写（test_runner.py）
- [ ] 真实LLM调用模式——需要 MiniMax API key
- [ ] 调账用例需要预置数据（模拟前一条记录才能触发匹配）
- [ ] 去重用例需要生成不同 message_id
- [ ] 鼓励语测试：验证 LLM 鼓励响应格式合理
- [ ] 币种混淆：Prompt 说 1元=100分，但"14.3积分"指"分"不是"元"
- [ ] SQL 注入防护：虽然家庭场景风险低，但作为治理案例需加白名单验证
