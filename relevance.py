"""Relevance score for (tool, task) pairs. Used by build_tasks.match() and scripts/check_relevance.py.
Rule: category/use-case match = 3; strong term in the name = 3; each distinct strong term in the description = 2;
each distinct weak term = 1; global and per-task negative contexts are removed first. A tool is listed when score >= MIN.
Tasks not in RX keep their old single-regex rule, minus the global negative contexts."""
import re
ART_CATS={"image generation","graphic design & branding","3D & concept art","photography & photo editing"}
NEG_GLOBAL=r"designed (?:to|for|with|around)|by design|visual (?:builder|workflow|editor|studio|playground|debugg\w*|canvas|interface|programming|flow)|prompt design|design docs?|system design|api design|schema design|data[- ]driven|enterprise[- ]grade|retrieval[- ]augmented|supports? (?:for|multiple|many|all|any|\d|MCP|models|OpenAI|local|both|over)|support(?:s|ed)? (?:by|with)"
# per-task (strong, weak, neg, extra_cats, extra_ucs)
RX={
"building-mcp-servers":(r"registry for (?:finding|publishing)|gateway and registry|scanner (?:that checks|for) MCP|building, testing and deploying MCP|testing (?:and debugging )?MCP servers|testing and evals platform for MCP|(?:Java|Python|TypeScript|Kotlin|C#|Go|Rust|Ruby|Swift) SDK|build(?:ing)? (?:your own |custom |production[- ]ready )?MCP servers?|MCP (?:SDK|framework|server framework)|framework for (?:building|creating) MCP|creat(?:e|ing) MCP servers|MCP (?:registry|inspector|gateway|proxy|hosting)|(?:API|OpenAPI|REST)[^.]{0,40}(?:into|to) (?:an )?MCP|OpenAPI[- ]to[- ]MCP|\bSDK for (?:the )?Model Context Protocol",None,None),
"making-images-and-design":(r"image (?:and video )?generat|Figma|Canva|design (?:context|system|assets|files|data)|editing images|images, video|asset generation|background removal|designing and managing|image generat|generat\w* (?:images|art|pictures)|text-to-image|graphic design|logos?\b|illustrat|\bUI design|mockups?|diagrams?|infographic|posters?|photo edit|vector (?:art|graphics|illustrations?|logos?)|\bSVG\b",r"\bimages?\b|\bdesign\b|visuals?\b",r"computer vision|object detection|label(?:l)?ing|annotat|segmentation|video analytics|image search|vector (?:database|search|store|index)|multimodal (?:database|search|data)"),
"data-analysis":(r"databases?\b|data apps?|data analy|spreadsheets?|business intelligence|\bBI\b|data science|notebooks?|charts?\b|text-to-SQL|SQL (?:queries|databases?)|data (?:platform|warehouses?)|datasets?\b|spatial|campaign performance",r"\bdata\b|analytics|dashboards?|\bSQL\b|quer(?:y|ies)\b|metrics",r"web data pipelines|verified datasets|label-quality analytics|support analytics|mission-control dashboard|monetization and analytics|SQL schemas|text-to-SQL on|data (?:scraping|extraction|label\w*)|(?:market|on-chain|blockchain|crypto|price|token|web) data"),
"making-videos":(r"(?:images?|audio),? (?:and )?video|video(?:,| and) (?:audio|images?|voice)|videos? from|into (?:\w+ )?videos?|\bMP4|video agents?|video (?:generat|edit|creat|production|clips?)|generat\w* (?:short )?videos?|text-to-video|AI videos?|edit(?:s|ing)? videos?|short-form|avatar videos?|explainer videos?",r"video",r"(?:web|image|news),? (?:and )?video|voice and video|real-time (?:voice and )?video|label\w*|detection|video (?:call|meeting|understanding|analytics|search|stream|frames|feeds)"),
"searching-the-web":(r"search API|web search|search engine|search the web|\bSERP",None,None),
"monitoring-agents":(r"monitor|session replay|log exploration|uptime|observab|tracing|traces\b|LLM monitoring|agent monitoring|logging|monitor(?:s|ing)? (?:your )?(?:agents?|LLM|AI|prompts|production)",r"monitor",r"(?:extraction|portfolio|metered) (?:and )?monitor\w*|monitor(?:,)? and (?:earn|maintain)|traces stolen|DNS analytics|observable apps|monitor content|security monitoring|monitor(?:s|ing)? (?:models|data sources|deals|portfolios|filings|markets?|wallets?|prices?|websites?|competitors?|changes|calls|news|brands?|pages|positions)|on-chain"),
"business-automation":(r"enterprise (?:agents?|AI agents?|agentic|RPA|automation|workflows?|customer service|service)|\bRPA\b|integration platform|AI workers|for (?:finance|legal|IT|go-to-market) teams|IT operations|call automation|back[- ]office|business process|operations teams?|finance teams?|\bHR\b|procurement|invoices?|accounts payable|\bERP\b|business agents?|automat\w* (?:business|company|enterprise) (?:work|process)",r"enterprise|operations",None),
"phone-calls":(r"phone (?:agents?|voice|calls?|numbers? for|lines?)|(?:voice|AI|phone|inbound|outbound|business|customer|sales|support|real) calls\b|calls and (?:support|SMS)|answers? (?:every |business |the )?(?:phone|calls?)|places? (?:phone )?calls|calls leads|call cent(?:er|re)|call automation|inbound (?:and outbound )?calls?|outbound calls?|telephon|over the phone|replays? real calls",r"\bphone\b",r"phone numbers? (?:lookup|data|enrichment|and email)|work emails and phone numbers|business names, phone numbers|contact data|(?:tool|function|API|LLM|MCP|network|failing|video|pay-per) calls|calls (?:tools|APIs|functions|MiniMax)|calls \d+|(?:framework|agent|model) calls|\d+-day calls|email, chat, docs, tasks, calls|phone app|discovery call|real sales calls"),
"testing-apps":(r"testing agents|Cypress|test results|(?:runs?|edits? and|and) tests?\b|test (?:workflows|executions)|testing (?:and|&) debugging|build(?:ing)?, test|develop and test|tests-to-run|testing and evals|\bQA\b|end-to-end tests?|\bE2E\b|test automation|(?:unit|integration|regression|UI|browser|mobile app|web app) tests?|tests? (?:your|web|mobile) apps?|test cases?|testing (?:apps|web|mobile)",r"\btest(?:s|ing)?\b",r"backtest|A/B test|stress[- ]test|test(?:s|ing)? (?:prompts|agents|voice agents|trading|strategies)"),
"agent-security":(r"penetration test|pentest|vulnerabilit|threats?\b|\bSOC\b|security (?:analysis|testing|scan\w*|risks?|alerts?|automation|operations|monitoring|for|and governance)|identity (?:security|and access)|secures\b|polic(?:y|ies)[- ](?:gated|controls?)|policy controls|access (?:control|policy|layer)|permission[- ]gated|permissions\b|guardrail|prompt injection|red[- ]team|jailbreak|(?:agent|AI|LLM|MCP) (?:security|safety|governance)|secur(?:e|ity) (?:for|of) (?:AI|agents|LLM)|policy enforcement|\bPII\b|\bDLP\b|access control|least privilege|security and (?:observability|compliance|IT)|(?:semantic|layered) security|deny-first",r"secur|safety|permission|policy|governance",r"(?:on-chain|DAO|token|protocol) governance|type[- ]safe|safety of (?:your )?funds"),
"scoring":(r"\bscore\b|soundtrack|background music|royalty-free|compos(?:e|er|ing|es) (?:music|scores?|songs?)|music compos|music generat|songs?\b",None,None),
"customer-support":(r"(?:calls|sales) and support|support bots?|handles? customer|help ?desk|customer service|customer support|support tickets?|ticketing|support (?:agents?|teams?|inbox)",r"support|ticket",None),
"documents":(r"\bRAG\b|documents?\b|\bPDFs?\b|knowledge base|\bOCR\b|contracts?\b|invoices?",r"\bRAG\b",r"LLM-ready Markdown|RAG systems|evals, RAG|RAG pipelines|task, PDF|approvals or documents|documentation|RAG chunks|RAG evals?|for RAG|LLM-ready|smart[- ]contracts?|token transfers, contracts|discovery documents"),
"chat-apps":(r"Telegram|WhatsApp|iMessage|\bDiscord\b",r"\bSlack\b(?! alerts)",None),
}
CATS={"making-videos":({"video generation","film & TV production"},set()),  # extra categories counted as a match
 "data-analysis":({"data & analytics"},set()),
 "testing-apps":({"QA & testing"},set()),
 "devops-and-incidents":({"DevOps & cloud"},set()),
 "business-automation":({"finance & accounting","legal & compliance","HR & recruiting","e-commerce & retail","healthcare & biotech"},set())}
