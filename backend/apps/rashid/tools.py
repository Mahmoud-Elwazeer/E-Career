"""
Rashid specialized tools — thin compatibility shim over the canonical
tool registry.

Previously this module defined a SEPARATE `RashidTool`/`RASHID_TOOLS`
registry with its own implementations of `search_jobs`/`recommend_jobs`
(reachable only via `POST /api/rashid/tools/execute/`), independently
drifting from the live pydantic-ai tool set in `apps/intelligence/agent.py`.
Both the duplicated logic and several real bugs it carried (e.g.
`profile.experience`, `profile.current_position`, `profile.years_of_experience`,
and `job.requirements` — none of which exist on the real `CareerProfile`/`Job`
models) have been removed. All tool bodies now live once, in
`apps.intelligence.tool_registry.TOOL_REGISTRY`.

This module keeps the same public functions (`execute_tool`,
`get_available_tools`) so `apps/rashid/views.py` and
`apps/intelligence/views.py` don't need to change their call sites —
they now resolve through the canonical registry instead.
"""
from typing import Any, Dict

from apps.intelligence.tool_registry import TOOL_REGISTRY, ToolContext


def execute_tool(tool_name: str, context: Dict[str, Any]) -> str:
    """Execute a canonical tool by name using a plain REST-style context dict.

    `context` carries `user` (a Django User instance, or None for anonymous
    callers) plus any tool-specific arguments (job_id, query, location, ...).
    """
    user = context.get("user")
    user_id = getattr(user, "id", None) if user and getattr(user, "is_authenticated", False) else None
    user_name = getattr(user, "full_name", "") or getattr(user, "email", "") if user else ""

    args = {k: v for k, v in context.items() if k != "user"}
    tool_ctx = ToolContext(user_id=user_id, user_name=user_name, args=args)

    result = TOOL_REGISTRY.execute(tool_name, tool_ctx)
    return result.with_trailer()


def get_available_tools():
    """Get list of available tools (name + description) for the tool-registry endpoints."""
    return [
        {"name": t.name, "description": t.description}
        for t in TOOL_REGISTRY.all()
    ]
