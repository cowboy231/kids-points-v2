# 🧪 从原始项目生产日志抽取的测试用例

> 数据来源：`openclaw-backup-20260507_235031/agents/kids-study/workspace/kids-points/logs/input.log`（3月24日~5月7日，1196行）
> 抽取原则：按五时期划分，每个时期选取不同类型、不同复杂度的原始用户输入
> 用途：kids-points-runtime 重构项目的端到端测试数据

---

## P1: 盲测期（3/24 - 3/28）

特征：第一条日志就是测试，格式混乱，早期 LLM 理解不稳定，+0分占比较高。

### TC-P1-001: 最早期基础记账
```json
{
  "input": "学习积分 测试 +1 分",
  "expected": {
    "intent": "record",
    "items": [{"type": "income", "amount": 1, "description": "测试"}]
  },
  "note": "第一行日志（3/24 15:33），系统最开始跑的测试。余额0.0分，说明代码刚上线无初始数据。"
}
```

### TC-P1-002: 消费扣分（含"积分消费"格式）
```json
{
  "input": "积分消费 2 分 - 早上把卷子发卷烂了",
  "expected": {
    "intent": "record",
    "items": [{"type": "expense", "amount": 2, "description": "早上把卷子发卷烂了"}]
  },
  "note": "最早期消费格式：\n1. 前缀 `积分消费` 标记支出\n2. 金额在最前面\n3. 用 `-` 分隔描述\n4. LLM 把 "积分消费 2"正确解析为 expense(-2)"
}
```

### TC-P1-003: 语义模糊「完成了汉字抄写2课」→ +0分
```json
{
  "input": "今天完成了汉字抄写 2 课",
  "expected": {
    "intent": "record",
    "items": [{"type": "income", "amount": 2, "description": "汉字抄写"}]
  },
  "note": "用户只说完成了任务没给分，早期LLM无法推断分数 → +0分。重构后应该支持从规则或历史推断默认分。"
}
```

### TC-P1-004: 首次多项目合并（补录格式）
```json
{
  "input": "补录 2026-03-25 积分：语文作业 +1 分，数学作业 +1 分，英语作业 +1 分，口算（没有全对）+1 分，家里写字作业 +1 分",
  "expected": {
    "intent": "record",
    "items": [
      {"type": "income", "amount": 1, "description": "语文作业"},
      {"type": "income", "amount": 1, "description": "数学作业"},
      {"type": "income", "amount": 1, "description": "英语作业"},
      {"type": "income", "amount": 1, "description": "口算（没有全对）"},
      {"type": "income", "amount": 1, "description": "家里写字作业"}
    ]
  },
  "note": "首次出现「补录」语义和批量多项目，5项全部解析成功。含「口算（没有全对）」的括号注释——不是所有+1分都是全对，LLM需要区分。"
}
```

### TC-P1-005: ""-""号歧义（消费格式不稳定期）
```json
{
  "input": "学习积分 测试减 -1 分",
  "expected": {
    "intent": "record",
    "items": [{"type": "expense", "amount": 1, "description": "测试减"}]
  },
  "note": "用户说「测试减 -1 分」，这里 `-1` 应该扣分但LLM判定为income？日志显示→最终余额0.0分（没变），说明代码层有重复检查。但LLM可能把"-1"的"-"和"减"的"-"混淆。这是最早期的符号歧义问题。"
}
```

### TC-P1-006: 自然语言描述（非结构化）
```json
{
  "input": "昨天完成了语文作业 +1 分，完成了英语作业 +1 分",
  "expected": {
    "intent": "record",
    "items": [
      {"type": "income", "amount": 1, "description": "语文作业"},
      {"type": "income", "amount": 1, "description": "英语作业"}
    ]
  },
  "note": "早期的「昨天完成了」结构，首次出现却被错误解析为 +0分（3/28 12:41:24），重发同一条就正确了（12:41:49）。说明LLM解析不稳定。"
}
```

---

## P2: 乱序期（3/29 - 4/4）

特征：格式开始统一（换行、编号），但小数处理出问题（2.5→2.导致扣5分），数据错误开始积累。

