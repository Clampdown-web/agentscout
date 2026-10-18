"""AgentScout's own browser-only free tools in free-tools/ (Oct 18 2026 batch). Called from build_extras.build().
Everything runs in the visitor's browser: no API calls, no servers, no fees. Prices come from assets/ai-prices.json,
copied by hand from each provider's official pricing page (date in "checked")."""
import json,os
import build_extras as X
B=X.B; e=X.e
CAP=lambda s:s[:1].upper()+s[1:]
INP='style="width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--text);font:inherit;box-sizing:border-box"'
LAB='style="display:block;margin:14px 0 6px;font-weight:600;font-size:14px"'
OUT='style="width:100%;min-height:260px;padding:12px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--text);font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;box-sizing:border-box;white-space:pre"'
BOX='style="border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:18px 0;background:var(--card)"'
# Shared approximate tokenizer (an estimate, not any vendor's real tokenizer)
TOK=r'''function asTok(s){if(!s)return 0;var n=0,re=/[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]|'(?:s|t|re|ve|m|ll|d)\b| ?[A-Za-z\u00C0-\u024F]+| ?[0-9]{1,3}| ?[^\sA-Za-z0-9\u00C0-\u024F\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]+|\s+/g,m;while((m=re.exec(s))){var p=m[0],w=p.replace(/^ /,"");if(/^\s+$/.test(p)){n+=p.indexOf("\n")>=0?p.split("\n").length-1:1;continue}if(/^[A-Za-z\u00C0-\u024F]+$/.test(w)){n+=w.length<=7?1:Math.ceil(w.length/4.5)}else if(/^[0-9]+$/.test(w)){n+=1}else if(w.length===1&&/[\u3040-\u9fff\uac00-\ud7af]/.test(w)){n+=1}else{n+=Math.ceil(w.length/2)}}return n}
function asCopy(id,btn){var v=document.getElementById(id);navigator.clipboard.writeText(v.value!==undefined?v.value:v.textContent).then(function(){var o=btn.textContent;btn.textContent="Copied";setTimeout(function(){btn.textContent=o},1500)})}'''
TOOLS=[
("ai-cost-calculator","AI API Cost Calculator","Estimate what an AI model costs per request, per day and per month. Compare GPT, Claude, Gemini and Grok API prices side by side.","🧮"),
("token-counter","AI Token Counter","Paste text and get an instant estimate of how many tokens it uses, plus words, characters and what it costs as input.","🔢"),
("prompt-builder","AI Prompt Builder","Fill in a few fields and get a clear, well-structured prompt for ChatGPT, Claude, Gemini or Grok. Copy it in one click.","🧱"),
("agent-setup-generator","AI Agent Setup Generator","Generate starter config files and system prompts for Claude Code, Codex, Cursor, CrewAI, LangChain and the OpenAI Agents SDK.","🤖"),
]
REL={"ai-cost-calculator":(["python-ai-agent-frameworks","open-source-llm-observability-tools","web-search-apis-for-ai-agents","free-ai-coding-agents"],["ai-engineers","developers","founders"]),
 "token-counter":(["open-source-llm-observability-tools","open-source-ai-research-agents"],["ai-engineers","developers","researchers"]),
 "prompt-builder":(["ai-research-assistants","free-ai-coding-agents"],["marketers","content-creators","researchers"]),
 "agent-setup-generator":(["terminal-ai-coding-agents","open-source-ai-agent-frameworks","multi-agent-frameworks","free-mcp-servers"],["developers","ai-engineers","security-engineers"])}
def rel(s):
    import build_landing as L
    st={p[0]:p[1] for p in L.S}; rn={r[0]:r[1] for r in L.R}; a,b=REL[s]
    return ('<p style="margin-top:28px">Popular searches: '+" · ".join(f'<a href="../s/{x}.html">{e(st[x])}</a>' for x in a if x in st)+'</p>'
            '<p>Popular with: '+" · ".join(f'<a href="../for/{x}.html">{e(CAP(rn[x]))}</a>' for x in b if x in rn)+'</p>')
def others(s): return " · ".join(f'<a href="{t[0]}.html">{e(t[1])}</a>' for t in TOOLS if t[0]!=s)
def wrap(s,h1,lede,inner,faq,js,t):
    slug,name,desc,_=next(x for x in TOOLS if x[0]==s)
    canon=f"{B}free-tools/{s}.html"; title=f"Free {name} (2026, no sign-up) · AgentScout"
    ld={"@context":"https://schema.org","@graph":[{"@type":"WebApplication","name":f"AgentScout {name}","url":canon,"description":desc,"applicationCategory":"DeveloperApplication","operatingSystem":"Any (runs in your browser)","isAccessibleForFree":True,"offers":{"@type":"Offer","price":"0","priceCurrency":"USD"},"publisher":{"@type":"Organization","name":"AgentScout","url":B}},
        {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq]},
        {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"AgentScout","item":B},{"@type":"ListItem","position":2,"name":"Free tools","item":B+"free-tools.html"},{"@type":"ListItem","position":3,"name":name,"item":canon}]}]}
    fq="".join(f'<h3 style="font-size:15px;margin:18px 0 4px">{e(q)}</h3><p style="margin:0">{e(a)}</p>' for q,a in faq)
    body=(f'<div class="crumb"><a href="../index.html">AgentScout</a> / <a href="../free-tools.html">Free tools</a> / {e(name)}</div><section style="padding-top:20px;text-align:left;max-width:860px">'
          f'<h1 style="text-align:left;margin-left:0">{e(h1)}</h1><p class="lede" style="margin-left:0;text-align:left">{lede}</p>'
          f'<p class="muted" style="margin:0 0 8px;font-size:13.5px">Free, no sign-up. Runs entirely in your browser: nothing you type is sent to AgentScout or any AI provider.</p>'
          f'{inner}<h2 style="font-size:18px;margin:36px 0 6px">FAQ</h2>{fq}{rel(s)}'
          f'<p>More free tools from AgentScout: {others(s)} · <a href="../generate.html">Free AI image generator</a> · <a href="../free-tools.html">All free tools</a></p></section><script>{TOK}\n{js}</script>')
    os.makedirs("free-tools",exist_ok=True)
    open(f"free-tools/{s}.html","w").write(X.shell("../",title,desc,canon,body,ld)); return canon

