# Repository Layout

## Top Level

- `agents/`: staged learning path and runnable harness walkthroughs
- `skills/`: human-readable skill contracts and boundaries
- `docs/`: architecture and artifact references
- `examples/`: integration-oriented demos
- `src/loop_agent/`: runtime package
- `tests/`: unit and structural tests

## Runtime Package

- `core/`: generic loop engine and base types
- `llm/`: provider adapters and mock provider
- `memory/`: JSONL memory store and summary handling
- `steps/`: strategy-specific step builders
- `tools.py`: workspace-safe tool layer
- `coding_agent.py`: coding-agent orchestration
- `agent_cli.py`: coding-agent oriented CLI
- `cli.py`: general loop CLI