### TC-P2-001: 语义理解「读了两篇，加5分」
```json
{
  "input": "ABC Reading 读了两篇，加 5 分",
  "expected": {
    "intent": "record",
    "items": [{"type": "income", "amount": 5, "description": "ABC Reading 读了两篇"}]
  },
  "note": "用户说「读了两篇，加5分」这种描述完成数量+奖励金额的自然语言。也是在3/29首次被解析为+0分后重发才正确。"
}
```

### TC-P2-002: 多项目+消费混合（用换行/编号）
```json
{
  "input": "今天积分记录：\n1. 语文抄写：加 1 分\n2. 口算：加 1 分（未全对）\n3. ABC Reading：加 2 分\n4. 手工材料消费 1 分",
  "expected": {
    "intent": "record",
    "items": [
      {"type": "income", "amount": 1, "description": "语文抄写"},
      {"type": "income", "amount": 1, "description": "口算（未全对）"},
      {"type": "income", "amount": 2, "description": "ABC Reading"},
      {"type": "expense", "amount": 1, "description": "手工材料消费"}
    ]
  },
  "note": "4/1出现的结构化格式：换行+编号+混合类型。日志显示这次LLM解析失败——第4项被当成收入+1（而不是消费扣1），说明当时还不能正确处理混合类型。这是LLM能力升级后的重点测试用例。"
}
```

### TC-P2-003: 小数截断灾难（2.5 → 2.）
```json
{
  "input": "今天做语文的拼音练习，加 1.5 分",
  "expected": {
    "intent": "record",
    "items": [{"type": "income", "amount": 1.5, "description": "语文的拼音练习"}]
  },
  "note": "首次出现小数（4/5），日志显示解析为 `加 1.`，缺少 `5` → LLM拿到 `1.` → 被当做"1" → 但实际竟被扣5分（最终余额 91.8分）。这是严重的数据错误Bug。"
}
```

### TC-P2-004: 小数截断在消费侧的镜像bug
```json
{
  "input": "积分记录，消费了一片口香糖，扣 0.5 分",
  "expected": {
    "intent": "record",
    "items": [{"type": "expense", "amount": 0.5, "description": "消费了一片口香糖"}]
  },
  "note": "同样的小数截断！「扣 0.」→ 被当做扣0分处理，但日志显示实际被扣了5分（余额从 91.8→83.3）。镜像Bug。"  
}
```

### TC-P2-005: 大额消费（"花了很多分"）
```json
{
  "input": "今天自己买了一个小置物架，花了 29.8 分",
  "expected": {
    "intent": "record",
    "items": [{"type": "expense", "amount": 29.8, "description": "买小置物架"}]
  },
  "note": "4/6：大额小数金额消费，29.8分不会触发小数截断（两位小数→完全保留），逻辑正常。但28.9和29.8这两种写法在JS解析中是否稳定需要关注。"
}
```

### TC-P2-006: 多事件并发（4条消息同一时间戳）
```json
{
  "input": "完成了语文的所有单元的改错",
  "expected": {
    "intent": "record",
    "items": [{"type": "income", "amount": 2, "description": "完成了语文的所有单元的改错"}]
  },
  "note": "4/8 00:34:38 同一秒发送4条消息（语文改错+口算+拼写+跳绳）。LLM准确分配了不同分数（+2/+1/+1/+1）。秒级并发消息处理的正确性和事务一致性是测试重点。"
}
```

### TC-P2-007: 隐性扣分（不写"积分消费"）
```json
{
  "input": "早上起床拖拖拉拉",
  "expected": {
    "intent": "record",
    "items": [{"type": "expense", "amount": 1, "description": "早上起床拖拖拉拉"}]
  },
  "note": "用户没有写「积分消费」或「扣分」，只说事实。LLM需要理解「拖拖拉拉」是坏行为→扣分。语义理解的典型case。"
}
```

### TC-P2-008: 多重语义（学校作业+托管班双倍）
```json
{
  "input": "学校作业在托管班完成，给双倍加 4 分",
  "expected": {
    "intent": "record",
    "items": [{"type": "income", "amount": 4, "description": "学校作业在托管班完成，双倍"}]
  },
  "note": "用户提到了「双倍」这个乘数概念，LLM需要理解「双倍」= base × 2。金额已是运算后的结果（4分），但LLM不应该再次乘以2。"
}
```

