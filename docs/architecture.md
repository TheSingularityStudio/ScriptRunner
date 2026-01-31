# ScriptRunner 架构文档

## 概述

ScriptRunner 是一个专为文字游戏设计的脚本运行器。它允许开发者使用 YAML 格式编写游戏脚本，支持自定义 DSL（领域特定语言）语法，并通过控制台界面运行游戏。系统采用分层架构设计，确保代码的可维护性、可扩展性和可测试性。

### 主要功能

- **脚本解析**: 支持传统 YAML 格式和自定义 DSL 语法
- **游戏执行**: 协调各种运行时组件执行游戏逻辑
- **状态管理**: 维护游戏状态、玩家属性和效果
- **事件系统**: 支持定时事件和反应事件
- **效果系统**: 管理游戏效果和状态修正
- **随机系统**: 提供骰子投掷和随机表功能
- **控制台界面**: 简单的文本界面用于游戏交互

## 架构原则

ScriptRunner 遵循以下架构原则：

### 1. 分层架构 (Layered Architecture)

系统分为四个主要层级，每个层级有明确的职责：

- **领域层 (Domain)**: 核心业务逻辑和规则
- **应用层 (Application)**: 用例协调和应用逻辑
- **基础设施层 (Infrastructure)**: 外部依赖和技术实现
- **表示层 (Presentation)**: 用户界面和输入输出

### 2. 依赖倒置原则 (Dependency Inversion)

高层模块不依赖低层模块，都依赖抽象接口。通过依赖注入容器实现解耦。

### 3. 接口抽象 (Interface Abstraction)

所有核心组件都通过抽象接口定义，确保实现的可替换性和可测试性。

### 4. 单一职责原则 (Single Responsibility)

每个类和模块都有明确的单一职责，便于维护和扩展。

## 架构层级详解

### 领域层 (Domain Layer)

**位置**: `src/domain/`

**职责**: 包含核心业务逻辑、实体和业务规则。

**主要组件**:

- **Parser** (`src/domain/parser/`): 脚本解析器
  - 支持 YAML 格式解析
  - DSL 语法解析
  - 脚本结构验证

- **Runtime** (`src/domain/runtime/`): 运行时组件
  - `ExecutionEngine`: 执行引擎，协调各组件
  - `SceneExecutor`: 场景执行器
  - `CommandExecutor`: 命令执行器
  - `ConditionEvaluator`: 条件评估器
  - `ChoiceProcessor`: 选择处理器
  - `InputHandler`: 输入处理器
  - `EventManager`: 事件管理器
  - `EffectsManager`: 效果管理器
  - `StateMachineManager`: 状态机管理器
  - `MetaManager`: 元数据管理器
  - `RandomManager`: 随机管理器

### 应用层 (Application Layer)

**位置**: `src/application/`

**职责**: 协调领域对象执行应用用例。

**主要组件**:

- **GameRunner**: 游戏运行器
  - 初始化应用组件
  - 加载游戏脚本
  - 初始化玩家
  - 运行游戏主循环

- **ApplicationInitializer**: 应用初始化器
  - 配置依赖注入容器
  - 注册服务和组件

### 基础设施层 (Infrastructure Layer)

**位置**: `src/infrastructure/`

**职责**: 处理外部依赖、技术框架和基础设施服务。

**主要组件**:

- **Container**: 依赖注入容器
  - 服务注册和解析
  - 构造函数注入支持
  - 工厂方法和类型注册

- **Logger**: 日志系统
  - 结构化日志记录
  - 多级别日志支持

- **StateManager**: 状态管理器
  - 游戏状态持久化
  - 变量和属性管理
  - 效果状态跟踪

- **PluginManager**: 插件管理器
  - 插件加载和卸载
  - 扩展点管理

### 表示层 (Presentation Layer)

**位置**: `src/presentation/`

**职责**: 处理用户界面和输入输出。

**主要组件**:

- **Renderer**: 渲染器
  - 场景渲染
  - 选择显示
  - 状态信息展示
  - 控制台界面管理

- **UI Interface**: UI 后端接口
  - 抽象界面定义
  - 支持不同 UI 实现

### 工具层 (Utils Layer)

**位置**: `src/utils/`

**职责**: 提供通用工具和辅助功能。

**主要组件**:

- **Exceptions**: 自定义异常类
- **SyntaxChecker**: 语法检查器

## 核心组件交互

### 数据流图

```
脚本文件 (YAML)
    ↓
Parser (解析)
    ↓
GameRunner (初始化)
    ↓
ExecutionEngine (协调执行)
    ↙        ↘
SceneExecutor  ChoiceProcessor
    ↓           ↓
Renderer ←──── InputHandler
    ↑           ↑
控制台输出 ← 玩家输入
```

### 依赖注入

系统使用依赖注入容器管理组件依赖：

```python
# 示例：ExecutionEngine 的依赖注入
execution_engine = ExecutionEngine(
    parser=parser,
    state_manager=state_manager,
    scene_executor=scene_executor,
    command_executor=command_executor,
    # ... 其他依赖
)
```

## 技术栈

- **编程语言**: Python 3.7+
- **脚本格式**: YAML
- **架构模式**: 分层架构 + 依赖注入
- **设计模式**: 抽象工厂、策略模式、观察者模式
- **用户界面**: 控制台 (Console)
- **日志系统**: Python logging
- **配置管理**: YAML 配置文件

## 部署和使用

### 系统要求

- Python 3.7 或更高版本
- 支持的操作系统: Windows, macOS, Linux

### 安装

```bash
pip install -r requirements.txt
```

### 运行游戏

```bash
python main.py [脚本文件路径]
```

如果不指定脚本文件，将使用默认脚本 `scripts/example_game.yaml`。

### 脚本开发

游戏脚本使用 YAML 格式，支持两种模式：

1. **传统格式**: 简单的场景-选择结构
2. **DSL 格式**: 高级语法，支持对象定义、事件系统、状态机等

详细语法请参考 `docs/syntax_manual.md`。

## 扩展性

### 添加新组件

1. 在 `src/domain/runtime/interfaces.py` 中定义接口
2. 在相应层级实现具体类
3. 通过依赖注入容器注册
4. 在初始化器中配置依赖关系

### 插件系统

系统支持插件扩展：

- 在 `plugins/` 目录放置插件
- 实现 `PluginInterface`
- 通过 `PluginManager` 加载

### UI 扩展

表示层抽象设计允许添加新的 UI 后端：

- 实现 `UIBackend` 接口
- 在容器中注册新的渲染器

## 测试策略

- **单元测试**: `tests/` 目录下的各个组件测试
- **集成测试**: 端到端脚本执行测试
- **测试覆盖**: 核心业务逻辑 80%+ 覆盖率

## 性能考虑

- **内存管理**: 状态管理器优化内存使用
- **执行效率**: 条件评估和命令执行优化
- **可扩展性**: 组件化设计支持水平扩展

## 总结

ScriptRunner 的架构设计注重可维护性、可扩展性和可测试性。通过分层架构和依赖注入，系统实现了高度的解耦和灵活性。DSL 语法支持使得脚本编写更加直观和强大，为文字游戏开发提供了坚实的技术基础。
