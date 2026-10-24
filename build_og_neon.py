"""Neon share images for /mcp/ pages (Oct 23 2026, owner request): dark background, purple/pink glow, glassy tool cards,
AgentScout logo top-left, matching the 'Fresh AI agents on AgentScout' video post. Tool and MCP server counts come from
tools.json on every build. Called from build_og.run for mcp/*.html; only the share image changes, never page colors."""
import io,os
from PIL import Image,ImageDraw,ImageFilter
W,H=1200,630
BG=(11,9,22); INK=(246,244,255); MUTED=(190,184,214); PUR=(167,139,250); PINK=(244,114,182); LINE=(120,100,190)
def _glow():
    im=Image.new("RGB",(W,H),BG); g=Image.new("RGB",(W,H),(0,0,0)); d=ImageDraw.Draw(g)
    for (cx,cy,r,col) in ((180,560,520,(110,40,220)),(1080,80,480,(200,40,150)),(760,640,380,(80,30,170))):
        d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=col)
    g=g.filter(ImageFilter.GaussianBlur(170))
    return Image.blend(im,g,0.55)
def _grad_text(im,xy,text,font):
    d=ImageDraw.Draw(im); w=int(d.textlength(text,font=font))+4; b=font.getbbox(text); h=b[3]+8
    m=Image.new("L",(w,h),0); ImageDraw.Draw(m).text((0,0),text,font=font,fill=255)
    grad=Image.new("RGB",(w,h)); gd=ImageDraw.Draw(grad)
    for i in range(w):
        t=i/max(1,w-1); gd.line([(i,0),(i,h)],fill=tuple(int(PUR[k]+(PINK[k]-PUR[k])*t) for k in range(3)))
    im.paste(grad,xy,m)
def _glass(im,box,r=22,hi=False):
    x0,y0,x1,y1=box; ov=Image.new("RGBA",im.size,(0,0,0,0)); d=ImageDraw.Draw(ov)
    if hi:
        gl=Image.new("RGBA",im.size,(0,0,0,0)); ImageDraw.Draw(gl).rounded_rectangle([x0-4,y0-4,x1+4,y1+4],radius=r+4,outline=(236,72,200,200),width=6)
        ov.alpha_composite(gl.filter(ImageFilter.GaussianBlur(9)))
    d.rounded_rectangle(box,radius=r,fill=(255,255,255,22),outline=(200,180,255,90) if not hi else (244,114,182,200),width=2)
    d.line([x0+r,y0+1,x1-r,y0+1],fill=(255,255,255,70),width=1)
    base=im.convert("RGBA"); base.alpha_composite(ov); return base.convert("RGB")
def render(F,wrap,label,title,sub,cards,foot,accent=None):
    im=_glow(); d=ImageDraw.Draw(im)
    x,y,s=64,46,1.5  # logo (logo-wordmark.svg shape) top-left, in neon
    im=_glass(im,[x-10,y-8,x+290,y+52],r=16); d=ImageDraw.Draw(im)
    d.ellipse([x+4.5*s,y+4.5*s,x+22.5*s,y+22.5*s],outline=INK,width=round(3*s))
    d.line([x+20.3*s,y+20.3*s,x+28*s,y+28*s],fill=INK,width=round(3.2*s))
    cx,cy,a,b=x+13.5*s,y+13.5*s,5.3*s,1.2*s
    d.polygon([(cx,cy-a),(cx+b,cy-b),(cx+a,cy),(cx+b,cy+b),(cx,cy+a),(cx-b,cy+b),(cx-a,cy),(cx-b,cy-b)],fill=PINK)
    f=F(32,650); d.text((x+40*s,y+23.5*s),"Agent",font=f,fill=INK,anchor="ls"); _grad_text(im,(int(x+40*s+d.textlength("Agent",font=f)),int(y+23.5*s-f.getbbox("Scout")[3]+ (f.getbbox("Scout")[3]-f.getbbox("Scout")[1])*0)) ,"Scout",f)
    d=ImageDraw.Draw(im); pf=F(21,650); pw=d.textlength(label.upper(),font=pf)+40
    d.rounded_rectangle([W-64-pw,52,W-64,96],radius=22,fill=(60,30,110),outline=PINK,width=2); d.text((W-64-pw/2,74),label.upper(),font=pf,fill=INK,anchor="mm")
    # title, with the accent word in a purple-pink gradient
    for size,ml in ((64,2),(56,2),(50,2)):
        tf=F(size,750); lines=wrap(d,title,tf,W-128,ml)
        if not lines[-1].endswith("…"): break
    ty=136; lh=int(size*1.12)
    for l in lines:
        if accent and accent in l:
            pre,post=l.split(accent,1); cx=64
            d.text((cx,ty),pre,font=tf,fill=INK); cx+=d.textlength(pre,font=tf)
            _grad_text(im,(int(cx),ty),accent,tf); d=ImageDraw.Draw(im); cx+=d.textlength(accent,font=tf)
            d.text((cx,ty),post,font=tf,fill=INK)
        else: d.text((64,ty),l,font=tf,fill=INK)
        ty+=lh
    if sub:
        sf=F(27,450)
        for l in wrap(d,sub,sf,W-128,1): d.text((64,ty+6),l,font=sf,fill=MUTED); ty+=38
    # glassy cards
    n=len(cards); gap=22; cw=(W-128-gap*(n-1))//n; cy0=max(ty+30,350); ch=150
    for i,c in enumerate(cards):
        bx=64+i*(cw+gap); im=_glass(im,[bx,cy0,bx+cw,cy0+ch],hi=(i==0)); d=ImageDraw.Draw(im); tx=bx+24
        if c.get("logo") and os.path.exists(c["logo"]):
            try:
                L=Image.open(c["logo"]).convert("RGBA"); L.thumbnail((52,52),Image.LANCZOS)
                t=Image.new("RGBA",(60,60),(255,255,255,255)); t.alpha_composite(L,((60-L.width)//2,(60-L.height)//2))
                m=Image.new("L",(60,60),0); ImageDraw.Draw(m).rounded_rectangle([0,0,59,59],radius=14,fill=255); im.paste(t.convert("RGB"),(bx+22,cy0+22),m); d=ImageDraw.Draw(im); tx=bx+22+60+16
            except Exception: pass
        name=c["name"]; sz=c.get("size",30)
        while sz>22 and d.textlength(name,font=F(sz,700))>bx+cw-20-tx: sz-=2
        nf=F(sz,700)
        while d.textlength(name,font=nf)>bx+cw-20-tx and len(name)>4: name=name[:-2].rstrip()+"…" if not name.endswith("…") else name[:-2]+"…"
        d.text((tx,cy0+50),name,font=nf,fill=INK,anchor="lm")
        tg=F(19,650); tw=d.textlength(c["tag"],font=tg)+24
        d.rounded_rectangle([bx+22,cy0+96,bx+22+tw,cy0+128],radius=16,fill=(70,35,120),outline=PUR,width=1); d.text((bx+22+tw/2,cy0+112),c["tag"],font=tg,fill=(232,220,255),anchor="mm")
    ff=F(24,650); d.text((64,H-34),"agentscouthq.com",font=ff,fill=INK,anchor="ls")
    d.text((64+d.textlength("agentscouthq.com",font=ff)+18,H-34),foot,font=F(22,450),fill=MUTED,anchor="ls")
    im=im.quantize(colors=200,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.FLOYDSTEINBERG)
    b=io.BytesIO(); im.save(b,"PNG",optimize=True); return b.getvalue()
