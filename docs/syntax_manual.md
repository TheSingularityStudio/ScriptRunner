# ScriptRunner 脚本语法手册

## 概述

ScriptRunner 使用基于 YAML 的领域特定语言 (DSL) 来定义脚本。这些脚本支持面向对象的执行方式，包括变量管理、动作执行和事件处理。

## 脚本结构

每个脚本都是一个 YAML 文档，必须包含以下顶级键：

### 必需键

- `name`: 脚本名称（字符串）
- `actions`: 动作定义（字典）
- `start_action`: 启动动作名称（字符串，必须在 actions 中存在）

### 可选键

- `variables`: 全局变量定义（字典）
- `events`: 事件处理器定义（字典）
- `includes`: 要包含的其他脚本文件（字符串或字符串列表）

## 详细语法

### 变量 (variables)

变量用于存储脚本执行过程中的数据。

```yaml
variables:
  health: 100
  score: 0
  player_name: "Hero"
  inventory: ["sword", "shield"]
```

变量支持以下类型：
- 字符串
- 数字（整数和浮点数）
- 布尔值
- 数组
- 对象（嵌套字典）

### 动作 (actions)

动作定义了脚本可以执行的操作序列。

```yaml
actions:
  greet:
    commands:
      - type: print
        message: "Hello, World!"
      - type: set_variable
        name: greeting_done
        value: true

  initialize:
    commands:
      - type: set_variable
        name: health
        value: 100
      - type: call_action
        action: greet
```

每个动作必须包含 `commands` 键，其值为命令列表。

#### 支持的命令类型

1. **print**: 输出消息
   ```yaml
   - type: print
     message: "要显示的消息"
   ```

2. **set_variable**: 设置变量值
   ```yaml
   - type: set_variable
     name: variable_name
     value: variable_value
   ```

3. **call_action**: 调用另一个动作
   ```yaml
   - type: call_action
     action: action_name
   ```

4. **condition**: 条件执行
   ```yaml
   - type: condition
     expression: "${health} > 50"
     then:
       - type: print
         message: "健康良好"
     else:
       - type: print
         message: "需要治疗"
   ```

### 事件 (events)

事件定义了在特定时机自动执行的动作。

```yaml
events:
  on_start:
    - type: call_action
      action: initialize

  on_damage:
    - type: set_variable
      name: health
      value: "${health} - 10"
    - type: condition
      expression: "${health} <= 0"
      then:
        - type: call_action
          action: game_over
```

支持的事件类型：
- `on_start`: 脚本启动时执行
- `on_end`: 脚本结束时执行
- 自定义事件名

### 包含 (includes)

允许脚本包含其他脚本文件，实现模块化。

```yaml
includes:
  - common_actions.yaml
  - game_logic.yaml
```

包含的文件路径可以是相对路径或绝对路径。包含的脚本内容会被合并到主脚本中，主脚本的定义优先。

## 表达式语法

在某些命令中可以使用表达式进行动态计算：

- 变量引用：`${variable_name}`
- 算术运算：`${health} + 10`
- 比较运算：`${score} > 100`
- 逻辑运算：`${health} > 0 and ${mana} > 0`

## 完整示例

```yaml
name: "冒险游戏"

variables:
  health: 100
  score: 0
  player_name: "冒险者"

actions:
  start_game:
    commands:
      - type: print
        message: "欢迎来到冒险游戏，${player_name}！"
      - type: set_variable
        name: game_started
        value: true
      - type: call_action
        action: show_menu

  show_menu:
    commands:
      - type: print
        message: "选择行动："
      - type: print
        message: "1. 探索"
      - type: print
        message: "2. 休息"
      - type: print
        message: "3. 查看状态"

  explore:
    commands:
      - type: print
        message: "你发现了宝藏！"
      - type: set_variable
        name: score
        value: "${score} + 50"

  rest:
    commands:
      - type: set_variable
        name: health
        value: "${health} + 20"
      - type: print
        message: "恢复了 20 点生命值"

  show_status:
    commands:
      - type: print
        message: "生命值：${health}"
      - type: print
        message: "分数：${score}"

start_action: start_game

events:
  on_start:
    - type: call_action
      action: start_game
```

## 验证规则

脚本在加载时会进行以下验证：

1. 脚本必须是字典格式
2. 必须包含 `name`、`actions`、`start_action` 键
3. `start_action` 必须在 `actions` 中存在
4. 每个动作必须包含 `commands` 键，且为列表格式
5. 变量（如果存在）必须是字典格式

## 最佳实践

1. 使用有意义的脚本名称和动作名称
2. 将复杂逻辑分解为多个小动作
3. 使用变量存储状态信息
4. 利用事件处理异步逻辑
5. 使用 includes 组织大型脚本
6. 在表达式中使用变量引用保持灵活性
