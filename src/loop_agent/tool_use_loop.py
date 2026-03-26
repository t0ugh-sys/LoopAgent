from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from .agent_protocol import ToolResult, parse_agent_step, render_agent_step_schema
from .core.types import StepContext, StepResult
from .policies import ToolPolicy
from .tools import ToolContext, ToolDispatchMap, build_default_tools, execute_tool_call

try:
    from .skills import SkillLoader
except ImportError:  # pragma: no cover
    SkillLoader = None  # type: ignore[assignment]


DeciderFn = Callable[[str, Tuple[str, ...], Tuple[ToolResult, ...], Dict[str, object], Tuple[str, ...]], str]


@dataclass(frozen=True)
class ToolUseState:
    history: Tuple[str, ...] = tuple()
    tool_results: Tuple[ToolResult, ...] = tuple()


def build_tool_dispatch(
    *,
    skills: Optional['SkillLoader'] = None,
    extra_tools: Optional[ToolDispatchMap] = None,
) -> ToolDispatchMap:
    dispatch_map = build_default_tools()
    if skills is not None:
        dispatch_map.update(skills.get_tools())
    if extra_tools is not None:
        dispatch_map.update(extra_tools)
    return dispatch_map


def execute_tool_use_round(
    *,
    decider: DeciderFn,
    context: StepContext[ToolUseState],
    tool_context: ToolContext,
    dispatch_map: ToolDispatchMap,
) -> StepResult[ToolUseState]:
    raw = decider(
        context.goal,
        context.state.history,
        context.state.tool_results,
        context.state_summary,
        context.last_steps,
    )
    parsed = parse_agent_step(raw)
    if parsed is None:
        output = 'invalid agent step json. expected schema: ' + render_agent_step_schema()
        return StepResult(
            output=output,
            state=context.state,
            done=False,
            metadata={'parse_error': True, 'raw_response': raw[:2000]},
        )

    executed: List[ToolResult] = []
    for tool_call in parsed.tool_calls:
        executed.append(execute_tool_call(tool_context, tool_call, dispatch_map))

    history = list(context.state.history)
    history.append(f'thought: {parsed.thought}')
    for item in executed:
        status = 'ok' if item.ok else f'error={item.error}'
        history.append(f'tool[{item.id}] {status}')

    new_state = ToolUseState(history=tuple(history), tool_results=tuple(executed))
    has_tool_calls = len(parsed.tool_calls) > 0
    metadata = {
        'thought': parsed.thought,
        'plan': parsed.plan,
        'tool_calls': [
            {'id': call.id, 'name': call.name, 'arguments': dict(call.arguments)}
            for call in parsed.tool_calls
        ],
        'tool_results': [
            {'id': item.id, 'ok': item.ok, 'error': item.error, 'output': item.output[:2000]}
            for item in executed
        ],
        'has_tool_calls': has_tool_calls,
        'state_summary': context.state_summary,
        'last_steps': list(context.last_steps),
    }
    if not has_tool_calls:
        final = parsed.final or parsed.thought or 'done'
        return StepResult(output=final, state=new_state, done=True, metadata=metadata)
    return StepResult(output='continue', state=new_state, done=False, metadata=metadata)


def make_tool_use_step(
    *,
    decider: DeciderFn,
    workspace_root: Path,
    skills: Optional['SkillLoader'] = None,
    policy: ToolPolicy = ToolPolicy.allow_all(),
    extra_tools: Optional[ToolDispatchMap] = None,
) -> Callable[[StepContext[ToolUseState]], StepResult[ToolUseState]]:
    dispatch_map = build_tool_dispatch(skills=skills, extra_tools=extra_tools)
    tool_context = ToolContext(workspace_root=workspace_root, policy=policy)

    def step(context: StepContext[ToolUseState]) -> StepResult[ToolUseState]:
        return execute_tool_use_round(
            decider=decider,
            context=context,
            tool_context=tool_context,
            dispatch_map=dispatch_map,
        )

    return step
