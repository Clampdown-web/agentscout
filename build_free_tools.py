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
          f'<p class="ftmore">More {X.BUILT_BY("../").replace("Free AI","free AI",1)}: {others(s)} · <a href="../generate.html">Free AI image generator</a> · <a href="../free-tools.html">All free tools</a></p></section><script>{TOK}\n{js}</script>')
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
           '</div><p id="cerr" role="alert" style="color:#e5484d;min-height:18px;margin:8px 0 0;font-size:14px"></p><div id="cres" style="margin-top:10px;display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px"></div><p id="cnote" class="muted" style="font-size:13px;margin:10px 0 0"></p></div>'
           '<h2 style="font-size:18px;margin:28px 0 6px">Compare every model at these numbers</h2><p class="muted" style="font-size:13.5px;margin:0 0 10px">Sorted by monthly cost (30 days). Click a row to select it.</p>'
           '<div style="overflow-x:auto" tabindex="0" role="region" aria-label="Cost comparison table"><table id="ctab" style="width:100%;border-collapse:collapse;font-size:14px"><thead><tr style="text-align:left;border-bottom:1px solid var(--line)"><th style="padding:6px">Model</th><th style="padding:6px">Provider</th><th style="padding:6px">Input $/1M</th><th style="padding:6px">Output $/1M</th><th style="padding:6px">Per request</th><th style="padding:6px">Per month</th></tr></thead><tbody></tbody></table></div>'
           f'<h2 style="font-size:18px;margin:28px 0 6px">Where these prices come from</h2><p style="margin:0 0 6px">Prices checked on <b>{e(P["checked"])}</b> from each provider\'s official pricing page, in US dollars per 1 million tokens, standard (non-batch) tier, short-context rates. Batch, flex and cached-write pricing, long prompts, data-residency uplifts and tool fees (like web search) are not included.</p><ul style="margin:0;padding-left:20px;font-size:14px">{src}</ul>'
           '<p class="muted" style="font-size:13px">Prices change often. Always confirm on the provider page before you budget. Need a token count first? Try the <a href="token-counter.html">token counter</a>.</p>')
    js=("var R="+json.dumps(rows)+r''';function $(i){return document.getElementById(i)}function v(i){var x=parseFloat($(i).value);return isFinite(x)&&x>0?x:0}
function f(x){return x>=100?"$"+x.toLocaleString(undefined,{maximumFractionDigits:0}):x>=1?"$"+x.toFixed(2):x>=0.01?"$"+x.toFixed(3):"$"+x.toPrecision(2)}
function c(m){var i=v("ci"),o=v("co"),cs=Math.min(v("cc"),100)/100;return(i*(1-cs)*m.in+i*cs*m.c+o*m.out)/1e6}
function chk(){var bad=[];[["ci","Input tokens"],["co","Output tokens"],["cc","Cached share"],["cr","Requests per day"]].forEach(function(x){var el=$(x[0]),r=el.value.trim(),n=parseFloat(r),ok=r!==""&&isFinite(n)&&n>=0&&!(x[0]==="cc"&&n>100);el.setAttribute("aria-invalid",ok?"false":"true");el.style.borderColor=ok?"":"#e5484d";if(!ok)bad.push(x[1]+(x[0]==="cc"?" (0 to 100)":""))});
$("cerr").textContent=bad.length?"Please enter a number of 0 or more for: "+bad.join(", ")+". Invalid fields count as 0 until fixed.":""}
function run(){chk();var m=R.filter(function(x){return x.id===$("cm").value})[0]||R[0],per=c(m),d=per*v("cr");
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
function art(r){r=r.replace(/^you are\s+/i,"").replace(/[.\s]+$/,"");if(/^(a|an|the|my|our|your|his|her|their)\s/i.test(r)||/^[A-Z][a-z]+(\s[A-Z][a-z]+)+$/.test(r)||/s$/i.test(r.split(/\s/)[0])&&r.split(/\s/).length===1)return r;var w=r.split(/\s/)[0].toLowerCase();var an=/^(hour|honest|honou?r|heir)/.test(w)||(/^[aeiou]/.test(w)&&!/^(uni|use|usu|uti|ure|euro|one|once)/.test(w))||/^[aefhilmnorsx]$/.test(w)||/^(fbi|mba|mvp|seo|sql|hr|llm|ml|nlp|rn|sre|sem|smb|svp|evp|avp|faq|api|ai)\b/.test(w);return(an?"an ":"a ")+r}
if(v.pr)out.push("You are "+art(v.pr)+".");
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
function run(){$("gout").innerHTML=files().map(function(f,i){return '<h3 style="font-size:15px;margin:20px 0 6px"><code>'+esc(f[0])+'</code></h3><textarea id="go'+i+'" aria-label="'+esc(f[0])+'" readonly rows="'+Math.min(24,f[1].split("\n").length+1)+'" style="width:100%;padding:12px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--text);font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;box-sizing:border-box;white-space:pre">'+esc(f[1])+'</textarea><p style="margin:6px 0 0"><button class="btn primary" type="button" onclick="asCopy(\'go'+i+'\',this)">Copy</button> <button class="btn" type="button" data-dl="'+i+'" style="white-space:normal;max-width:100%">Download '+esc(dn(f[0]))+'</button>'+(f[0].split("/").pop()[0]==="."?' <span class="muted" style="font-size:13px">Browsers drop the leading dot, so rename the file to <code>'+esc(f[0].split("/").pop())+'</code> after saving.</span>':'')+'</p>'}).join("")}
function dn(p){var b=p.split("/").pop();return b[0]==="."?b.slice(1)+" (rename to "+b+")":b}
$("gout").addEventListener("click",function(ev){var b=ev.target.closest("[data-dl]");if(!b)return;var f=files()[+b.dataset.dl],a=document.createElement("a");a.href=URL.createObjectURL(new Blob([f[1]],{type:"text/plain"}));a.download=f[0].split("/").pop().replace(/^\./,"");a.click();setTimeout(function(){URL.revokeObjectURL(a.href)},1000)});
document.querySelectorAll("textarea:not([readonly]),select,input").forEach(function(el){el.addEventListener("input",run)});run();'''
    faq=[("Which frameworks does the generator support?","Claude Code (CLAUDE.md and .mcp.json), OpenAI Codex CLI (AGENTS.md), Cursor project rules, CrewAI YAML config, LangChain's create_agent in Python, the OpenAI Agents SDK in Python, and a plain system prompt for any model."),
         ("Do I need an API key?","Not to use the generator. To run the generated Python or CrewAI code you need a key for the model provider you choose, set as an environment variable."),
         ("Is anything sent to a server?","No. Files are generated in your browser, and the download button saves them straight to your device."),
         ("Are these files production-ready?","They are starter scaffolds. Review them, add real tool code and check each framework's documentation for the latest options.")]
    return wrap("agent-setup-generator","AI agent setup generator","Describe your agent once and get starter config files and system prompts for Claude Code, Codex, Cursor, CrewAI, LangChain and the OpenAI Agents SDK.",inner,faq,js,t)

def hub_cards(d=""):
    """Cards for the free-tools.html hub (AgentScout's own tools)."""
    return "".join(f'<div class="card tile" style="position:relative"><a class="stretch" href="{d}free-tools/{s}.html" aria-label="{e(n)}"></a><div class="ct"><span class="ico"><span aria-hidden="true">{ic}</span></span><div class="tn"><h3>{e(n)}</h3><div class="badges"><span class="b new">Free</span></div></div></div><p class="hook">{e(desc)}</p></div>' for s,n,desc,ic in TOOLS)
def see_all_card(d=""):
    """'See all free tools' tile in the same card style (homepage grid), so the grid has a full last row."""
    return (f'<div class="card tile ftall" style="position:relative"><a class="stretch" href="{d}free-tools.html" aria-label="See all free tools"></a><div class="ct"><span class="ico"><img src="{d}favicon.svg" alt="" width="40" height="40" loading="lazy" decoding="async"></span>'
            f'<div class="tn"><h3>See all free tools →</h3><div class="badges"><span class="b new">Free</span></div></div></div><p class="hook">All {len(TOOLS)} calculators and generators in one place. No sign-up.</p></div>')
def pages(t):
    P=json.load(open("assets/ai-prices.json"))
    urls=[cost(t,P),tokens(t,P),prompt(t),agent(t),mcpcfg(t),llmstxt(t),toolschema(t),runcost(t,P),rules(t),stack(t),linter(t),ctxplan(t),license(t),bvb(t),mcppick(t),jsonval(t),cmpcard(t),ready(t)]
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
    return "".join(f'<h3 style="font-size:15px;margin:20px 0 6px">{lab}</h3><textarea id="{i}" readonly rows="12" aria-label="{e(lab)}" {OUT}></textarea><button class="btn" type="button" onclick="asCopy(\'{i}\',this)">Copy</button>' for i,lab in ids)
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
         ("Where do I find MCP servers?",f"Browse the {sum(1 for x in t if x['category']=='MCP servers')} MCP servers in the AgentScout directory, or the free MCP servers list.")]
    return wrap("mcp-config-builder","MCP config builder","Add your MCP servers once and get config you can paste into Claude Desktop, Cursor, VS Code and Claude Code. See also the <a href=\"../categories/mcp-servers.html\">MCP servers category</a>.",inner,faq,js,t)
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
    inner=(f'<div {BOX}><label {LAB} for="sn">Function name</label><input id="sn" {INP} value="get_weather" maxlength="64" aria-describedby="serr">'
           f'<label {LAB} for="sd">What it does</label><input id="sd" {INP} value="Get the current weather for a city." maxlength="500">'
           f'<label {LAB} for="sp">Parameters</label><p class="muted" style="margin:0 0 6px;font-size:13px">One per line: <code>name | type | required or optional | description</code>. Types: string, number, integer, boolean, array, object, or <code>enum(a,b,c)</code>.</p>'
           f'<textarea id="sp" rows="5" {TA}>city | string | required | City name, e.g. Paris\nunit | enum(celsius,fahrenheit) | optional | Temperature unit</textarea>'
           f'<label style="display:flex;gap:8px;align-items:center;margin:12px 0 0;font-size:14px"><input type="checkbox" id="sx"> Strict mode for OpenAI (all fields required, no extra properties)</label>'
           '<p id="serr" role="alert" style="color:#e5484d;min-height:18px;margin:8px 0 0;font-size:14px"></p></div>'
           +_outs([("so1","OpenAI Responses API (tools)"),("so2","OpenAI Chat Completions (tools)"),("so3","Anthropic Claude (tools)"),("so4","Google Gemini (functionDeclarations)")]))
    js=r'''function $(i){return document.getElementById(i)}
function schema(strict){var props={},req=[],err="";$("sp").value.split("\n").forEach(function(l,i){l=l.trim();if(!l)return;var p=l.split("|").map(function(x){return x.trim()}),n=p[0],ty=(p[1]||"string").toLowerCase();
if(!/^[A-Za-z_][A-Za-z0-9_]*$/.test(n||"")){err=err||"Line "+(i+1)+": parameter names use letters, numbers and _";return}var o={},m=/^enum\((.*)\)$/.exec(ty);if(m){o.type="string";o["enum"]=m[1].split(",").map(function(x){return x.trim()}).filter(Boolean)}
else if(["string","number","integer","boolean","array","object"].indexOf(ty)>=0){o.type=ty;if(ty==="array")o.items={type:"string"};if(ty==="object"){o.properties={};if(strict){o.additionalProperties=false;o.required=[]}}}else{err=err||"Line "+(i+1)+": unknown type \u201c"+p[1]+"\u201d. Use string, number, integer, boolean, array, object or enum(a,b,c).";return}
if(p[3])o.description=p[3];props[n]=o;if(strict||/^req/.test((p[2]||"").toLowerCase()))req.push(n)});var s={type:"object",properties:props,required:req};if(strict)s.additionalProperties=false;return[s,err]}
function run(){var raw=$("sn").value.trim()||"my_function",n=raw.replace(/[^A-Za-z0-9_-]+/g,"_").replace(/^_+|_+$/g,"").slice(0,64)||"my_function",d=$("sd").value.trim(),st=$("sx").checked,a=schema(st),b=schema(false);$("sn").setAttribute("aria-invalid",n!==raw?"true":"false");$("serr").textContent=a[1]||(n!==raw?"Function names can only use letters, numbers, _ and - (max 64 characters), so the output uses \u201c"+n+"\u201d.":"");
$("sp").setAttribute("aria-invalid",a[1]?"true":"false");if(a[1]){["so1","so2","so3","so4"].forEach(function(i){if($(i))$(i).value="Fix the error above to generate the schema."});return}
var r={type:"function",name:n,description:d,parameters:a[0]};if(st)r.strict=true;var c={type:"function",function:{name:n,description:d,parameters:a[0]}};if(st)c["function"].strict=true;
$("so1").value=JSON.stringify([r],null,2);$("so2").value=JSON.stringify([c],null,2);$("so3").value=JSON.stringify([{name:n,description:d,input_schema:b[0]}],null,2);
$("so4").value=JSON.stringify({functionDeclarations:[{name:n,description:d,parameters:b[0]}]},null,2)}
["sn","sd","sp"].forEach(function(i){$(i).addEventListener("input",run)});$("sx").addEventListener("change",run);run();'''
    faq=[("Why does each provider need a different format?","They all use JSON Schema for the parameters, but wrap it differently: OpenAI's Responses API takes type, name, description and parameters at the top level; Chat Completions nests them under function; Anthropic calls the schema input_schema; Gemini lists functions under functionDeclarations."),
         ("What does OpenAI strict mode change?","With strict set to true, the model's arguments are guaranteed to match your schema. OpenAI requires every property to be listed as required and additionalProperties to be false; use a nullable type if a field is truly optional."),
         ("Can I use nested objects?","This builder makes flat parameter lists with empty object and string-array placeholders. Edit the output by hand for deeper nesting."),
         ("Is anything sent to an AI provider?","No. The schema is generated in your browser.")]
    return wrap("tool-schema-builder","AI tool schema builder (function calling)","Define a function once and export the tool-calling JSON for OpenAI, Anthropic Claude and Google Gemini. Building agents? See <a href=\"../tasks/building-ai-agents.html\">agent frameworks by task</a>.",inner,faq,js,t)

