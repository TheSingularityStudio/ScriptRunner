"""
Unit tests for ScriptObject.
"""

import pytest
from src.domain.runtime.script_object import ScriptObject


class TestScriptObject:
    def test_init(self):
        """测试ScriptObject初始化。"""
        variables = {'health': 100}
        actions = {'attack': [{'set': 'health -= 10'}]}
        events = {'on_death': [{'log': 'Game Over'}]}

        script = ScriptObject(variables, actions, events)

        assert script.get_variable('health') == 100
        assert script.get_variable('unknown') is None

    def test_set_variable(self):
        """测试设置变量。"""
        script = ScriptObject()
        script.set_variable('score', 50)

        assert script.get_variable('score') == 50

    def test_execute_action(self):
        """测试执行动作。"""
        actions = {'attack': [{'set': 'damage=10'}], 'defend': [{'set': 'defense += 5'}]}
        script = ScriptObject(actions=actions)

        commands = script.execute_action('attack')
        assert len(commands) == 1
        assert commands[0]['set'] == 'damage=10'

        commands = script.execute_action('defend')
        assert len(commands) == 1

        commands = script.execute_action('unknown')
        assert commands == []

    def test_trigger_event(self):
        """测试触发事件。"""
        events = {'on_enter': [{'log': 'Welcome'}], 'on_exit': [{'set': 'exited=true'}]}
        script = ScriptObject(events=events)

        commands = script.trigger_event('on_enter')
        assert len(commands) == 1
        assert commands[0]['log'] == 'Welcome'

        commands = script.trigger_event('on_exit')
        assert len(commands) == 1

        commands = script.trigger_event('unknown')
        assert commands == []

    def test_empty_script_object(self):
        """测试空脚本对象。"""
        script = ScriptObject()

        assert script.get_variable('any') is None
        assert script.execute_action('any') == []
        assert script.trigger_event('any') == []