def cost(t,P):
    rows=[]
    for p in P["providers"]:
        for m in p["models"]: rows.append({"p":p["name"],"id":m["id"],"in":m["in"],"c":m.get("cached",m["in"]),"out":m["out"],"n":m.get("note","")})
    opts="".join(f'<optgroup label="{e(p["name"])}">'+"".join(f'<option value="{e(m["id"])}">{e(m["id"])}</option>' for m in p["models"])+"</optgroup>" for p in P["providers"])
    src="".join(f'<li><a href="{e(p["source"])}" target="_blank" rel="noopener noreferrer">{e(p["name"])} pricing</a>: {e(p.get("context_note",""))}</li>' for p in P["providers"])
    num=lambda id,lab,v,extra="":f'<div><label {LAB} for="{id}">{lab}</label><input id="{id}" type="number" min="0" step="any" value="{v}" {extra} {INP}></div>'
    inner=(f'<div {BOX}><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:0 16px">'
           f'<div><label {LAB} for="cm">Model</label><select id="cm" {INP}>{opts}</select></div>'
           +num("ci","Input tokens per request",2000)+num("co","Output tokens per request",500)+num("cc","Cached share of input (%)",0,'max="100"')+num("cr","Requests per day",1000)+
           '</div><div id="cres" style="margin-top:18px;display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px"></div><p id="cnote" class="muted" style="font-size:13px;margin:10px 0 0"></p></div>'
           '<h2 style="font-size:18px;margin:28px 0 6px">Compare every model at these numbers</h2><p class="muted" style="font-size:13.5px;margin:0 0 10px">Sorted by monthly cost (30 days). Click a row to select it.</p>'
           '<div style="overflow-x:auto"><table id="ctab" style="width:100%;border-collapse:collapse;font-size:14px"><thead><tr style="text-align:left;border-bottom:1px solid var(--line)"><th style="padding:6px">Model</th><th style="padding:6px">Provider</th><th style="padding:6px">Input $/1M</th><th style="padding:6px">Output $/1M</th><th style="padding:6px">Per request</th><th style="padding:6px">Per month</th></tr></thead><tbody></tbody></table></div>'
           f'<h2 style="font-size:18px;margin:28px 0 6px">Where these prices come from</h2><p style="margin:0 0 6px">Prices checked on <b>{e(P["checked"])}</b> from each provider\'s official pricing page, in US dollars per 1 million tokens, standard (non-batch) tier, short-context rates. Batch, flex and cached-write pricing, long prompts, data-residency uplifts and tool fees (like web search) are not included.</p><ul style="margin:0;padding-left:20px;font-size:14px">{src}</ul>'
           '<p class="muted" style="font-size:13px">Prices change often. Always confirm on the provider page before you budget. Need a token count first? Try the <a href="token-counter.html">token counter</a>.</p>')
    js=("var R="+json.dumps(rows)+r''';function $(i){return document.getElementById(i)}function v(i){var x=parseFloat($(i).value);return isFinite(x)&&x>0?x:0}
function f(x){return x>=100?"$"+x.toLocaleString(undefined,{maximumFractionDigits:0}):x>=1?"$"+x.toFixed(2):x>=0.01?"$"+x.toFixed(3):"$"+x.toPrecision(2)}
function c(m){var i=v("ci"),o=v("co"),cs=Math.min(v("cc"),100)/100;return(i*(1-cs)*m.in+i*cs*m.c+o*m.out)/1e6}
function run(){var m=R.filter(function(x){return x.id===$("cm").value})[0]||R[0],per=c(m),d=per*v("cr");
$("cres").innerHTML=[["Per request",per],["Per day",d],["Per month (30 days)",d*30],["Per year",d*365]].map(function(x){return '<div class="card" style="padding:12px"><div class="muted" style="font-size:12.5px">'+x[0]+'</div><div style="font-size:22px;font-weight:700">'+f(x[1])+'</div></div>'}).join("");
$("cnote").textContent=m.p+" "+m.id+": $"+m.in+" input, $"+m.c+" cached input, $"+m.out+" output per 1M tokens."+(m.n?" Note: "+m.n+".":"");
var s=R.slice().sort(function(a,b){return c(a)-c(b)});$("ctab").tBodies[0].innerHTML=s.map(function(x){var on=x.id===m.id;return '<tr data-id="'+x.id+'" style="cursor:pointer;border-bottom:1px solid var(--line)'+(on?';background:var(--line)':'')+'"><td style="padding:6px"><b>'+x.id+'</b>'+(x.n?' <span class="muted" style="font-size:12px">('+x.n+')</span>':'')+'</td><td style="padding:6px">'+x.p+'</td><td style="padding:6px">$'+x.in+'</td><td style="padding:6px">$'+x.out+'</td><td style="padding:6px">'+f(c(x))+'</td><td style="padding:6px">'+f(c(x)*v("cr")*30)+'</td></tr>'}).join("")}
["cm","ci","co","cc","cr"].forEach(function(i){$(i).addEventListener("input",run)});$("ctab").addEventListener("click",function(ev){var r=ev.target.closest("tr[data-id]");if(r){$("cm").value=r.dataset.id;run();window.scrollTo({top:$("cm").getBoundingClientRect().top+scrollY-120,behavior:"smooth"})}});
try{var q=new URLSearchParams(location.search);if(q.get("in"))$("ci").value=q.get("in");if(q.get("model"))$("cm").value=q.get("model")}catch(e){}run();''')
    faq=[("How is the cost calculated?","Cost per request = (uncached input tokens × input price + cached input tokens × cached price + output tokens × output price) ÷ 1,000,000. Daily cost multiplies by requests per day; monthly uses 30 days."),
         ("Are these prices current?",f"They were copied from the official OpenAI, Anthropic, Google and xAI pricing pages on {P['checked']}. Providers change prices and add models often, so confirm on the linked pages."),
         ("Why do reasoning models cost more than the calculator shows?","Thinking or reasoning tokens are billed as output tokens. If a model thinks before answering, add those tokens to the output figure."),
         ("Does the calculator include batch or cached-write discounts?","No. It uses standard rates. Batch APIs are usually about 50% cheaper, and cache writes can cost more than plain input. Check each provider page.")]
    return wrap("ai-cost-calculator","AI API cost calculator","Estimate what an AI model will cost you per request, per day and per month, then compare "+str(len(rows))+" GPT, Claude, Gemini and Grok models at the same usage.",inner,faq,js,t)