# ---- Batch A, Oct 20 2026: agent run cost estimator, rule-file generator, agent stack builder (all browser-only) ----
TOOLS+=[
("agent-run-cost-estimator","AI Agent Run Cost Estimator","Estimate what one multi-step agent task costs: steps, tool results, growing context, caching and retries, then per day and per month across 33 models.","🧾"),
("rules-file-generator","AGENTS.md & Rules File Generator","Write your project rules once and export AGENTS.md, CLAUDE.md, GEMINI.md, Cursor rules and GitHub Copilot instructions.","📐"),
("ai-agent-stack-builder","AI Agent Stack Builder","Pick your goal, skill level and budget and get a recommended AI agent stack from the AgentScout directory, with a shareable stack card.","🏗️"),
]
REL.update({"agent-run-cost-estimator":(["open-source-llm-observability-tools","python-ai-agent-frameworks","multi-agent-frameworks"],["ai-engineers","founders","product-managers"]),
 "rules-file-generator":(["terminal-ai-coding-agents","free-ai-coding-agents","open-source-ai-coding-agents"],["developers","open-source-maintainers"]),
 "ai-agent-stack-builder":(["open-source-ai-agent-frameworks","free-mcp-servers","free-no-code-ai-agent-builders"],["founders","ai-engineers","startup-ctos"])})
def _num(id,lab,v,extra=""): return f'<div><label {LAB} for="{id}">{lab}</label><input id="{id}" type="number" min="0" step="any" value="{v}" {extra} {INP}></div>'
ERR=lambda id:f'<p id="{id}" role="alert" style="color:#e5484d;min-height:18px;margin:8px 0 0;font-size:14px"></p>'
CARDS='margin-top:10px;display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px'
# shared JS: number validation + money format (same rules as the cost calculator)
NUMJS=r'''function $(i){return document.getElementById(i)}
function chkN(list,errId){var bad=[];list.forEach(function(x){var el=$(x[0]),r=el.value.trim(),n=parseFloat(r),mx=x[2],ok=r!==""&&isFinite(n)&&n>=0&&!(mx!=null&&n>mx);el.setAttribute("aria-invalid",ok?"false":"true");el.style.borderColor=ok?"":"#e5484d";if(!ok)bad.push(x[1]+(mx!=null?" (0 to "+mx+")":""))});$(errId).textContent=bad.length?"Please enter a number of 0 or more for: "+bad.join(", ")+". Invalid fields count as 0 until fixed.":"";return bad.length===0}
function v(i){var x=parseFloat($(i).value);return isFinite(x)&&x>0?x:0}
function fm(x){return x>=100?"$"+x.toLocaleString(undefined,{maximumFractionDigits:0}):x>=1?"$"+x.toFixed(2):x>=0.01?"$"+x.toFixed(3):x>0?"$"+x.toPrecision(2):"$0"}
function card(l,val){return '<div class="card" style="padding:12px"><div class="muted" style="font-size:12.5px">'+l+'</div><div style="font-size:22px;font-weight:700">'+val+'</div></div>'}
function dl(name,text){var a=document.createElement("a");a.href=URL.createObjectURL(new Blob([text],{type:"text/plain"}));a.download=name.replace(/^\./,"");a.click();setTimeout(function(){URL.revokeObjectURL(a.href)},1000)}'''
def _rows(P): return [{"p":p["name"],"id":m["id"],"in":m["in"],"c":m.get("cached",m["in"]),"out":m["out"],"n":m.get("note","")} for p in P["providers"] for m in p["models"]]
def _opts(P,sel=""): return "".join(f'<optgroup label="{e(p["name"])}">'+"".join(f'<option value="{e(m["id"])}"{" selected" if m["id"]==sel else ""}>{e(m["id"])}</option>' for m in p["models"])+"</optgroup>" for p in P["providers"])

def runcost(t,P):
    rows=_rows(P); n=len(rows)
    inner=(f'<div {BOX}><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:0 16px">'
           f'<div><label {LAB} for="rm">Model</label><select id="rm" {INP}>{_opts(P,"gpt-6.1-sol")}</select></div>'
           +_num("rs","Steps (model calls) per task",8)+_num("rb","System prompt + tool definitions (tokens)",3000)+_num("ru","User request + starting context (tokens)",1000)
           +_num("rt","Tool result added per step (tokens)",1500)+_num("ro","Model output per step (tokens)",300)+_num("rc","Cached share of repeated input (%)",50,'max="100"')
           +_num("rr","Extra steps from retries (%)",10)+_num("rd","Tasks per day",100)+
           '</div>'+ERR("rerr")+f'<div id="rres" style="{CARDS}"></div><p id="rnote" class="muted" style="font-size:13px;margin:10px 0 0"></p></div>'
           '<h2 style="font-size:18px;margin:28px 0 6px">The same agent on every model</h2><p class="muted" style="font-size:13.5px;margin:0 0 10px">Sorted by cost per task. Click a row to select it.</p>'
           '<div style="overflow-x:auto" tabindex="0" role="region" aria-label="Agent cost by model"><table id="rtab" style="width:100%;border-collapse:collapse;font-size:14px"><thead><tr style="text-align:left;border-bottom:1px solid var(--line)"><th style="padding:6px">Model</th><th style="padding:6px">Provider</th><th style="padding:6px">Per task</th><th style="padding:6px">Per month</th></tr></thead><tbody></tbody></table></div>'
           f'<h2 style="font-size:18px;margin:28px 0 6px">How it works</h2><p>An agent re-sends its whole conversation on every step, so input grows: step <i>k</i> sends the system prompt and tools, the starting context, and every earlier tool result and model reply. The estimator adds those up step by step. The cached share applies to input that was already sent on an earlier step (prompt caching), billed at the cached rate; the first step is always full price. Retries add extra steps at the average step cost.</p>'
           f'<p class="muted" style="font-size:13px">Prices are the same verified list the <a href="ai-cost-calculator.html">AI API cost calculator</a> uses, checked on <b>{e(P["checked"])}</b> from each provider\'s official pricing page (standard tier, short-context rates). This tool does not list context-window sizes: check the provider page to make sure your final-step context fits the model.</p>')
    js=NUMJS+"\nvar R="+json.dumps(rows)+r''';
var F=[["rs","Steps"],["rb","System prompt + tools"],["ru","Starting context"],["rt","Tool result per step"],["ro","Output per step"],["rc","Cached share",100],["rr","Retries"],["rd","Tasks per day"]];
function sim(m){var s=Math.round(v("rs")),b=v("rb"),u=v("ru"),tr=v("rt"),o=v("ro"),cs=Math.min(v("rc"),100)/100,ret=v("rr")/100,cost=0,inT=0,outT=0,ctx=0,prev=0;
for(var k=0;k<s;k++){ctx=b+u+k*(tr+o);var cached=k===0?0:Math.min(prev,ctx)*cs;cost+=((ctx-cached)*m.in+cached*m.c+o*m.out)/1e6;inT+=ctx;outT+=o;prev=ctx+o+tr}
var f=1+ret;return{cost:cost*f,inT:inT*f,outT:outT*f,ctx:ctx,steps:s}}
function run(){chkN(F,"rerr");var m=R.filter(function(x){return x.id===$("rm").value})[0]||R[0],r=sim(m),d=r.cost*v("rd");
$("rres").innerHTML=card("Per task",fm(r.cost))+card("Per day",fm(d))+card("Per month (30 days)",fm(d*30))+card("Tokens per task",Math.round(r.inT+r.outT).toLocaleString())+card("Context at last step",Math.round(r.ctx).toLocaleString());
$("rnote").textContent=m.p+" "+m.id+": $"+m.in+" input, $"+m.c+" cached input, $"+m.out+" output per 1M tokens. Per task: about "+Math.round(r.inT).toLocaleString()+" input and "+Math.round(r.outT).toLocaleString()+" output tokens."+(m.n?" Note: "+m.n+".":"");
var S=R.map(function(x){return[x,sim(x).cost]}).sort(function(a,b){return a[1]-b[1]});$("rtab").tBodies[0].innerHTML=S.map(function(z){var x=z[0],on=x.id===m.id;return '<tr data-id="'+x.id+'" style="cursor:pointer;border-bottom:1px solid var(--line)'+(on?';background:var(--line)':'')+'"><td style="padding:6px"><b>'+x.id+'</b></td><td style="padding:6px">'+x.p+'</td><td style="padding:6px">'+fm(z[1])+'</td><td style="padding:6px">'+fm(z[1]*v("rd")*30)+'</td></tr>'}).join("")}
["rm"].concat(F.map(function(x){return x[0]})).forEach(function(i){$(i).addEventListener("input",run)});$("rtab").addEventListener("click",function(ev){var r=ev.target.closest("tr[data-id]");if(r){$("rm").value=r.dataset.id;run()}});run();'''
    faq=[("Why is an agent task so much more expensive than one chat request?","Each step re-sends the full conversation so far, including every tool result, so input tokens grow with every step. A 10-step task can use many times the tokens of a single prompt."),
         ("How does prompt caching change the cost?","Input already sent on an earlier step can often be served from the provider's prompt cache at a lower cached rate. Set the cached share to how much of that repeated input you expect to hit the cache; 0% means no caching."),
         ("Are reasoning tokens included?","Only if you add them. Thinking tokens are billed as output, so raise the output-per-step figure if your model reasons before acting."),
         ("Where do the prices come from?",f"The same list as the AgentScout cost calculator, copied from the official OpenAI, Anthropic, Google and xAI pricing pages on {P['checked']}. Confirm on the provider page before you budget.")]
    return wrap("agent-run-cost-estimator","AI agent run cost estimator",f"Work out what one multi-step agent task really costs, with a growing context, tool results, prompt caching and retries, then compare it on {n} GPT, Claude, Gemini and Grok models.",inner,faq,js,t)

