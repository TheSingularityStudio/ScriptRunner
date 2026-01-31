# ScriptRunner API Documentation

## Overview

ScriptRunner is a text-based game engine that uses a Domain Specific Language (DSL) defined in YAML format to create interactive stories and games. The engine follows clean architecture principles with proper separation of concerns.

## Core Components

### Container (Dependency Injection)

The `Container` class provides dependency injection support for the application.

#### Constructor
```python
Container()
```

#### Methods

##### register(service_name: str, service: Any)
Registers a singleton service instance.
- **Parameters:**
  - `service_name` (str): Name of the service
  - `service` (Any): Service instance

##### register_factory(service_name: str, factory: Callable)
Registers a factory function for creating services.
- **Parameters:**
  - `service_name` (str): Name of the service
  - `factory` (Callable): Factory function

##### register_type(service_name: str, cls: Type)
Registers a type for automatic dependency resolution.
- **Parameters:**
  - `service_name` (str): Name of the service
  - `cls` (Type): Class to register

##### get(service_name: str) -> Any
Retrieves a service instance, creating it if necessary.
- **Parameters:**
  - `service_name` (str): Name of the service
- **Returns:** Service instance
- **Raises:** ValueError if service not registered

##### resolve(cls: Type) -> Any
Resolves and creates an instance of the specified type with dependencies injected.
- **Parameters:**
  - `cls` (Type): Class to instantiate
- **Returns:** Instance with dependencies injected

##### has(service_name: str) -> bool
Checks if a service is registered.
- **Parameters:**
  - `service_name` (str): Name of the service
- **Returns:** True if registered, False otherwise

### GameRunner

The main game runner responsible for initializing and executing games.

#### Constructor
```python
GameRunner(container: Container)
```
- **Parameters:**
  - `container` (Container): DI container instance

#### Methods

##### run_game(script_file: str)
Runs a game from the specified script file.
- **Parameters:**
  - `script_file` (str): Path to the YAML script file
- **Raises:**
  - ConfigurationError: If configuration is invalid
  - ScriptError: If script parsing fails
  - GameError: If game execution fails

### ApplicationInitializer

Handles the initialization and registration of all application components.

#### Constructor
```python
ApplicationInitializer(container: Container)
```
- **Parameters:**
  - `container` (Container): DI container instance

#### Methods

##### initialize()
Initializes the entire application and registers all components.
- **Raises:** Various initialization errors

### ScriptParser

Parses YAML script files and provides access to game data.

#### Constructor
```python
ScriptParser()
```

#### Methods

##### load_script(file_path: str) -> Dict[str, Any]
Loads and parses a YAML script file.
- **Parameters:**
  - `file_path` (str): Path to the script file
- **Returns:** Parsed script data
- **Raises:** FileNotFoundError, ValueError, yaml.YAMLError

##### get_scene(scene_id: str) -> Dict[str, Any]
Retrieves scene data by ID.
- **Parameters:**
  - `scene_id` (str): Scene identifier
- **Returns:** Scene data dictionary

##### get_start_scene() -> str
Gets the starting scene ID.
- **Returns:** Starting scene identifier

##### parse_player_command(input_text: str) -> Dict[str, Any]
Parses natural language player input into structured commands.
- **Parameters:**
  - `input_text` (str): Player input text
- **Returns:** Parsed command dictionary with 'action', 'target', etc.

### StateManager

Manages game state including variables, flags, and effects.

#### Constructor
```python
StateManager(save_file: Optional[str] = None)
```
- **Parameters:**
  - `save_file` (Optional[str]): Path for save file (default: "game_save.json")

#### Methods

##### set_variable(key: str, value: Any)
Sets a game variable.
- **Parameters:**
  - `key` (str): Variable name
  - `value` (Any): Variable value

##### get_variable(key: str, default=None) -> Any
Gets a game variable.
- **Parameters:**
  - `key` (str): Variable name
  - `default` (Any): Default value if not found
- **Returns:** Variable value

##### set_flag(flag: str)
Sets a game flag.
- **Parameters:**
  - `flag` (str): Flag name

##### has_flag(flag: str) -> bool
Checks if a flag is set.
- **Parameters:**
  - `flag` (str): Flag name
- **Returns:** True if flag is set

