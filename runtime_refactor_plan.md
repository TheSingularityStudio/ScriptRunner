重构Runtime模块的详细计划
信息收集
通过分析runtime模块的相关文件，我了解到当前架构：

interfaces.py: 定义了多个接口，如IExecutionEngine、ICommandExecutor、IEffectsManager等，用于抽象组件。
execution_engine.py: 作为协调器，注入各种管理器（如scene_executor、command_executor等）来执行游戏逻辑。
action_executor.py: 处理DSL动作，如set、add_flag、broadcast等，但这些动作部分依赖插件。
script_command_executor.py: 支持脚本驱动的命令执行，通过插件加载动作函数，命令行为在YAML脚本中定义。
当前问题：动作和效果依赖插件，runtime模块过于庞大，缺乏面向对象的脚本运作方式。

重构目标
让脚本像面向对象编程一样运作：具体动作、效果等功能全部在脚本中定义，不依赖插件。
Runtime只保留最核心的命令处理（如设置变量）和必要模块。
详细计划
1. 脚本对象化设计
脚本结构重构: 将脚本定义为类结构，每个脚本包含属性（variables）、方法（actions）、事件（events）。
动作封装: 动作不再通过插件注入，而是在脚本中直接定义为方法。
效果系统: 效果逻辑移到脚本中，通过脚本方法实现。
2. Runtime模块精简
保留核心: 只保留变量设置、条件评估、基本执行引擎。
移除依赖: 移除effects_manager、event_manager等复杂管理器，将其逻辑移到脚本。
接口简化: 更新interfaces.py，移除不必要的接口，保留核心接口。
3. 文件级更新计划
src/domain/runtime/interfaces.py:

移除IEffectsManager、IEventManager、IStateMachineManager、IMetaManager、IRandomManager等接口。
保留IExecutionEngine、ICommandExecutor、IConditionEvaluator、IChoiceProcessor、IInputHandler、IInteractionManager。
添加新接口如IScriptObject用于脚本对象。
src/domain/runtime/execution_engine.py:

移除effects_manager、event_manager等依赖注入。
简化execute_scene方法，专注于脚本对象执行。
src/domain/runtime/action_executor.py:

重构为ScriptActionExecutor，动作通过脚本对象方法调用。
移除插件依赖。
src/domain/runtime/script_command_executor.py:

重构为ScriptObjectExecutor，命令执行通过脚本对象方法。
移除plugin_manager依赖。
新增文件:

src/domain/runtime/script_object.py: 定义脚本对象基类，支持面向对象脚本。
src/domain/runtime/script_factory.py: 负责从YAML创建脚本对象实例。
4. 依赖文件更新
src/domain/parser/parser.py: 更新解析器，支持脚本对象结构。
src/application/game_runner.py: 更新游戏运行器，使用新的脚本对象执行方式。
scripts/: 更新示例脚本，采用面向对象结构。
5. 后续步骤
测试: 运行现有测试套件，确保重构后功能正常。
文档更新: 更新docs/architecture.md和docs/syntax_manual.md，反映新架构。
插件迁移: 将插件中的动作逻辑迁移到脚本中（可选，后续任务）。