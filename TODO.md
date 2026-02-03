# Runtime Module Refactoring Fixes

## 1. Simplify ExecutionEngine
- [ ] Remove unnecessary dependencies (interaction_manager, script_factory, action_executor)
- [ ] Keep core components: parser, state_manager, scene_executor, command_executor, condition_evaluator, choice_processor, input_handler
- [ ] Update ExecutionEngine initialization

## 2. Remove Dual Execution Mode
- [ ] Make script_object mandatory in all executors
- [ ] Remove conditional logic (if self.script_object) in SceneExecutor
- [ ] Remove fallback to traditional commands

## 3. Refactor Executor Responsibilities
- [ ] Create CoreCommandExecutor for basic commands (set variables)
- [ ] Update ScriptObjectExecutor to focus on script-specific commands (action, event)
- [ ] Remove builtin action fallbacks in ScriptActionExecutor

## 4. Simplify Interface Layer
- [ ] Remove unnecessary interfaces (IInteractionManager)
- [ ] Simplify IExecutionEngine interface

## 5. Ensure Consistent Script Object Integration
- [ ] Make all executors depend on script_object
- [ ] Remove compatibility with traditional command structures

## Dependent Files to Update
- [ ] src/domain/runtime/execution_engine.py
- [ ] src/domain/runtime/scene_executor.py
- [ ] src/domain/runtime/script_object_executor.py
- [ ] src/domain/runtime/script_action_executor.py
- [ ] src/domain/runtime/interfaces.py
- [ ] src/application/game_runner.py (if needed)

## Testing
- [ ] Run tests to ensure fixes work
- [ ] Update tests if necessary
