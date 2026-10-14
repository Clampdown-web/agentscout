import json
old={t["name"]:t for t in json.load(open("tools.json"))}
fix={"OpenPilot":"https://github.com/ibmshaikh/OpenPilot","ExcaliClaw":"https://excaliclaw.com","Manifold MCP":"https://manifoldmcp.com"}
catmap={"MCP & integrations":"MCP & infra","safety & infra":"MCP & infra","observability & evals":"evals & observability"}
tools=[]
for t in old.values():
    t["url"]=fix.get(t["name"],t["url"]); t["category"]=catmap.get(t["category"],t["category"]); t["new"]=True
    if t["name"]=="koodlo": t["name"]="kōdlo"
    tools.append(t)
B,R="builders","ready to use"
OS="Open source";FP="Free tier + paid plans";OC="Open source + paid cloud"
E=[
("Claude Code","https://github.com/anthropics/claude-code","Anthropic's terminal coding agent that edits code, runs commands and handles git.","coding","Paid (Claude plan or API)","Mature",B),
("OpenAI Codex CLI","https://github.com/openai/codex","OpenAI's open-source coding agent for the terminal; also runs in the cloud.","coding","Open source; uses ChatGPT plan or API","Mature",B),
("Cursor","https://cursor.com","AI code editor with an agent mode and background agents.","coding",FP,"Mature",R),
("Devin","https://devin.ai","Cognition's autonomous software engineer that takes tickets and opens PRs.","coding","Paid","Mature",B),
("OpenHands","https://github.com/All-Hands-AI/OpenHands","Open-source platform for autonomous coding agents.","coding",OC,"Mature",B),
("Aider","https://aider.chat","Pair-programming agent in your terminal that commits changes to git.","coding",OS,"Mature",B),
("Cline","https://github.com/cline/cline","Autonomous coding agent inside VS Code with step-by-step approvals.","coding",OS,"Mature",B),
("Roo Code","https://github.com/RooCodeInc/Roo-Code","VS Code agent with custom modes (architect, code, debug).","coding",OS,"Mature",B),
("Windsurf","https://windsurf.com","AI IDE with the Cascade agent.","coding",FP,"Mature",R),
("opencode","https://github.com/sst/opencode","Open-source terminal coding agent that works with many model providers.","coding",OS,"Active",B),
("Amp","https://ampcode.com","Agentic coding tool for the terminal and editor.","coding","Paid (usage-based)","Active",B),
("Gemini CLI","https://github.com/google-gemini/gemini-cli","Google's open-source terminal agent powered by Gemini.","coding","Open source; free tier","Mature",B),
("GitHub Copilot","https://github.com/features/copilot","AI pair programmer with a coding agent that works from issues.","coding",FP,"Mature",R),
("Replit Agent","https://replit.com","Builds and deploys full apps from a prompt in the browser.","app builders",FP,"Mature",R),
("Bolt","https://bolt.new","Prompt-to-app builder that runs full-stack apps in the browser.","app builders",FP,"Mature",R),
("v0","https://v0.app","Vercel's agent that generates and deploys web apps and UI.","app builders",FP,"Mature",R),
("Browser Use","https://github.com/browser-use/browser-use","Library that lets AI agents control a web browser.","browser/computer use",OC,"Mature",B),
("Browserbase","https://www.browserbase.com","Hosted headless browsers built for agents.","browser/computer use",FP,"Mature",B),
("Stagehand","https://github.com/browserbase/stagehand","Browser automation framework mixing code with natural-language actions.","browser/computer use",OS,"Mature",B),
("Playwright MCP","https://github.com/microsoft/playwright-mcp","Microsoft's MCP server giving agents browser control via Playwright.","browser/computer use",OS,"Mature",B),
("Skyvern","https://www.skyvern.com","Automates browser workflows with vision + LLMs.","browser/computer use",OC,"Active",B),
("Manus","https://manus.im","General-purpose autonomous agent that does research and tasks in a cloud computer.","personal agents",FP,"Mature",R),
("OpenClaw","https://github.com/openclaw/openclaw","Open-source personal agent you run yourself and reach over chat apps.","personal agents",OS,"Active",B),
("LangGraph","https://github.com/langchain-ai/langgraph","Framework for stateful, graph-based agent workflows.","frameworks",OS,"Mature",B),
("CrewAI","https://github.com/crewAIInc/crewAI","Framework for role-based multi-agent crews.","frameworks",OC,"Mature",B),
("AutoGen","https://github.com/microsoft/autogen","Microsoft's framework for multi-agent conversations.","frameworks",OS,"Mature",B),
("Pydantic AI","https://github.com/pydantic/pydantic-ai","Type-safe Python agent framework from the Pydantic team.","frameworks",OS,"Mature",B),
("Google ADK","https://github.com/google/adk-python","Google's Agent Development Kit for building and deploying agents.","frameworks",OS,"Mature",B),
("Mastra","https://mastra.ai","TypeScript framework for agents, workflows and RAG.","frameworks",OS,"Active",B),
("smolagents","https://github.com/huggingface/smolagents","Hugging Face's minimal library for code-writing agents.","frameworks",OS,"Active",B),
("LlamaIndex","https://github.com/run-llama/llama_index","Framework for agents over your data (RAG, document agents).","frameworks",OC,"Mature",B),
("Vercel AI SDK","https://ai-sdk.dev","TypeScript toolkit for building AI apps and agents.","frameworks",OS,"Mature",B),
("GPT Researcher","https://github.com/assafelovic/gpt-researcher","Autonomous agent that researches the web and writes cited reports.","research",OS,"Mature",B),
("Elicit","https://elicit.com","Research assistant that finds and summarizes academic papers.","research",FP,"Mature",R),
("STORM","https://github.com/stanford-oval/storm","Stanford system that writes Wikipedia-style articles from web research.","research",OS,"Research project",B),
("Firecrawl","https://firecrawl.dev","Turns websites into clean, LLM-ready data for agents.","research",OC,"Mature",B),
("Exa","https://exa.ai","Search API built for AI agents.","research","Paid API with free credits","Mature",B),
("Tavily","https://tavily.com","Search and extraction API tuned for agents.","research","Paid API with free tier","Mature",B),
("LiveKit Agents","https://www.livekit.io","Real-time voice and video infrastructure with an agents framework.","voice",OC,"Mature",B),
("Pipecat","https://github.com/pipecat-ai/pipecat","Open-source framework for voice and multimodal conversational agents.","voice",OS,"Mature",B),
("Vapi","https://vapi.ai","Platform for building and deploying phone voice agents.","voice","Usage-based","Mature",B),
("ElevenLabs Agents","https://elevenlabs.io","Voice AI platform with conversational agents and TTS.","voice",FP,"Mature",R),
("Retell AI","https://www.retellai.com","Builds AI phone agents for calls and support.","voice","Usage-based","Mature",R),
("n8n","https://n8n.io","Workflow automation with AI agent nodes; self-host or cloud.","no-code builders","Self-host free; paid cloud","Mature",R),
("Make","https://www.make.com","Visual automation platform with AI agents.","no-code builders",FP,"Mature",R),
("Zapier Agents","https://zapier.com/agents","AI agents that act across 7,000+ Zapier apps.","no-code builders",FP,"Mature",R),
("Lindy","https://www.lindy.ai","No-code AI assistants for email, meetings and ops.","no-code builders",FP,"Mature",R),
("Relevance AI","https://www.relevanceai.com","No-code platform to build AI agent teams for business work.","no-code builders",FP,"Mature",R),
("Dify","https://github.com/langgenius/dify","Open-source platform for building LLM apps and agents visually.","no-code builders",OC,"Mature",R),
("Flowise","https://github.com/FlowiseAI/Flowise","Drag-and-drop builder for agents and LLM flows.","no-code builders",OC,"Mature",R),
("Model Context Protocol","https://modelcontextprotocol.io","Open standard for connecting agents to tools and data.","MCP & infra","Open standard","Mature",B),
("MCP reference servers","https://github.com/modelcontextprotocol/servers","Official collection of reference MCP servers.","MCP & infra",OS,"Mature",B),
("Smithery","https://smithery.ai","Registry for finding and installing MCP servers.","MCP & infra","Free + paid","Active",B),
("E2B","https://e2b.dev","Secure cloud sandboxes for running agent-generated code.","MCP & infra",OC,"Mature",B),
("Modal","https://modal.com","Serverless compute and sandboxes for AI workloads.","MCP & infra","Usage-based, free credits","Mature",B),
("Composio","https://composio.dev","Tool integrations and auth for agents across hundreds of apps.","MCP & infra",FP,"Mature",B),
("Mem0","https://github.com/mem0ai/mem0","Memory layer for AI agents.","MCP & infra",OC,"Mature",B),
("Letta","https://github.com/letta-ai/letta","Framework for stateful agents with long-term memory (formerly MemGPT).","frameworks",OC,"Mature",B),
("LangSmith","https://www.langchain.com/langsmith","Tracing, evals and monitoring for LLM apps and agents.","evals & observability",FP,"Mature",B),
("Langfuse","https://langfuse.com","Open-source LLM observability, tracing and evals.","evals & observability",OC,"Mature",B),
("Braintrust","https://www.braintrust.dev","Evals and observability platform for AI products.","evals & observability",FP,"Mature",B),
("Arize Phoenix","https://github.com/Arize-ai/phoenix","Open-source tracing and evaluation for LLM apps.","evals & observability",OS,"Mature",B),
("W&B Weave","https://wandb.ai/site/weave","Weights & Biases toolkit for tracing and evaluating agents.","evals & observability",FP,"Mature",B),
("AgentOps","https://agentops.ai","Monitoring and session replay for AI agents.","evals & observability",FP,"Active",B),
("Helicone","https://www.helicone.ai","Open-source LLM observability and gateway.","evals & observability",OC,"Mature",B),
]
k=["name","url","description","category","pricing","maturity","audience"]
for t in E: tools.append(dict(zip(k,t),featured=False,new=False,verified="2026-10-14"))
for i,t in enumerate(tools): t["id"]=i+1
json.dump(tools,open("tools.json","w"),indent=2,ensure_ascii=False)
from collections import Counter
print(len(tools),Counter(t["category"] for t in tools),Counter(t["audience"] for t in tools),sum(t["new"] for t in tools))