##### set_current_scene(scene_id: str)
Sets the current scene.
- **Parameters:**
  - `scene_id` (str): Scene identifier

##### apply_effect(effect_name: str, effect_data: Dict[str, Any])
Applies a DSL effect.
- **Parameters:**
  - `effect_name` (str): Effect name
  - `effect_data` (Dict[str, Any]): Effect configuration

##### get_active_effects() -> Dict[str, Dict[str, Any]]
Gets all active effects.
- **Returns:** Dictionary of active effects

##### update_effects()
Updates effect states (duration, etc.).

##### save_game()
Saves game state to file.

##### load_game() -> bool
Loads game state from file.
- **Returns:** True if successful, False otherwise

### ExecutionEngine

Coordinates runtime components to execute game logic.

#### Constructor
```python
ExecutionEngine(parser, state_manager, scene_executor, command_executor,
                condition_evaluator, choice_processor, input_handler,
                event_manager, effects_manager, state_machine_manager,
                meta_manager, random_manager)
```
- **Parameters:** Various manager and executor instances

#### Methods

##### execute_scene(scene_id: str) -> Dict[str, Any]
Executes a scene and returns the result.
- **Parameters:**
  - `scene_id` (str): Scene to execute
- **Returns:** Scene execution result

##### process_choice(choice_index: int) -> tuple[Optional[str], List[str]]
Processes a player choice.
- **Parameters:**
  - `choice_index` (int): Index of chosen option
- **Returns:** Tuple of (next_scene, messages)

##### process_player_input(input_text: str) -> Dict[str, Any]
Processes natural language player input.
- **Parameters:**
  - `input_text` (str): Player input
- **Returns:** Processing result

### PluginManager

Manages loading and lifecycle of plugins.

#### Constructor
```python
PluginManager(plugin_dir: str = 'plugins')
```
- **Parameters:**
  - `plugin_dir` (str): Directory containing plugins

#### Methods

##### load_plugins()
Loads all available plugins from the plugin directory.

##### register_plugin(name: str, plugin: PluginInterface)
Registers a plugin instance.
- **Parameters:**
  - `name` (str): Plugin name
  - `plugin` (PluginInterface): Plugin instance

##### get_plugin(name: str) -> PluginInterface
Retrieves a registered plugin.
- **Parameters:**
  - `name` (str): Plugin name
- **Returns:** Plugin instance

##### shutdown_all()
Shuts down all registered plugins.

## Interfaces

### IScriptParser

Abstract interface for script parsers.

#### Methods

##### load_script(file_path: str) -> Dict[str, Any]
Abstract method to load and parse scripts.

##### get_scene(scene_id: str) -> Dict[str, Any]
Abstract method to get scene data.

##### get_start_scene() -> str
Abstract method to get starting scene.

##### parse_player_command(input_text: str) -> Dict[str, Any]
Abstract method to parse player commands.

### PluginInterface

Base interface for all plugins.

#### Properties

##### name -> str
Plugin name (abstract property).

##### version -> str
Plugin version (abstract property).

#### Methods

##### initialize(context: Dict[str, Any]) -> bool
Initializes the plugin with context.
- **Parameters:**
  - `context` (Dict[str, Any]): Initialization context
- **Returns:** True if successful

##### shutdown()
Shuts down the plugin.

### Specialized Plugin Interfaces

#### CommandPlugin
For plugins that provide custom commands.

##### get_commands() -> Dict[str, Dict[str, Any]]
Returns custom commands provided by the plugin.

##### execute_command(command_name: str, args: Dict[str, Any]) -> Any
Executes a custom command.

#### UIPlugin
For plugins that provide custom UI backends.

##### get_ui_backends() -> Dict[str, type]
Returns UI backend classes.

#### EventPlugin
For plugins that handle game events.

##### on_scene_start(scene_id: str, context: Dict[str, Any])
Called when a scene starts.

##### on_scene_end(scene_id: str, context: Dict[str, Any])
Called when a scene ends.

##### on_choice_selected(choice_index: int, context: Dict[str, Any])
Called when a choice is selected.

##### on_game_start(context: Dict[str, Any])
Called when game starts.

##### on_game_end(context: Dict[str, Any])
Called when game ends.

#### StoragePlugin
For plugins that provide custom storage backends.