RF=[("AGENTS.md","AGENTS.md","OpenAI Codex and many other coding agents (agents.md)"),("CLAUDE.md","CLAUDE.md","Claude Code"),("GEMINI.md","GEMINI.md","Gemini CLI"),
    (".cursor/rules/project.mdc","Cursor project rule","Cursor (.cursor/rules)"),(".github/copilot-instructions.md","Copilot instructions","GitHub Copilot"),(".cursorrules",".cursorrules (legacy)","older Cursor setups")]
def rules(t):
    f=lambda id,lab,v,rows=3,ph="":f'<label {LAB} for="{id}">{lab}</label><textarea id="{id}" rows="{rows}" placeholder="{e(ph)}" {TA}>{e(v)}</textarea>'
    chk="".join(f'<label style="display:inline-flex;gap:6px;align-items:center;margin:0 14px 6px 0;font-size:14px"><input type="checkbox" class="rfk" value="{i}" checked> {e(l)}</label>' for i,(p,l,_) in enumerate(RF))
    inner=(f'<div {BOX}><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:0 18px"><div>'
           f'<label {LAB} for="fn">Project name</label><input id="fn" value="acme-web" {INP}>'
           +f("fo","What the project is","A Next.js storefront with a Postgres database and a small admin dashboard.",2)
           +f("fs","Stack and versions","TypeScript, Next.js 15, React 19, pnpm, Prisma, Vitest",2)
           +f("fc","Commands (one per line, label: command)","Install: pnpm install\nDev server: pnpm dev\nTest: pnpm test\nLint: pnpm lint",4)
           +'</div><div>'
           +f("fy","Code style (one per line)","Use TypeScript strict mode; no any\nPrefer server components; mark client components with \"use client\"\nKeep functions small and named clearly",4)
           +f("fd","Always do (one per line)","Run tests and lint before you finish\nExplain changes in a short summary",3)
           +f("fx","Never do (one per line)","Never commit secrets or .env files\nDon't change database migrations that already ran",3)
           +f("fp","Key folders (one per line, path: what lives there)","src/app: routes and pages\nsrc/lib: shared helpers\nprisma: schema and migrations",3)
           +f'</div></div><p style="margin:14px 0 6px;font-weight:600;font-size:14px">Files to make</p>{chk}</div><div id="fout"></div>'
           '<h2 style="font-size:18px;margin:28px 0 6px">Which file does my coding agent read?</h2><ul>'
           +"".join(f'<li><code>{e(p)}</code>: {e(w)}</li>' for p,_,w in RF)+
           '</ul><p class="muted" style="font-size:13.5px">Tools change fast: check each tool\'s docs for the exact file it reads today. Keeping one AGENTS.md and pointing the others at it is a common way to avoid copies drifting apart.</p>')
    js=NUMJS+"\nvar RF="+json.dumps([[p,l] for p,l,_ in RF])+r''';function L(id){return $(id).value.split("\n").map(function(s){return s.trim()}).filter(Boolean)}
function esc(s){return s.replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
function body(){var o="",d=$("fo").value.trim(),s=$("fs").value.trim();if(d)o+=d+"\n";if(s)o+="\n## Stack\n"+s+"\n";
var c=L("fc");if(c.length)o+="\n## Commands\n"+c.map(function(x){var i=x.indexOf(":");return i>0?"- "+x.slice(0,i).trim()+": `"+x.slice(i+1).trim()+"`":"- `"+x+"`"}).join("\n")+"\n";
var p=L("fp");if(p.length)o+="\n## Project layout\n"+p.map(function(x){var i=x.indexOf(":");return i>0?"- `"+x.slice(0,i).trim()+"`: "+x.slice(i+1).trim():"- `"+x+"`"}).join("\n")+"\n";
[["fy","Code style"],["fd","Always"],["fx","Never"]].forEach(function(k){var a=L(k[0]);if(a.length)o+="\n## "+k[1]+"\n"+a.map(function(x){return"- "+x}).join("\n")+"\n"});return o}
function file(i){var n=$("fn").value.trim()||"Project",b=body(),p=RF[i][0];
if(p===".cursor/rules/project.mdc")return"---\ndescription: Project rules for "+n+"\nglobs:\nalwaysApply: true\n---\n\n# "+n+"\n\n"+b;
if(p===".cursorrules")return"# "+n+"\n\n"+b;
if(p===".github/copilot-instructions.md")return"# Copilot instructions for "+n+"\n\n"+b;
return"# "+n+"\n\n"+b}
function run(){var ks=[].slice.call(document.querySelectorAll(".rfk")).filter(function(x){return x.checked}).map(function(x){return+x.value});
$("fout").innerHTML=ks.map(function(i){var p=RF[i][0],b=p.split("/").pop(),txt=file(i);return '<h3 style="font-size:15px;margin:20px 0 6px"><code>'+esc(p)+'</code></h3><textarea id="fo'+i+'" aria-label="'+esc(p)+'" readonly rows="'+Math.min(20,txt.split("\n").length+1)+'" style="width:100%;padding:12px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--text);font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;box-sizing:border-box;white-space:pre">'+esc(txt)+'</textarea><p style="margin:6px 0 0"><button class="btn primary" type="button" onclick="asCopy(\'fo'+i+'\',this)">Copy</button> <button class="btn" type="button" data-dl="'+i+'" style="white-space:normal;max-width:100%">Download '+esc(b[0]==="."?b.slice(1)+" (rename to "+b+")":b)+'</button>'+(b[0]==="."?' <span class="muted" style="font-size:13px">Browsers drop the leading dot, so rename the file to <code>'+esc(b)+'</code> after saving.</span>':'')+'</p>'}).join("")||'<p class="muted">Tick at least one file above.</p>'}
$("fout").addEventListener("click",function(ev){var b=ev.target.closest("[data-dl]");if(b){var i=+b.dataset.dl;dl(RF[i][0].split("/").pop(),file(i))}});
document.querySelectorAll("textarea:not([readonly]),input").forEach(function(el){el.addEventListener("input",run);el.addEventListener("change",run)});run();'''
    faq=[("What is AGENTS.md?","AGENTS.md is a plain Markdown file at the root of a repository that tells AI coding agents how to work on the project: what it is, how to build and test it, and the rules to follow. OpenAI Codex reads it, and a growing list of other agents support it (see agents.md)."),
         ("What is the difference between CLAUDE.md, GEMINI.md and AGENTS.md?","They do the same job for different agents: Claude Code reads CLAUDE.md, Gemini CLI reads GEMINI.md, and Codex and many others read AGENTS.md. The content can be identical, which is why this generator writes them all from one form."),
         ("Should I use .cursorrules or .cursor/rules?",".cursor/rules/*.mdc project rules are Cursor's current format; a single .cursorrules file in the project root is the older way and is still recognised by some setups. Check Cursor's docs for your version."),
         ("Where does copilot-instructions.md go?","Save it as .github/copilot-instructions.md in your repository so GitHub Copilot uses it as repository custom instructions."),
         ("Is anything uploaded?","No. The files are built in your browser and downloaded straight to your device.")]
    return wrap("rules-file-generator","AGENTS.md and rules file generator","Write your project rules once and export AGENTS.md, CLAUDE.md, GEMINI.md, Cursor rules and GitHub Copilot instructions for your AI coding agents. Need agent config too? Try the <a href=\"agent-setup-generator.html\">agent setup generator</a>.",inner,faq,js,t)

STACK_GOALS=[("coding","Write and ship code",[("Coding agent",["coding"]),("Code sandbox",["sandboxes & code execution"]),("MCP servers and connectors",["MCP servers"]),("Evals and observability",["evals & observability"])]),
 ("support","Customer support",[("Support agent",["customer support"]),("Voice",["voice"]),("Memory and knowledge (RAG)",["memory & RAG"]),("Evals and observability",["evals & observability"])]),
 ("research","Research and analysis",[("Research agent",["research"]),("Web and browser access",["browser/computer use"]),("Memory and knowledge (RAG)",["memory & RAG"])]),
 ("automation","Automate business workflows",[("Business agent",["business agents"]),("No-code builder",["no-code builders"]),("MCP servers and connectors",["MCP servers"])]),
 ("sales","Sales and marketing",[("Sales and marketing agent",["sales & marketing"]),("Business agent",["business agents"]),("Web and browser access",["browser/computer use"])]),
 ("browse","Use the web or a computer",[("Browser or computer-use agent",["browser/computer use"]),("Sandbox",["sandboxes & code execution"]),("MCP servers and connectors",["MCP servers"])]),
 ("build","Build my own agent",[("Agent framework",["frameworks"]),("Memory and knowledge (RAG)",["memory & RAG"]),("MCP servers and connectors",["MCP servers"]),("Evals and observability",["evals & observability"]),("Sandbox",["sandboxes & code execution"])])]
