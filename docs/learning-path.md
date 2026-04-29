# Learning Path

Anvil keeps its staged concepts in the production runtime and docs, instead of
shipping separate walkthrough scripts.

## Stages

1. Minimal loop engine: `src/anvil/core/`
2. JSON protocol flow: `src/anvil/agent_protocol.py`
3. Persistent memory: `src/anvil/memory/`
4. Skill loading: `src/anvil/skills.py`
5. Coding-agent execution: `src/anvil/coding_agent.py`
6. Team orchestration: `src/anvil/subagents.py` and `src/anvil/scheduler.py`
7. Worktree isolation: `src/anvil/worktree_manager.py`
8. Consolidated runtime loop: `src/anvil/tool_use_loop.py`

## Why This Layout

- New users can still understand the system incrementally.
- Production code stays under `src/anvil/`.
- The repo avoids shipping disposable walkthrough scripts as first-class surface area.
- The orchestration layer stays explicit instead of being hidden in prompt text.
