from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .entrypoints.parser_builders import (
    register_code_parser,
    register_doctor_parser,
    register_replay_parser,
    register_skills_parser,
    register_team_parser,
    register_tools_parser,
)
from .llm.providers import build_invoke_from_args
from .ops.doctor import format_doctor_report, run_provider_doctor
from .services import coding_runtime as _coding_runtime
from .services.session_runtime import should_launch_interactive as _should_launch_interactive
from .skills import get_skill, list_skills
from .task_graph import Task
from .team_runtime import PersistentTeamRuntime, PersistentTeammateSpec
from .tools import build_default_tools, builtin_tool_specs


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


def _parse_teammate(value: str) -> Tuple[str, str]:
    raw = value.strip()
    if ':' not in raw:
        raise ValueError('teammate must be NAME:ROLE')
    name, role = raw.split(':', 1)
    name = name.strip()
    role = role.strip()
    if not name or not role:
        raise ValueError('teammate must be NAME:ROLE')
    return name, role


def _parse_team_message(value: str) -> Tuple[str, str]:
    raw = value.strip()
    if '=' not in raw:
        raise ValueError('message must be TARGET=BODY')
    target, body = raw.split('=', 1)
    target = target.strip()
    body = body.strip()
    if not target or not body:
        raise ValueError('message must be TARGET=BODY')
    return target, body


def _run_team_run_command(args: argparse.Namespace) -> int:
    runtime, team_root, teammate_specs = _spawn_team_runtime(args)
    _append_startup_tasks(runtime, args.task, args.sender)

    expected_replies = 0
    task_mode = bool(args.task)
    for item in args.message:
        recipient, body = _parse_team_message(item)
        runtime.send_message(recipient, body, sender=args.sender)
        expected_replies += 1
    for body in args.broadcast:
        runtime.broadcast(body, sender=args.sender)
        expected_replies += len(teammate_specs)

    replies: List[Dict[str, Any]] = []
    deadline = datetime.now(timezone.utc).timestamp() + args.service_timeout_s
    try:
        while datetime.now(timezone.utc).timestamp() < deadline:
            inbox = runtime.inbox_store.drain(args.sender)
            for item in inbox:
                replies.append(item.to_dict())
            tasks_still_active = task_mode and runtime.has_active_tasks()
            if expected_replies > 0 and len(replies) >= expected_replies and not tasks_still_active:
                break
            if expected_replies == 0 and not tasks_still_active:
                break
            time.sleep(args.poll_interval_s)
    finally:
        runtime.shutdown_all(sender=args.sender, timeout_s=min(5.0, args.service_timeout_s))

    payload = {
        'team_dir': str(team_root),
        'members': [member.to_dict() for member in runtime.config_store.load().members],
        'replies': replies,
        'tasks': runtime.load_task_graph().to_dict().get('tasks', []),
    }
    if args.output == 'json':
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f'team_dir: {team_root}')
        print(f'members: {[member["name"] for member in payload["members"]]}')
        for reply in replies:
            print(f'{reply["sender"]} -> {reply["recipient"]}: {reply["body"]}')
    return 0


def _spawn_team_runtime(args: argparse.Namespace) -> tuple[PersistentTeamRuntime, Path, list[PersistentTeammateSpec]]:
    workspace_root = Path(args.workspace).resolve()
    team_root = (workspace_root / args.team_dir).resolve()
    runtime = PersistentTeamRuntime(team_root)
    decider = _build_coding_decider(args, _load_skills_from_args(args))
    teammate_specs: List[PersistentTeammateSpec] = []
    for item in args.teammate:
        name, role = _parse_teammate(item)
        teammate_specs.append(
            PersistentTeammateSpec(
                name=name,
                role=role,
                workspace_root=workspace_root,
                decider=decider,
                stop=StopConfig(max_steps=args.max_steps, max_elapsed_s=args.timeout_s),
                skills=tuple(args.skills),
            )
        )
    for spec in teammate_specs:
        runtime.spawn_teammate(spec)
    return runtime, team_root, teammate_specs


def _append_startup_tasks(runtime: PersistentTeamRuntime, task_bodies: List[str], sender: str) -> None:
    if not task_bodies:
        return
    runtime.replace_task_graph(
        [
            Task(id=f'task_{index}', title=body, goal=body)
            for index, body in enumerate(task_bodies, start=1)
        ]
    )
    runtime.dispatch_ready_tasks(sender=sender)


