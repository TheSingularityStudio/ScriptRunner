# ScriptRunner API 文档

## 概述

ScriptRunner 是一个基于文本的游戏引擎，使用 YAML 格式定义的领域特定语言 (DSL) 来创建互动故事和游戏。该引擎遵循清洁架构原则，具有适当的关注点分离。

## 核心组件

### Container (依赖注入)

`Container` 类为应用程序提供依赖注入支持。

#### 构造函数
```python
Container()
```

#### 方法

##### register(service_name: str, service: Any)
注册单例服务实例。
- **参数：**
  - `service_name` (str): 服务名称
  - `service` (Any): 服务实例

##### register_factory(service_name: str, factory: Callable)
注册用于创建服务的工厂函数。
- **参数：**
  - `service_name` (str): 服务名称
  - `factory` (Callable): 工厂函数

##### register_type(service_name: str, cls: Type)
注册类型以进行自动依赖解析。
- **参数：**
  - `service_name` (str): 服务名称
  - `cls` (Type): 要注册的类

##### get(service_name: str) -> Any
检索服务实例，如有必要则创建它。
- **参数：**
  - `service_name` (str): 服务名称
- **返回：** 服务实例
- **引发：** 如果服务未注册，则引发 ValueError

##### resolve(cls: Type) -> Any
解析并创建指定类型的实例，并注入依赖项。
- **参数：**
  - `cls` (Type): 要实例化的类
- **返回：** 注入依赖项的实例

##### has(service_name: str) -> bool
检查服务是否已注册。
- **参数：**
  - `service_name` (str): 服务名称
- **返回：** 如果已注册则为 True，否则为 False

### GameRunner

负责初始化和执行游戏的主要游戏运行器。

#### 构造函数
```python
GameRunner(container: Container)
```
- **参数：**
  - `container` (Container): DI 容器实例

#### 方法

##### run_game(script_file: str)
从指定的脚本文件运行游戏。
- **参数：**
  - `script_file` (str): YAML 脚本文件的路径
- **引发：**
  - ConfigurationError: 如果配置无效
  - ScriptError: 如果脚本解析失败
  - GameError: 如果游戏执行失败

### ApplicationInitializer

处理所有应用程序组件的初始化和注册。

#### 构造函数
```python
ApplicationInitializer(container: Container)
```
- **参数：**
  - `container` (Container): DI 容器实例

#### 方法

##### initialize()
初始化整个应用程序并注册所有组件。
- **引发：** 各种初始化错误

### ScriptParser

解析 YAML 脚本文件并提供对游戏数据的访问。

#### 构造函数
```python
ScriptParser()
```

#### 方法

##### load_script(file_path: str) -> Dict[str, Any]
加载并解析 YAML 脚本文件。
- **参数：**
  - `file_path` (str): 脚本文件的路径
- **返回：** 解析后的脚本数据
- **引发：** FileNotFoundError, ValueError, yaml.YAMLError

##### get_scene(scene_id: str) -> Dict[str, Any]
通过 ID 检索场景数据。
- **参数：**
  - `scene_id` (str): 场景标识符
- **返回：** 场景数据字典

##### get_start_scene() -> str
获取起始场景 ID。
- **返回：** 起始场景标识符

##### parse_player_command(input_text: str) -> Dict[str, Any]
将自然语言玩家输入解析为结构化命令。
- **参数：**
  - `input_text` (str): 玩家输入文本
- **返回：** 包含 'action'、'target' 等字段的解析命令字典

### StateManager

管理游戏状态，包括变量、标志和效果。

#### 构造函数
```python
StateManager(save_file: Optional[str] = None)
```
- **参数：**
  - `save_file` (Optional[str]): 保存文件的路径（默认："game_save.json"）

#### 方法

##### set_variable(key: str, value: Any)
设置游戏变量。
- **参数：**
  - `key` (str): 变量名称
  - `value` (Any): 变量值

##### get_variable(key: str, default=None) -> Any
获取游戏变量。
- **参数：**
  - `key` (str): 变量名称
  - `default` (Any): 如果未找到则使用默认值
- **返回：** 变量值

##### set_flag(flag: str)
设置游戏标志。
- **参数：**
  - `flag` (str): 标志名称

##### has_flag(flag: str) -> bool
检查标志是否已设置。
- **参数：**
  - `flag` (str): 标志名称
- **返回：** 如果标志已设置则为 True