---

## P3: 范式期（4/4 - 4/22）

特征：格式稳定（`项目: 分数`），-号歧义爆发（减分变加分），调账首次出现。

### TC-P3-001: 简单记账（稳定格式期）
```json
{
  "input": "口算 +1 分",
  "expected": {
    "intent": "record",
    "items": [{"type": "income", "amount": 1, "description": "口算"}]
  },
  "note": "4/22的极简格式，只写「项目 +N 分」。后期用户已经形成固定表达习惯。"
}
```

### TC-P3-002: 调账（首次出现）
```json
{
  "input": "调账：修正看动画片扣分错误（应扣 -5 分但扣了 -10 分，调账 +5 分）",
  "expected": {
    "intent": "adjust",
    "items": [{"type": "adjustment", "amount": 5, "description": "修正看动画片扣分错误"}]
  },
  "note": "4/13首次调账操作，用户描述了「多扣了，要补回」的完整逻辑。LLM需要从`应扣-5但扣了-10`推算出`调账+5`。这是调账流程的关键case。"
}
```

### TC-P3-003: "-"负号歧义（致命Bug）
```json
{
  "input": "吃口香糖 -1 分",
  "expected": {
    "intent": "record",
    "items": [{"type": "expense", "amount": 1, "description": "吃口香糖"}]
  },
  "note": "4/12：用户说「吃口香糖 -1 分」，`-1`表示扣1分。但LLM错误解析为+1分（把`-1`当成`减号+1`=加1）。直到「积分消费 吃口香糖花了 1 分」才正确扣除。这是多次出现的`-`号歧义Bug。"
}
```

### TC-P3-004: 补录（"昨天"时间语义）
```json
{
  "input": "昨天语文写字加 3 分，因为还改了课上要写错的字",
  "expected": {
    "intent": "record",
    "items": [{"type": "income", "amount": 3, "description": "语文写字，还改了课上要写错的字"}]
  },
  "note": "用户说「昨天」表示补录，附带了原因说明。LLM需要从语义中正确提取分数，而不是把描述当成绩分依据。"
}
```

### TC-P3-005: 调账的二次小数截断
```json
{
  "input": "调账加 2.5 分，因为昨天动画片只看了一半",
  "expected": {
    "intent": "adjust",
    "items": [{"type": "adjustment", "amount": 2.5, "description": "动画片只看了一半"}]
  },
  "note": "4/15：调账小数金额2.5再次出现截断！日志显示提取到 `加 2.` → 实际加了5分。同一问题（小数截断）在调账场景再次出现。"
}
```

### TC-P3-006: "扣"写在末尾而非开头
```json
{
  "input": "晚睡觉减 2 分",
  "expected": {
    "intent": "record",
    "items": [{"type": "expense", "amount": 2, "description": "晚睡觉"}]
  },
  "note": "4/16：用户写「晚睡觉减 2 分」，用「减」而非「扣」。LLM需要理解「减」= expense。"
}
```

---

## P4: 秩序与崩坏期（4/22 - 4/28）

特征：去重失败（同条消息连续发 5 次均记账），测试攻击（"测试消费"导致余额 -100），余额震荡。

### TC-P4-001: 去重失败（同条消息 ×5）
```json
{
  "input": "在托管班完成学校课内作业加4分",
  "expected": {
    "intent": "record",
    "items": [{"type": "income", "amount": 4, "description": "在托管班完成学校课内作业"}]
  },
  "note": "4/27 连续5次发送完全相同的消息（12:37~12:39），系统每次都记账，余额从117.4→133.4，多入了16分。原始系统按input.log和balance.md双重检查去重，但在这里失败。这是去重逻辑的痛点case。"
}
```

### TC-P4-002: "积分"→"积分"混用
```json
{
  "input": "口算全对，4积分",
  "expected": {
    "intent": "record",
    "items": [{"type": "income", "amount": 4, "description": "口算全对"}]
  },
  "note": "4/28：用户使用了「4积分」而非「4分」。LLM需要理解二者等价，不存在「积分」= 1积分 ≠ 1分的歧义。"
}
```

