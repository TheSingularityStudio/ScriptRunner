# ScriptRunner 脚本语法文档

## 概述

ScriptRunner 是一个基于文本的游戏引擎，支持两种脚本格式：**传统格式** 和 **DSL（领域特定语言）格式**。脚本使用 YAML 格式编写，可以定义游戏世界、场景、选择、对象、事件等游戏元素。

## 脚本格式

### 传统格式

传统格式是最简单的脚本格式，适合创建基本的选择式故事游戏。

#### 基本结构

```yaml
scenes:
  scene_id:
    text: "场景描述文本"
    choices:
      - text: "选择文本"
        next: "下一个场景ID"
        condition: "条件表达式"  # 可选
        commands:  # 可选
          - set_variable: {key: "变量名", value: "值"}
          - add_flag: "标志名"

start_scene: "起始场景ID"
```

#### 示例

```yaml
scenes:
  start:
    text: "你醒来发现自己在一个陌生的房间里。门是开着的。"
    choices:
      - text: "走出房间"
        next: "hallway"
      - text: "检查房间"
        next: "search_room"

  hallway:
    text: "你来到走廊上。走廊两边都是门。"
    choices:
      - text: "进入左边的门"
        next: "left_room"
        condition: "has_flag('searched_room')"
      - text: "进入右边的门"
        next: "right_room"

  search_room:
    text: "你在房间里找到了一把钥匙。"
    choices:
      - text: "拿起钥匙"
        next: "hallway"
        commands:
          - set_variable: {key: "has_key", value: true}
          - add_flag: "searched_room"

start_scene: "start"
```

#### 字段说明

- `scenes`: 场景定义（也可以使用 `locations`）
- `scene_id`: 场景唯一标识符
- `text`: 场景描述文本（也可以使用 `description`）
- `choices`: 玩家可选择的选项列表
- `text`: 选择显示文本
- `next`: 选择后跳转的场景ID
- `condition`: 选择显示条件（可选）
- `commands`: 选择执行的命令列表（可选）
- `start_scene`: 游戏起始场景ID

### DSL 格式

DSL（领域特定语言）格式提供了更高级的功能，支持对象定义、事件系统、状态机、效果系统等。

#### 基本结构

```yaml
game:
  title: "游戏标题"
  version: "1.0"
  author: "作者名"

world:
  start: "起始场景ID"
  description: "世界描述"

# 可选的 DSL 结构
define_object: {}      # 对象定义
event_system: {}       # 事件系统
command_parser: {}     # 命令解析器
random_system: {}      # 随机系统
state_machines: {}     # 状态机
effects: {}           # 效果系统
commands: {}          # 命令定义
interaction: {}       # 互动系统
meta: {}              # 元数据

# 场景定义（与传统格式相同）
scenes: {}
# 或
locations: {}
```

## DSL 结构详解

### define_object（对象定义）

用于定义游戏中的对象，如武器、物品、NPC 等。

```yaml
define_object:
  sword:
    type: "weapon"
    name: "铁剑"
    damage: 10
    description: "一把普通的铁剑"
    aliases: ["铁剑", "剑"]

  key:
    type: "item"
    name: "铜钥匙"
    description: "可以打开某些门的钥匙"
    usable: true

  goblin:
    type: "enemy"
    name: "哥布林"
    health: 20
    damage: 5
    loot_table: "goblin_loot"

  treasure_chest:
    type: "loot_table"
    items:
      - item: "gold"
        weight: 50
        count: [1, 10]
      - item: "sword"
        weight: 20
        count: 1
```

### event_system（事件系统）

定义游戏事件和触发条件。

```yaml
event_system:
  events:
    player_death:
      trigger: "health <= 0"
      actions:
        - type: "scene_change"
          scene: "game_over"
        - type: "message"
          text: "你死了！"

    item_found:
      trigger: "inventory_add"
      conditions:
        - "item.type == 'rare'"
      actions:
        - type: "message"
          text: "你找到了一件稀有物品！"

  scheduled_events:
    morning:
      time: "08:00"
      actions:
        - type: "message"
          text: "新的一天开始了。"
```

### command_parser（命令解析器）

定义如何解析玩家的自然语言输入。