def text(x,pricing=False): return re.sub(NEG_GLOBAL,' ',f'{x.get("description","")}'+(f' {x.get("pricing","")}' if pricing else ''),flags=re.I)
def score(x,T):
    slug,_,cats,ucs,rx,_=T
    if slug in CATS: cats=set(cats)|CATS[slug][0]; ucs=set(ucs)|CATS[slug][1]
    if slug not in RX:   # unchanged tasks: old rule minus global negatives
        if x.get("category") in cats or set(x.get("use_cases",[]))&ucs: return 3
        return 3 if re.search(rx,x.get("name",""),re.I) or re.search(rx,text(x,True),re.I) else 0
    st,wk,ng=RX[slug]
    tx=text(x)
    if ng: tx=re.sub(ng,' ',tx,flags=re.I)
    if slug=="making-images-and-design" and x.get("category")=="vision": return 0
    if x.get("category") in cats or set(x.get("use_cases",[]))&ucs: return 3
    s=0
    if re.search(st,x.get("name",""),re.I): s+=3
    s+=2*len({m.group(0).lower() for m in re.finditer(st,tx,re.I)})
    if wk: s+=len({m.group(0).lower() for m in re.finditer(wk,tx,re.I)})
    return s
MIN=2

def relevant(x,T): return score(x,T)>=MIN