##### set_current_scene(scene_id: str)
设置当前场景。
- **参数：**
  - `scene_id` (str): 场景标识符

##### apply_effect(effect_name: str, effect_data: Dict[str, Any])
应用 DSL 效果。
- **参数：**
  - `effect_name` (str): 效果名称
  - `effect_data` (Dict[str, Any]): 效果配置

##### get_active_effects() -> Dict[str, Dict[str, Any]]
获取所有活跃效果。
- **返回：** 活跃效果字典

##### update_effects()
更新效果状态（持续时间等）。

##### save_game()
将游戏状态保存到文件。

##### load_game() -> bool
从文件加载游戏状态。
- **返回：** 如果成功则为 True，否则为 False

### ExecutionEngine

协调运行时组件以执行游戏逻辑。

#### 构造函数
```python
ExecutionEngine(parser, state_manager, scene_executor, command_executor,
                condition_evaluator, choice_processor, input_handler,
                event_manager, effects_manager, state_machine_manager,
                meta_manager, random_manager)
```
- **参数：** 各种管理器和执行器实例

#### 方法

##### execute_scene(scene_id: str) -> Dict[str, Any]
执行场景并返回结果。
- **参数：**
  - `scene_id` (str): 要执行的场景
- **返回：** 场景执行结果

##### process_choice(choice_index: int) -> tuple[Optional[str], List[str]]
处理玩家选择。
- **参数：**
  - `choice_index` (int): 所选选项的索引
- **返回：** (next_scene, messages) 元组

##### process_player_input(input_text: str) -> Dict[str, Any]
处理自然语言玩家输入。
- **参数：**
  - `input_text` (str): 玩家输入
- **返回：** 处理结果

### PluginManager

管理插件的加载和生命周期。

#### 构造函数
```python
PluginManager(plugin_dir: str = 'plugins')
```
- **参数：**
  - `plugin_dir` (str): 包含插件的目录

#### 方法

##### load_plugins()
从插件目录加载所有可用插件。

##### register_plugin(name: str, plugin: PluginInterface)
注册插件实例。
- **参数：**
  - `name` (str): 插件名称
  - `plugin` (PluginInterface): 插件实例

##### get_plugin(name: str) -> PluginInterface
检索已注册的插件。
- **参数：**
  - `name` (str): 插件名称
- **返回：** 插件实例

##### shutdown_all()
关闭所有已注册的插件。

## 接口

### IScriptParser

脚本解析器的抽象接口。

#### 方法

##### load_script(file_path: str) -> Dict[str, Any]
加载和解析脚本的抽象方法。

##### get_scene(scene_id: str) -> Dict[str, Any]
获取场景数据的抽象方法。

##### get_start_scene() -> str
获取起始场景的抽象方法。

##### parse_player_command(input_text: str) -> Dict[str, Any]
解析玩家命令的抽象方法。

### PluginInterface

所有插件的基础接口。

#### 属性

##### name -> str
插件名称（抽象属性）。

##### version -> str
插件版本（抽象属性）。

#### 方法

##### initialize(context: Dict[str, Any]) -> bool
使用上下文初始化插件。
- **参数：**
  - `context` (Dict[str, Any]): 初始化上下文
- **返回：** 如果成功则为 True

##### shutdown()
关闭插件。

### 专用插件接口

#### CommandPlugin
为提供自定义命令的插件。

##### get_commands() -> Dict[str, Dict[str, Any]]
返回插件提供的自定义命令。

##### execute_command(command_name: str, args: Dict[str, Any]) -> Any
执行自定义命令。

#### UIPlugin
为提供自定义 UI 后端的插件。

##### get_ui_backends() -> Dict[str, type]
返回 UI 后端类。

#### EventPlugin
为处理游戏事件的插件。

##### on_scene_start(scene_id: str, context: Dict[str, Any])
场景开始时调用。

##### on_scene_end(scene_id: str, context: Dict[str, Any])
场景结束时调用。

##### on_choice_selected(choice_index: int, context: Dict[str, Any])
选择选项时调用。

##### on_game_start(context: Dict[str, Any])
游戏开始时调用。

##### on_game_end(context: Dict[str, Any])
游戏结束时调用。

#### StoragePlugin
为提供自定义存储后端的插件。

##### save_game(game_data: Dict[str, Any]) -> bool
保存游戏数据。

##### load_game() -> Optional[Dict[str, Any]]
加载游戏数据。