```yaml
command_parser:
  verbs:
    take:
      patterns: ["拿", "拿起", "取", "捡起"]
      aliases: ["get", "pick"]
    use:
      patterns: ["使用", "用"]
      aliases: ["utilize"]
    attack:
      patterns: ["攻击", "打", "杀"]
      aliases: ["fight", "hit"]
    look:
      patterns: ["看", "查看", "观察"]
      aliases: ["examine", "inspect"]

  nouns:
    pronouns:
      它: "last_object"
      他: "last_character"
      她: "last_character"

    objects:
      剑: "sword"
      钥匙: "key"
      门: "door"
```

### random_system（随机系统）

定义随机表和随机事件。

```yaml
random_system:
  tables:
    goblin_loot:
      - item: "gold"
        weight: 60
        count: [1, 5]
      - item: "dagger"
        weight: 30
        count: 1
      - item: "potion"
        weight: 10
        count: 1

    weather:
      - result: "sunny"
        weight: 50
      - result: "rainy"
        weight: 30
      - result: "stormy"
        weight: 20

  dice:
    damage_dice: "1d6+2"
    treasure_dice: "2d10"
```

### state_machines（状态机）

定义游戏状态和状态转换。

```yaml
state_machines:
  quest_state:
    initial: "not_started"
    states:
      not_started:
        transitions:
          start_quest:
            target: "in_progress"
            conditions: ["has_item('quest_item')"]
      in_progress:
        transitions:
          complete_quest:
            target: "completed"
            actions:
              - type: "reward"
                item: "gold"
                amount: 100
      completed:
        transitions: {}

  game_phase:
    initial: "exploration"
    states:
      exploration:
        transitions:
          combat_start:
            target: "combat"
      combat:
        transitions:
          combat_end:
            target: "exploration"
```

### effects（效果系统）

定义游戏效果，如增益、减益等。

```yaml
effects:
  strength_buff:
    type: "temporary"
    duration: 5
    modifiers:
      strength: +2
    description: "力量增强"

  poison:
    type: "temporary"
    duration: 10
    damage_per_turn: 2
    description: "中毒状态"

  permanent_strength:
    type: "permanent"
    modifiers:
      strength: +1
    description: "永久力量提升"
```

### commands（命令定义）

定义自定义命令。

```yaml
commands:
  teleport:
    description: "传送到指定位置"
    parameters:
      - name: "location"
        type: "string"
        required: true
    execute:
      - set_current_scene: "{location}"
      - message: "你传送到 {location}"

  heal:
    description: "治疗玩家"
    parameters:
      - name: "amount"
        type: "number"
        default: 10
    execute:
      - modify_health: "+{amount}"
      - message: "恢复了 {amount} 点生命值"
```

### interaction（互动系统）

定义对象间的互动规则。

```yaml
interaction:
  rules:
    sword_door:
      objects: ["sword", "locked_door"]
      action: "use"
      result:
        - unlock_door: "door"
        - message: "你用剑撬开了门"

    key_door:
      objects: ["key", "locked_door"]
      action: "use"
      conditions: ["has_item('key')"]
      result:
        - unlock_door: "door"
        - remove_item: "key"
        - message: "你用钥匙打开了门"
```

### meta（元数据）

定义游戏元数据。

```yaml
meta:
  version: "1.0"
  author: "游戏作者"
  description: "游戏描述"
  tags: ["冒险", "文字游戏"]
  difficulty: "normal"
  estimated_time: "30分钟"
```

## 条件表达式

条件表达式用于控制选择的显示、事件的触发等。

### 基本语法

```yaml
# 变量检查
variable_name == "value"
variable_name != "value"
variable_name > 10
variable_name < 10
variable_name >= 10
variable_name <= 10

# 标志检查
has_flag("flag_name")
not has_flag("flag_name")

# 物品检查
has_item("item_name")
not has_item("item_name")

# 逻辑运算
condition1 and condition2
condition1 or condition2
not condition

# 函数调用
inventory_count() > 5
current_scene() == "room1"
```

### 示例

```yaml
choices:
  - text: "使用钥匙"
    next: "unlocked_room"
    condition: "has_item('key') and not has_flag('door_unlocked')"

  - text: "强行破门"
    next: "broken_door"
    condition: "get_variable('strength', 0) > 15"
```

## 命令系统

命令用于执行游戏逻辑，如设置变量、添加物品等。

### 内置命令

