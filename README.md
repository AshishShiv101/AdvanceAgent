# DevToolScout

A Python-based developer tools research agent that extracts, researches, and analyzes developer tools using the Google Gemini API and Firecrawl SDK, built with LangGraph for workflow orchestration.

## Overview

AdvanceAgent is designed to help developers discover and compare tools, libraries, and platforms (e.g., Firebase alternatives like Supabase). It performs the following tasks:
- *Tool Extraction*: Identifies relevant tools from web content.
- *Research*: Scrapes official websites for detailed information.
- *Analysis*: Provides structured insights (e.g., pricing, tech stack, integrations).
- *Recommendations*: Offers concise, actionable tool recommendations.

The agent uses:
- *Google Gemini API* for natural language processing and structured analysis.
- *Firecrawl SDK* for web scraping and search.
- *LangGraph* for managing the research workflow.
- *Python* with dependencies like langchain-core and python-dotenv.

## Features

- Extracts up to 5 relevant tools per query.
- Analyzes tools for pricing, open-source status, tech stack, APIs, language support, and integrations.
- Generates developer-focused recommendations in 3-4 sentences.
- Handles rate limits with built-in delays.
- Configurable via environment variables for API keys.
### 🖼️ Screenshots

#### 🔍 Tool Extraction & Research Flow  
![Tool Extraction Screenshot](https://github.com/user-attachments/assets/2b244194-45b6-4040-b5e0-a950c94a404b)

#### 📊 Tool Analysis & Recommendation Output  
![Tool Analysis Screenshot](https://github.com/user-attachments/assets/6daacbeb-5f19-4a97-9b30-5ebb89d50ca7)


## Prerequisites

- Python 3.7+
- A virtual environment (recommended)
- API keys for:
  - [Google Gemini API](https://ai.google.dev/) (free tier available)
  - [Firecrawl SDK](https://www.firecrawl.dev/) (free or paid tier)

## Installation

1. *Clone the Repository*:
   ```bash
   git clone https://github.com/your-username/AdvanceAgent.git
   cd AdvanceAgent
