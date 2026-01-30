# ScriptRunner Architecture Documentation

## Overview

ScriptRunner is a text-based game engine that has been refactored to follow modern software architecture principles. The system supports running games defined in YAML scripts with DSL (Domain Specific Language) extensions.

## Core Architecture Principles

- **Dependency Injection**: Components are loosely coupled using a DI container
- **Single Responsibility**: Each class has a focused, single purpose
- **Plugin Architecture**: Extensible through plugins
- **Modular Design**: Components can be easily replaced or extended
- **Testability**: Comprehensive unit test coverage

## Component Architecture

### 1. Dependency Injection Container (`src/di/container.py`)

A simple service locator pattern implementation that manages component dependencies.

**Key Features:**
- Service registration and resolution
- Factory function support
- Singleton instance caching

### 2. Logging System (`src/logging/logger.py`)

Centralized logging configuration using Python's built-in logging module.

**Key Features:**
- Configurable log levels and handlers
- File and console output
- Structured logging

### 3. Configuration Management (`src/config/config.py`)

YAML-based configuration system for application settings.

**Key Features:**
- Dot notation access (e.g., `config.get('logging.level')`)
- Default configuration values
- Runtime configuration updates

### 4. Plugin System (`src/plugins/`)

Extensible plugin architecture for adding custom functionality.

**Plugin Types:**
- `CommandPlugin`: Custom game commands
- `UIPlugin`: Custom UI backends
- `ParserPlugin`: Parser extensions
- `EventPlugin`: Event handling
- `StoragePlugin`: Custom storage backends

### 5. UI Abstraction (`src/ui/`)

Multiple UI backend support with a common interface.

**Current Backends:**
- Console UI (`ConsoleRenderer`)

**Interface Methods:**
- `render_scene()`: Display scene content
- `get_player_choice()`: Get user input
- `show_message()`: Display messages
- `clear_screen()`: Clear display
- `render_status()`: Show player status

### 6. Execution Engine (`src/runtime/`)

Refactored from a monolithic class into specialized components:

- **SceneExecutor**: Handles scene execution and variable replacement
- **CommandExecutor**: Processes game commands and effects
- **ConditionEvaluator**: Evaluates conditional logic
- **ChoiceProcessor**: Manages player choices and navigation
- **InputHandler**: Processes natural language input

### 7. State Management (`src/state/state_manager.py`)

Enhanced with caching and performance optimizations.

**Features:**
- Variable and flag management
- Effect system with duration tracking
- Save/load functionality
- Performance caching
- Auto-save capabilities

### 8. Error Handling (`src/utils/exceptions.py`)

Custom exception hierarchy for better error categorization.

**Exception Types:**
- `GameError`: Game-related errors
- `ScriptError`: Script parsing errors
- `ConfigurationError`: Configuration issues
- `PluginError`: Plugin loading/execution errors
- `ExecutionError`: Runtime execution errors
- `UIError`: UI-related errors

## Application Flow

1. **Initialization** (`main.py`):
   - Setup logging and configuration
   - Initialize DI container
   - Register core services
   - Load plugins
   - Setup UI backend

2. **Game Loading**:
   - Parse YAML script
   - Initialize player state
   - Set starting scene

3. **Game Loop**:
   - Execute current scene
   - Render scene content
   - Process player input
   - Navigate to next scene

## Testing

Comprehensive unit test suite using pytest:

- `tests/test_state_manager.py`: State management tests
- Additional test files for other components

**Test Coverage Areas:**
- Component initialization
- Core functionality
- Error conditions
- Save/load operations
- Plugin integration

## Configuration

Default configuration (`config.yaml`):

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

## Plugin Development

### Creating a Custom Command Plugin

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

### Creating a Custom UI Backend

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

## Performance Optimizations

- **Caching**: StateManager includes result caching
- **Lazy Loading**: Components loaded on demand
- **Efficient Data Structures**: Optimized for game state operations
- **Modular Execution**: Reduced coupling improves performance

## Future Enhancements

- Additional UI backends (Web, GUI)
- Advanced plugin APIs
- Performance profiling tools
- Script validation and debugging tools
- Multi-language support
- Cloud save functionality

## Migration Guide

For existing ScriptRunner installations:

1. Update `main.py` to use new initialization pattern
2. Replace direct component instantiation with DI container
3. Update custom scripts to use new exception types
4. Migrate configuration to new YAML format
5. Test with existing game scripts

## API Reference

### Core Classes

- `Container`: Dependency injection container
- `Logger`: Logging utilities
- `Config`: Configuration management
- `PluginManager`: Plugin lifecycle management
- `ExecutionEngine`: Game execution coordination
- `StateManager`: Game state management
- `ScriptParser`: YAML/DSL script parsing

### Key Methods

- `Container.get()`: Resolve service instances
- `Logger.get_logger()`: Get named logger
- `Config.get()`: Retrieve configuration values
- `PluginManager.load_plugins()`: Load available plugins
- `ExecutionEngine.execute_scene()`: Run game scene
- `StateManager.save_game()`: Persist game state

This architecture provides a solid foundation for extending ScriptRunner with new features while maintaining code quality and testability.
