import json
B,R="builders","ready to use"
T=[
("Hermes Agent (Nous Research)","https://github.com/NousResearch/hermes-agent","Open-source agent harness; v0.21.7 stable shipped Oct 12, v0.22.0 RCs Oct 13-14.","frameworks","Open source","Active, frequent releases",B),
("OpenAI Agents SDK (Python)","https://github.com/openai/openai-agents-python","OpenAI's Python SDK for building multi-agent workflows; v0.23.0/0.23.1 released Oct 1-2.","frameworks","Open source","Mature, official SDK",B),
("LangChain Deep Agents","https://github.com/langchain-ai/deepagents","Library for long-running agents with subagents and skills; 0.7.23 (Oct 7) adds pinned_skills.","frameworks","Open source","Active",B),
("GitHub Agentic Workflows (gh-aw)","https://github.com/github/gh-aw","Run AI agents in GitHub Actions workflows; v0.91.10 pre-release (Oct 13) defaults read-only workflows to no network.","coding","Open source","Pre-release",B),
("Jevgrep","https://github.com/dzhng/jevgrep","CLI that finds relevant repo files and excerpts from natural-language questions for coding agents; claims ~40% cheaper agent runs.","coding","Open source (MIT); needs a model provider key","Early (v0.1.x)",B),
("NVIDIA OpenShell","https://github.com/nvidia/openShell","Sandboxed runtime for autonomous agents with declarative YAML policies on file, network and credential access.","safety & infra","Open source (Apache 2.0)","Active; part of newly announced Open Agent Safety Platform",B),
("NVIDIA Open Agent Safety Platform","https://developer.nvidia.com/blog/nvidia-open-agent-safety-platform-a-reference-for-continuous-in-silicon-agent-monitoring/","Reference stack pairing OpenShell with NVIDIA Sentry on BlueField-4 DPUs for hardware-level agent monitoring.","safety & infra","OpenShell open source; hardware layer needs NVIDIA systems","Newly announced reference",B),
("CoreWeave Forge","https://forge.coreweave.com","One product to run, observe, evaluate and post-train agents (W&B, OpenPipe, sandboxes).","observability & evals","Free tier; Pro from $60/mo","Newly launched",B),
("Roboflow Agent","https://roboflow.com/blog/roboflow-agent","Computer-vision agent that picks models and builds/deploys vision apps; plugs into Claude Code, Codex, Cursor via MCP.","vision","Paid platform (see site)","Launched Oct 14",B),
("Voiceloop","https://github.com/todoforai/voiceloop","Zero-dependency JS library for an interruptible in-browser voice loop (VAD, STT, LLM, TTS).","voice","Open source (MIT)","Early",B),
("Cicero","https://github.com/5uck1ess/cicero","Self-hosted voice interface for coding agents (Claude Code, Codex, ACP); talk from a browser or Telegram call.","voice","Open source","Early",B),
("TryVoice","https://github.com/AaronZ021/tryvoice-oss","Hands-free voice runtime for coding agents with wake word, push-to-talk and streaming replies.","voice","Open source","Early",B),
("Holo4 (H Company)","https://huggingface.co/Hcompany","Open-weight computer-use models (27B and 35B-A3B) released Oct 1.","browser/computer use","Open weights","New release",B),
("Manifold MCP","https://hunted.space/product/manifold-mcp","Hosted MCP server giving agents SEO, AI-answer, social, ad and leads data.","MCP & integrations","Free to start","Launched Oct 12 (Product Hunt #5)",B),
("NanoMuse","https://github.com/nano-muse","Open-source AI agent for your phone and computer (Show HN, Oct 7).","personal agents","Open source","Early",B),
("OpenPilot","https://hunted.space/product/openpilot","Free desktop agent for any OpenAI-compatible model; edits files and runs commands in a folder with approvals.","personal agents","Free, open source (MIT)","Windows; macOS early beta",R),
("OpenSwarm","https://www.hunted.space/product/openswarm-3","AI-first 'operating system' where swarms of agents run apps and browsers in parallel.","browser/computer use","See site","Launched Oct 8 (Product Hunt #1 of day)",R),
("ExcaliClaw","https://hunted.space/product/excaliclaw","Hand-drawn diagram workspace your agent can draw in via MCP (Claude, Cursor, VS Code).","productivity","Free plan; paid from EUR 9/mo","Launched Oct 12",R),
("koodlo","https://hunted.space/dashboard/kodlo","Sales workspace whose agent finds prospects and drafts outreach, decks and searches; has an MCP server.","sales","See site","Launched Oct 11 (Product Hunt #2 of day)",R),
("Trig","https://www.trig.ai/blog/a-new-way-to-manage-your-customers","Rebuilt as an agent workspace for account managers: agents follow up, prep renewals, build expansion cases.","customer success","Paid (see site)","Relaunched Oct 13",R),
("Cresta Deputy Agent","https://cresta.com/deputy-agent","Long-running agent that finishes customer-service back-office workflows, pausing for approvals or documents.","customer support","Enterprise, paid","Launched Oct 13",R),
("Meta Muse Wonder","https://research.meta.ai/blog/muse-wonder","Meta's new models for personal and professional agent tasks, available via Meta Model API and Muse Code.","models for agents","Paid API / subscription","Released Oct 12",R),
]
names=["name","url","description","category","pricing","maturity","audience"]
tools=[dict(zip(names,t),id=i+1,featured=False,verified="2026-10-14") for i,t in enumerate(T)]
tools[0]["featured"]=True
json.dump(tools,open("tools.json","w"),indent=2)
print(len(tools))