def tokens(t,P):
    opts="".join(f'<option value="{e(m["id"])}" data-in="{m["in"]}">{e(p["name"])} {e(m["id"])} (${m["in"]}/1M input)</option>' for p in P["providers"] for m in p["models"])
    inner=(f'<div {BOX}><label {LAB} for="tt">Your text</label><textarea id="tt" rows="10" placeholder="Paste a prompt, document or chat log here…" {INP}></textarea>'
           '<div id="tres" style="margin-top:14px;display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px"></div>'
           f'<label {LAB} for="tm">Input cost for this text on</label><select id="tm" {INP}>{opts}</select><p id="tcost" style="margin:10px 0 0;font-weight:600"></p>'
           '<p style="margin:12px 0 0"><button class="btn" type="button" id="tclr">Clear</button> <a class="btn" id="tcalc" href="ai-cost-calculator.html">Open in the cost calculator</a></p></div>'
           '<h2 style="font-size:18px;margin:28px 0 6px">How accurate is this?</h2><p>This is an <b>estimate</b>. It splits text the way modern byte-pair tokenizers roughly do (short common words are one token, long words, symbols and numbers split into several), but it is not OpenAI\'s, Anthropic\'s, Google\'s or xAI\'s real tokenizer. For plain English it usually lands within about 10–15% of real counts. Code, non-English text and unusual symbols vary more.</p>'
           '<p>Different models count the same text differently. Anthropic says Claude 4.7 and later models use a newer tokenizer that makes about 30% more tokens for the same text, so the counter also shows that figure. For exact counts, use each provider\'s token-counting API or the usage numbers in an API response.</p>')
    js=r'''function $(i){return document.getElementById(i)}function run(){var s=$("tt").value,n=asTok(s),w=(s.match(/\S+/g)||[]).length;
$("tres").innerHTML=[["Estimated tokens",n],["Claude 4.7+ (≈ +30%)",Math.round(n*1.3)],["Rule of thumb (chars ÷ 4)",Math.ceil(s.length/4)],["Words",w],["Characters",s.length]].map(function(x){return '<div class="card" style="padding:12px"><div class="muted" style="font-size:12.5px">'+x[0]+'</div><div style="font-size:22px;font-weight:700">'+x[1].toLocaleString()+'</div></div>'}).join("");
var o=$("tm").selectedOptions[0],p=parseFloat(o.dataset.in),c=n*p/1e6;$("tcost").textContent="≈ $"+(c>=0.01?c.toFixed(4):c.toPrecision(2))+" as input ("+n.toLocaleString()+" tokens × $"+p+" per 1M)";
$("tcalc").href="ai-cost-calculator.html?in="+n+"&model="+encodeURIComponent(o.value)}
$("tt").addEventListener("input",run);$("tm").addEventListener("change",run);$("tclr").addEventListener("click",function(){$("tt").value="";run()});run();'''
    faq=[("What is a token?","A token is a chunk of text a language model reads or writes, often a short word or part of a longer word. In English, one token is about 4 characters or three-quarters of a word on average."),
         ("Is this the exact token count?","No. It is an approximation that runs in your browser. Real counts depend on each model's tokenizer; use the provider's token-counting API when you need exact numbers."),
         ("Is my text uploaded anywhere?","No. Counting happens in your browser with JavaScript. Nothing is sent to AgentScout or to any AI provider."),
         ("Why count tokens?","API prices, context-window limits and rate limits are all measured in tokens, so a token count tells you whether a prompt fits and what it will cost.")]
    return wrap("token-counter","AI token counter (estimate)","Paste any text to estimate its token count for GPT, Claude, Gemini and Grok models, see words and characters, and check what it costs as input.",inner,faq,js,t)