## 运行时组件接口

### ISceneExecutor
场景执行接口。

##### execute_scene(scene_id: str) -> Dict[str, Any]
执行场景。

### ICommandExecutor
命令执行接口。

##### execute_commands(commands: List[Dict[str, Any]])
执行命令列表。

##### execute_command(command: Dict[str, Any])
执行单个命令。

### IConditionEvaluator
条件评估接口。

##### evaluate_condition(condition: Optional[str]) -> bool
评估条件字符串。

### IChoiceProcessor
选择处理接口。

##### process_choice(choice_index: int) -> tuple[Optional[str], List[str]]
处理玩家选择。

##### get_available_choices() -> List[Dict[str, Any]]
获取可用选择。

### IInputHandler
输入处理接口。

##### process_player_input(input_text: str) -> Dict[str, Any]
处理玩家输入。

### IEventManager
事件管理接口。

##### check_scheduled_events()
检查预定事件。

##### check_reactive_events(trigger_type: str, **kwargs)
检查反应事件。

##### update_game_time(delta_time: float)
更新游戏时间。

##### trigger_player_action(action: str, **kwargs)
触发玩家动作。

### IEffectsManager
效果管理接口。

##### apply_effect(effect_name: str, target: Optional[str] = None) -> bool
应用效果。

##### remove_effect(effect_name: str) -> bool
移除效果。

##### update_effects()
更新效果。

##### get_active_effects(target: Optional[str] = None) -> Dict[str, Dict[str, Any]]
获取活跃效果。

##### has_effect(effect_name: str, target: Optional[str] = None) -> bool
检查效果。

##### get_effect_modifier(stat_name: str, target: Optional[str] = None) -> float
获取效果修饰符。

### IStateMachineManager
状态机管理接口。

##### load_state_machines()
加载状态机。

##### get_current_state(machine_name: str) -> Optional[str]
获取当前状态。

##### transition_state(machine_name: str, event: str) -> bool
转换状态。

### IMetaManager
元数据管理接口。

##### load_meta_data()
加载元数据。

##### get_meta_value(key: str) -> Any
获取元数据值。

##### set_meta_value(key: str, value: Any)
设置元数据值。

### IRandomManager
随机数生成和表格接口。

##### load_random_tables()
加载随机表格。

##### roll_dice(sides: int) -> int
掷骰子。

##### get_random_from_table(table_name: str) -> Any
从表格获取随机值。

## 使用示例

### 基本游戏执行
```python
from src.infrastructure.container import Container
from src.application.game_runner import GameRunner

# 创建 DI 容器
container = Container()

# 创建并运行游戏
game_runner = GameRunner(container)
game_runner.run_game("scripts/example_game.yaml")
```

### 自定义插件创建
```python
from src.infrastructure.plugin_interface import CommandPlugin

class MyPlugin(CommandPlugin):
    @property
    def name(self):
        return "my_plugin"

    @property
    def version(self):
        return "1.0.0"

    def initialize(self, context):
        # 初始化逻辑
        return True

    def shutdown(self):
        # 清理逻辑
        pass

    def get_commands(self):
        return {
            "custom_command": {
                "description": "一个自定义命令",
                "parameters": ["arg1", "arg2"]
            }
        }

    def execute_command(self, command_name, args):
        if command_name == "custom_command":
            # 执行自定义逻辑
            return "命令已执行"
```

## 错误处理

API 使用自定义异常来处理不同类型的错误：

- `ScriptError`: 脚本解析和验证错误
- `GameError`: 游戏执行错误
- `ConfigurationError`: 配置相关错误
- `ScriptRunnerException`: 所有 ScriptRunner 错误的基础异常

## 配置

配置通过 `Config` 类和 YAML 配置文件处理。主要配置领域包括：

- 日志设置
- 插件目录
- UI 后端选择
- 游戏保存位置

## DSL 参考

有关 ScriptRunner DSL 语法的详细信息，请参见：
- [DSL 语法手册](syntax_manual.md)
- [DSL 计划](dsl-plan.md)

## 测试

项目包含全面的单元测试。主要测试模块：

- `tests/test_script_parser.py`: 解析器功能
- `tests/test_execution_engine.py`: 运行时执行
- `tests/test_state_manager.py`: 状态管理
- `tests/test_command_executor.py`: 命令执行

运行测试：`python -m pytest tests/`
