"""
LoopAgent Tools Module - Tool System

This module re-exports from the legacy tools.py for backward compatibility.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple

# Re-export everything from legacy tools.py for backward compatibility
from loop_agent.tools import (
    ToolContext,
    ToolDispatchMap,
    ToolFn,
    ToolRegistration,
    analyze_command,
    builtin_tool_registrations,
    build_default_tools,
    execute_tool_call,
    fetch_url_tool,
    read_file_tool,
    register_tool_handler,
    run_command_tool,
    write_file_tool,
)

# Also export from tool_def and tool_builder for new system
from loop_agent.tool_def import (
    ToolRegistration as ToolDefRegistration,
    ToolUseContext,
)
from loop_agent.tool_builder import (
    build_tool,
    build_dispatch_map,
    execute_tool,
)

# Alias for compatibility
__all__ = [
    # Legacy types
    'ToolContext',
    'ToolDispatchMap',
    'ToolFn',
    'ToolRegistration',
    
    # Legacy functions
    'analyze_command',
    'builtin_tool_registrations',
    'build_default_tools',
    'execute_tool_call',
    'fetch_url_tool',
    'read_file_tool',
    'register_tool_handler',
    'run_command_tool',
    'write_file_tool',
    
    # New system types
    'ToolUseContext',
    'ToolDefRegistration',
    
    # New system functions
    'build_tool',
    'build_dispatch_map',
    'execute_tool',
]
