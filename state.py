from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage


class AgentState(TypedDict, total=False):

    # =========================================
    # USER REQUEST
    # =========================================

    query: str
    user: str
    session_id: str


    # =========================================
    # PLANNING
    # =========================================

    plan: Optional[List[Dict[str, Any]]]


    # =========================================
    # TOOL EXECUTION
    # =========================================

    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]


    # =========================================
    # DATA
    # =========================================

    emails: List[Dict[str, Any]]
    context: str


    # =========================================
    # GENERATED REPORT
    # =========================================

    report: str
    final_response: str


    # =========================================
    # CONVERSATION
    # =========================================

    messages: List[BaseMessage]


    # =========================================
    # HUMAN APPROVAL
    # =========================================

    approved: Optional[bool]
    approval_comment: str


    # =========================================
    # EXECUTION
    # =========================================

    current_step: Optional[int]
    status: str
    error: Optional[str]