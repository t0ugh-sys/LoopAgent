from __future__ import annotations

from typing import Dict, Iterable, List

from .tool_spec import ToolSpec


def render_tool_overview(specs: Iterable[ToolSpec]) -> str:
    grouped: Dict[str, List[ToolSpec]] = {}
    for spec in sorted(specs, key=lambda item: (item.risk_level.value, item.name)):
        for capability in spec.capabilities or ():
            grouped.setdefault(capability.value, []).append(spec)
        if not spec.capabilities:
            grouped.setdefault('none', []).append(spec)

    ordered_groups = ['read', 'write', 'execute', 'network', 'memory', 'none']
    lines: List[str] = []
    for group_name in ordered_groups:
        items = grouped.get(group_name, [])
        if not items:
            continue
        lines.append(f'[{group_name}]')
        for item in items:
            notes = f' notes={item.input_notes}' if item.input_notes else ''
            lines.append(f'- {item.name} risk={item.risk_level.value}: {item.description}{notes}')
        lines.append('')
    return '\n'.join(lines).rstrip()