def stack(t):
    cats={x["category"] for x in t}
    GT={"coding":["coding"],"support":["support"],"research":["research"],"automation":["automation"],"sales":["automation"],"browse":["automation"],"build":["coding","automation"]}
    G=[[k,l,[[n,[c for c in cs if c in cats]] for n,cs in L],GT[k]] for k,l,L in STACK_GOALS]
    sel=lambda id,lab,opts:f'<div><label {LAB} for="{id}">{lab}</label><select id="{id}" {INP}>'+"".join(f'<option value="{a}">{e(b)}</option>' for a,b in opts)+'</select></div>'
    inner=(f'<div {BOX}><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:0 16px">'
           +sel("kg","What should the agent do?",[(k,l) for k,l,_ in STACK_GOALS])+sel("ks","How technical are you?",[("any","Any"),("no-code","No code, please"),("developer","I'm a developer")])
           +sel("kb","Budget",[("any","Any"),("free","Free only"),("freemium","Free to start (free or freemium)")])+sel("ko","Open source?",[("any","Doesn't matter"),("yes","Open source only")])+
           '</div></div><div id="kout" aria-live="polite"><p class="muted">Loading the directory…</p></div>'
           '<p style="margin:12px 0 0;display:flex;flex-wrap:wrap;gap:8px"><button class="btn primary" type="button" id="kcopy">Copy stack as text</button><button class="btn" type="button" id="kpng">Download stack card (PNG)</button><button class="btn" type="button" id="klink">Copy link to this stack</button><span id="kmsg" class="muted" aria-live="polite" style="align-self:center"></span></p>'
           '<h2 style="font-size:18px;margin:28px 0 6px">How picks are chosen</h2><p>Every pick comes from the AgentScout directory of link-checked tools. Your answers filter the list (no-code, budget and open-source choices are strict), then tools that match your goal come first, followed by AgentScout weekly picks and GitHub stars where a project has them. Pricing labels are as each maker states them. For the model layer, compare prices in the <a href="ai-cost-calculator.html">AI API cost calculator</a> and the <a href="agent-run-cost-estimator.html">agent run cost estimator</a>.</p>')
    js=NUMJS+"\nvar G="+json.dumps(G)+r''';var T=null,cur=null;function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
function ok(x,s,b,o){if(s==="no-code"&&x.skill!=="no-code")return false;if(b==="free"&&x.price_tag!=="free")return false;if(b==="freemium"&&["free","freemium"].indexOf(x.price_tag)<0)return false;if(o==="yes"&&!x.open_source)return false;return true}
function sc(x,gt){return((x.tags||[]).indexOf("hardware")>=0?-4e9:0)+((x.goals||[]).some(function(g){return gt.indexOf(g)>=0})?2e9:0)+(x.weekly_pick?1e9:0)+(x.github_stars||0)+(x.logo?1:0)}
function pick(){var g=G.filter(function(z){return z[0]===$("kg").value})[0],s=$("ks").value,b=$("kb").value,o=$("ko").value;
return{goal:g[1],layers:g[2].map(function(L){function f(bb){return T.filter(function(x){return L[1].indexOf(x.category)>=0&&ok(x,s,bb,o)}).sort(function(a,b2){return sc(b2,g[3])-sc(a,g[3])}).slice(0,3)}var c=f(b),fb=false;if(!c.length&&b==="free"){c=f("freemium");fb=c.length>0}return[L[0],c,fb]})}}
function run(){if(!T)return;var h="kg="+$("kg").value+"&ks="+$("ks").value+"&kb="+$("kb").value+"&ko="+$("ko").value;try{history.replaceState(null,"","#"+h)}catch(e){}
cur=pick();$("kout").innerHTML='<h2 style="font-size:18px;margin:24px 0 6px">Your stack: '+esc(cur.goal)+'</h2>'+cur.layers.map(function(L){return '<h3 style="font-size:15px;margin:18px 0 8px">'+esc(L[0])+'</h3>'+(L[2]?'<p class="muted" style="margin:0 0 8px;font-size:13.5px">No fully free option in the directory yet, so these have a free plan or free tier.</p>':'')+(L[1].length?'<div class="grid">'+L[1].map(function(x){return AS.card(x.seed?Object.assign({},x,{added:""}):x).replace(/href="tools\//,'href="../tools/').replace(/src="assets\//,'src="../assets/')}).join("")+'</div>':'<p class="muted" style="margin:0">No tools in the directory match these filters for this layer yet. Try a wider budget or "Doesn\'t matter" for open source.</p>')}).join("")
+'<h3 style="font-size:15px;margin:18px 0 8px">Model</h3><p style="margin:0">Pick a model by price and fit in the <a href="ai-cost-calculator.html">AI API cost calculator</a>.</p>';AS.fixImgs&&AS.fixImgs($("kout"));window.ASHearts&&ASHearts($("kout"))}
function txt(){return"My AI agent stack ("+cur.goal+"), via AgentScout:\n"+cur.layers.map(function(L){return"- "+L[0]+": "+(L[1].map(function(x){return x.name}).join(", ")||"none matched")}).join("\n")+"\n"+location.href.split("?")[0]}
function msg(s){$("kmsg").textContent=s;setTimeout(function(){$("kmsg").textContent=""},2500)}
$("kcopy").addEventListener("click",function(){cur&&navigator.clipboard.writeText(txt()).then(function(){msg("Copied")})});
$("klink").addEventListener("click",function(){navigator.clipboard.writeText(location.href.replace(/([?&])notrack(=[^&#]*)?(&|(?=#)|$)/,function(m,a,b,c){return c?a:""})).then(function(){msg("Link copied")})});
$("kpng").addEventListener("click",function(){if(!cur)return;var W=1200,H=630,c=document.createElement("canvas");c.width=W;c.height=H;var x=c.getContext("2d");x.fillStyle="#0b0d12";x.fillRect(0,0,W,H);x.fillStyle="#7c8cff";x.fillRect(0,0,W,8);
x.fillStyle="#fff";x.font="700 44px Inter,system-ui,sans-serif";x.fillText("My AI agent stack",60,100);x.fillStyle="#aab";x.font="28px Inter,system-ui,sans-serif";x.fillText(cur.goal,60,145);
var y=215;cur.layers.slice(0,5).forEach(function(L){x.fillStyle="#7c8cff";x.font="600 24px Inter,system-ui,sans-serif";x.fillText(L[0],60,y);x.fillStyle="#fff";x.font="26px Inter,system-ui,sans-serif";var s=L[1].map(function(t){return t.name}).join("  ·  ")||"none matched";while(x.measureText(s).width>W-120&&s.length>4)s=s.slice(0,-2);x.fillText(s,60,y+36);y+=80});
x.fillStyle="#aab";x.font="24px Inter,system-ui,sans-serif";x.fillText("Build yours free at agentscouthq.com/free-tools",60,H-40);c.toBlob(function(b){var a=document.createElement("a");a.href=URL.createObjectURL(b);a.download="my-ai-agent-stack.png";a.click();setTimeout(function(){URL.revokeObjectURL(a.href)},1000)})});
try{location.hash.replace(/^#/,"").split("&").forEach(function(p){var kv=p.split("=");if(kv[1]&&$(kv[0])&&[].some.call($(kv[0]).options,function(o){return o.value===kv[1]}))$(kv[0]).value=kv[1]})}catch(e){}
["kg","ks","kb","ko"].forEach(function(i){$(i).addEventListener("change",run)});
fetch("../api/tools.json").then(function(r){return r.json()}).then(function(d){T=Array.isArray(d)?d:d.tools;run()}).catch(function(){$("kout").innerHTML='<p class="empty">Couldn\'t load the directory. Please refresh.</p>'});'''
    faq=[("What is an AI agent stack?","The set of tools an AI agent runs on: the agent or framework itself, the model, memory and knowledge retrieval (RAG), connectors such as MCP servers, a sandbox to run code safely, and evals or observability to see what it is doing."),
         ("Where do the recommendations come from?",f"From the AgentScout directory of {len(t):,} link-checked AI agent tools. Your answers filter it, and tools are ordered by AgentScout weekly picks and GitHub stars."),
         ("Can I share my stack?","Yes. Copy the link (your choices are saved in it), copy the stack as text, or download a PNG stack card to post."),
         ("Does this cost anything?","No. It is free, needs no sign-up and runs in your browser.")]
    return wrap("ai-agent-stack-builder","AI agent stack builder","Tell us what your agent should do, how technical you are and your budget, and get a recommended stack from the AgentScout directory, layer by layer, with a shareable stack card.",inner,faq,js,t)

# ---- Batch B, Oct 20 2026: system prompt linter, context window planner, license checker, build vs buy (all browser-only) ----
TOOLS+=[
("system-prompt-linter","System Prompt Linter","Paste a system prompt and get a score out of 10 with checks for role, task, output format, rules, conflicts, vague wording and prompt-injection defenses.","🩺"),
("context-window-planner","Context Window Planner","See how much of your model's context window the system prompt, tools, documents, history and output reserve use, as one clear bar.","📏"),
("open-source-license-checker","Open-Source License Checker for AI Tools","Pick a license (MIT, Apache, GPL, AGPL, ELv2, BSL and more) and see if you can use it commercially, self-host it or offer it as a service.","⚖️"),
("build-vs-buy-calculator","Build vs Buy AI Agent Calculator","Compare self-hosting an open-source AI agent with paying for a hosted tool over 12 to 36 months, with the break-even month.","💰"),
]
REL.update({"system-prompt-linter":(["open-source-llm-observability-tools","ai-research-assistants"],["ai-engineers","developers","product-managers"]),
 "context-window-planner":(["open-source-llm-observability-tools","python-ai-agent-frameworks"],["ai-engineers","developers"]),
 "open-source-license-checker":(["open-source-ai-agent-frameworks","open-source-ai-coding-agents","open-source-personal-ai-assistants"],["founders","startup-ctos","open-source-maintainers"]),
 "build-vs-buy-calculator":(["open-source-ai-agent-frameworks","enterprise-ai-agent-platforms","free-no-code-ai-agent-builders"],["founders","startup-ctos","operations-teams"])})

def linter(t):
    ex="You are a support assistant for Acme.\nAnswer billing questions using the help center.\nAlways be friendly.\nTry to keep answers short if possible.\nNever share internal notes."
    inner=(f'<div {BOX}><label {LAB} for="lp">Your system prompt</label><textarea id="lp" rows="12" {TA}>{e(ex)}</textarea>'
           f'<div id="lres" style="{CARDS}"></div></div><div id="lout"></div>'
           '<p style="margin:12px 0 0"><button class="btn primary" type="button" id="lcopy">Copy report</button> <span id="lmsg" class="muted" aria-live="polite"></span></p>'
           '<h2 style="font-size:18px;margin:28px 0 6px">What the linter checks</h2><p>Ten rule-of-thumb checks that catch the most common system prompt problems: a clear role, a stated task, an output format, explicit rules, a way to handle uncertainty, examples, no vague hedging, no conflicting always/never rules, no unfilled placeholders, and a defense against instructions hidden in user or tool content. It runs simple text rules in your browser, so it can miss things or flag a deliberate choice: treat it as a checklist, not a grade from a model.</p>')
    js=NUMJS+r''';function esc(s){return String(s).replace(/[&<>]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;"}[c]})}
var C=[["Role","Says who the AI is (\u201cYou are\u2026\u201d, \u201cAct as\u2026\u201d).",function(s){return/\b(you are|act as|your role|you're an?)\b/i.test(s)}],
["Task","States what to do (answer, write, help, review, summarize\u2026).",function(s){return/\b(your (job|task|goal) is|help (the )?users?|answer|write|summari[sz]e|review|classify|draft|extract|translate)\b/i.test(s)}],
["Output format","Says how to format replies (length, list, JSON, Markdown, sections).",function(s){return/\b(format|json|markdown|bullet|numbered|table|respond (with|in)|reply (with|in)|under \d+ (words|sentences|characters)|sections?|headings?)\b/i.test(s)}],
["Clear rules","Has explicit must / never / don't rules.",function(s){return/\b(never|must|do not|don't|always|only)\b/i.test(s)}],
["Uncertainty","Says what to do when unsure (ask, say you don't know, escalate).",function(s){return/(if (you are |you're )?(unsure|not sure|uncertain)|don't know|do not know|ask (a |the user|for)|clarif|escalat|hand (it )?off)/i.test(s)}],
["Examples","Gives at least one example of a good answer.",function(s){return/(example|e\.g\.|for instance|<example>)/i.test(s)}],
["No vague hedging","Avoids \u201ctry to\u201d, \u201cif possible\u201d, \u201cmaybe\u201d, \u201cetc.\u201d and \u201cas needed\u201d.",function(s){return!/\b(try to|if possible|maybe|perhaps|etc\.?|as needed|as appropriate|somewhat)\b/i.test(s)}],
["No conflicting rules","No word appears in both an \u201calways\u201d and a \u201cnever\u201d rule.",function(s){var a=[],n=[];s.split(/[\n.!]/).forEach(function(l){var w=(l.toLowerCase().match(/[a-z]{5,}/g)||[]).filter(function(x){return["always","never","should","their","there","about","which","would","could"].indexOf(x)<0});if(/\balways\b/i.test(l))a=a.concat(w);if(/\b(never|don't|do not)\b/i.test(l))n=n.concat(w)});return!a.some(function(x){return n.indexOf(x)>=0})}],
["No placeholders","No unfilled {{variables}}, [INSERT\u2026] or TODO.",function(s){return!/(\{\{[^}]*\}\}|\[(insert|your|todo)[^\]]*\]|\bTODO\b|\bTBD\b)/i.test(s)}],
["Injection defense","Tells the AI to treat documents, web pages or tool results as data, not instructions.",function(s){return/(ignore (any )?instructions (in|inside|from|found)|treat .{0,40}(as data|as untrusted|not as instructions)|untrusted|prompt injection|do not follow instructions (in|from))/i.test(s)}]];
var rep="";function run(){var s=$("lp").value,res=C.map(function(c){return[c,!!(s.trim()&&c[2](s))]}),sc=res.filter(function(x){return x[1]}).length,tk=asTok(s),caps=(s.match(/\b[A-Z]{4,}\b/g)||[]).length;
var notes=[];if(tk>4000)notes.push("Long prompt (\u2248"+tk.toLocaleString()+" tokens). Every request pays for it; move rarely used detail into tools or retrieved docs.");if(caps>=5)notes.push(caps+" ALL-CAPS words. Shouting rarely helps modern models; plain, specific rules work better.");
var ln=s.split("\n").map(function(x){return x.trim().toLowerCase()}).filter(Boolean),dup=ln.filter(function(x,i){return ln.indexOf(x)!==i});if(dup.length)notes.push(dup.length+" repeated line(s).");
$("lres").innerHTML=card("Score",sc+" / 10")+card("Estimated tokens",tk.toLocaleString())+card("Words",(s.match(/\S+/g)||[]).length.toLocaleString());
$("lout").innerHTML='<ul style="list-style:none;padding:0;margin:14px 0 0">'+res.map(function(x){return'<li style="padding:8px 0;border-bottom:1px solid var(--line)"><b>'+(x[1]?"\u2705":"\u26a0\ufe0f")+" "+x[0][0]+'</b><br><span class="muted" style="font-size:14px">'+x[0][1]+'</span></li>'}).join("")+'</ul>'+(notes.length?'<p style="margin:12px 0 0"><b>Also:</b> '+notes.map(esc).join(" ")+'</p>':"");
rep="System prompt lint: "+sc+"/10 (AgentScout)\n"+res.map(function(x){return(x[1]?"[ok] ":"[fix] ")+x[0][0]}).join("\n")+(notes.length?"\n"+notes.join("\n"):"")}
$("lp").addEventListener("input",run);$("lcopy").addEventListener("click",function(){navigator.clipboard.writeText(rep).then(function(){$("lmsg").textContent="Copied";setTimeout(function(){$("lmsg").textContent=""},1500)})});run();'''
    faq=[("What makes a good system prompt?","A clear role and task, the output format you want, explicit rules, what to do when unsure, and one example. Specific instructions beat long lists of vague ones."),
         ("How is the score worked out?","One point for each of ten checks passed. The checks are simple text rules that run in your browser, not an AI model, so read each item rather than chasing a perfect score."),
         ("What is prompt injection?","Text in a web page, document, email or tool result that tries to give the AI new instructions. Telling the model to treat that content as data, not instructions, is a basic first defense; agents with real tools also need permission checks."),
         ("Is my prompt sent anywhere?","No. Everything runs in your browser.")]
    return wrap("system-prompt-linter","System prompt linter","Paste a system prompt and get a score out of 10, with checks for role, task, output format, rules, conflicts, vague wording and prompt-injection defense. Build one from scratch with the <a href=\"prompt-builder.html\">prompt builder</a>.",inner,faq,js,t)

