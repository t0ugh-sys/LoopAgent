from __future__ import annotations

import json
from pathlib import Path


def load_event_rows(events_file: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if not events_file.exists():
        return rows
    for line in events_file.read_text(encoding='utf-8').splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def render_event_row(row: dict[str, object]) -> str:
    ts = str(row.get('ts', '') or '')
    event = str(row.get('event', 'unknown'))
    session_id = str(row.get('session_id', '') or '')
    tool_name = str(row.get('tool_name', '') or '')
    permission = str(row.get('permission_decision', '') or '')
    parts = [part for part in [ts, event] if part]
    line = ' '.join(parts)
    if tool_name:
        line += f' [{tool_name}]'
    if permission:
        line += f' permission={permission}'
    if session_id:
        line += f' session={session_id}'
    return line or 'unknown'


def render_event_stream(events_file: Path, *, limit: int | None = None) -> str:
    rows = load_event_rows(events_file)
    if limit is not None:
        rows = rows[-limit:]
    rendered = [f'- {render_event_row(row)}' for row in rows]
    return '\n'.join(rendered) if rendered else '(empty)'