##### save_game(game_data: Dict[str, Any]) -> bool
Saves game data.

##### load_game() -> Optional[Dict[str, Any]]
Loads game data.

## Runtime Component Interfaces

### ISceneExecutor
Interface for scene execution.

##### execute_scene(scene_id: str) -> Dict[str, Any]
Executes a scene.

### ICommandExecutor
Interface for command execution.

##### execute_commands(commands: List[Dict[str, Any]])
Executes a list of commands.

##### execute_command(command: Dict[str, Any])
Executes a single command.

### IConditionEvaluator
Interface for condition evaluation.

##### evaluate_condition(condition: Optional[str]) -> bool
Evaluates a condition string.

### IChoiceProcessor
Interface for choice processing.

##### process_choice(choice_index: int) -> tuple[Optional[str], List[str]]
Processes a player choice.

##### get_available_choices() -> List[Dict[str, Any]]
Gets available choices.

### IInputHandler
Interface for input handling.

##### process_player_input(input_text: str) -> Dict[str, Any]
Processes player input.

### IEventManager
Interface for event management.

##### check_scheduled_events()
Checks scheduled events.

##### check_reactive_events(trigger_type: str, **kwargs)
Checks reactive events.

##### update_game_time(delta_time: float)
Updates game time.

##### trigger_player_action(action: str, **kwargs)
Triggers player actions.

### IEffectsManager
Interface for effects management.

##### apply_effect(effect_name: str, target: Optional[str] = None) -> bool
Applies an effect.

##### remove_effect(effect_name: str) -> bool
Removes an effect.

##### update_effects()
Updates effects.

##### get_active_effects(target: Optional[str] = None) -> Dict[str, Dict[str, Any]]
Gets active effects.

##### has_effect(effect_name: str, target: Optional[str] = None) -> bool
Checks for effects.

##### get_effect_modifier(stat_name: str, target: Optional[str] = None) -> float
Gets effect modifiers.

### IStateMachineManager
Interface for state machine management.

##### load_state_machines()
Loads state machines.

##### get_current_state(machine_name: str) -> Optional[str]
Gets current state.

##### transition_state(machine_name: str, event: str) -> bool
Transitions state.

### IMetaManager
Interface for metadata management.

##### load_meta_data()
Loads metadata.

##### get_meta_value(key: str) -> Any
Gets metadata value.

##### set_meta_value(key: str, value: Any)
Sets metadata value.

### IRandomManager
Interface for random number generation and tables.

##### load_random_tables()
Loads random tables.

##### roll_dice(sides: int) -> int
Rolls dice.

##### get_random_from_table(table_name: str) -> Any
Gets random value from table.

## Usage Examples

### Basic Game Execution
```python
from src.infrastructure.container import Container
from src.application.game_runner import GameRunner

# Create DI container
container = Container()

# Create and run game
game_runner = GameRunner(container)
game_runner.run_game("scripts/example_game.yaml")
```

### Custom Plugin Creation
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
        # Initialization logic
        return True

    def shutdown(self):
        # Cleanup logic
        pass

    def get_commands(self):
        return {
            "custom_command": {
                "description": "A custom command",
                "parameters": ["arg1", "arg2"]
            }
        }

    def execute_command(self, command_name, args):
        if command_name == "custom_command":
            # Execute custom logic
            return "Command executed"
```

## Error Handling

The API uses custom exceptions for different error types:

- `ScriptError`: Script parsing and validation errors
- `GameError`: Game execution errors
- `ConfigurationError`: Configuration-related errors
- `ScriptRunnerException`: Base exception for all ScriptRunner errors

## Configuration

Configuration is handled through the `Config` class and YAML configuration files. Key configuration areas include:

- Logging settings
- Plugin directories
- UI backend selection
- Game save locations

## DSL Reference

For detailed information about the ScriptRunner DSL syntax, see:
- [DSL Syntax Manual](syntax_manual.md)
- [DSL Plan](dsl-plan.md)

## Testing

The project includes comprehensive unit tests. Key test modules:

- `tests/test_script_parser.py`: Parser functionality
- `tests/test_execution_engine.py`: Runtime execution
- `tests/test_state_manager.py`: State management
- `tests/test_command_executor.py`: Command execution

Run tests with: `python -m pytest tests/`