def prompt(t):
    f=lambda id,lab,ph,rows=2:f'<label {LAB} for="{id}">{lab}</label><textarea id="{id}" rows="{rows}" placeholder="{e(ph)}" {INP}></textarea>'
    inner=(f'<div {BOX}><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:0 18px"><div>'
           +f("pr","Role (who the AI should act as)","e.g. a senior product marketer at a B2B SaaS company",1)
           +f("pt","Task (what you want done) *","e.g. Write three subject lines for our launch email",3)
           +f("pc","Context and background","Facts, audience details, links, the draft to edit…",4)
           +'</div><div>'
           +f("pa","Audience","e.g. busy engineering managers",1)
           +f("pf","Output format","e.g. a numbered list, a table, JSON with keys title and body",1)
           +f("pk","Rules and constraints","e.g. under 60 characters each; no emojis; UK spelling",2)
           +f("pe","Example of a good answer (optional)","Paste one example the AI should copy the style of",2)
           +f'<label {LAB} for="pn">Tone</label><select id="pn" {INP}><option value="">No preference</option><option>clear and friendly</option><option>formal and precise</option><option>concise and direct</option><option>persuasive</option><option>playful</option><option>technical</option></select>'
           +'</div></div><div style="display:flex;flex-wrap:wrap;gap:14px;margin:16px 0 0;font-size:14px">'
           '<label><input type="radio" name="ps" value="md" checked> Markdown headings</label><label><input type="radio" name="ps" value="xml"> XML tags (good for Claude)</label><label><input type="radio" name="ps" value="plain"> Plain text</label>'
           '<label><input type="checkbox" id="pq"> Ask me questions first if anything is unclear</label><label><input type="checkbox" id="pth"> Think step by step before answering</label></div></div>'
           f'<label {LAB} for="po">Your prompt</label><textarea id="po" readonly rows="14" {OUT}></textarea>'
           '<p style="margin:10px 0 0"><button class="btn primary" type="button" onclick="asCopy(\'po\',this)">Copy prompt</button> <span id="pcount" class="muted" style="font-size:13.5px"></span></p>'
           '<h2 style="font-size:18px;margin:28px 0 6px">Tips for better prompts</h2><ul><li><b>Be specific about the task.</b> "Write three subject lines under 60 characters" beats "help with my email".</li><li><b>Give the context the AI can\'t guess:</b> who it is for, what has been tried, and what good looks like.</li><li><b>Say the format you want</b> so the answer is ready to paste.</li><li><b>One example is worth a paragraph of rules.</b></li><li>For long documents, put the document first and your question at the end.</li></ul>')
    js=r'''function $(i){return document.getElementById(i)}var F=[["pr","Role"],["pt","Task"],["pc","Context"],["pa","Audience"],["pf","Output format"],["pk","Rules"],["pe","Example"]];
function run(){var st=document.querySelector("input[name=ps]:checked").value,v={};F.forEach(function(x){v[x[0]]=$(x[0]).value.trim()});var tone=$("pn").value,out=[];
if(v.pr)out.push(st==="xml"?"You are "+v.pr+".":"You are "+v.pr+".");
var parts=[];F.slice(1).forEach(function(x){if(v[x[0]])parts.push([x[1],v[x[0]]])});if(tone)parts.push(["Tone","Write in a "+tone+" tone."]);
var ex=[];if($("pth").checked)ex.push("Think through the problem step by step before you give your final answer.");if($("pq").checked)ex.push("If anything important is unclear, ask me up to 3 short questions before you start.");if(ex.length)parts.push(["Instructions",ex.join("\n")]);
parts.forEach(function(p){var k=p[0],b=p[1];if(st==="xml"){var tg=k.toLowerCase().replace(/ /g,"_");out.push("<"+tg+">\n"+b+"\n</"+tg+">")}else if(st==="md"){out.push("## "+k+"\n"+b)}else{out.push(k+": "+b)}});
var s=out.join("\n\n");$("po").value=s||"Fill in at least the Task field to build your prompt.";$("pcount").textContent=s?"≈ "+asTok(s).toLocaleString()+" tokens (estimate)":""}
document.querySelectorAll("textarea:not([readonly]),select,input").forEach(function(el){el.addEventListener("input",run);el.addEventListener("change",run)});run();'''
    faq=[("Which AI models does this work with?","Any chat model: ChatGPT, Claude, Gemini, Grok, Llama and others. The XML style suits Claude well; Markdown and plain text work everywhere."),
         ("What makes a good prompt?","A clear task, the context the model can't guess, the audience, the output format and any hard rules. One good example helps a lot."),
         ("Is my prompt saved or sent anywhere?","No. The builder runs in your browser and nothing you type leaves your device."),
         ("Can I use the prompt as a system prompt?","Yes. Paste the Role, Rules and Tone parts into a system prompt and keep the Task for each message. For agents, try the agent setup generator.")]
    return wrap("prompt-builder","AI prompt builder","Fill in a few fields and get a clear, structured prompt for ChatGPT, Claude, Gemini or Grok. Choose Markdown, XML tags or plain text, then copy it.",inner,faq,js,t)

FW=[("claude-code","Claude Code","CLAUDE.md + .mcp.json"),("openai-codex-cli","OpenAI Codex CLI","AGENTS.md"),("cursor","Cursor","project rule (.mdc)"),
    ("crewai","CrewAI","agents.yaml + tasks.yaml"),("langchain","LangChain / LangGraph","Python, create_agent"),("openai-agents-sdk-python","OpenAI Agents SDK","Python"),("system","Any model","plain system prompt")]
