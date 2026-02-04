# ScriptRunner 脚本语法手册 v2.0

## 概述

ScriptRunner 使用基于 YAML 的领域特定语言 (DSL) 来定义脚本。这些脚本支持面向对象的执行方式，包括变量管理、动作执行和事件处理。新版本的语法提供了更一致、更强大的命令结构和表达式系统。

## 脚本结构

每个脚本都是一个 YAML 文档，必须包含以下顶级键：

### 必需键

- `name`: 脚本名称（字符串）
- `actions`: 动作定义（字典）
- `start_action`: 启动动作名称（字符串，必须在 actions 中存在）

### 可选键

- `variables`: 全局变量定义（字典，带类型提示）
- `events`: 事件处理器定义（字典，支持参数化）
- `includes`: 要包含的其他脚本文件（字典或列表，支持命名空间）

## 详细语法

### 变量 (variables)

变量用于存储脚本执行过程中的数据，支持类型提示以提高类型安全。

```yaml
variables:
  health: {value: 100, type: int}
  score: {value: 0, type: int}
  player_name: {value: "Hero", type: str}
  inventory: {value: ["sword", "shield"], type: array}
  player_stats: {value: {level: 1, exp: 0}, type: object}
```

支持的类型：
- `int`: 整数
- `float`: 浮点数
- `str`: 字符串
- `bool`: 布尔值
- `array`: 数组
- `object`: 对象（嵌套字典）

### 动作 (actions)

动作定义了脚本可以执行的操作序列。所有命令使用统一的 YAML 映射结构。

```yaml
actions:
  greet:
    commands:
      - print: {message: "Hello, World!"}
      - set_variable: {name: greeting_done, value: true}

  initialize:
    commands:
      - set_variable: {name: health, value: 100}
      - call_action: {action: greet}
```

每个动作必须包含 `commands` 键，其值为命令列表。

#### 支持的命令类型

1. **print**: 输出消息
   ```yaml
   - print: {message: "要显示的消息"}
   ```

2. **set_variable**: 设置变量值
   ```yaml
   - set_variable: {name: variable_name, value: variable_value}
   ```

3. **call_action**: 调用另一个动作
   ```yaml
   - call_action: {action: action_name}
   ```

4. **condition**: 条件执行
   ```yaml
   - condition:
       expression: "{{health}} > 50"
       then:
         - print: {message: "健康良好"}
       else:
         - print: {message: "需要治疗"}
   ```

5. **for**: 循环执行
   ```yaml
   - for:
       item: item_var
       in: inventory
       do:
         - print: {message: "物品：{{item_var}}"}
   ```

6. **while**: 条件循环
   ```yaml
   - while:
       condition: "{{health}} < 100"
       do:
         - set_variable: {name: health, value: "{{health + 10}}"}
   ```

7. **prompt_input**: 用户输入提示
   ```yaml
   - prompt_input:
       message: "请输入你的名字："
       variable: player_name
   ```

8. **try_catch**: 错误处理
   ```yaml
   - try_catch:
       try:
         - set_variable: {name: result, value: "{{100 / 0}}"}
       catch:
         - print: {message: "发生错误！"}
   ```

9. **log**: 日志记录
   ```yaml
   - log: {level: info, message: "游戏开始"}
   ```

10. **assert**: 断言检查
    ```yaml
    - assert: {condition: "{{health > 0}}", message: "生命值不能为负"}
    ```

### 事件 (events)

事件定义了在特定时机自动执行的动作，支持参数化。

```yaml
events:
  on_start:
    - call_action: {action: initialize}
    - call_action: {action: greet}

  on_damage(amount):
    - set_variable: {name: health, value: "{{health - amount}}"}
    - condition:
        expression: "{{health <= 0}}"
        then:
          - call_action: {action: game_over}

  on_level_up(new_level):
    - print: {message: "升级到 {{new_level}} 级！"}
    - set_variable: {name: level, value: new_level}
```

支持的事件类型：
- `on_start`: 脚本启动时执行
- `on_end`: 脚本结束时执行
- 自定义事件名（可带参数）

