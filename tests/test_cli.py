from __future__ import annotations

import argparse
import json
import os
import tempfile
import unittest

import _bootstrap  # noqa: F401

from loop_agent.cli import build_jsonl_observer, build_parser, execute, resolve_goal
from loop_agent.steps.registry import build_default_registry


class CliTests(unittest.TestCase):
    def test_should_parse_strategy(self) -> None:
        parser = build_parser(build_default_registry())
        args = parser.parse_args(['--goal', 'x', '--strategy', 'json_stub'])
        self.assertEqual(args.strategy, 'json_stub')

    def test_should_read_goal_from_utf8_file(self) -> None:
        parser = build_parser(build_default_registry())
        with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8', suffix='.txt') as file:
            file.write('目标')
            path = file.name
        try:
            args = parser.parse_args(['--goal-file', path])
            self.assertEqual(resolve_goal(args), '目标')
        finally:
            os.remove(path)

    def test_should_parse_json_output_options(self) -> None:
        parser = build_parser(build_default_registry())
        args = parser.parse_args(['--goal', 'x', '--output', 'json', '--include-history'])
        self.assertEqual(args.output, 'json')
        self.assertTrue(args.include_history)

    def test_should_parse_observer_and_exit_options(self) -> None:
        parser = build_parser(build_default_registry())
        args = parser.parse_args(['--goal', 'x', '--observer-file', 'events.jsonl', '--exit-on-failure'])
        self.assertEqual(args.observer_file, 'events.jsonl')
        self.assertTrue(args.exit_on_failure)

    def test_should_reject_empty_goal(self) -> None:
        args = argparse.Namespace(goal='   ', goal_file=None)
        with self.assertRaises(ValueError):
            resolve_goal(args)

    def test_should_write_observer_jsonl(self) -> None:
        with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8', suffix='.jsonl') as file:
            path = file.name
        try:
            observer = build_jsonl_observer(path)
            observer('step_started', {'step': 1})
            with open(path, 'r', encoding='utf-8') as file:
                line = file.readline().strip()
            payload = json.loads(line)
            self.assertEqual(payload['event'], 'step_started')
            self.assertEqual(payload['payload']['step'], 1)
        finally:
            os.remove(path)

    def test_should_return_nonzero_when_exit_on_failure_and_not_done(self) -> None:
        parser = build_parser(build_default_registry())
        args = parser.parse_args(
            [
                '--goal',
                'x',
                '--strategy',
                'json_stub',
                '--max-steps',
                '1',
                '--exit-on-failure',
                '--output',
                'json',
            ]
        )
        rendered, exit_code = execute(args, build_default_registry())
        self.assertEqual(exit_code, 1)
        payload = json.loads(rendered)
        self.assertEqual(payload['stop_reason'], 'max_steps')

    def test_should_return_zero_when_not_done_but_exit_not_required(self) -> None:
        parser = build_parser(build_default_registry())
        args = parser.parse_args(['--goal', 'x', '--strategy', 'json_stub', '--max-steps', '1'])
        _, exit_code = execute(args, build_default_registry())
        self.assertEqual(exit_code, 0)


if __name__ == '__main__':
    unittest.main()