```yaml
commands:
  # 变量操作
  - set_variable: {key: "health", value: 100}
  - add_variable: {key: "score", value: 10}
  - multiply_variable: {key: "damage", value: 1.5}

  # 标志操作
  - add_flag: "completed_tutorial"
  - remove_flag: "in_combat"

  # 物品操作
  - add_item: "sword"
  - remove_item: "key"
  - equip_item: "armor"

  # 场景操作
  - set_current_scene: "new_location"
  - show_message: "欢迎来到新场景！"

  # 效果操作
  - apply_effect: "strength_buff"
  - remove_effect: "poison"

  # 随机操作
  - roll_dice: {table: "treasure", result_var: "loot"}
```

## 完整示例

### 传统格式示例

```yaml
scenes:
  start:
    text: "你是一个年轻的冒险者，刚刚进入了一个神秘的洞穴。"
    choices:
      - text: "向前走"
        next: "chamber"
      - text: "检查入口"
        next: "entrance_search"

  entrance_search:
    text: "你在入口处发现了一把生锈的剑。"
    choices:
      - text: "拿起剑"
        next: "start"
        commands:
          - add_item: "rusty_sword"
          - add_flag: "has_sword"
      - text: "离开"
        next: "start"

  chamber:
    text: "你进入了一个大房间，中央有一个宝箱。"
    choices:
      - text: "打开宝箱"
        next: "treasure"
        condition: "has_flag('has_sword')"
      - text: "离开房间"
        next: "exit"

start_scene: "start"
```

### DSL 格式示例

```yaml
game:
  title: "冒险者传说"
  version: "1.0"
  author: "游戏开发者"

world:
  start: "cave_entrance"
  description: "一个充满危险和宝藏的奇幻世界"

define_object:
  rusty_sword:
    type: "weapon"
    name: "生锈的剑"
    damage: 8
    description: "一把生锈但仍然锋利的剑"

  treasure_chest:
    type: "container"
    locked: true
    contents: ["gold", "potion"]

command_parser:
  verbs:
    take:
      patterns: ["拿", "拿起", "取"]
    attack:
      patterns: ["攻击", "打"]
    open:
      patterns: ["打开", "开"]

  nouns:
    objects:
      剑: "rusty_sword"
      宝箱: "treasure_chest"

effects:
  sword_buff:
    type: "temporary"
    duration: 3
    modifiers:
      damage: +3

locations:
  cave_entrance:
    description: "你站在洞穴入口，里面漆黑一片。"
    choices:
      - text: "进入洞穴"
        next: "main_chamber"
      - text: "离开"
        next: "exit_game"

  main_chamber:
    description: "你进入了大房间，看到一个宝箱。"
    choices:
      - text: "打开宝箱"
        next: "treasure_found"
        condition: "has_item('rusty_sword')"
        commands:
          - apply_effect: "sword_buff"
      - text: "离开"
        next: "cave_entrance"

  treasure_found:
    description: "宝箱里有很多金币！"
    choices:
      - text: "拿走金币"
        next: "exit_game"
        commands:
          - add_variable: {key: "gold", value: 100}
          - show_message: "你获得了100金币！"
```

## 最佳实践

1. **选择合适的格式**：简单游戏使用传统格式，复杂游戏使用DSL格式
2. **保持一致性**：在整个脚本中使用一致的命名约定
3. **使用条件**：合理使用条件来创建动态的游戏体验
4. **测试脚本**：使用ScriptRunner的测试功能验证脚本正确性
5. **模块化**：将大型脚本分解为多个文件，使用引用系统
6. **注释**：为复杂的逻辑添加YAML注释

## 故障排除

### 常见错误

1. **缩进错误**：YAML对缩进非常敏感，确保使用一致的缩进
2. **缺失字段**：传统格式必须有scenes/locations，DSL格式必须有game和world
3. **无效条件**：检查条件表达式的语法
4. **循环引用**：避免场景间的循环引用

### 调试技巧

1. 使用`--debug`模式运行游戏查看详细日志
2. 检查脚本语法使用内置的语法检查器
3. 逐步添加功能，每次只添加一个新特性
4. 使用测试文件验证脚本的各个部分

---

本文档涵盖了ScriptRunner脚本语法的主要功能。如有疑问，请参考API文档或示例代码。