def _run_team_serve_command(args: argparse.Namespace) -> int:
    runtime, team_root, teammate_specs = _spawn_team_runtime(args)
    _append_startup_tasks(runtime, args.task, args.sender)
    for item in args.message:
        recipient, body = _parse_team_message(item)
        runtime.send_message(recipient, body, sender=args.sender)
    for body in args.broadcast:
        runtime.broadcast(body, sender=args.sender)

    replies: List[Dict[str, Any]] = []
    deadline = datetime.now(timezone.utc).timestamp() + args.service_timeout_s if args.service_timeout_s > 0 else None
    idle_since = datetime.now(timezone.utc).timestamp()
    try:
        while True:
            runtime.dispatch_ready_tasks(sender='scheduler')
            inbox = runtime.inbox_store.drain(args.sender)
            for item in inbox:
                replies.append(item.to_dict())

            active = runtime.has_active_tasks() or runtime.has_pending_member_messages()
            if active:
                idle_since = datetime.now(timezone.utc).timestamp()
            if args.idle_exit_s > 0 and not active and (datetime.now(timezone.utc).timestamp() - idle_since) >= args.idle_exit_s:
                break
            if deadline is not None and datetime.now(timezone.utc).timestamp() >= deadline:
                break
            if runtime.all_teammates_shutdown():
                break
            time.sleep(args.poll_interval_s)
    finally:
        if not runtime.all_teammates_shutdown():
            runtime.shutdown_all(sender=args.sender, timeout_s=min(5.0, args.timeout_s))

    payload = {
        'team_dir': str(team_root),
        'mode': 'service',
        'members': [member.to_dict() for member in runtime.config_store.load().members],
        'replies': replies,
        'tasks': runtime.load_task_graph().to_dict().get('tasks', []),
        'teammates': [spec.name for spec in teammate_specs],
    }
    if args.output == 'json':
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f'team_dir: {team_root}')
        print(f'mode: service')
        print(f'teammates: {[spec.name for spec in teammate_specs]}')
        print(f'replies: {len(replies)}')
    return 0


def _run_team_add_task_command(args: argparse.Namespace) -> int:
    workspace_root = Path(args.workspace).resolve()
    runtime = PersistentTeamRuntime((workspace_root / args.team_dir).resolve())
    metadata: Dict[str, Any] = {}
    if args.role:
        metadata['role'] = args.role
    task = Task(
        id=args.task_id or f'task_{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")}',
        title=args.title or args.goal,
        goal=args.goal,
        dependencies=tuple(args.depends_on),
        assignee=args.assignee or None,
        metadata=metadata,
    )
    graph = runtime.add_task(task)
    runtime.dispatch_ready_tasks(sender=args.sender)
    payload = {
        'team_dir': str((workspace_root / args.team_dir).resolve()),
        'task': graph.get_task(task.id).to_dict(),
    }
    if args.output == 'json':
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f'added task: {task.id}')
    return 0


def _run_team_send_command(args: argparse.Namespace) -> int:
    workspace_root = Path(args.workspace).resolve()
    runtime = PersistentTeamRuntime((workspace_root / args.team_dir).resolve())
    runtime.send_message(args.to, args.message, sender=args.sender)
    print('ok')
    return 0


def _run_team_broadcast_command(args: argparse.Namespace) -> int:
    workspace_root = Path(args.workspace).resolve()
    runtime = PersistentTeamRuntime((workspace_root / args.team_dir).resolve())
    runtime.broadcast(args.message, sender=args.sender)
    print('ok')
    return 0


def _run_team_shutdown_command(args: argparse.Namespace) -> int:
    workspace_root = Path(args.workspace).resolve()
    runtime = PersistentTeamRuntime((workspace_root / args.team_dir).resolve())
    if args.all:
        runtime.shutdown_all(sender=args.sender, timeout_s=args.timeout_s)
    else:
        runtime.shutdown_teammate(args.to, sender=args.sender)
    print('ok')
    return 0


def _run_tools_command(args: argparse.Namespace) -> int:
    specs = sorted(builtin_tool_specs(), key=lambda item: item.name)
    if getattr(args, 'verbose', False):
        for item in specs:
            capabilities = ','.join(cap.value for cap in item.capabilities) or 'none'
            print(f'{item.name}: {item.description} [{capabilities}] risk={item.risk_level.value}')
        return 0
    names = sorted(build_default_tools().keys())
    print('\n'.join(names))
    return 0


def _run_skills_command(_: argparse.Namespace) -> int:
    """List all available skills."""
    skills = list_skills()
    print("Available skills:")
    for name in skills:
        skill = get_skill(name)
        if skill:
            print(f"  - {name}: {skill.description}")
    print("\nUse --skill <name> to load specific skills")
    print("Use --skill all to load all skills")
    return 0


def _run_replay_command(args: argparse.Namespace) -> int:
    events_file_value = getattr(args, 'events_file', '')
    if getattr(args, 'session_id', ''):
        events_file = Path(args.sessions_dir) / args.session_id / 'events.jsonl'
    else:
        events_file = Path(events_file_value)
    if not events_file.exists():
        print(f'events file not found: {events_file}')
        return 1
    print(events_file.read_text(encoding='utf-8'))
    return 0


def _run_doctor_command(args: argparse.Namespace) -> int:
    api_key = os.getenv(args.api_key_env, '').strip()
    payload = run_provider_doctor(
        base_url=args.base_url,
        model=args.model,
        wire_api=args.wire_api,
        timeout_s=args.provider_timeout_s,
        api_key_present=bool(api_key),
        extra_headers=args.provider_header,
    )
    if args.output == 'json':
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(format_doctor_report(payload))
    return 0


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