def ctxplan(t):
    ta=lambda id,lab,v="":f'<label {LAB} for="{id}">{lab} <span class="muted" id="{id}n" style="font-weight:400"></span></label><textarea id="{id}" rows="4" {TA}>{e(v)}</textarea>'
    inner=(f'<div {BOX}><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:0 16px">'
           +_num("xw","Your model's context window (tokens)",128000)+_num("xo","Reserve for the reply (tokens)",4000)+_num("xh","Conversation history (tokens)",6000)+_num("xr","Retrieved documents (tokens)",20000)+
           '</div><p class="muted" style="font-size:13px;margin:8px 0 0">128,000 is only an example: enter the context window from your provider\'s model page. AgentScout does not list context sizes because they change often and differ by plan.</p>'
           +ta("xs","System prompt","You are a research assistant. Answer with sources.")+ta("xt","Tool definitions (JSON)",'[{"type":"function","name":"search","description":"Search the web","parameters":{"type":"object","properties":{"q":{"type":"string"}},"required":["q"]}}]')
           +ERR("xerr")+'<div id="xbar" role="img" aria-label="Context window usage" style="display:flex;height:28px;border-radius:8px;overflow:hidden;border:1px solid var(--line);margin-top:14px"></div><div id="xleg" style="display:flex;flex-wrap:wrap;gap:6px 14px;margin-top:8px;font-size:13.5px"></div>'
           f'<div id="xres" style="{CARDS}"></div></div>'
           '<p class="muted" style="font-size:13px">Token counts for pasted text are estimates from the same method as the <a href="token-counter.html">token counter</a>. Price thresholds also matter: some providers bill long prompts at a higher rate (see the notes in the <a href="ai-cost-calculator.html">cost calculator</a>).</p>')
    js=NUMJS+r''';var P=[["System prompt","#7c8cff"],["Tools","#2bb673"],["Documents","#f5a623"],["History","#e5484d"],["Reply reserve","#8e8e93"]];
function run(){chkN([["xw","Context window"],["xo","Reply reserve"],["xh","History"],["xr","Documents"]],"xerr");var s=asTok($("xs").value),tl=asTok($("xt").value);$("xsn").textContent="\u2248 "+s.toLocaleString()+" tokens";$("xtn").textContent="\u2248 "+tl.toLocaleString()+" tokens";
var parts=[s,tl,v("xr"),v("xh"),v("xo")],W=v("xw"),used=parts.reduce(function(a,b){return a+b},0),base=Math.max(W,used)||1;
$("xbar").innerHTML=parts.map(function(p,i){return'<div title="'+P[i][0]+'" style="width:'+(p/base*100)+'%;background:'+P[i][1]+'"></div>'}).join("");
$("xleg").innerHTML=P.map(function(p,i){return'<span><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:'+p[1]+';margin-right:5px"></span>'+p[0]+": "+Math.round(parts[i]).toLocaleString()+'</span>'}).join("");
var free=W-used;$("xres").innerHTML=card("Used",Math.round(used).toLocaleString())+card("Share of window",W?Math.round(used/W*100)+"%":"\u2013")+card(free>=0?"Room left":"Over by",Math.abs(Math.round(free)).toLocaleString());
$("xres").lastChild.style.borderColor=free<0?"#e5484d":""}
["xw","xo","xh","xr","xs","xt"].forEach(function(i){$(i).addEventListener("input",run)});run();'''
    faq=[("What is a context window?","The maximum number of tokens a model can take in one request, counting the system prompt, tool definitions, conversation history, documents and the reply it writes."),
         ("Why reserve tokens for the reply?","The model's output shares the same window on most APIs. If the input fills it, the reply gets cut short or the request fails."),
         ("Why doesn't AgentScout list each model's context size?","Sizes change often and can differ by plan, region or API tier, so we only show figures you can check. Enter the number from the provider's model page."),
         ("What if I'm over the limit?","Trim history (summarize older turns), retrieve fewer or shorter documents, shorten tool descriptions, or choose a model with a larger window.")]
    return wrap("context-window-planner","Context window planner","See how much of your model's context window the system prompt, tool definitions, retrieved documents, chat history and reply reserve take up, and how much room is left.",inner,faq,js,t)

LIC=[("MIT","MIT",["yes","yes","yes","yes"],"Keep the copyright and license notice in copies. No patent clause."),
 ("Apache-2.0","Apache 2.0",["yes","yes","yes","yes"],"Keep the license and NOTICE file, state significant changes. Includes an explicit patent grant."),
 ("BSD-3-Clause","BSD 3-Clause",["yes","yes","yes","yes"],"Keep the copyright notice; don't use the authors' names to endorse your product."),
 ("MPL-2.0","Mozilla Public License 2.0",["yes","yes","yes","cond"],"File-level copyleft: if you distribute changed MPL files, share those files' source. Your own separate files can stay closed."),
 ("LGPL-3.0","GNU LGPL 3.0",["yes","yes","yes","cond"],"You can link it from closed-source software, but if you distribute changes to the library itself, share them under the LGPL."),
 ("GPL-3.0","GNU GPL 3.0",["yes","yes","yes","cond"],"If you distribute the software or a modified version, you must release the source under the GPL. Running it privately or as a hosted service without distributing it does not trigger that."),
 ("AGPL-3.0","GNU AGPL 3.0",["yes","yes","cond","cond"],"Like the GPL, plus: if you modify it and let users interact with it over a network, you must offer them the source of your modified version."),
 ("ELv2","Elastic License 2.0",["cond","yes","no","cond"],"Source-available, not open source. You can't offer it to others as a hosted or managed service, or bypass license-key features."),
 ("BUSL-1.1","Business Source License 1.1",["cond","cond","cond","cond"],"Source-available. Production use is limited by the project's Additional Use Grant; each version converts to an open-source license on its Change Date."),
 ("SSPL-1.0","Server Side Public License",["cond","yes","cond","cond"],"Source-available. If you offer it as a service, you must release the source of the whole service stack under the SSPL.")]
def license(t):
    # licences from the verified facts in tool_rich.json (repo LICENSE files); mixed or multi-licence projects are left out
    MAP={"the MIT License":"MIT","MIT":"MIT","the Apache License 2.0":"Apache-2.0","Apache-2.0":"Apache-2.0","the GNU AGPL v3.0":"AGPL-3.0","the GNU Affero General Public License v3.0":"AGPL-3.0",
         "the GNU GPL v3.0":"GPL-3.0","Elastic License 2.0 (source-available)":"ELv2","the BSD 3-Clause License":"BSD-3-Clause","the Mozilla Public License 2.0":"MPL-2.0"}
    RF_=json.load(open("tool_rich.json")); have={}
    for x in t:
        l=MAP.get(((RF_.get(x["slug"]) or {}).get("facts") or {}).get("license") or "")
        if l: have.setdefault(l,[]).append((x["slug"],x["name"]))
    data=[[k,n,c,note,sorted(have.get(k,[]),key=lambda z:z[1].lower())] for k,n,c,note in LIC]
    opts="".join(f'<option value="{e(k)}">{e(n)} ({e(k)})</option>' for k,n,_,_ in LIC)
    inner=(f'<div {BOX}><label {LAB} for="ql">License</label><select id="ql" {INP}>{opts}</select><div id="qout" aria-live="polite"></div></div>'
           '<p class="muted" style="font-size:13px">Plain-English summary of common terms, not legal advice. Always read the license text in the project\'s repository, and ask a lawyer for anything important. Some projects add extra terms or use different licenses for different parts.</p>'
           '<h2 style="font-size:18px;margin:28px 0 6px">Open source vs source-available</h2><p>Open-source licenses (MIT, Apache, BSD, MPL, LGPL, GPL, AGPL) let anyone use, change and share the code, with conditions that range from keeping a notice (permissive) to sharing your changes (copyleft). Source-available licenses (ELv2, BSL, SSPL) publish the code but restrict some uses, most often offering it as a competing hosted service. AgentScout labels these as "Source-available" in the directory.</p>')
    js=NUMJS+"\nvar LD="+json.dumps(data)+r''';function esc(s){return String(s).replace(/[&<>]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;"}[c]})}
var Q=["Use it in a commercial product","Modify it","Offer it as a hosted service (SaaS)","Keep your changes private"],M={yes:["\u2705","Yes"],cond:["\u26a0\ufe0f","With conditions"],no:["\u274c","No"]};
function run(){var d=LD.filter(function(x){return x[0]===$("ql").value})[0];try{history.replaceState(null,"","#"+d[0])}catch(e){}
$("qout").innerHTML='<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:14.5px;margin-top:14px">'+Q.map(function(q,i){var m=M[d[2][i]];return'<tr style="border-bottom:1px solid var(--line)"><td style="padding:8px 6px">'+q+'</td><td style="padding:8px 6px;white-space:nowrap"><b>'+m[0]+" "+m[1]+'</b></td></tr>'}).join("")+'</table></div><p style="margin:12px 0 0"><b>Main condition:</b> '+esc(d[3])+'</p>'
+'<p style="margin:12px 0 0">'+(d[4].length?"<b>"+d[4].length+" tool"+(d[4].length>1?"s":"")+" in the AgentScout directory use this license</b> (from each project's repository):<br>"+d[4].slice(0,30).map(function(z){return'<a href="../tools/'+z[0]+'.html">'+esc(z[1])+'</a>'}).join(" \u00b7 ")+(d[4].length>30?" \u00b7 and "+(d[4].length-30)+" more":""):'<span class="muted">No tools in the directory are recorded with this exact license yet.</span>')+'</p>'}
try{var h=decodeURIComponent(location.hash.slice(1));if(h&&LD.some(function(x){return x[0]===h}))$("ql").value=h}catch(e){}$("ql").addEventListener("change",run);run();'''
    faq=[("Can I use MIT or Apache 2.0 AI tools in a commercial product?","Yes. Both are permissive: you can use, change and sell software that includes them, as long as you keep the license and copyright notices (and, for Apache 2.0, the NOTICE file and a note of significant changes)."),
         ("What is the catch with AGPL?","If you change AGPL software and let people use it over a network, for example as a web app, you must offer them the source code of your changed version."),
         ("Is source-available the same as open source?","No. Licenses like the Elastic License 2.0, Business Source License and SSPL publish the code but restrict some uses, typically running it as a competing hosted service."),
         ("Is this legal advice?","No. It is a plain-English summary of common license terms. Read the actual license and ask a lawyer when it matters.")]
    return wrap("open-source-license-checker","Open-source license checker for AI tools","Pick a license and see in plain English whether you can use it commercially, modify it, run it as a hosted service and keep changes private, plus which AgentScout directory tools use it.",inner,faq,js,t)

