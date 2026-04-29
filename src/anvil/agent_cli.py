from __future__ import annotations

import argparse
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from .entrypoints.parser_builders import (
    register_code_parser,
    register_doctor_parser,
    register_replay_parser,
    register_skills_parser,
    register_team_parser,
    register_tools_parser,
)
from .llm.providers import build_invoke_from_args
from .services import coding_runtime as _coding_runtime
from .services.cli_commands import (
    run_doctor_command as _run_doctor_command,
    run_replay_command as _run_replay_command,
    run_skills_command as _run_skills_command,
    run_tools_command as _run_tools_command,
)
from .services.session_runtime import should_launch_interactive as _should_launch_interactive
from .services.team_commands import (
    run_team_add_task_command as _run_team_add_task_command_impl,
    run_team_broadcast_command as _run_team_broadcast_command_impl,
    run_team_run_command as _run_team_run_command_impl,
    run_team_send_command as _run_team_send_command_impl,
    run_team_serve_command as _run_team_serve_command_impl,
    run_team_shutdown_command as _run_team_shutdown_command_impl,
)


def _default_run_id() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def _build_coding_prompt(
    *,
    goal: str,
    history: Tuple[str, ...],
    tool_results: Tuple[Any, ...],
    state_summary: Dict[str, object],
    last_steps: Tuple[str, ...],
    history_window: int,
    skills=None,
) -> str:
    return _coding_runtime.build_coding_prompt(
        goal=goal,
        history=history,
        tool_results=tool_results,
        state_summary=state_summary,
        last_steps=last_steps,
        history_window=history_window,
        skills=skills,
    )


def _build_coding_decider(args: argparse.Namespace, skills=None):
    original = _coding_runtime.build_invoke_from_args
    _coding_runtime.build_invoke_from_args = build_invoke_from_args
    try:
        return _coding_runtime.build_coding_decider(args, skills)
    finally:
        _coding_runtime.build_invoke_from_args = original


def _build_coding_summarizer(args: argparse.Namespace):
    original = _coding_runtime.build_invoke_from_args
    _coding_runtime.build_invoke_from_args = build_invoke_from_args
    try:
        return _coding_runtime.build_coding_summarizer(args)
    finally:
        _coding_runtime.build_invoke_from_args = original


def _load_skills_from_args(args: argparse.Namespace):
    return _coding_runtime.load_skills_from_args(args)


def _run_code_command(args: argparse.Namespace) -> int:
    return _coding_runtime.run_code_command(args)


def _run_team_run_command(args: argparse.Namespace) -> int:
    return _run_team_run_command_impl(
        args,
        build_coding_decider=_build_coding_decider,
        load_skills_from_args=_load_skills_from_args,
    )


def _run_team_serve_command(args: argparse.Namespace) -> int:
    return _run_team_serve_command_impl(
        args,
        build_coding_decider=_build_coding_decider,
        load_skills_from_args=_load_skills_from_args,
    )


def _run_team_add_task_command(args: argparse.Namespace) -> int:
    return _run_team_add_task_command_impl(args)


def _run_team_send_command(args: argparse.Namespace) -> int:
    return _run_team_send_command_impl(args)


def _run_team_broadcast_command(args: argparse.Namespace) -> int:
    return _run_team_broadcast_command_impl(args)


def _run_team_shutdown_command(args: argparse.Namespace) -> int:
    return _run_team_shutdown_command_impl(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='anvil',
        description='Run Anvil as a tool-use feedback loop: model decides, tools execute, results feed back.',
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    register_code_parser(subparsers, handler=_run_code_command)

    register_tools_parser(subparsers, handler=_run_tools_command)
    register_skills_parser(subparsers, handler=_run_skills_command)
    register_replay_parser(subparsers, handler=_run_replay_command)
    register_team_parser(
        subparsers,
        run_handler=_run_team_run_command,
        serve_handler=_run_team_serve_command,
        send_handler=_run_team_send_command,
        broadcast_handler=_run_team_broadcast_command,
        shutdown_handler=_run_team_shutdown_command,
        add_task_handler=_run_team_add_task_command,
    )

    register_doctor_parser(subparsers, handler=_run_doctor_command)
    return parser


def main() -> None:
    from .entrypoints.agent import main as entrypoint_main

    entrypoint_main()


if __name__ == '__main__':
    main()