### 包含 (includes)

允许脚本包含其他脚本文件，实现模块化，支持命名空间。

```yaml
includes:
  - file: common_actions.yaml
  - file: game_logic.yaml
    as: game
  - file: utils.yaml
    import: [helper_function, constants]
```

包含的文件路径可以是相对路径或绝对路径。支持以下选项：
- `file`: 文件路径
- `as`: 命名空间别名
- `import`: 选择性导入（动作或变量列表）

## 表达式语法

在命令中使用双花括号 `{{}}` 包围的表达式进行动态计算：

- 变量引用：`{{variable_name}}`
- 算术运算：`{{health + 10}}`
- 比较运算：`{{score > 100}}`
- 逻辑运算：`{{health > 0 and mana > 0}}`
- 函数调用：`{{len(inventory)}}`, `{{random(1, 10)}}`
- 数组操作：`{{inventory[0]}}`, `{{inventory + ['new_item']}}`
- 条件表达式：`{{health > 50 ? '健康' : '虚弱'}}`

支持的内置函数：
- `len(array)`: 数组长度
- `random(min, max)`: 随机数
- `concat(str1, str2)`: 字符串连接
- `contains(array, item)`: 检查包含
- `sum(array)`: 数组求和
- `max(array)`: 数组最大值
- `min(array)`: 数组最小值

## 完整示例

```yaml
name: "冒险游戏 v2"

variables:
  health: {value: 100, type: int}
  score: {value: 0, type: int}
  player_name: {value: "冒险者", type: str}
  inventory: {value: [], type: array}

actions:
  start_game:
    commands:
      - print: {message: "欢迎来到冒险游戏，{{player_name}}！"}
      - set_variable: {name: game_started, value: true}
      - call_action: {action: show_menu}

  show_menu:
    commands:
      - print: {message: "选择行动："}
      - print: {message: "1. 探索"}
      - print: {message: "2. 休息"}
      - print: {message: "3. 查看状态"}

  explore:
    commands:
      - print: {message: "你发现了宝藏！"}
      - set_variable: {name: score, value: "{{score + 50}}"}
      - set_variable: {name: inventory, value: "{{inventory + ['gold_coin']}}"}

  rest:
    commands:
      - set_variable: {name: health, value: "{{health + 20}}"}
      - print: {message: "恢复了 20 点生命值"}

  show_status:
    commands:
      - print: {message: "生命值：{{health}}"}
      - print: {message: "分数：{{score}}"}
      - print: {message: "物品数量：{{len(inventory)}}"}
      - for:
          item: item
          in: inventory
          do:
            - print: {message: "- {{item}}"}

  game_over:
    commands:
      - print: {message: "游戏结束！最终分数：{{score}}"}

start_action: start_game

events:
  on_start:
    - call_action: {action: start_game}

  on_damage(amount):
    - set_variable: {name: health, value: "{{health - amount}}"}
    - condition:
        expression: "{{health <= 0}}"
        then:
          - call_action: {action: game_over}
```

## 验证规则

脚本在加载时会进行以下验证：

1. 脚本必须是字典格式
2. 必须包含 `name`、`actions`、`start_action` 键
3. `start_action` 必须在 `actions` 中存在
4. 每个动作必须包含 `commands` 键，且为列表格式
5. 每个命令必须是包含单个键的字典（统一结构）
6. 变量必须包含 `value` 和 `type` 键，`type` 必须是有效类型
7. 表达式中的变量引用必须存在
8. 事件参数必须正确定义

## 最佳实践

1. 使用有意义的脚本名称和动作名称
2. 将复杂逻辑分解为多个小动作
3. 使用类型提示的变量提高代码质量
4. 利用事件处理异步逻辑和外部触发
5. 使用 includes 和命名空间组织大型脚本
6. 在表达式中使用内置函数简化逻辑
7. 使用 try_catch 处理潜在错误
8. 使用 assert 添加运行时检查
9. 利用 for 和 while 循环处理集合和重复逻辑
10. 使用 prompt_input 创建交互式脚本
