# ScriptRunner 架构文档

## 概述

ScriptRunner 是一个基于文本的游戏引擎，经过重构以遵循现代软件架构原则。该系统支持运行以 YAML 脚本定义的游戏，并带有 DSL（领域特定语言）扩展。

## 核心架构原则

- **依赖注入**：组件使用 DI 容器实现松耦合
- **单一职责**：每个类具有专注的单一目的
- **插件架构**：通过插件实现可扩展性
- **模块化设计**：组件可以轻松替换或扩展
- **可测试性**：全面的单元测试覆盖

## 组件架构

### 1. 依赖注入容器 (`src/di/container.py`)

一个简单的服务定位器模式实现，用于管理组件依赖。

**关键特性：**
- 服务注册和解析
- 工厂函数支持
- 单例实例缓存

### 2. 日志系统 (`src/logging/logger.py`)

使用 Python 内置日志模块的集中式日志配置。

**关键特性：**
- 可配置的日志级别和处理器
- 文件和控制台输出
- 结构化日志

### 3. 配置管理 (`src/config/config.py`)

基于 YAML 的应用程序设置配置系统。

**关键特性：**
- 点符号访问（例如 `config.get('logging.level')`）
- 默认配置值
- 运行时配置更新

### 4. 插件系统 (`src/plugins/`)

用于添加自定义功能的扩展插件架构。

**插件类型：**
- `CommandPlugin`：自定义游戏命令
- `UIPlugin`：自定义 UI 后端
- `ParserPlugin`：解析器扩展
- `EventPlugin`：事件处理
- `StoragePlugin`：自定义存储后端

### 5. UI 抽象 (`src/ui/`)

支持多个 UI 后端，具有通用接口。

**当前后端：**
- 控制台 UI (`ConsoleRenderer`)

**接口方法：**
- `render_scene()`：显示场景内容
- `get_player_choice()`：获取用户输入
- `show_message()`：显示消息
- `clear_screen()`：清除显示
- `render_status()`：显示玩家状态

### 6. 执行引擎 (`src/runtime/`)

从单体类重构为专门化组件：

- **SceneExecutor**：处理场景执行和变量替换
- **CommandExecutor**：处理游戏命令和效果
- **ConditionEvaluator**：评估条件逻辑
- **ChoiceProcessor**：管理玩家选择和导航
- **InputHandler**：处理自然语言输入

### 7. 状态管理 (`src/state/state_manager.py`)

增强了缓存和性能优化。

**特性：**
- 变量和标志管理
- 具有持续时间跟踪的效果系统
- 保存/加载功能
- 性能缓存
- 自动保存功能

### 8. 错误处理 (`src/utils/exceptions.py`)

用于更好错误分类的自定义异常层次结构。

**异常类型：**
- `GameError`：游戏相关错误
- `ScriptError`：脚本解析错误
- `ConfigurationError`：配置问题
- `PluginError`：插件加载/执行错误
- `ExecutionError`：运行时执行错误
- `UIError`：UI 相关错误

## 应用程序流程

1. **初始化** (`main.py`):
   - 设置日志和配置
   - 初始化 DI 容器
   - 注册核心服务
   - 加载插件
   - 设置 UI 后端

2. **游戏加载**:
   - 解析 YAML 脚本
   - 初始化玩家状态
   - 设置起始场景

3. **游戏循环**:
   - 执行当前场景
   - 渲染场景内容
   - 处理玩家输入
   - 导航到下一个场景

## 测试

使用 pytest 的全面单元测试套件：

- `tests/test_state_manager.py`：状态管理测试
- 其他组件的附加测试文件

**测试覆盖领域：**
- 组件初始化
- 核心功能
- 错误条件
- 保存/加载操作
- 插件集成

## 配置

默认配置 (`config.yaml`)：

```yaml
logging:
  level: INFO
  file: scriptrunner.log

game:
  save_file: game_save.json
  auto_save: true

ui:
  type: console
  clear_screen: true

plugins:
  enabled: []
  directory: plugins
```

## 插件开发

### 创建自定义命令插件

```python
from src.plugins.plugin_interface import CommandPlugin

class MyCommands(CommandPlugin):
    @property
    def name(self):
        return "my_commands"

    @property
    def version(self):
        return "1.0.0"

    def get_commands(self):
        return {
            "custom_action": {
                "description": "A custom game action",
                "parameters": ["target"]
            }
        }

    def execute_command(self, command_name, args):
        if command_name == "custom_action":
            # Implement custom logic
            pass
```

### 创建自定义 UI 后端

```python
from src.ui.ui_interface import UIBackend

class WebUIRenderer(UIBackend):
    def render_scene(self, scene_data):
        # Implement web-based rendering
        pass

    def get_player_choice(self):
        # Implement web input handling
        pass
```

## 性能优化

- **缓存**：StateManager 包含结果缓存
- **延迟加载**：按需加载组件
- **高效数据结构**：针对游戏状态操作优化
- **模块化执行**：减少耦合提高性能

## 迁移指南

对于现有 ScriptRunner 安装：

1. 更新 `main.py` 以使用新的初始化模式
2. 将直接组件实例化替换为 DI 容器
3. 更新自定义脚本以使用新的异常类型
4. 将配置迁移到新的 YAML 格式
5. 使用现有游戏脚本进行测试

## API 参考

### 核心类

- `Container`：依赖注入容器
- `Logger`：日志工具
- `Config`：配置管理
- `PluginManager`：插件生命周期管理
- `ExecutionEngine`：游戏执行协调
- `StateManager`：游戏状态管理
- `ScriptParser`：YAML/DSL 脚本解析

### 关键方法

- `Container.get()`：解析服务实例
- `Logger.get_logger()`：获取命名日志器
- `Config.get()`：检索配置值
- `PluginManager.load_plugins()`：加载可用插件
- `ExecutionEngine.execute_scene()`：运行游戏场景
- `StateManager.save_game()`：持久化游戏状态

此架构为扩展 ScriptRunner 新功能提供了坚实基础，同时保持代码质量和可测试性。
