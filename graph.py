from langgraph.graph import (
    StateGraph,
    START,
    END
)

from langgraph.types import interrupt

from langgraph.checkpoint.memory import MemorySaver


from state import AgentState


# Agents
from agents.planner import planner as planner_agent

from agents.router import router as router_agent

from agents.executor import executor as executor_agent

from agents.responder import responder as responder_agent


# ==========================================================
# NODE 1 — PLANNER
# ==========================================================

def planner(state: AgentState):

    print("[Planner] Running...")


    result = planner_agent(
        state
    )


    return {

        "plan": result.get(
            "plan",
            []
        ),

        "status": "planned",

        "messages": [

            "[Planner] Plan created"

        ]

    }


# ==========================================================
# NODE 2 — ROUTER
# ==========================================================

def router(state: AgentState):

    print("[Router] Running...")


    result = router_agent(
        state
    )


    return {

        "tool_calls": result.get(
            "tool_calls",
            []
        ),

        "status": "routed",

        "messages": [

            "[Router] Proposed actions created"

        ]

    }


# ==========================================================
# NODE 3 — HUMAN REVIEW
# ==========================================================

def human_review(state: AgentState):

    report = (

        state.get(
            "report"
        )

        or state.get(
            "final_response"
        )

        or "No report was generated."

    )


    decision = interrupt(

        {

            "message": (

                "The AI has prepared the following "

                "internal work report for your review."

            ),

            "report": report,

            "response": report

        }

    )


    approved = (

        str(
            decision
        ).lower().strip()

        == "approve"

    )


    return {

        "approved": approved,

        "approval_comment": (

            ""

            if approved

            else str(
                decision
            )

        ),

        "report": report,

        "final_response": report,

        "status": (

            "approved"

            if approved

            else "rejected"

        )

    }

# ==========================================================
# ROUTE AFTER HUMAN REVIEW
# ==========================================================

def route_after_review(state: AgentState):

    if state.get(
        "approved"
    ) is True:

        return "executor"


    return "end"


# ==========================================================
# NODE 4 — EXECUTOR
# ==========================================================

def executor(state: AgentState):

    print(
        "[Executor] Running..."
    )


    result = executor_agent(
        state
    )


    return {

        "tool_results": result.get(
            "tool_results",
            []
        ),

        "status": result.get(
            "status",
            "executed"
        ),

        "messages": [

            "[Executor] Approved actions executed"

        ]

    }


# ==========================================================
# NODE 5 — RESPONDER
# ==========================================================

def responder(state: AgentState):

    print(
        "[Responder] Running..."
    )


    result = responder_agent(
        state
    )


    return {

        "final_response": result.get(
            "final_response",
            ""
        ),

        "status": "completed",

        "messages": [

            "[Responder] Final response generated"

        ]

    }


# ==========================================================
# BUILD GRAPH
# ==========================================================

graph = StateGraph(
    AgentState
)


# ==========================================================
# ADD NODES
# ==========================================================

graph.add_node(
    "planner",
    planner
)

graph.add_node(
    "router",
    router
)

graph.add_node(
    "human_review",
    human_review
)

graph.add_node(
    "executor",
    executor
)

graph.add_node(
    "responder",
    responder
)


# ==========================================================
# FLOW
# ==========================================================

graph.add_edge(
    START,
    "planner"
)

graph.add_edge(
    "planner",
    "router"
)

graph.add_edge(
    "router",
    "human_review"
)


# ==========================================================
# HUMAN APPROVAL ROUTING
# ==========================================================

graph.add_conditional_edges(

    "human_review",

    route_after_review,

    {

        "executor": "executor",

        "end": END

    }

)


# ==========================================================
# AFTER APPROVAL
# ==========================================================

graph.add_edge(
    "executor",
    "responder"
)

graph.add_edge(
    "responder",
    END
)


# ==========================================================
# CHECKPOINTER
# ==========================================================

checkpointer = MemorySaver()


app = graph.compile(
    checkpointer=checkpointer
)