def bvb(t):
    inner=(f'<div {BOX}><h2 style="font-size:16px;margin:0">Buy: hosted tool</h2><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:0 16px">'
           +_num("bs","Price per seat per month ($)",30)+_num("bn","Seats",5)+_num("bu","Usage or overage per month ($)",0)+_num("bo","One-time setup ($)",0)+
           f'</div><h2 style="font-size:16px;margin:22px 0 0">Build: self-host open source</h2><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:0 16px">'
           +_num("hs","Servers or hosting per month ($)",60)+_num("ha","Model API cost per month ($)",80)+_num("hh","Setup hours",40)+_num("hm","Maintenance hours per month",6)+_num("hr","Hourly cost of your time ($)",75)+
           f'</div><div><label {LAB} for="hy">Compare over</label><select id="hy" {INP}><option value="12">12 months</option><option value="24" selected>24 months</option><option value="36">36 months</option></select></div>'
           +ERR("berr")+f'<div id="bres" style="{CARDS}"></div><p id="bver" style="font-weight:600;margin:12px 0 0"></p></div>'
           '<p class="muted" style="font-size:13px">Need the model API figure? Estimate it with the <a href="agent-run-cost-estimator.html">agent run cost estimator</a>. Looking for open-source options? Browse the <a href="../best/index.html">best-of lists</a> or check a license with the <a href="open-source-license-checker.html">license checker</a>.</p>')
    js=NUMJS+r''';var F=[["bs","Seat price"],["bn","Seats"],["bu","Usage"],["bo","Setup"],["hs","Hosting"],["ha","Model API"],["hh","Setup hours"],["hm","Maintenance hours"],["hr","Hourly cost"]];
function run(){chkN(F,"berr");var y=+$("hy").value,buyM=v("bs")*v("bn")+v("bu"),buy0=v("bo"),bldM=v("hs")+v("ha")+v("hm")*v("hr"),bld0=v("hh")*v("hr"),B=buy0+buyM*y,S=bld0+bldM*y,be=null;
for(var m=1;m<=120;m++){if(bld0+bldM*m<=buy0+buyM*m){be=m;break}}
$("bres").innerHTML=card("Buy, "+y+" months",fm(B))+card("Build, "+y+" months",fm(S))+card("Buy per month",fm(buyM))+card("Build per month",fm(bldM))+card("Break-even",be?"Month "+be:"Not within 10 years");
$("bver").textContent=S<B?"Building looks cheaper over "+y+" months by "+fm(B-S)+".":S>B?"Buying looks cheaper over "+y+" months by "+fm(S-B)+".":"They cost the same over "+y+" months."}
F.map(function(x){return x[0]}).concat(["hy"]).forEach(function(i){$(i).addEventListener("input",run)});run();'''
    faq=[("How is the comparison calculated?","Buy = one-time setup + (seats × seat price + usage) × months. Build = setup hours × hourly cost + (hosting + model API + maintenance hours × hourly cost) × months. Break-even is the first month where building has cost no more in total than buying."),
         ("What does this leave out?","Things that are hard to price: security reviews, uptime, support, features the hosted tool adds over time, and what your team could build instead. Add rough figures to maintenance hours if they matter."),
         ("Are any prices filled in for me?","No. The starting numbers are examples only. Enter your real quotes and costs."),
         ("Is anything sent to a server?","No. The calculator runs in your browser.")]
    return wrap("build-vs-buy-calculator","Build vs buy AI agent calculator","Compare self-hosting an open-source AI agent with paying for a hosted tool: setup, hosting, model API, maintenance time and seats, over 12, 24 or 36 months, with the break-even month.",inner,faq,js,t)

# ---- Batch C, Oct 20 2026: MCP server picker, JSON output validator, comparison card maker (all browser-only).
TOOLS+=[
("mcp-server-picker","MCP Server Picker","Tick the apps you use, like GitHub, Slack, Notion or Postgres, and find matching MCP servers in the AgentScout directory.","🧲"),
("json-output-validator","JSON Output Schema Validator","Paste a JSON Schema and a model's output to see if it passes, with exact error paths and OpenAI strict-mode checks.","✅"),
("ai-tool-comparison-card","AI Tool Comparison Card Maker","Pick 2 or 3 AI tools from the directory and get a side-by-side comparison and a shareable image card.","🃏"),
]
REL.update({"mcp-server-picker":(["free-mcp-servers","terminal-ai-coding-agents"],["mcp-developers","developers","ai-engineers"]),
 "json-output-validator":(["python-ai-agent-frameworks","typescript-ai-agent-frameworks","open-source-llm-observability-tools"],["ai-engineers","developers","qa-engineers"]),
 "ai-tool-comparison-card":(["free-ai-coding-agents","open-source-ai-agent-frameworks"],["content-creators","founders","marketers"])})
APPS=[("GitHub",r"github"),("GitLab",r"gitlab"),("Slack",r"slack"),("Discord",r"discord"),("Notion",r"notion"),("Linear",r"linear"),("Jira",r"jira|atlassian"),("Google Drive",r"google drive|gdrive"),("Gmail",r"gmail"),("Google Calendar",r"google calendar"),
 ("Postgres",r"postgres|postgresql"),("MySQL",r"mysql"),("SQLite",r"sqlite"),("MongoDB",r"mongodb"),("Supabase",r"supabase"),("Redis",r"redis"),("Stripe",r"stripe"),("Figma",r"figma"),("Sentry",r"sentry"),
 ("Docker",r"docker"),("Kubernetes",r"kubernetes|k8s"),("AWS",r"aws|amazon web services"),("Cloudflare",r"cloudflare"),("Browser / web automation",r"browser|playwright|puppeteer|chrome"),("Web search",r"web search|search api|search engine"),
 ("Files on my computer",r"filesystem|file system|local files"),("Obsidian",r"obsidian"),("Zapier",r"zapier"),("Shopify",r"shopify"),("HubSpot",r"hubspot"),("Salesforce",r"salesforce")]
def mcppick(t):
    pool=[x for x in t if x["category"]=="MCP servers"]
    def txt(x): return " ".join([x["name"],x["description"]]+x.get("use_cases",[])+x.get("tags",[])).lower()
    import re as _re
    apps=[[n,p,sum(1 for x in pool if _re.search(r"\b("+p+r")\b",txt(x)))] for n,p in APPS]
    apps=[a for a in apps if a[2]>0]
    chk="".join(f'<label style="display:inline-flex;gap:6px;align-items:center;margin:0 14px 8px 0;font-size:14px"><input type="checkbox" class="mpa" value="{i}"> {e(n)} <span class="muted" style="font-size:12.5px">({c})</span></label>' for i,(n,p,c) in enumerate(apps))
    inner=(f'<div {BOX}><p style="margin:0 0 8px;font-weight:600;font-size:14px">Which apps should your agent connect to?</p>{chk}'
           f'<label {LAB} for="mpq">Or search by keyword</label><input id="mpq" placeholder="e.g. calendar, crm, vector database" {INP}>'
           f'<label style="display:flex;gap:8px;align-items:center;margin:12px 0 0;font-size:14px"><input type="checkbox" id="mpo"> Open source only</label></div><div id="mpout" aria-live="polite"><p class="muted">Loading the directory…</p></div>'
           f'<p class="muted" style="font-size:13.5px;margin-top:14px">Matches come from the names, descriptions and tags of the {len(pool)} MCP servers in the directory. Check each server\'s own docs for install steps, then turn them into config for Claude Desktop, Cursor, VS Code or Claude Code with the <a href="mcp-config-builder.html">MCP config builder</a>. Only connect servers you trust.</p>')
    js=NUMJS+"\nvar A="+json.dumps([[n,p] for n,p,_ in apps])+r''';var T=null;function txt(x){return[x.name,x.description].concat(x.tags||[]).join(" ").toLowerCase()}
function run(){if(!T)return;var sel=[].slice.call(document.querySelectorAll(".mpa:checked")).map(function(c){return A[+c.value]}),q=$("mpq").value.trim().toLowerCase(),os=$("mpo").checked,h="";
var groups=sel.map(function(a){return[a[0],new RegExp("\\b("+a[1]+")\\b")]});if(q)groups.push(["\u201c"+q+"\u201d",null]);
if(!groups.length){$("mpout").innerHTML='<p class="muted" style="margin-top:14px">Tick an app or type a keyword to see matching MCP servers.</p>';return}
groups.forEach(function(g){var m=T.filter(function(x){if(os&&!x.open_source)return false;var s=txt(x);return g[1]?g[1].test(s):s.indexOf(q)>=0}).sort(function(a,b){var na=g[1]?+g[1].test(a.name.toLowerCase()):+(a.name.toLowerCase().indexOf(q)>=0),nb=g[1]?+g[1].test(b.name.toLowerCase()):+(b.name.toLowerCase().indexOf(q)>=0);return nb-na||(b.weekly_pick?1:0)-(a.weekly_pick?1:0)||(b.github_stars||0)-(a.github_stars||0)});
h+='<h2 style="font-size:17px;margin:24px 0 8px">'+g[0]+' <span class="muted" style="font-weight:400;font-size:14px">('+m.length+')</span></h2>'+(m.length?'<div class="grid">'+m.slice(0,9).map(function(x){return AS.card(x.seed?Object.assign({},x,{added:""}):x).replace(/href="tools\//,'href="../tools/').replace(/src="assets\//,'src="../assets/')}).join("")+'</div>'+(m.length>9?'<p class="muted" style="font-size:13.5px">Showing the top 9: name matches first, then AgentScout picks and GitHub stars. <a href="../categories/mcp-servers.html">See every MCP server</a>.</p>':''):'<p class="muted" style="margin:0">No MCP servers in the directory match this yet.</p>')});
$("mpout").innerHTML=h;AS.fixImgs&&AS.fixImgs($("mpout"));window.ASHearts&&ASHearts($("mpout"))}
document.querySelectorAll(".mpa,#mpo").forEach(function(c){c.addEventListener("change",run)});$("mpq").addEventListener("input",run);
fetch("../api/tools.json").then(function(r){return r.json()}).then(function(d){T=(Array.isArray(d)?d:d.tools).filter(function(x){return x.category==="MCP servers"});run()}).catch(function(){$("mpout").innerHTML='<p class="empty">Couldn\'t load the directory. Please refresh.</p>'});'''
    faq=[("What is an MCP server?","A Model Context Protocol server is a small program that gives an AI app like Claude Desktop, Cursor or VS Code access to a tool or data source, such as GitHub, a database or your files, through one standard interface."),
         ("How are matches found?","By keyword across the name, description and tags of every MCP and infrastructure tool in the AgentScout directory, with servers named after the app first, then AgentScout picks and GitHub stars. Read each server's page to confirm it does what you need."),
         ("How do I install the servers I pick?","Follow the install steps in each server's own docs, then paste the details into the MCP config builder to get config for Claude Desktop, Cursor, VS Code or Claude Code."),
         ("Are MCP servers safe?","Only as safe as the code and the permissions you give them. Prefer official or well-maintained servers, give the least access needed, and never paste real secrets into shared files.")]
    return wrap("mcp-server-picker","MCP server picker","Tick the apps your AI agent should connect to, like GitHub, Slack, Notion or Postgres, and find matching MCP servers in the AgentScout directory. Then build the config with the <a href=\"mcp-config-builder.html\">MCP config builder</a>.",inner,faq,js,t)