def agent(t):
    bs={x["slug"] for x in t}
    opts="".join(f'<option value="{k}">{e(n)} ({e(d)})</option>' for k,n,d in FW)
    links=" · ".join(f'<a href="../tools/{k}.html">{e(n)}</a>' for k,n,_ in FW if k in bs)
    f=lambda id,lab,ph,v="",rows=2:f'<label {LAB} for="{id}">{lab}</label><textarea id="{id}" rows="{rows}" placeholder="{e(ph)}" {INP}>{e(v)}</textarea>'
    inner=(f'<div {BOX}><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:0 18px"><div>'
           f'<label {LAB} for="gf">Framework or tool</label><select id="gf" {INP}>{opts}</select>'
           f'<label {LAB} for="gn">Agent name</label><input id="gn" value="Support triage agent" {INP}>'
           +f("gp","What the agent does *","","Reads new support tickets, labels them by product area and urgency, and drafts a first reply for a human to approve.",3)
           +f("gs","Project or stack details (coding tools)","e.g. Next.js 15 app, TypeScript, pnpm, tests with Vitest","",2)
           +'</div><div>'
           +f("gr","Rules (one per line)","","Never send anything without human approval\nCite the ticket ID in every reply\nAsk when the product area is unclear",4)
           +f("gt","Tools it can use (one per line, name: what it does)","","search_docs: search the help center\nget_ticket: fetch a ticket by ID",3)
           +f'<label {LAB} for="gm">Model id (optional)</label><input id="gm" placeholder="e.g. gpt-6.1-sol (leave empty for the default)" {INP}>'
           +'</div></div></div>'
           '<div id="gout"></div>'
           f'<p class="muted" style="font-size:13.5px">These are starting points. Check each project\'s docs for the latest options. Framework pages on AgentScout: {links}.</p>'
           '<h2 style="font-size:18px;margin:28px 0 6px">What each file is for</h2><ul><li><b>CLAUDE.md</b> is read by Claude Code at the start of every session in that folder; <b>.mcp.json</b> adds project-scoped MCP servers.</li><li><b>AGENTS.md</b> is the instructions file OpenAI Codex CLI (and a growing list of other coding agents) read from your repo.</li><li><b>.cursor/rules/*.mdc</b> are Cursor project rules; <code>alwaysApply: true</code> includes the rule in every chat.</li><li><b>agents.yaml</b> and <b>tasks.yaml</b> live in <code>src/&lt;project&gt;/config/</code> of a CrewAI project.</li><li>The <b>LangChain</b> and <b>OpenAI Agents SDK</b> snippets are runnable Python starters; add your API key as an environment variable.</li></ul>')
    js=r'''function $(i){return document.getElementById(i)}function L(id){return $(id).value.split("\n").map(function(s){return s.trim()}).filter(Boolean)}
function slug(s){return(s.toLowerCase().replace(/[^a-z0-9]+/g,"_").replace(/^_|_$/g,"")||"agent")}function q(s){return JSON.stringify(s)}
function tl(){return L("gt").map(function(s){var i=s.indexOf(":");return i>0?[s.slice(0,i).trim(),s.slice(i+1).trim()]:[s,""]})}
function sys(){var n=$("gn").value.trim()||"Agent",p=$("gp").value.trim(),r=L("gr"),t=tl(),o="You are "+n+". "+p+"\n";if($("gs").value.trim())o+="\nProject: "+$("gs").value.trim()+"\n";
if(t.length)o+="\nTools you can use:\n"+t.map(function(x){return"- "+x[0]+(x[1]?": "+x[1]:"")}).join("\n")+"\n";if(r.length)o+="\nRules:\n"+r.map(function(x){return"- "+x}).join("\n")+"\n";
o+="\nWhen you finish, summarize what you did and anything that still needs a human.";return o}
function md(h){var n=$("gn").value.trim()||"Agent",o="# "+n+"\n\n"+$("gp").value.trim()+"\n";if($("gs").value.trim())o+="\n## Project\n"+$("gs").value.trim()+"\n";
var r=L("gr");if(r.length)o+="\n## Rules\n"+r.map(function(x){return"- "+x}).join("\n")+"\n";var t=tl();if(t.length)o+="\n## Tools\n"+t.map(function(x){return"- `"+x[0]+"`"+(x[1]?": "+x[1]:"")}).join("\n")+"\n";
return o+"\n"+h}
function files(){var fw=$("gf").value,n=$("gn").value.trim()||"Agent",s=slug(n),m=$("gm").value.trim(),t=tl(),p=$("gp").value.trim();
if(fw==="claude-code")return[["CLAUDE.md",md("## Workflow\n- Read the relevant files before editing.\n- Run the tests after changes and fix failures before you finish.\n- Keep changes small and explain them in the summary.\n")],[".mcp.json",JSON.stringify({mcpServers:{"example-server":{command:"npx",args:["-y","your-mcp-server-package"],env:{}}}},null,2)+"\n"]];
if(fw==="openai-codex-cli")return[["AGENTS.md",md("## Workflow\n- Explore the repo before making changes.\n- Run the project's tests and linters before you finish.\n- Prefer small, reviewable diffs.\n")]];
if(fw==="cursor")return[[".cursor/rules/"+s.replace(/_/g,"-")+".mdc","---\ndescription: "+(p.split(".")[0]||n)+"\nglobs:\nalwaysApply: true\n---\n\n"+md("")]];
if(fw==="crewai"){var y=function(x){return"    "+x.replace(/\n/g,"\n    ")};return[["config/agents.yaml",s+":\n  role: >\n"+y(n)+"\n  goal: >\n"+y(p)+"\n  backstory: >\n"+y("You follow these rules: "+(L("gr").join("; ")||"be accurate and concise")+".")+(m?"\n  llm: "+m:"")+"\n"],["config/tasks.yaml",s+"_task:\n  description: >\n"+y(p+" Input: {input}")+"\n  expected_output: >\n"+y("A short report of what was done, plus anything that needs a human.")+"\n  agent: "+s+"\n"]]}
if(fw==="langchain"){var fn=t.map(function(x){var f=slug(x[0]);return"@tool\ndef "+f+"(query: str) -> str:\n    \"\"\""+(x[1]||x[0])+"\"\"\"\n    return \"TODO: implement "+f+"\"\n"}).join("\n");
return[["agent.py","# pip install -U langchain langchain-openai  (or langchain-anthropic, langchain-google-genai)\nfrom langchain.agents import create_agent\nfrom langchain.tools import tool\n\n"+fn+"\nSYSTEM_PROMPT = "+q(sys())+"\n\nagent = create_agent(\n    model="+q(m?(m.indexOf(":")>0?m:"openai:"+m):"openai:gpt-6.1-sol")+",\n    tools=["+t.map(function(x){return slug(x[0])}).join(", ")+"],\n    system_prompt=SYSTEM_PROMPT,\n)\n\nresult = agent.invoke({\"messages\": [{\"role\": \"user\", \"content\": \"Hello\"}]})\nprint(result[\"messages\"][-1].content)\n"]]}
if(fw==="openai-agents-sdk-python"){var fn2=t.map(function(x){var f=slug(x[0]);return"@function_tool\ndef "+f+"(query: str) -> str:\n    \"\"\""+(x[1]||x[0])+"\"\"\"\n    return \"TODO: implement "+f+"\"\n"}).join("\n");
return[["agent.py","# pip install openai-agents   (export OPENAI_API_KEY=...)\nfrom agents import Agent, Runner, function_tool\n\n"+fn2+"\nagent = Agent(\n    name="+q(n)+",\n    instructions="+q(sys())+",\n"+(m?"    model="+q(m)+",\n":"")+"    tools=["+t.map(function(x){return slug(x[0])}).join(", ")+"],\n)\n\nresult = Runner.run_sync(agent, \"Hello\")\nprint(result.final_output)\n"]]}
return[["system-prompt.txt",sys()]]}
function esc(s){return s.replace(/[&<>]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;"}[c]})}
function run(){$("gout").innerHTML=files().map(function(f,i){return '<h3 style="font-size:15px;margin:20px 0 6px"><code>'+esc(f[0])+'</code></h3><textarea id="go'+i+'" readonly rows="'+Math.min(24,f[1].split("\n").length+1)+'" style="width:100%;padding:12px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--text);font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;box-sizing:border-box;white-space:pre">'+esc(f[1])+'</textarea><p style="margin:6px 0 0"><button class="btn primary" type="button" onclick="asCopy(\'go'+i+'\',this)">Copy</button> <button class="btn" type="button" data-dl="'+i+'">Download '+esc(f[0].split("/").pop())+'</button></p>'}).join("")}
$("gout").addEventListener("click",function(ev){var b=ev.target.closest("[data-dl]");if(!b)return;var f=files()[+b.dataset.dl],a=document.createElement("a");a.href=URL.createObjectURL(new Blob([f[1]],{type:"text/plain"}));a.download=f[0].split("/").pop();a.click();setTimeout(function(){URL.revokeObjectURL(a.href)},1000)});
document.querySelectorAll("textarea:not([readonly]),select,input").forEach(function(el){el.addEventListener("input",run)});run();'''
    faq=[("Which frameworks does the generator support?","Claude Code (CLAUDE.md and .mcp.json), OpenAI Codex CLI (AGENTS.md), Cursor project rules, CrewAI YAML config, LangChain's create_agent in Python, the OpenAI Agents SDK in Python, and a plain system prompt for any model."),
         ("Do I need an API key?","Not to use the generator. To run the generated Python or CrewAI code you need a key for the model provider you choose, set as an environment variable."),
         ("Is anything sent to a server?","No. Files are generated in your browser, and the download button saves them straight to your device."),
         ("Are these files production-ready?","They are starter scaffolds. Review them, add real tool code and check each framework's documentation for the latest options.")]
    return wrap("agent-setup-generator","AI agent setup generator","Describe your agent once and get starter config files and system prompts for Claude Code, Codex, Cursor, CrewAI, LangChain and the OpenAI Agents SDK.",inner,faq,js,t)

