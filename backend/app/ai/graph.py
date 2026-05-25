from __future__ import annotations

import uuid
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.ai.actions import classifier, planner
from app.ai.dashboard import dashboard_chart_builder
from app.ai.tools import tool_executor
from app.models.schemas import (
    AgentIntent,
    AgentRequest,
    AgentResponse,
    ChartDataSpec,
    DataAction,
    ToolExecutionResult,
)
from app.services.dataset_repository import dataset_repository
from app.services.dataset_service import dataset_service


class DataAgentState(TypedDict, total=False):
    dataset_id: str
    message: str
    conversation_id: str
    intent: AgentIntent
    actions: list[DataAction]
    tool_results: list[ToolExecutionResult]
    charts: list[ChartDataSpec]
    insights: list[str]
    response: str


class DataAgentGraph:
    def __init__(self) -> None:
        graph = StateGraph(DataAgentState)
        graph.add_node("classify_intent", self._classify_intent)
        graph.add_node("plan_actions", self._plan_actions)
        graph.add_node("execute_tools", self._execute_tools)
        graph.add_node("summarize", self._summarize)
        graph.add_edge(START, "classify_intent")
        graph.add_edge("classify_intent", "plan_actions")
        graph.add_edge("plan_actions", "execute_tools")
        graph.add_edge("execute_tools", "summarize")
        graph.add_edge("summarize", END)
        self._graph = graph.compile()

    def invoke(self, request: AgentRequest) -> AgentResponse:
        conversation_id = request.conversation_id or uuid.uuid4().hex
        state = self._graph.invoke(
            {
                "dataset_id": request.dataset_id,
                "message": request.message,
                "conversation_id": conversation_id,
                "tool_results": [],
                "charts": [],
                "insights": [],
            }
        )
        session = dataset_repository.get(request.dataset_id)
        profile = dataset_service.build_profile(session.dataframe, request.dataset_id, session.filename)
        return AgentResponse(
            conversation_id=conversation_id,
            intent=state["intent"],
            response=state["response"],
            actions=state["actions"],
            tool_results=state["tool_results"],
            profile=profile,
            charts=state.get("charts", []),
            insights=state.get("insights", []),
        )

    def _classify_intent(self, state: DataAgentState) -> DataAgentState:
        return {"intent": classifier.classify(state["message"])}

    def _plan_actions(self, state: DataAgentState) -> DataAgentState:
        session = dataset_repository.get(state["dataset_id"])
        actions = planner.plan(state["message"], session.dataframe, state["intent"])
        return {"actions": actions}

    def _execute_tools(self, state: DataAgentState) -> DataAgentState:
        session = dataset_repository.get(state["dataset_id"])
        dataframe = session.dataframe.copy()
        results: list[ToolExecutionResult] = []
        charts: list[ChartDataSpec] = []
        insights: list[str] = []
        mutating_actions = {
            "drop_missing",
            "fill_missing",
            "drop_duplicates",
            "rename_column",
            "modify_column",
            "filter_rows",
            "normalize_column",
            "remove_outliers",
        }

        for action in state["actions"]:
            dataframe, result, chart, action_insights = tool_executor.execute(dataframe, action)
            results.append(result)
            if chart:
                charts.append(chart)
            insights.extend(action_insights)

        if any(action.action in mutating_actions for action in state["actions"]):
            operation = " -> ".join(action.action for action in state["actions"])
            dataset_repository.update(state["dataset_id"], dataframe, operation)

        charts = dashboard_chart_builder.build(dataframe, charts)

        return {"tool_results": results, "charts": charts, "insights": insights}

    def _summarize(self, state: DataAgentState) -> DataAgentState:
        messages = [result.message for result in state.get("tool_results", []) if result.success]
        insights = state.get("insights", [])
        summary = " ".join(messages) if messages else "I analyzed the dataset and prepared the next dashboard state."
        if insights:
            summary = f"{summary} Key insight: {insights[0]}"
        return {"response": summary}


data_agent_graph = DataAgentGraph()