def jsonval(t):
    sch='{\n  "type": "object",\n  "properties": {\n    "title": {"type": "string", "maxLength": 60},\n    "priority": {"type": "string", "enum": ["low", "medium", "high"]},\n    "tags": {"type": "array", "items": {"type": "string"}}\n  },\n  "required": ["title", "priority", "tags"],\n  "additionalProperties": false\n}'
    out='Here is the result:\n```json\n{"title": "Refund request for order 1042", "priority": "urgent", "tags": ["billing"], "notes": "VIP"}\n```'
    inner=(f'<div {BOX}><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:0 18px"><div><label {LAB} for="js">JSON Schema</label><textarea id="js" rows="14" spellcheck="false" {TA}>{e(sch)}</textarea></div>'
           f'<div><label {LAB} for="jo">Model output</label><textarea id="jo" rows="14" spellcheck="false" {TA}>{e(out)}</textarea></div></div>'
           f'<div id="jres" style="{CARDS}"></div><div id="jout" aria-live="polite"></div></div>'
           '<p style="margin:12px 0 0"><button class="btn primary" type="button" id="jcopy">Copy report</button> <span id="jmsg" class="muted" aria-live="polite"></span></p>'
           '<h2 style="font-size:18px;margin:28px 0 6px">What it supports</h2><p>The validator covers the JSON Schema keywords most used for structured outputs: <code>type</code> (including type lists for nullable fields), <code>properties</code>, <code>required</code>, <code>additionalProperties</code>, <code>items</code>, <code>enum</code>, <code>const</code>, <code>anyOf</code>, <code>minLength</code>/<code>maxLength</code>, <code>minimum</code>/<code>maximum</code>, <code>minItems</code>/<code>maxItems</code>, <code>pattern</code> and local <code>$ref</code> to <code>#/$defs</code>. Other keywords are listed as not checked. If the output has text or a ```json fence around the JSON, the JSON part is pulled out first. Need a schema? Make one with the <a href="tool-schema-builder.html">tool schema builder</a>.</p>')
    js=NUMJS+r''';function esc(s){return String(s).replace(/[&<>]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;"}[c]})}
var KNOWN=["type","properties","required","additionalProperties","items","enum","const","anyOf","minLength","maxLength","minimum","maximum","minItems","maxItems","pattern","$ref","$defs","definitions","description","title","default","strict","$schema","examples","format"];
function ty(v){return v===null?"null":Array.isArray(v)?"array":typeof v==="number"?(Number.isInteger(v)?"integer":"number"):typeof v}
function extract(s){s=s.trim();var m=/```(?:json)?\s*([\s\S]*?)```/i.exec(s);if(m)return[m[1].trim(),"Pulled the JSON out of a code fence."];try{JSON.parse(s);return[s,""]}catch(e){}var a=s.search(/[\[{]/),b=Math.max(s.lastIndexOf("}"),s.lastIndexOf("]"));if(a>=0&&b>a)return[s.slice(a,b+1),"Ignored text around the JSON."];return[s,""]}
var ROOT,unk={};function res(r){if(r&&r.$ref){var p=r.$ref.replace(/^#\//,"").split("/"),o=ROOT;p.forEach(function(k){o=o&&o[k]});return o||{}}return r}
function val(s,v,p,E){s=res(s);if(!s||typeof s!=="object")return;Object.keys(s).forEach(function(k){if(KNOWN.indexOf(k)<0)unk[k]=1});
if(s.anyOf){var ok=s.anyOf.some(function(x){var e2=[];val(x,v,p,e2);return!e2.length});if(!ok)E.push([p,"matches none of the anyOf options"]);return}
if(s.type){var ts=[].concat(s.type),t=ty(v);if(!(ts.indexOf(t)>=0||(t==="integer"&&ts.indexOf("number")>=0))){E.push([p,"should be "+ts.join(" or ")+", got "+t]);return}}
if(s["enum"]&&!s["enum"].some(function(x){return JSON.stringify(x)===JSON.stringify(v)}))E.push([p,"must be one of "+JSON.stringify(s["enum"])+", got "+JSON.stringify(v)]);
if("const" in s&&JSON.stringify(s["const"])!==JSON.stringify(v))E.push([p,"must equal "+JSON.stringify(s["const"])]);
if(typeof v==="string"){if(s.minLength!=null&&v.length<s.minLength)E.push([p,"is shorter than "+s.minLength+" characters"]);if(s.maxLength!=null&&v.length>s.maxLength)E.push([p,"is longer than "+s.maxLength+" characters ("+v.length+")"]);if(s.pattern){try{if(!new RegExp(s.pattern,"u").test(v))E.push([p,"does not match pattern "+s.pattern])}catch(e){E.push([p,"schema pattern is not a valid regex"])}}}
if(typeof v==="number"){if(s.minimum!=null&&v<s.minimum)E.push([p,"is below the minimum "+s.minimum]);if(s.maximum!=null&&v>s.maximum)E.push([p,"is above the maximum "+s.maximum])}
if(Array.isArray(v)){if(s.minItems!=null&&v.length<s.minItems)E.push([p,"has fewer than "+s.minItems+" items"]);if(s.maxItems!=null&&v.length>s.maxItems)E.push([p,"has more than "+s.maxItems+" items"]);if(s.items)v.forEach(function(x,i){val(s.items,x,p+"["+i+"]",E)})}
if(v&&typeof v==="object"&&!Array.isArray(v)){var pr=s.properties||{};(s.required||[]).forEach(function(k){if(!(k in v))E.push([p,"is missing required property \u201c"+k+"\u201d"])});
Object.keys(v).forEach(function(k){if(pr[k])val(pr[k],v[k],p+"."+k,E);else if(s.additionalProperties===false)E.push([p,"has unexpected property \u201c"+k+"\u201d"]);else if(s.additionalProperties&&typeof s.additionalProperties==="object")val(s.additionalProperties,v[k],p+"."+k,E)})}}
function strict(s,p,W){s=res(s);if(!s||typeof s!=="object")return;if(s.type==="object"||[].concat(s.type||[]).indexOf("object")>=0||s.properties){var ks=Object.keys(s.properties||{}),rq=s.required||[];if(s.additionalProperties!==false)W.push(p+": set \u201cadditionalProperties\u201d: false");var miss=ks.filter(function(k){return rq.indexOf(k)<0});if(miss.length)W.push(p+": list every property in \u201crequired\u201d (missing "+miss.join(", ")+")");ks.forEach(function(k){strict(s.properties[k],p+"."+k,W)})}
if(s.items)strict(s.items,p+"[]",W);(s.anyOf||[]).forEach(function(x,i){strict(x,p+".anyOf["+i+"]",W)})}
var rep="";function run(){var S,O,E=[],W=[],note="";unk={};$("jres").innerHTML="";
try{S=JSON.parse($("js").value)}catch(e){$("jout").innerHTML='<p style="color:#e5484d;margin:14px 0 0"><b>The schema is not valid JSON:</b> '+esc(e.message)+'</p>';rep="Schema is not valid JSON";return}
var x=extract($("jo").value);note=x[1];try{O=JSON.parse(x[0])}catch(e){$("jres").innerHTML=card("Result","\u274c Not JSON");$("jout").innerHTML='<p style="color:#e5484d;margin:14px 0 0"><b>The output is not valid JSON:</b> '+esc(e.message)+'</p>';rep="Output is not valid JSON: "+e.message;return}
ROOT=S;val(S,O,"$",E);strict(S,"$",W);var u=Object.keys(unk);
$("jres").innerHTML=card("Result",E.length?"\u274c Fails":"\u2705 Passes")+card("Errors",E.length)+card("OpenAI strict mode",W.length?"\u26a0\ufe0f "+W.length+" fix"+(W.length>1?"es":""):"\u2705 Ready");
$("jout").innerHTML=(note?'<p class="muted" style="margin:14px 0 0">'+note+'</p>':"")+(E.length?'<h3 style="font-size:15px;margin:16px 0 6px">Errors</h3><ul style="margin:0;padding-left:20px">'+E.map(function(z){return"<li><code>"+esc(z[0])+"</code> "+esc(z[1])+"</li>"}).join("")+"</ul>":"")
+(W.length?'<h3 style="font-size:15px;margin:16px 0 6px">For OpenAI strict structured outputs</h3><ul style="margin:0;padding-left:20px">'+W.map(function(z){return"<li>"+esc(z)+"</li>"}).join("")+"</ul>":"")+(u.length?'<p class="muted" style="margin:12px 0 0;font-size:13.5px">Not checked: '+u.map(esc).join(", ")+'</p>':"");
rep="JSON output check (AgentScout): "+(E.length?"FAILS with "+E.length+" error(s)":"passes")+"\n"+E.map(function(z){return"- "+z[0]+" "+z[1]}).join("\n")+(W.length?"\nStrict mode:\n"+W.map(function(z){return"- "+z}).join("\n"):"")}
["js","jo"].forEach(function(i){$(i).addEventListener("input",run)});$("jcopy").addEventListener("click",function(){navigator.clipboard.writeText(rep).then(function(){$("jmsg").textContent="Copied";setTimeout(function(){$("jmsg").textContent=""},1500)})});run();'''
    faq=[("Why validate a model's JSON output?","Even with structured-output modes, models can return missing fields, wrong types or values outside an enum, especially without strict mode. Checking against your schema catches this before it breaks your app."),
         ("What does OpenAI strict mode need?","OpenAI's strict structured outputs require every object to set additionalProperties to false and to list all of its properties in required. Use a type list like [\"string\", \"null\"] for optional values."),
         ("Does it support the full JSON Schema spec?","No. It covers the keywords most used for structured outputs and lists any others in the schema as not checked."),
         ("Is my data uploaded?","No. Validation runs in your browser.")]
    return wrap("json-output-validator","JSON output schema validator","Paste a JSON Schema and a model's output to see whether it passes, with the exact path of every error, plus checks for OpenAI strict structured outputs.",inner,faq,js,t)

