#!/usr/bin/env python3
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'PRINT_RULES.pdf'
def text(c,x,y,s,size=9,bold=False):
    c.setFont('Helvetica-Bold' if bold else 'Helvetica',size); c.drawString(x,y,s)
def block(c,x,y,w,title,lines):
    h=24+15*len(lines); c.setStrokeColor(colors.HexColor('#d0d5dd')); c.setFillColor(colors.HexColor('#f8fafc')); c.roundRect(x,y-h,w,h,6,fill=1,stroke=1); c.setFillColor(colors.HexColor('#111827')); text(c,x+10,y-17,title,10,True); yy=y-34
    for line in lines: text(c,x+10,yy,line,7.5); yy-=15
    return y-h-10
def main():
    c=canvas.Canvas(str(OUT),pagesize=landscape(A4)); W,H=landscape(A4); m=25
    c.setFillColor(colors.HexColor('#172033')); c.roundRect(m,H-80,W-2*m,55,8,fill=1,stroke=0); c.setFillColor(colors.white); text(c,m+14,H-48,'SGLang + Ascend - Daily Workflow Rules',18,True); text(c,m+14,H-66,'Codex/OpenAI default UI; GLM optional provider; correctness gates are provider-independent.',8)
    gap=10; cw=(W-2*m-2*gap)/3; xs=[m,m+cw+gap,m+2*(cw+gap)]; top=H-95
    y=top; y=block(c,xs[0],y,cw,'SESSION',['New objective -> new session','New strategy -> new session','One editing agent per worktree']); y=block(c,xs[0],y,cw,'LARGE LOG',['>=1 MiB or >=10,000 lines','Run extract-log-context.py first','Read narrow raw ranges only if needed']);
    y=top; y=block(c,xs[1],y,cw,'PROVIDERS',['OpenAI remains default Codex config','GLM uses isolated low/high/max profiles','balanced: hard NPU/perf/kernel -> OpenAI']); y=block(c,xs[1],y,cw,'HANDOFFS',['Implementation resolves handoff first','Re-verify against current HEAD','Consume only after all items are done']);
    y=top; y=block(c,xs[2],y,cw,'ASCEND BASELINE',['hardware + CANN + torch + torch_npu','SGLang/sgl-kernel-npu commits','precision + TP/DP/EP + graph + workload']); y=block(c,xs[2],y,cw,'PERFORMANCE',['One hypothesis + one scoped change','Correctness + identical benchmark','Microbenchmark != E2E serving result']);
    c.setFillColor(colors.HexColor('#334155')); text(c,m,30,'Kernel work: sglang-ascend-kernel-dev | Long optimization: sglang-npu-perf-experiment | State: .codex-artifacts/',8,True)
    c.save(); print(OUT)
if __name__=='__main__': main()
