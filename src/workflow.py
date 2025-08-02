import os
import json
import time
from typing import Dict, Any
from langgraph.graph import StateGraph, END
import google.generativeai as genai
from langchain_core.messages import HumanMessage, SystemMessage

from .models import ResearchState, CompanyInfo, CompanyAnalysis
from .prompts import DeveloperToolsPrompts
from .firecrawl import FirecrawlService


class Workflow:
    def __init__(self):
        # Configure Firecrawl (assumes FIRECRAWL_API_KEY is set in environment)
        self.firecrawl = FirecrawlService()  # Ensure FirecrawlService uses fc-0c8e188b3f00406a9c80381dd6c34758
        # Configure Gemini API
        genai.configure(api_key="AIzaSyA7D3UfvFh6qhPtKYAiG13r0BspPVlCo4A")  # Or os.getenv("GEMINI_API_KEY")
        self.llm = genai.GenerativeModel("gemini-2.5-flash", generation_config={"temperature": 0.1})
        self.prompts = DeveloperToolsPrompts()
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        graph = StateGraph(ResearchState)
        graph.add_node("extract_tools", self._extract_tools_step)
        graph.add_node("research", self._research_step)
        graph.add_node("analyze", self._analyze_step)
        graph.set_entry_point("extract_tools")
        graph.add_edge("extract_tools", "research")
        graph.add_edge("research", "analyze")
        graph.add_edge("analyze", END)
        return graph.compile()

    def run(self, query: str) -> ResearchState:
        initial_state = ResearchState(query=query)
        final_state = self.workflow.invoke(initial_state)
        return final_state if isinstance(final_state, ResearchState) else ResearchState(**final_state)

    def _extract_tools_step(self, state: ResearchState) -> Dict[str, Any]:
        print(f"🔎 Searching for tools related to: {state.query}")
        article_query = f"{state.query} tools comparison best alternatives"

        search_results = self.firecrawl.search_company(article_query)
        all_content = ""

        if not search_results or not getattr(search_results, "data", None):
            print("❌ No search results found.")
            return {"extracted_tools": []}

        for result in search_results.data[:3]:
            url = result.get("url", "")
            if not url:
                continue
            scraped = self.firecrawl.scrape_company_pages(url)
            if scraped and getattr(scraped, "markdown", None):
                all_content += scraped.markdown[:1500] + "\n\n"

        prompt = f"{self.prompts.TOOL_EXTRACTION_SYSTEM}\n\n{self.prompts.tool_extraction_user(state.query, all_content)}"
        try:
            response = self.llm.generate_content(prompt)
            tool_names = [n.strip() for n in response.text.strip().split("\n") if n.strip()]
            print(f"✅ Extracted tools: {', '.join(tool_names[:5])}")
            return {"extracted_tools": tool_names}
        except Exception as e:
            print("⚠️ Error extracting tools:", e)
            return {"extracted_tools": []}

    def _analyze_company_content(self, company_name: str, content: str) -> CompanyAnalysis:
        # Prompt Gemini for structured JSON output
        system_prompt = (
            f"{self.prompts.TOOL_ANALYSIS_SYSTEM}\n\n"
            "Return a JSON object with the following schema:\n"
            "{\n"
            '  "pricing_model": "Free|Freemium|Paid|Enterprise|Unknown",\n'
            '  "is_open_source": boolean|null,\n'
            '  "tech_stack": string[],\n'
            '  "description": string,\n'
            '  "api_available": boolean|null,\n'
            '  "language_support": string[],\n'
            '  "integration_capabilities": string[]\n'
            "}\n"
            "Ensure the response is valid JSON and matches the schema exactly."
        )
        user_prompt = self.prompts.tool_analysis_user(company_name, content)
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        try:
            response = self.llm.generate_content(full_prompt)
            # Parse JSON response
            json_response = json.loads(response.text.strip("```json\n").strip("```"))
            return CompanyAnalysis(
                pricing_model=json_response.get("pricing_model", "Unknown"),
                is_open_source=json_response.get("is_open_source", None),
                tech_stack=json_response.get("tech_stack", []),
                description=json_response.get("description", "Analysis failed"),
                api_available=json_response.get("api_available", None),
                language_support=json_response.get("language_support", []),
                integration_capabilities=json_response.get("integration_capabilities", []),
            )
        except Exception as e:
            print(f"⚠️ Analysis failed for {company_name}:", e)
            return CompanyAnalysis(
                pricing_model="Unknown",
                is_open_source=None,
                tech_stack=[],
                description="Analysis failed",
                api_available=None,
                language_support=[],
                integration_capabilities=[],
            )

    def _research_step(self, state: ResearchState) -> Dict[str, Any]:
        extracted = getattr(state, "extracted_tools", [])
        if not extracted:
            print("⚠️ No tools found; falling back to raw search.")
            raw = self.firecrawl.search_company(state.query)
            if not raw or not getattr(raw, "data", None):
                return {"companies": []}
            tool_names = [r.get("metadata", {}).get("title", "Unknown") for r in raw.data[:4]]
        else:
            tool_names = extracted[:4]

        print(f"🧠 Researching: {', '.join(tool_names)}")
        companies = []

        for tool_name in tool_names:
            time.sleep(1)  # Avoid rate limits
            raw = self.firecrawl.search_company(f"{tool_name} official site")
            if not raw or not raw.data:
                continue

            info = raw.data[0]
            website = info.get("url", "")
            if not website:
                continue

            company = CompanyInfo(
                name=tool_name,
                description=info.get("markdown", ""),
                website=website,
                tech_stack=[],
                competitors=[],
            )

            scraped = self.firecrawl.scrape_company_pages(company.website)
            if scraped and getattr(scraped, "markdown", None):
                analysis = self._analyze_company_content(company.name, scraped.markdown)
                company.pricing_model = analysis.pricing_model
                company.is_open_source = analysis.is_open_source
                company.tech_stack = analysis.tech_stack
                company.description = analysis.description
                company.api_available = analysis.api_available
                company.language_support = analysis.language_support
                company.integration_capabilities = analysis.integration_capabilities
            else:
                print(f"⚠️ No valid content scraped for {company.name}")
                company.description = "No content available"

            companies.append(company)

        return {"companies": companies}

    def _analyze_step(self, state: ResearchState) -> Dict[str, Any]:
        print("🧾 Generating final recommendations.")
        company_data = ",".join([c.json() for c in state.companies])
        prompt = f"{self.prompts.RECOMMENDATIONS_SYSTEM}\n\n{self.prompts.recommendations_user(state.query, company_data)}"
        try:
            response = self.llm.generate_content(prompt)
            return {"analysis": response.text}
        except Exception as e:
            print("⚠️ Final analysis generation failed:", e)
            return {"analysis": "No recommendation available due to an error."}