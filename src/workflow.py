from typing import Dict,Any
from langgraph.graph import StateGraph,END
from langchain_openai import ChatOpenAi
from langchain_core.messages import HumanMessage,SystemMessage
from .models import ResearchState,CompanyInfo,CompanyAnalysis
from .firecrawl import FirecrawlService
from .prompts import DeveloperToolsPrompts

class Workflow:
    def __init__(self):
        self.firecrawl = FirecrawlService()
        self.llm = ChatOpenAi(model="gpt-40-mini",temperature=0.1)
        self.prompts = DeveloperToolsPrompts()
        self.workflow = self._build_workflow()

    def _build_workflow(self):