### TC-P4-003: 测试攻击（"测试消费"）
```json
{
  "input": "测试消费",
  "expected": {
    "intent": "reject",
    "reason": "包含测试关键词，拒绝执行"
  },
  "note": "4/28 21:47:17 用户发了「测试消费」，系统真实扣了30分。紧接着发了 `undefined`（NaN分bug），再来一次「测试消费」余额变成-30.0。这是安全设计缺失——"测试"关键词应该触发沙箱模式或拒绝执行。"
}
```

### TC-P4-004: `undefined` 消息处理
```json
{
  "input": "undefined",
  "expected": {
    "intent": "reject",
    "reason": "无效输入，拒绝执行"
  },
  "note": "4/28 收到 `undefined`（通常是飞书消息解析失败产生的垃圾数据），系统日志显示 NaN分 → 余额污染。系统应该过滤掉这类输入。"
```

### TC-P4-005: 余额从-100.5分回到77.4分的诡异跳跃
```json
{
  "input": "积分消费买零食花了30分",
  "expected": {
    "intent": "record",
    "items": [{"type": "expense", "amount": 30, "description": "买零食"}]
  },
  "note": "4/28 22:07~22:11 之间余额从 -100.5 跳到 77.4（跳了 177.9 分），之后又到47.4→77.4来回跳跃。这是因为系统被测试攻击导致余额错乱后的恢复操作。作为测试数据，验证重构系统是否正确记录了这笔30分消费。"
}
```

### TC-P4-006: 同一条消息去重失败（测试+生产混用）
```json
{
  "input": "改学校错题加2分，ABC Reading加3分，英赛尔加2分。因为今天英赛尔放水了",
  "expected": {
    "intent": "record",
    "items": [
      {"type": "income", "amount": 2, "description": "改学校错题"},
      {"type": "income", "amount": 3, "description": "ABC Reading"},
      {"type": "income", "amount": 2, "description": "英赛尔"}
    ]
  },
  "note": "4/28 22:58:04 和 22:58:50 两条完全相同的消息，间隔46秒。第一次记账后余额没变（应+7但显示114.4即余额不变），第二次才正确增加7分到121.4。说明第一次被某种逻辑抑制了记账但没完全防住重复。"
}
```

### TC-P4-007: 混合加减在一条消息中
```json
{
  "input": "改学校错题加2分，ABC Reading加3分，英赛尔加2分。因为今天英赛尔放水了",
  "expected": {
    "intent": "record",
    "items": [
      {"type": "income", "amount": 2, "description": "改学校错题"},
      {"type": "income", "amount": 3, "description": "ABC Reading"},
      {"type": "income", "amount": 2, "description": "英赛尔"}
    ]
  },
  "note": "长消息+备注：「因为今天英赛尔放水了」是对某事做补充说明，不是记账项。LLM需区分什么是项、什么是备注。"
}
```

---

## P5: 默契与遗忘期（4/30 - 5/7）

特征：格式高度结构化（容错率极低），新Bug（同内容去重失败、余额跳跃、"方格训练"回滚），数据量开始下降。

### TC-P5-001: 修正语义（带括号说明）
```json
{
  "input": "昨天ABC Reading +2分（修正）",
  "expected": {
    "intent": "record",
    "items": [{"type": "income", "amount": 2, "description": "ABC Reading（修正）"}]
  },
  "note": "5/1：用户用「修正」标记补录，说明之前漏记或少记。系统应该记录为普通收入还是特殊的修正类型？需要设计策略。"
}
```

### TC-P5-002: 一条消息多个项目+简写
```json
{
  "input": "ABC加1分",
  "expected": {
    "intent": "record",
    "items": [{"type": "income", "amount": 1, "description": "ABC Reading"}]
  },
  "note": "5/1：用户简写成「ABC」而非完整「ABC Reading」。LLM需要把简写理解成完整的项目名。核心考察点：LLM的实体标准化能力。"
}
```

### TC-P5-003: 带单位「元」的语义识别
```json
{
  "input": "扣消费海苔卷14.3积分",
  "expected": {
    "intent": "record",
    "items": [{"type": "expense", "amount": 14.3, "description": "海苔卷"}]
  },
  "note": "5/7：用户用「14.3积分」替代「14.3分」，且前缀是「扣消费」而非标准格式。说明用户习惯不是固定的，LLM要根据语义理解。"
}
```

