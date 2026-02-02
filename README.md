# ScriptRunner

一个基于文本的游戏引擎，使用 YAML 格式定义的领域特定语言 (DSL) 来创建互动故事和游戏。该引擎遵循清洁架构原则，具有适当的关注点分离。

## 概述

ScriptRunner 是一个简单的基于文本的游戏引擎，用于运行 YAML 脚本定义的游戏，支持 DSL 语法。它允许开发者通过 YAML 文件定义游戏世界、角色、事件和交互，而无需编写复杂的代码。

## 特性

- **YAML-based DSL**: 使用易读的 YAML 格式定义游戏逻辑
- **自然语言命令**: 支持中文自然语言输入，如"攻击哥布林"、"检查箱子"
- **事件系统**: 定时和反应式事件处理
- **随机生成**: 程序化内容生成和随机事件
- **状态管理**: 持久化游戏状态和效果系统
- **插件系统**: 可扩展的插件架构
- **清洁架构**: 清晰的代码组织和依赖注入

## 安装

### 要求

- Python 3.7+
- PyYAML

### 安装步骤

1. 克隆仓库：
   ```bash
   git clone https://github.com/TheSingularityStudio/ScriptRunner.git
   cd ScriptRunner
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

### 基本运行

运行默认游戏脚本：
```bash
python main.py
```

运行自定义脚本：
```bash
python main.py scripts/your_game.yaml
```

### 游戏脚本格式

游戏脚本使用 YAML 格式定义。查看 `scripts/main.yaml` 获取完整示例。

基本结构：
```yaml
game: "游戏标题"
world:
  start: "起始场景"
player:
  attributes:
    strength: 10
    health: 100
# ... 更多定义
locations:
  scene_id:
    description: "场景描述"
    choices:
      - text: "选择文本"
        next: "下一个场景"
```

## 示例

项目包含一个示例游戏 `scripts/main.yaml`（洞穴冒险），演示了以下特性：

- 洞穴入口和主室场景
- 哥布林敌人
- 战斗系统
- 物品交互
- 效果系统
- 随机事件和掉落

运行示例：
```bash
python main.py scripts/main.yaml
```

## 文档

- [DSL 语法手册](docs/syntax_manual.md) - 完整的 DSL 语法指南
- [架构文档](docs/architecture.md) - 系统架构说明

## 测试

运行测试套件：
```bash
python -m pytest tests/
```

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件获取详情。

## 致谢

- 感谢所有贡献者
- 灵感来源于各种文本冒险游戏引擎
