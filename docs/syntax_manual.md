# ScriptRunner DSL Syntax Manual

This manual describes the Domain Specific Language (DSL) for ScriptRunner, designed for high-freedom, instruction-driven text-based games. The DSL uses YAML format for readability and structure.

## Table of Contents
1. [Core Design Principles](#core-design-principles)
2. [Object Definition System](#object-definition-system)
3. [Scene and Environment Definition](#scene-and-environment-definition)
4. [Event and Response System](#event-and-response-system)
5. [Command Parser Rules](#command-parser-rules)
6. [Interaction System](#interaction-system)
7. [Random System](#random-system)
8. [State and Effects System](#state-and-effects-system)
9. [Advanced Features](#advanced-features)
10. [Complete Game Script Structure](#complete-game-script-structure)

## Core Design Principles

The DSL follows a two-layer structure:
- **Player Input Layer**: Natural language commands (e.g., "攻击哥布林", "检查箱子")
- **Game Logic Layer**: Structured DSL for objects, events, and behaviors

This separation allows for flexible player interaction while maintaining structured game logic.

## Object Definition System

Define game objects with properties, states, and behaviors.

```yaml
define_object:
  object_name:
    type: "creature|item|container|etc."
    name: "Display Name"
    aliases: ["alias1", "alias2"]  # For natural language recognition

    # State attributes
    states:
      - name: "health"
        value: 30
        min: 0
        max: 100
        type: "integer"

      - name: "hostile"
        value: true
        type: "boolean"

    # Interactive behaviors
    behaviors:
      attack:
        success: "你击中了{target}"
        failure: "你没能打中{target}"

      talk:
        responses: ["Response 1", "Response 2"]

    # Random properties
    random:
      health: "10-50"
      loot_table: "loot_table_name"
```

## Scene and Environment Definition

Define locations with descriptions, objects, and interactions.

```yaml
scene:
  id: "scene_id"
  name: "Scene Name"

  description: |
    {time_of_day}的{location}，{weather}。
    你能看到{visible_objects}。

  # Dynamic content variables
  variables:
    time_of_day: ["清晨", "正午", "黄昏", "深夜"]
    weather: ["细雨蒙蒙", "雾气弥漫", "月光皎洁"]

  objects:
    - ref: "object_name"
      count: "1-3"
      spawn_condition: "!player.stealth"

  exits:
    north: "next_scene_id"
    east: "another_scene_id"

  # Environmental effects
  effects:
    - type: "dim_light"
      modifier:
        perception: -20
        stealth: 10
```

## Event and Response System

Handle timed and reactive events.

```yaml
event_system:
  # Scheduled events
  scheduled_events:
    - trigger: "time > 1800"
      action: "spawn_werewolf"
      chance: 0.3

  # Reactive events
  reactive_events:
    - trigger: "player.action = 'search'"
      conditions:
        - "location = 'dark_forest'"
        - "perception_check > 15"
      actions:
        - "spawn_object: 'hidden_cache'"
        - "log: '你在树根下发现了一些东西...'"
```

## Command Parser Rules

Define how player input is interpreted.

```yaml
command_parser:
  verbs:
    attack:
      patterns: ["攻击", "打击", "砍", "杀"]
      requires: ["target"]
      aliases: ["fight", "hit"]

    examine:
      patterns: ["检查", "查看", "观察", "调查"]
      requires: ["object"]

  nouns:
    dynamic_match:
      - pattern: "(. )的(. )"
        capture: ["owner", "object"]

    pronouns:
      它: "last_target"
      这里: "current_location"
```

## Interaction System

Define complex interactions and physics.

```yaml
interaction:
  multi_step:
    craft_potion:
      steps:
        1:
          prompt: "你想要制作什么药水？"
          options: ["治疗药水", "力量药水"]
        2:
          prompt: "选择主要材料："
          validate: "item in inventory and item.type = 'herb'"
      result:
        success: "你成功制作了{potion_name}！"
        failure: "混合物发出奇怪的声音然后消失了..."

  physics:
    push:
      base_chance: 0.7
      modifiers:
        strength: "0.1 per point above 10"
        object_weight: "-0.05 per kg"
```

## Random System

Handle procedural generation and random events.

```yaml
random_system:
  tables:
    forest_encounters:
      type: "weighted"
      entries:
        - value: "nothing"
          weight: 40
        - value: "hostile_goblin"
          weight: 25
          condition: "!player.reputation.evil"

  procedural:
    dungeon_room:
      algorithm: "cellular_automata"
      parameters:
        size: "10x10"
        wall_density: 0.45
```

## State and Effects System

Manage game states and persistent effects.

```yaml
state_machines:
  day_night_cycle:
    states: ["dawn", "day", "dusk", "night"]
    transitions:
      - from: "night"
        to: "dawn"
        condition: "time > 240 && time < 300"
    effects:
      night:
        - "visibility: 0.3"
        - "monster_spawn_rate: 2.0"

effects:
  poisoned:
    duration: "5 turns"
    tick: "every turn"
    action: "health -= 5"
    message: "你感到毒液在体内蔓延..."
```

## Advanced Features

### Meta Programming
```yaml
meta:
  macros:
    is_combat_ready: >
      health > 0 and
      stamina > 10 and
      not has_status('stunned')

  dynamic_scripts:
    generate_quest:
      parameters: ["target", "reward"]
      template: |
        quest:
          objective: "击败{target}"
          reward: "{reward}"
```

## Complete Game Script Structure

A full game script includes:

```yaml
game: "Game Title"

world:
  start: "starting_scene"
  time_scale: "1 minute real = 10 minutes game"

player:
  attributes:
    strength: 10
    intelligence: 8
  skills:
    - name: "swordsmanship"
      base_attribute: "strength"

define_object: { ... }
event_system: { ... }
command_parser: { ... }
random_system: { ... }
effects: { ... }

locations:
  scene_id:
    description: "..."
    objects: [...]
    choices: [...]
```

## Implementation Notes

- All YAML files should be valid YAML syntax
- Use consistent indentation (2 spaces recommended)
- Variables in strings use {variable_name} syntax
- Conditions use logical operators: &&, ||, !, ==, >, <
- Random values use "min-max" format for ranges
- Optional parameters marked with ?

For more details, refer to the DSL plan in docs/dsl-plan.md.