def hub_cards(d=""):
    """Cards for the free-tools.html hub (AgentScout's own tools)."""
    return "".join(f'<div class="card tile" style="position:relative"><a class="stretch" href="{d}free-tools/{s}.html" aria-label="{e(n)}"></a><div class="ct"><span class="ico"><span aria-hidden="true">{ic}</span></span><div class="tn"><h3>{e(n)}</h3><div class="badges"><span class="b new">Free</span><span class="b cat">by AgentScout</span></div></div></div><p class="hook">{e(desc)}</p></div>' for s,n,desc,ic in TOOLS)
def pages(t):
    P=json.load(open("assets/ai-prices.json"))
    urls=[cost(t,P),tokens(t,P),prompt(t),agent(t),mcpcfg(t),llmstxt(t),toolschema(t)]
    # /free-tools/ folder URL -> hub (not in sitemap)
    open("free-tools/index.html","w").write('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Free tools · AgentScout</title><link rel="canonical" href="'+B+'free-tools.html"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url=../free-tools.html"></head><body><a href="../free-tools.html">Free tools from AgentScout</a></body></html>\n')
    print("free tools:",len(urls),"pages")
    return urls

# ---- Batch (g), Oct 18 2026: MCP config builder, llms.txt generator, tool-schema builder (all browser-only) ----
TOOLS+=[
("mcp-config-builder","MCP Config Builder","Add MCP servers once and get ready-to-paste config for Claude Desktop, Claude Code, Cursor and VS Code.","🔌"),
("llms-txt-generator","llms.txt Generator","Fill in your site's name, summary and key links and get a valid llms.txt file that AI assistants can read.","📄"),
("tool-schema-builder","AI Tool Schema Builder","Define a function once and export the tool-calling JSON schema for OpenAI, Anthropic Claude and Google Gemini.","🧩"),
]
REL.update({"mcp-config-builder":(["free-mcp-servers","terminal-ai-coding-agents"],["developers","ai-engineers"]),
 "llms-txt-generator":(["web-search-apis-for-ai-agents"],["marketers","developers","founders"]),
 "tool-schema-builder":(["python-ai-agent-frameworks","typescript-ai-agent-frameworks","open-source-ai-agent-frameworks"],["ai-engineers","developers"])})
TA='style="width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--text);font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;box-sizing:border-box"'
def _outs(ids):
    return "".join(f'<h3 style="font-size:15px;margin:20px 0 6px">{lab}</h3><textarea id="{i}" readonly rows="12" {OUT}></textarea><button class="btn" type="button" onclick="asCopy(\'{i}\',this)">Copy</button>' for i,lab in ids)
