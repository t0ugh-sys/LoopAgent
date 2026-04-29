"""
Tool System - Core Type Definitions

参�?Claude Code Tool.ts 的设计，提供完整�?Tool 类型系统�?
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol, runtime_checkable

# �?agent_protocol 导入 ToolResult（避免重复定义）
from anvil.agent_protocol import ToolResult


@dataclass
class ToolPermissionContext:
    """Tool 权限上下�?""
    mode: str = 'default'  # 'default', 'auto', 'readonly'
    always_allow_rules: Dict[str, List[str]] = field(default_factory=dict)
    always_deny_rules: Dict[str, List[str]] = field(default_factory=dict)
    additional_working_directories: Dict[str, str] = field(default_factory=dict)


# ============== Tool Definition ==============

@runtime_checkable
class Tool(Protocol):
    """Tool 协议 - 参�?Claude Code Tool.ts"""
    
    name: str
    
    input_schema: dict[str, Any]
    output_schema: Optional[dict[str, Any]] = None
    
    # 核心方法
    def call(
        self,
        args: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        """执行 Tool"""
        ...
    
    def description(self, input: dict[str, Any]) -> str:
        """返回 Tool 的描�?""
        ...
    
    def prompt(self, options: dict[str, Any]) -> str:
        """返回 Tool 的系统提�?""
        ...
    
    # 状态判�?
    def is_enabled(self) -> bool:
        """Tool 是否启用"""
        return True
    
    def is_concurrency_safe(self, input: Any) -> bool:
        """Tool 是否可以并发执行"""
        return False
    
    def is_read_only(self, input: Any) -> bool:
        """Tool 是否只读"""
        return False
    
    def is_destructive(self, input: Any) -> bool:
        """Tool 是否具有破坏�?""
        return False
    
    # 权限
    def check_permissions(self, input: Any, context: ToolUseContext) -> bool:
        """检查权�?""
        return True
    
    # UI 相关
    def get_tool_use_summary(self, input: dict[str, Any]) -> Optional[str]:
        """获取 Tool 使用的摘�?""
        return None
    
    def get_activity_description(self, input: dict[str, Any]) -> Optional[str]:
        """获取活动描述（用�?spinner�?""
        return None
    
    def render_tool_result_message(
        self,
        output: Any,
        options: dict[str, Any],
    ) -> Optional[str]:
        """渲染工具结果消息"""
        return None


# ============== Tool Use Context ==============

@dataclass
class ToolUseContext:
    """Tool 执行时的上下�?""
    workspace_root: str
    tools: Dict[str, Callable] = field(default_factory=dict)
    mcp_clients: List[Any] = field(default_factory=list)
    agent_definitions: List[Any] = field(default_factory=list)
    permission_context: ToolPermissionContext = field(default_factory=ToolPermissionContext)
    
    # 回调
    get_app_state: Optional[Callable[[], Any]] = None
    set_app_state: Optional[Callable[[Callable[[Any], Any]], None]] = None
    
    # 可选组�?
    todo_manager: Any = None
    skill_loader: Any = None
    compact_manager: Any = None
    background_runner: Any = None
    
    # 额外选项
    verbose: bool = False
    debug: bool = False


# ============== Tool Registration ==============

@dataclass
class ToolRegistration:
    """Tool 注册信息"""
    name: str
    handler: Callable[[ToolUseContext, dict[str, Any]], ToolResult]
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: Optional[dict[str, Any]] = None
    
    # 描述
    description: str = ''
    search_hint: str = ''
    
    # 特性标�?
    max_result_size_chars: int = 100_000
    should_defer: bool = False
    always_load: bool = False
    
    # 权限
    is_read_only: bool = False
    is_destructive: bool = False


# ============== Validation ==============

@dataclass
class ValidationResult:
    """验证结果"""
    result: bool
    message: str = ''
    error_code: int = 0


def tool_matches_name(tool: ToolRegistration, name: str) -> bool:
    """检�?tool 名称是否匹配（支持别名）"""
    if tool.name == name:
        return True
    return False


def find_tool_by_name(
    tools: List[ToolRegistration],
    name: str,
) -> Optional[ToolRegistration]:
    """根据名称查找 tool"""
    for tool in tools:
        if tool_matches_name(tool, name):
            return tool
    return None


# ============== Helper Types ==============

@dataclass
class ToolCallProgress:
    """Tool 调用进度"""
    tool_use_id: str
    data: dict[str, Any]


@dataclass
class PermissionResult:
    """权限结果"""
    behavior: str  # 'allow', 'deny', 'ask'
    updated_input: Optional[dict[str, Any]] = None
    message: Optional[str] = None
