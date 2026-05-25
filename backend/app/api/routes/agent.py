from fastapi import APIRouter

from app.ai.graph import data_agent_graph
from app.models.schemas import AgentRequest, AgentResponse


router = APIRouter()


@router.post("/invoke", response_model=AgentResponse)
async def invoke_agent(request: AgentRequest) -> AgentResponse:
    return data_agent_graph.invoke(request)
