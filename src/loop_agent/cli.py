from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .core.agent import LoopAgent
from .core.serialization import run_result_to_json
from .core.types import ObserverFn, RunResult, StopConfig, StopReason
from .steps.registry import StepRegistry, build_default_registry


def build_parser(registry: StepRegistry) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='LoopAgent')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--goal', help='用户目标/需求描述（短文本，尽量避免复杂编码问题）')
    group.add_argument('--goal-file', help='从 UTF-8 文件读取目标（推荐用于中文/长文本）')
    parser.add_argument('--strategy', choices=registry.names(), default='demo')
    parser.add_argument('--history-window', type=int, default=3, help='JSON 策略下带入历史输出条数')
    parser.add_argument('--max-steps', type=int, default=20)
    parser.add_argument('--timeout-s', type=float, default=60.0)
    parser.add_argument('--output', choices=['text', 'json'], default='text')
    parser.add_argument('--include-history', action='store_true', help='JSON 输出时是否包含 history')
    parser.add_argument('--observer-file', help='将事件回调按 JSONL 写入指定文件')
    parser.add_argument('--exit-on-failure', action='store_true', help='当未完成时返回非零退出码')
    return parser


def resolve_goal(args: argparse.Namespace) -> str:
    if args.goal_file:
        with open(args.goal_file, 'r', encoding='utf-8-sig') as file:
            goal = file.read().strip()
    else:
        goal = args.goal
    if not goal.strip():
        raise ValueError('goal must not be empty')
    return goal


def should_exit_failure(result: RunResult[Any]) -> bool:
    failure_reasons = {StopReason.timeout, StopReason.max_steps, StopReason.step_error}
    return (not result.done) and (result.stop_reason in failure_reasons)


def build_jsonl_observer(path: str) -> ObserverFn:
    def observer(event: str, payload: dict[str, Any]) -> None:
        record = {'event': event, 'payload': payload}
        with open(path, 'a', encoding='utf-8') as file:
            file.write(json.dumps(record, ensure_ascii=False))
            file.write('\n')

    return observer


def execute(args: argparse.Namespace, registry: StepRegistry) -> tuple[str, int]:
    goal = resolve_goal(args)
    step, initial_state = registry.create(args.strategy, args)
    observer = build_jsonl_observer(args.observer_file) if args.observer_file else None

    agent = LoopAgent(step=step, stop=StopConfig(max_steps=args.max_steps, max_elapsed_s=args.timeout_s))
    result = agent.run(goal=goal, initial_state=initial_state, observer=observer)

    if args.output == 'json':
        rendered = run_result_to_json(result, include_history=args.include_history)
    else:
        rendered = '\n'.join(
            [
                f'done: {result.done}',
                f'stop_reason: {result.stop_reason.value}',
                f'steps: {result.steps}',
                f'final_output: {result.final_output}',
            ]
        )

    exit_code = 1 if (args.exit_on_failure and should_exit_failure(result)) else 0
    return rendered, exit_code


def main() -> None:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')  # type: ignore[call-arg]
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')  # type: ignore[call-arg]

    registry = build_default_registry()
    args = build_parser(registry).parse_args()
    rendered, exit_code = execute(args, registry)
    print(rendered)
    if exit_code != 0:
        raise SystemExit(exit_code)


if __name__ == '__main__':
    main()