def cmpcard(t):
    inner=(f'<div {BOX}><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:0 16px">'
           +"".join(f'<div><label {LAB} for="cc{i}">Tool {i+1}{" (optional)" if i==2 else ""}</label><input id="cc{i}" list="ccl" autocomplete="off" placeholder="Start typing a tool name" {INP}></div>' for i in range(3))+
           '</div><datalist id="ccl"></datalist><p id="cerr2" role="alert" style="color:#e5484d;margin:8px 0 0;font-size:13.5px"></p></div><div id="ccout" aria-live="polite"></div>'
           '<p style="margin:12px 0 0;display:flex;flex-wrap:wrap;gap:8px"><button class="btn primary" type="button" id="ccpng">Download comparison card (PNG)</button><button class="btn" type="button" id="cclink">Copy link</button><button class="btn" type="button" id="cctxt">Copy as text</button><span id="ccmsg" class="muted" aria-live="polite" style="align-self:center"></span></p>'
           '<p class="muted" style="font-size:13px">Data comes from the AgentScout directory: pricing as each maker states it, open source as listed, and GitHub stars from our latest snapshot of the repository linked on the tool page. For a written head-to-head, see <a href="../compare/index.html">AgentScout comparisons</a>.</p>')
    js=NUMJS+r''';var T=null,BY={},cur=[];function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
var ROWS=[["Category",function(x){return x.category}],["Pricing",function(x){return x.pricing}],["Open source",function(x){return x.open_source?"Yes":"No"}],["Skill level",function(x){return x.skill==="no-code"?"No code needed":"For developers"}],["Platforms",function(x){return(x.platforms||[]).join(", ")||"\u2013"}],["GitHub stars",function(x){return x.github_stars?x.github_stars.toLocaleString():"\u2013"}]];
function find(n){n=n.trim().toLowerCase();return BY[n]||null}
function run(){if(!T)return;cur=[0,1,2].map(function(i){return find($("cc"+i).value)}).filter(Boolean);var bad=[0,1,2].filter(function(i){return $("cc"+i).value.trim()&&!find($("cc"+i).value)});
$("cerr2").textContent=bad.map(function(i){return"No tool named \u201c"+$("cc"+i).value.trim()+"\u201d in the directory. Pick a name from the list."}).join(" ");[0,1,2].forEach(function(i){$("cc"+i).setAttribute("aria-invalid",bad.indexOf(i)>=0?"true":"false")});
try{history.replaceState(null,"","#"+cur.map(function(x){return encodeURIComponent(x.slug)}).join(","))}catch(e){}
if(cur.length<2){$("ccout").innerHTML='<p class="muted" style="margin-top:14px">'+(bad.length?'Fix the tool name above, then choose at least two tools to compare.':'Choose at least two tools to compare.')+'</p>';return}
$("ccout").innerHTML='<div style="overflow-x:auto;margin-top:16px" tabindex="0" role="region" aria-label="Comparison table"><table style="width:100%;border-collapse:collapse;font-size:14px;min-width:'+(cur.length*150+110)+'px"><thead><tr style="text-align:left;border-bottom:1px solid var(--line)"><th style="padding:8px 6px"></th>'+cur.map(function(x){return'<th style="padding:8px 6px"><a href="../tools/'+esc(x.slug)+'.html">'+esc(x.name)+'</a></th>'}).join("")+'</tr></thead><tbody>'
+ROWS.map(function(r){return'<tr style="border-bottom:1px solid var(--line)"><td style="padding:8px 6px;font-weight:600">'+r[0]+'</td>'+cur.map(function(x){return'<td style="padding:8px 6px">'+esc(r[1](x))+'</td>'}).join("")+'</tr>'}).join("")
+'<tr><td style="padding:8px 6px;font-weight:600">What it does</td>'+cur.map(function(x){return'<td style="padding:8px 6px;font-size:13.5px">'+esc(x.description)+'</td>'}).join("")+'</tr></tbody></table></div>'}
function msg(s){$("ccmsg").textContent=s;setTimeout(function(){$("ccmsg").textContent=""},2000)}
function wrapT(x,s,w){var out=[],l="";s.split(" ").forEach(function(wd){var t=l?l+" "+wd:wd;if(x.measureText(t).width>w&&l){out.push(l);l=wd}else l=t});if(l)out.push(l);return out}
$("ccpng").addEventListener("click",function(){if(cur.length<2){msg("Choose two tools first");return}var W=1200,H=630,c=document.createElement("canvas");c.width=W;c.height=H;var x=c.getContext("2d"),n=cur.length,cw=(W-280)/n;
x.fillStyle="#0b0d12";x.fillRect(0,0,W,H);x.fillStyle="#7c8cff";x.fillRect(0,0,W,8);x.fillStyle="#fff";x.font="700 40px Inter,system-ui,sans-serif";x.fillText(cur.map(function(t){return t.name}).join(" vs ").slice(0,48),50,80);
cur.forEach(function(t,i){x.fillStyle="#7c8cff";x.font="700 28px Inter,system-ui,sans-serif";x.fillText(t.name.slice(0,22),260+i*cw,150)});
ROWS.forEach(function(r,j){var y=210+j*62;x.fillStyle="#aab";x.font="600 22px Inter,system-ui,sans-serif";x.fillText(r[0],50,y);x.fillStyle="#fff";x.font="22px Inter,system-ui,sans-serif";
cur.forEach(function(t,i){var ln=wrapT(x,String(r[1](t)),cw-24).slice(0,2);ln.forEach(function(s,k){x.fillText(s,260+i*cw,y+k*26)})})});
x.fillStyle="#aab";x.font="22px Inter,system-ui,sans-serif";x.fillText("Compare AI tools free at agentscouthq.com/free-tools",50,H-30);
c.toBlob(function(b){var a=document.createElement("a");a.href=URL.createObjectURL(b);a.download=cur.map(function(t){return t.slug}).join("-vs-")+".png";a.click();setTimeout(function(){URL.revokeObjectURL(a.href)},1000)})});
$("cclink").addEventListener("click",function(){navigator.clipboard.writeText(location.href.replace(/([?&])notrack(=[^&#]*)?(&|(?=#)|$)/,function(m,a,b,c){return c?a:""})).then(function(){msg("Link copied")})});
$("cctxt").addEventListener("click",function(){if(cur.length<2)return;navigator.clipboard.writeText(cur.map(function(t){return t.name}).join(" vs ")+" (via AgentScout)\n"+ROWS.map(function(r){return r[0]+": "+cur.map(function(t){return t.name+" "+r[1](t)}).join(" | ")}).join("\n")+"\n"+location.href.split("?")[0]).then(function(){msg("Copied")})});
[0,1,2].forEach(function(i){$("cc"+i).addEventListener("input",run);$("cc"+i).addEventListener("change",run)});
fetch("../api/tools.json").then(function(r){return r.json()}).then(function(d){T=Array.isArray(d)?d:d.tools;T.forEach(function(x){BY[x.name.toLowerCase()]=x;BY[x.slug]=BY[x.slug]||x});
$("ccl").innerHTML=T.map(function(x){return'<option value="'+esc(x.name)+'">'}).join("");
var h=location.hash.slice(1).split(",").map(decodeURIComponent).filter(Boolean);if(h.length){h.slice(0,3).forEach(function(s,i){var x=BY[s]||BY[s.toLowerCase()];$("cc"+i).value=x?x.name:s})}else{$("cc0").value="Cursor";$("cc1").value="Claude Code"}run()}).catch(function(){$("ccout").innerHTML='<p class="empty">Couldn\'t load the directory. Please refresh.</p>'});'''
    faq=[("Where does the comparison data come from?",f"From the AgentScout directory of {len(t):,} link-checked AI tools: category, pricing as each maker states it, open source, who it suits, platforms and GitHub stars from our latest repository snapshot."),
         ("Can I share the comparison?","Yes. Copy the link (the tools you picked are saved in it), copy it as text, or download a 1200×630 PNG card that fits X, LinkedIn and most social sites."),
         ("How many tools can I compare?","Two or three at a time."),
         ("Is it free?","Yes. No sign-up, and it runs in your browser.")]
    return wrap("ai-tool-comparison-card","AI tool comparison card maker","Pick two or three AI tools from the AgentScout directory and get a side-by-side comparison of pricing, open source, platforms and GitHub stars, plus a shareable image card.",inner,faq,js,t)


# ---- Oct 20 2026: AI Agent Readiness Checker. Uses the Worker's read-only GET /readiness route (owner-approved), which fetches a fixed list
# of public files on one site and returns only derived checks.
TOOLS+=[("ai-agent-readiness-checker","AI Agent Readiness Checker","Enter a website and see how ready it is for AI agents and AI search: llms.txt, robots.txt AI crawler rules, sitemap, structured data, MCP and agent files.","🛰️")]
REL["ai-agent-readiness-checker"]=(["free-mcp-servers","web-search-apis-for-ai-agents"],["founders","marketers","developers"])
def ready(t):
    inner=(f'<div {BOX}><form id="rf"><label {LAB} for="ru">Website address</label><div style="display:flex;gap:8px;flex-wrap:wrap"><input id="ru" inputmode="url" autocomplete="url" placeholder="example.com" {INP.replace("width:100%","flex:1 1 220px;min-width:0")}>'
           '<button class="btn primary" type="submit" id="rb">Check site</button></div></form><p class="muted" style="font-size:13px;margin:8px 0 0">We read only public files: the homepage, robots.txt, sitemap.xml, llms.txt and a few standard agent files. Nothing is stored.</p></div>'
           '<div id="rout" aria-live="polite"></div>'
           '<h2 style="font-size:18px;margin:28px 0 6px">What it checks</h2><p><b>llms.txt</b> (a Markdown map of your site for AI models; make one with the <a href="llms-txt-generator.html">llms.txt generator</a>), <b>robots.txt</b> rules for AI crawlers such as GPTBot, ClaudeBot, PerplexityBot and Google-Extended, a <b>sitemap</b>, <b>structured data</b> (JSON-LD), page title, description and Open Graph tags, readable text on the homepage, and machine-readable agent files: <code>/.well-known/mcp.json</code>, <code>/.well-known/agent.json</code> (A2A agent card), <code>ai-plugin.json</code> and <code>openapi.json</code>.</p>')
    js=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"free_tools_js","readiness.js")).read()
    faq=[("What is AI agent readiness?","How easily AI agents, assistants and AI search engines can find, read and use your site: whether their crawlers are allowed, whether there's an llms.txt map, a sitemap, structured data and machine-readable agent files."),
         ("How is the score worked out?","Each check has a weight (llms.txt and AI crawler access count most). The score is the share of weights your site passes. It's a quick guide, not an official standard."),
         ("Is anything stored?","No. We fetch only public files from the site you enter and keep the result in a short cache for 10 minutes. You can check up to 10 sites a minute."),
         ("Why does my site say it can't be reached?","Some sites block automated requests or take longer than 6 seconds to answer. Only public web addresses can be checked.")]
    return wrap("ai-agent-readiness-checker","AI agent readiness checker","Enter any website and see how ready it is for AI agents and AI search: llms.txt, AI crawler rules in robots.txt, sitemap, structured data, and MCP or agent files, with a score and fixes.",inner,faq,js,t)