def mcpcfg(t):
    inner=(f'<div {BOX}><p style="margin:0 0 6px">One server per line. Local (stdio) servers: <code>name | command and arguments | KEY=value KEY2=value</code>. Remote servers: <code>name | https://url</code>.</p>'
           f'<label {LAB} for="ms">Servers</label><textarea id="ms" rows="5" {TA}>filesystem | npx -y @modelcontextprotocol/server-filesystem /Users/me/Documents\ngithub | npx -y @modelcontextprotocol/server-github | GITHUB_PERSONAL_ACCESS_TOKEN=your-token-here</textarea>'
           '<p id="merr" role="alert" style="color:#e5484d;min-height:18px;margin:8px 0 0;font-size:14px"></p></div>'
           +_outs([("mo1","Claude Desktop: claude_desktop_config.json"),("mo2","Cursor: .cursor/mcp.json (project) or ~/.cursor/mcp.json"),("mo3","VS Code: .vscode/mcp.json"),("mo4","Claude Code: terminal commands")])
           +'<p class="muted" style="font-size:13px;margin-top:14px">Claude Desktop connects to remote servers through the <code>mcp-remote</code> bridge here; newer versions can also add remote servers under Settings → Connectors. Never paste real secrets into shared files.</p>')
    js=r'''function $(i){return document.getElementById(i)}
function sp(s){var a=[],m,re=/"([^"]*)"|'([^']*)'|(\S+)/g;while((m=re.exec(s)))a.push(m[1]!==undefined?m[1]:m[2]!==undefined?m[2]:m[3]);return a}
function parse(){var out=[],err="";$("ms").value.split("\n").forEach(function(l,i){l=l.trim();if(!l||l[0]==="#")return;var p=l.split("|").map(function(x){return x.trim()});var n=(p[0]||"").replace(/[^A-Za-z0-9_.-]/g,"-");if(!n||!p[1]){err="Line "+(i+1)+": use name | command or name | https://url";return}
var s={name:n};if(/^https?:\/\//.test(p[1])){s.url=p[1]}else{var a=sp(p[1]);s.command=a[0];s.args=a.slice(1)}var env={};(p[2]||"").split(/\s+/).forEach(function(kv){var k=kv.indexOf("=");if(k>0)env[kv.slice(0,k)]=kv.slice(k+1)});if(Object.keys(env).length)s.env=env;out.push(s)});$("merr").textContent=err;return out}
function q(s){return /^[A-Za-z0-9_./:@=-]+$/.test(s)?s:"'"+s.replace(/'/g,"'\\''")+"'"}
function run(){var S=parse(),cd={},cu={},vs={},cc=[];S.forEach(function(s){if(s.url){cd[s.name]={command:"npx",args:["-y","mcp-remote",s.url]};cu[s.name]={url:s.url};vs[s.name]={type:"http",url:s.url};cc.push("claude mcp add --transport http "+q(s.name)+" "+q(s.url))}
else{var b={command:s.command,args:s.args};if(s.env)b.env=s.env;cd[s.name]=b;cu[s.name]=JSON.parse(JSON.stringify(b));var v={type:"stdio",command:s.command,args:s.args};if(s.env)v.env=s.env;vs[s.name]=v;cc.push("claude mcp add "+q(s.name)+(s.env?" "+Object.keys(s.env).map(function(k){return"--env "+q(k+"="+s.env[k])}).join(" "):"")+" -- "+[s.command].concat(s.args).map(q).join(" "))}});
$("mo1").value=JSON.stringify({mcpServers:cd},null,2);$("mo2").value=JSON.stringify({mcpServers:cu},null,2);$("mo3").value=JSON.stringify({servers:vs},null,2);$("mo4").value=cc.join("\n")}
$("ms").addEventListener("input",run);run();'''
    faq=[("Where does the Claude Desktop config file live?","On macOS it is ~/Library/Application Support/Claude/claude_desktop_config.json and on Windows %APPDATA%\\Claude\\claude_desktop_config.json. You can also open it from Claude Desktop's Settings → Developer → Edit Config. Restart Claude Desktop after saving."),
         ("What is the difference between the Cursor and VS Code formats?","Cursor's mcp.json uses a top-level mcpServers object, like Claude Desktop. VS Code's .vscode/mcp.json uses a top-level servers object and a type field (stdio or http) for each server."),
         ("Does this tool install or run anything?","No. It only formats text in your browser. You still need Node.js (for npx servers) or whatever runtime each server needs, and you should only add servers you trust."),
         ("Where do I find MCP servers?",f"Browse the {sum(1 for x in t if x['category']=='MCP & infra')} MCP and infrastructure tools in the AgentScout directory, or the free MCP servers list.")]
    return wrap("mcp-config-builder","MCP config builder","Add your MCP servers once and get config you can paste into Claude Desktop, Cursor, VS Code and Claude Code. See also the <a href=\"../categories/mcp-infra.html\">MCP &amp; infra category</a>.",inner,faq,js,t)
def llmstxt(t):
    inner=(f'<div {BOX}><label {LAB} for="ln">Site or project name</label><input id="ln" {INP} value="Acme Docs" maxlength="100">'
           f'<label {LAB} for="ls">One-sentence summary</label><input id="ls" {INP} value="Acme is an open-source library for building AI agents in Python." maxlength="300">'
           f'<label {LAB} for="ld">More details <span style="color:var(--faint);font-weight:400">(optional, plain text or Markdown)</span></label><textarea id="ld" rows="3" {TA}>Use the Quickstart first. The API reference covers every public class.</textarea>'
           f'<label {LAB} for="lk">Sections and links</label><p class="muted" style="margin:0 0 6px;font-size:13px">Start a section with <code>## Name</code>. Then one link per line: <code>Title | https://url | optional note</code>. A section named <code>Optional</code> marks links an AI can skip.</p>'
           f'<textarea id="lk" rows="8" {TA}>## Docs\nQuickstart | https://example.com/docs/quickstart.md | Install and run your first agent\nAPI reference | https://example.com/docs/api.md\n\n## Optional\nChangelog | https://example.com/changelog.md</textarea>'
           '<p id="lerr" role="alert" style="color:#e5484d;min-height:18px;margin:8px 0 0;font-size:14px"></p></div>'
           +_outs([("lo","llms.txt (save at your site root, e.g. https://example.com/llms.txt)")])
           +'<p><button class="btn" type="button" id="ldl">Download llms.txt</button></p>')
    js=r'''function $(i){return document.getElementById(i)}
function run(){var o="# "+($("ln").value.trim()||"Untitled")+"\n",s=$("ls").value.trim(),d=$("ld").value.trim(),err="",cur=null;if(s)o+="\n> "+s.replace(/\n+/g," ")+"\n";if(d)o+="\n"+d+"\n";
$("lk").value.split("\n").forEach(function(l,i){l=l.trim();if(!l)return;if(/^##\s+/.test(l)){cur=l.replace(/^##\s+/,"");o+="\n## "+cur+"\n\n";return}var p=l.split("|").map(function(x){return x.trim()});
if(!cur){cur="Docs";o+="\n## Docs\n\n"}if(!p[1]||!/^https?:\/\//.test(p[1])){err="Line "+(i+1)+": use Title | https://url | note";return}o+="- ["+p[0]+"]("+p[1]+")"+(p[2]?": "+p[2]:"")+"\n"});
$("lerr").textContent=err;$("lo").value=o}
["ln","ls","ld","lk"].forEach(function(i){$(i).addEventListener("input",run)});run();
$("ldl").addEventListener("click",function(){var a=document.createElement("a");a.href=URL.createObjectURL(new Blob([$("lo").value],{type:"text/plain"}));a.download="llms.txt";a.click();setTimeout(function(){URL.revokeObjectURL(a.href)},1000)});'''
    faq=[("What is llms.txt?","llms.txt is a proposed standard (llmstxt.org) for a Markdown file at the root of a website that gives AI assistants a short summary and a curated list of the most useful pages, so they don't have to crawl everything."),
         ("What format does this generator follow?","An H1 with the site name, an optional blockquote summary, optional details, then H2 sections that contain Markdown link lists, with an optional note after each link. A section called Optional holds links that can be skipped when context is short."),
         ("Does AgentScout have one?","Yes: agentscouthq.com/llms.txt lists the directory's categories and machine-readable catalog."),
         ("Is anything uploaded?","No. The file is built in your browser and downloaded directly.")]
    return wrap("llms-txt-generator","llms.txt generator","Fill in your site's name, a one-line summary and your key links, and get a valid llms.txt file AI assistants can read. Example: <a href=\"../llms.txt\">AgentScout's llms.txt</a>.",inner,faq,js,t)