### TC-P5-004: 重复记账防御测试
```json
{
  "input": "口算：今天完成了两篇，都没全对，记2分",
  "expected": {
    "intent": "record",
    "items": [{"type": "income", "amount": 2, "description": "口算（两篇未全对）"}]
  },
  "note": "5/5 同一消息被发送了约14次（14:00~14:15），系统每次都成功记账，余额从136.5跳到170.5。这是最严重的重复记账灾难。原因可能是用户多次发送或网络重试。验证重构系统的processed_messages去重能否拦住。"
}
```

### TC-P5-005: 表情+消费混合
```json
{
  "input": "买冰激凌扣1分",
  "expected": {
    "intent": "record",
    "items": [{"type": "expense", "amount": 1, "description": "买冰激凌"}]
  },
  "note": "5/7：简单消费格式，无需前缀「积分消费」，用户已经知道系统能理解语义。"
}
```

### TC-P5-006: JSON格式的日志（新格式）
```json
{
  "input": "消费1级分，买糯米糍冰激凌",
  "expected": {
    "intent": "record",
    "items": [{"type": "expense", "amount": 1, "description": "买糯米糍冰激凌"}]
  },
  "note": "5/6起日志开始出现JSON格式记录，替换了之前的文本格式。原始输入是「消费1级分，买糯米糍冰激凌」——「1级分」可能是用户口误或飞书识别错误。测试LLM能否理解模糊表达。"
}
```

### TC-P5-007: 多类型混合（收入+支出同消息）
```json
{
  "input": "语文写字加3分，语文作文修辞手法加1分，晚睡扣2分",
  "expected": {
    "intent": "record",
    "items": [
      {"type": "income", "amount": 3, "description": "语文写字"},
      {"type": "income", "amount": 1, "description": "语文作文修辞手法"},
      {"type": "expense", "amount": 2, "description": "晚睡"}
    ]
  },
  "note": "5/6 23:40:25 出现的新格式——条消息中混合收入和支出，日志明确标记为 `type:\"mixed\"`。LLM需要正确区分哪些是加分哪些是扣分。"
}
```

---

## 汇总统计

| 维度 | 数量 | 说明 |
|------|------|------|
| 总用例 | 31 | 覆盖全部五时期 |
| P1 盲测期 | 6 | 格式混乱、+0分 |
| P2 乱序期 | 8 | 小数截断、混合类型 |
| P3 范式期 | 6 | 调账、-号歧义、格式定型 |
| P4 秩序与崩坏期 | 7 | 去重失败、测试攻击、余额震荡 |
| P5 默契与遗忘期 | 7 | 结构化、重复记账、简写 |
| 记账(record) | 25 | 占 81% |
| 调账(adjust) | 2 | 含一次小数截断失败 |
| 查询(query) | 0 | 无查询用例（日志不记录查询） |
| 拒绝(reject) | 2 | 测试攻击 + undefined |
| 应被去重但未被拦截的 | 3 | P4-001 ×5、P5-004 ×14、P2-006秒级并发 |

**待补充（需用户提供）：**
- 查询类测试数据（用户问"现在多少分"这类）
- 原始系统返回的正确回复（用于验证重构系统的输出一致性）

---

## 高价值 Bug 复现单

下面几个 Bug 在 input.log 中留下了完整轨迹，可以用于复现测试：

1. **小数截断「2.5→2.→扣5分」**（P2-003 + P2-004 + P3-005）
   - 同一类Bug出现3次，覆盖收入、支出、调账所有场景
   - 根因：LLM输出截断了小数末尾

2. **「」**负号歧义（P2-{need check} + P3-003/P3-006）
   - 「吃口香糖 -1 分」被当成+1分
   - 「晚睡觉减 2 分」用「减」而非「扣」

3. **同消息×14次重复记账**（P5-004）
   - 5/5 同一消息被系统连续写入14次
   - 最严重的重复记账灾难

4. **测试攻击保护缺失**（P4-003 + P4-004）
   - 「测试消费」导致真实扣30分
   - `undefined` 导致NaN分污染

5. **余额跳跃**（P4-005）
   - -100.5 → 77.4 跳跃177.9分
   - 之后又在47.4和77.4之间来回跳
