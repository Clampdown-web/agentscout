const { spawn } = require("child_process");
const http = require("http");
const fs = require("fs");
function get(p){return new Promise((res,rej)=>http.get(p,r=>{let d="";r.on("data",c=>d+=c);r.on("end",()=>res(d))}).on("error",rej))}
const pages=[
["home","/index.html"],
["tool","/tools/11x.html"],
["category","/categories/mcp-servers.html"],
["mcp","/mcp/index.html"],
["status","/mcp/status/"],
["connect","/mcp/connect.html"],
["best","/best/index.html"],
["tasks","/tasks/index.html"],
["compare","/compare/index.html"],
["for","/for/index.html"],
["lists","/s/index.html"],
["new","/new.html"],
["trending","/trending.html"],
["free","/free-tools.html"],
["guides","/videos/index.html"],
["news","/news.html"],
["newsletter","/newsletter.html"],
["store","/bot-store/index.html"],
["templates","/bot-templates/index.html"],
["submit","/submit.html"],
["sponsor","/sponsor.html"],
["badges","/badges.html"],
["about","/about.html"],
["privacy","/privacy.html"],
["missing","/404.html"],
];
const views=[[360,780],[390,800],[430,800],[844,390],[1024,473],[768,900],[1100,900],[1280,900]];
const expr=`(()=>{
  const vw=document.documentElement.clientWidth||innerWidth;
  function box(sel){
    const el=document.querySelector(sel); if(!el) return null;
    const r=el.getBoundingClientRect();
    if(r.width<8||r.height<8) return null;
    const left=+r.left.toFixed(1), right=+(vw-r.right).toFixed(1);
    return {left,right,d:+(left-right).toFixed(1)};
  }
  function ink(sel){
    const root=document.querySelector(sel); if(!root) return null;
    let L=1e9,R=-1e9,n=0;
    root.querySelectorAll("a,h2,h3").forEach(el=>{
      const r=el.getBoundingClientRect();
      if(r.width<2||r.height<2) return;
      L=Math.min(L,r.left); R=Math.max(R,r.right); n++;
    });
    if(!n||R<0) return null;
    const left=+L.toFixed(1), right=+(vw-R).toFixed(1);
    return {left,right,d:+(left-right).toFixed(1),n};
  }
  const blocks={};
  for (const sel of ["main.wrap","main","header.hero .wrap","footer.footcols .wrap","footer .footgrid","footer .footpop","footer .footbase",".cmpscroll",".st-counts",".home-later",".linkpile"]){
    const g=box(sel); if(g) blocks[sel]=g;
  }
  const inks={footgrid:ink("footer .footgrid"), footpop:ink("footer .footpop")};
  const pageOverflow=document.documentElement.scrollWidth-vw;
  const past=[];
  document.querySelectorAll("main,footer,.linkpile,.st-table,aside.panel,.footpop,.footgrid").forEach(el=>{
    if(el.closest(".cmpscroll")) return;
    const r=el.getBoundingClientRect();
    if(r.width<2) return;
    if(r.left<-2||r.right>vw+2) past.push(el.className&&String(el.className).slice(0,40)||el.tagName);
  });
  const hits=[];
  document.querySelectorAll(".scrollbtn.show").forEach(btn=>{
    const s=getComputedStyle(btn);
    if(parseFloat(s.opacity)<0.2||s.visibility==="hidden") return;
    const r=btn.getBoundingClientRect();
    const prev=btn.style.pointerEvents; btn.style.pointerEvents="none";
    if(btn.parentElement) btn.parentElement.style.pointerEvents="none";
    const pts=[[r.left+6,r.top+6],[r.right-6,r.bottom-6],[(r.left+r.right)/2,(r.top+r.bottom)/2]];
    for (const [x,y] of pts){
      const el=document.elementFromPoint(x,y);
      if(!el||el.closest(".scrollbtns,.as-bar")) continue;
      const host=el.closest("a,button,input,select,textarea,summary,p,h1,h2,h3,li,td,th,label,.card");
      if(host){hits.push((host.innerText||host.tagName).trim().replace(/\\s+/g," ").slice(0,50)); break;}
    }
    btn.style.pointerEvents=prev;
  });
  const row=document.querySelector(".st-table tbody tr");
  const name=document.querySelector(".st-table thead th");
  let table=null;
  if(row&&name){
    const nr=name.getBoundingClientRect(), rr=row.getBoundingClientRect();
    table={nameX:+nr.left.toFixed(1), nameW:+nr.width.toFixed(1), name:name.textContent, rowH:+rr.height.toFixed(1), tableW:+document.querySelector(".st-table").getBoundingClientRect().width.toFixed(1)};
  }
  return {vw, pageOverflow, blocks, inks, past:[...new Set(past)].slice(0,8), hits:[...new Set(hits)].slice(0,4), table, menu:!!document.querySelector("nav.sitenav.is-open")};
})()`;
(async()=>{
  const chrome=spawn("/usr/local/bin/google-chrome",["--headless=new","--disable-gpu","--no-sandbox","--remote-debugging-port=9341","--user-data-dir=/tmp/chrome-audit2","--window-size=1280,900"],{stdio:"ignore"});
  await new Promise(r=>setTimeout(r,800));
  const list=JSON.parse(await get("http://127.0.0.1:9341/json/version"));
  const ws=new WebSocket(list.webSocketDebuggerUrl);
  let id=0; const pending=new Map();
  ws.addEventListener("message",ev=>{const m=JSON.parse(ev.data); if(m.id&&pending.has(m.id)){pending.get(m.id)(m);pending.delete(m.id)}});
  const send=(method,params={},sid)=>new Promise(res=>{const i=++id; pending.set(i,res); const b={id:i,method,params}; if(sid)b.sessionId=sid; ws.send(JSON.stringify(b))});
  await new Promise(r=>ws.addEventListener("open",r,{once:true}));
  const {result:{targetId}}=await send("Target.createTarget",{url:"about:blank"});
  const {result:{sessionId}}=await send("Target.attachToTarget",{targetId,flatten:true});
  await send("Page.enable",{},sessionId);
  async function ev(e){const r=await send("Runtime.evaluate",{expression:e,returnByValue:true},sessionId); if(r.result.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails).slice(0,300)); return r.result.result.value}
  const flags=[];
  function note(page,view,where,msg){flags.push({page,view,where,msg})}
  for (const [name,path] of pages){
    for (const [w,h] of views){
      const view=w+"x"+h;
      await send("Emulation.setDeviceMetricsOverride",{width:w,height:h,deviceScaleFactor:1,mobile:w<500||h<500},sessionId);
      await send("Page.navigate",{url:"http://127.0.0.1:8765"+path},sessionId);
      await new Promise(r=>setTimeout(r,450));
      await ev(`(()=>{const b=document.querySelector('.as-bar'); if(b) b.style.display='none'; const n=document.querySelector('nav.sitenav'); if(n) n.classList.remove('is-open'); return 1})()`);
      async function check(where){
        await ev(`(()=>{dispatchEvent(new Event('scroll')); return 1})()`);
        await new Promise(r=>setTimeout(r, w<=640?260:40));
        const d=await ev(expr);
        if(d.pageOverflow>2) note(name,view,where,"hscroll "+d.pageOverflow);
        for (const [sel,g] of Object.entries(d.blocks)){
          if(Math.abs(g.d)>8) note(name,view,where,sel+" L"+g.left+" R"+g.right+" d"+g.d);
        }
        for (const [sel,g] of Object.entries(d.inks)){
          if(g && Math.abs(g.d)>8) note(name,view,where,"ink "+sel+" L"+g.left+" R"+g.right+" d"+g.d);
        }
        if(d.past.length) note(name,view,where,"past "+d.past.join(","));
        if(d.hits.length) note(name,view,where,"btn "+d.hits.join(" | "));
        if(d.table && (d.table.nameX<0 || d.table.nameX>40 && d.table.nameW<20)) note(name,view,where,"table name "+JSON.stringify(d.table));
        if(d.table && d.table.rowH>72) note(name,view,where,"rowH "+d.table.rowH);
        return d;
      }
      await check("top");
      await ev(`scrollTo(0, Math.round((document.documentElement.scrollHeight-innerHeight)*0.5))`);
      await check("mid");
      await ev(`scrollTo(0, document.documentElement.scrollHeight)`);
      await check("bottom");
      await ev(`(()=>{const n=document.querySelector('nav.sitenav'); if(n) n.classList.add('is-open'); return 1})()`);
      const open=await ev(expr);
      if(open.pageOverflow>2) note(name,view,"menu","hscroll "+open.pageOverflow);
      await ev(`(()=>{const n=document.querySelector('nav.sitenav'); if(n) n.classList.remove('is-open'); return 1})()`);
    }
    console.error("done", name, "flags", flags.length);
  }
  fs.writeFileSync("/tmp/audit-flags.json", JSON.stringify(flags,null,2));
  console.log("FLAGS", flags.length);
  const brief=flags.slice(0,80).map(f=>f.page+" "+f.view+" "+f.where+" "+f.msg);
  console.log(brief.join("\n"));
  chrome.kill("SIGKILL");
})().catch(e=>{console.error(e); process.exit(1)});