def toolschema(t):
    inner=(f'<div {BOX}><label {LAB} for="sn">Function name</label><input id="sn" {INP} value="get_weather" maxlength="64">'
           f'<label {LAB} for="sd">What it does</label><input id="sd" {INP} value="Get the current weather for a city." maxlength="500">'
           f'<label {LAB} for="sp">Parameters</label><p class="muted" style="margin:0 0 6px;font-size:13px">One per line: <code>name | type | required or optional | description</code>. Types: string, number, integer, boolean, array, object, or <code>enum(a,b,c)</code>.</p>'
           f'<textarea id="sp" rows="5" {TA}>city | string | required | City name, e.g. Paris\nunit | enum(celsius,fahrenheit) | optional | Temperature unit</textarea>'
           f'<label style="display:flex;gap:8px;align-items:center;margin:12px 0 0;font-size:14px"><input type="checkbox" id="sx"> Strict mode for OpenAI (all fields required, no extra properties)</label>'
           '<p id="serr" role="alert" style="color:#e5484d;min-height:18px;margin:8px 0 0;font-size:14px"></p></div>'
           +_outs([("so1","OpenAI Responses API (tools)"),("so2","OpenAI Chat Completions (tools)"),("so3","Anthropic Claude (tools)"),("so4","Google Gemini (functionDeclarations)")]))
    js=r'''function $(i){return document.getElementById(i)}
function schema(strict){var props={},req=[],err="";$("sp").value.split("\n").forEach(function(l,i){l=l.trim();if(!l)return;var p=l.split("|").map(function(x){return x.trim()}),n=p[0],ty=(p[1]||"string").toLowerCase();
if(!/^[A-Za-z_][A-Za-z0-9_]*$/.test(n||"")){err="Line "+(i+1)+": parameter names use letters, numbers and _";return}var o={},m=/^enum\((.*)\)$/.exec(ty);if(m){o.type="string";o["enum"]=m[1].split(",").map(function(x){return x.trim()}).filter(Boolean)}
else if(["string","number","integer","boolean","array","object"].indexOf(ty)>=0){o.type=ty;if(ty==="array")o.items={type:"string"};if(ty==="object"){o.properties={};if(strict){o.additionalProperties=false;o.required=[]}}}else{err="Line "+(i+1)+": unknown type "+ty;return}
if(p[3])o.description=p[3];props[n]=o;if(strict||/^req/.test((p[2]||"").toLowerCase()))req.push(n)});var s={type:"object",properties:props,required:req};if(strict)s.additionalProperties=false;return[s,err]}
function run(){var n=$("sn").value.trim()||"my_function",d=$("sd").value.trim(),st=$("sx").checked,a=schema(st),b=schema(false);$("serr").textContent=a[1]||(/^[A-Za-z0-9_-]{1,64}$/.test(n)?"":"Function names use letters, numbers, _ and - (max 64).");
var r={type:"function",name:n,description:d,parameters:a[0]};if(st)r.strict=true;var c={type:"function",function:{name:n,description:d,parameters:a[0]}};if(st)c["function"].strict=true;
$("so1").value=JSON.stringify([r],null,2);$("so2").value=JSON.stringify([c],null,2);$("so3").value=JSON.stringify([{name:n,description:d,input_schema:b[0]}],null,2);
$("so4").value=JSON.stringify({functionDeclarations:[{name:n,description:d,parameters:b[0]}]},null,2)}
["sn","sd","sp"].forEach(function(i){$(i).addEventListener("input",run)});$("sx").addEventListener("change",run);run();'''
    faq=[("Why does each provider need a different format?","They all use JSON Schema for the parameters, but wrap it differently: OpenAI's Responses API takes type, name, description and parameters at the top level; Chat Completions nests them under function; Anthropic calls the schema input_schema; Gemini lists functions under functionDeclarations."),
         ("What does OpenAI strict mode change?","With strict set to true, the model's arguments are guaranteed to match your schema. OpenAI requires every property to be listed as required and additionalProperties to be false; use a nullable type if a field is truly optional."),
         ("Can I use nested objects?","This builder makes flat parameter lists with empty object and string-array placeholders. Edit the output by hand for deeper nesting."),
         ("Is anything sent to an AI provider?","No. The schema is generated in your browser.")]
    return wrap("tool-schema-builder","AI tool schema builder (function calling)","Define a function once and export the tool-calling JSON for OpenAI, Anthropic Claude and Google Gemini. Building agents? See <a href=\"../tasks/building-ai-agents.html\">agent frameworks by task</a>.",inner,faq,js,t)
