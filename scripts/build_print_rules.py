#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Paragraph
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "PRINT_RULES.pdf"

PAGE_W, PAGE_H = landscape(A4)
M = 24
G = 10
HEADER_H = 62
FOOTER_H = 28
COL_W = (PAGE_W - 2 * M - 2 * G) / 3
BODY_TOP = PAGE_H - M - HEADER_H
BODY_BOTTOM = M + FOOTER_H

NAVY = colors.HexColor("#162033")
BLUE = colors.HexColor("#EAF2FF")
GREEN = colors.HexColor("#EAF8EF")
AMBER = colors.HexColor("#FFF6DD")
RED = colors.HexColor("#FDECEC")
GRAY = colors.HexColor("#F3F4F6")
BORDER = colors.HexColor("#D5D9E2")
TEXT = colors.HexColor("#20242C")
MUTED = colors.HexColor("#596273")

styles = {
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=20, leading=22, textColor=colors.white),
    "subtitle": ParagraphStyle("subtitle", fontName="Helvetica", fontSize=8.5, leading=10.5, textColor=colors.HexColor("#DCE6F7")),
    "card_title": ParagraphStyle("card_title", fontName="Helvetica-Bold", fontSize=10.2, leading=12, textColor=NAVY, spaceAfter=4),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=7.4, leading=9.2, textColor=TEXT),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=6.8, leading=8.4, textColor=MUTED),
    "footer": ParagraphStyle("footer", fontName="Helvetica-Bold", fontSize=7.2, leading=9, textColor=NAVY, alignment=TA_LEFT),
}


def draw_para(c: canvas.Canvas, text: str, style: ParagraphStyle, x: float, y_top: float, w: float) -> float:
    p = Paragraph(text, style)
    _, h = p.wrap(w, 1000)
    p.drawOn(c, x, y_top - h)
    return h


def card(c: canvas.Canvas, x: float, y_top: float, h: float, title: str, body: str, fill) -> None:
    c.setFillColor(fill)
    c.setStrokeColor(BORDER)
    c.roundRect(x, y_top - h, COL_W, h, 7, fill=1, stroke=1)
    pad = 10
    used = draw_para(c, title, styles["card_title"], x + pad, y_top - pad, COL_W - 2 * pad)
    draw_para(c, body, styles["body"], x + pad, y_top - pad - used - 3, COL_W - 2 * pad)


def main() -> None:
    c = canvas.Canvas(str(OUT), pagesize=landscape(A4))
    c.setTitle("Codex + SGLang / Ascend Daily Rules")

    c.setFillColor(NAVY)
    c.roundRect(M, PAGE_H - M - HEADER_H, PAGE_W - 2 * M, HEADER_H, 9, fill=1, stroke=0)
    draw_para(c, "CODEX + SGLANG / ASCEND - Daily Rules", styles["title"], M + 16, PAGE_H - M - 13, PAGE_W - 2 * M - 32)
    draw_para(c, "Default: open ~/code/sglang with VS Code in WSL and use the Codex sidebar. Repo rules/skills handle the workflow.", styles["subtitle"], M + 16, PAGE_H - M - 39, PAGE_W - 2 * M - 32)

    xs = [M, M + COL_W + G, M + 2 * (COL_W + G)]

    # Column 1
    y = BODY_TOP
    card(c, xs[0], y, 122, "START HERE - 4 QUESTIONS",
         "<b>1. New objective?</b> -> new session.<br/>"
         "<b>2. Review found actionable local issues?</b> -> handoff before STOP, then new implementation session.<br/>"
         "<b>3. Large local/downloaded log?</b> -> reducer before any full raw-log read.<br/>"
         "<b>4. Just Git plumbing?</b> push/status/fetch/switch -> terminal.", BLUE)
    y -= 132
    card(c, xs[0], y, 150, "LARGE LOG - MUST REDUCE FIRST",
         "Trigger: <b>&gt;= 1 MiB OR &gt;= 10,000 lines</b>.<br/><br/>"
         "size check -> <font name='Courier'>extract-log-context.py</font> -> <font name='Courier'>.codex/logs/*.focused.txt</font> -> inspect focused artifact -> narrow raw ranges only if needed.<br/><br/>"
         "<b>Never read/cat the whole raw log first.</b> You do not need to tell Codex to use the reducer.", RED)
    y -= 160
    card(c, xs[0], y, 120, "SEARCH ROUTING",
         "Exact symbol/error/path -> <b>rg</b>.<br/>Known PR/commit -> <b>git show/diff</b>.<br/>Model history -> <b>model-pr-history</b>.<br/>Unknown concept -> <b>Semble</b>.<br/>Known symbol relations -> <b>Serena</b> (optional).<br/><br/>Once a symbol is found, stop broad semantic discovery.", GRAY)

    # Column 2
    y = BODY_TOP
    card(c, xs[1], y, 166, "REVIEW -> HANDOFF -> NEW SESSION",
         "If report-only review/investigation finds actionable issues and GitHub review threads are not already authoritative:<br/><br/>"
         "review -> <font name='Courier'>.codex/handoffs/...</font> -> STOP -> new implementation session -> re-verify -> patch.<br/><br/>"
         "Implementation <b>does not redo the broad review</b>.<br/><br/>"
         "Handoff only stores: severity | file/symbol | root cause | intended change | constraints | validation.", GREEN)
    y -= 176
    card(c, xs[1], y, 130, "SESSION + MODEL ROUTING",
         "<b>Luna/low:</b> metadata, PR description, docs, mechanical.<br/>"
         "<b>Terra/medium:</b> default development, conflicts, comments, normal bugs/refactors.<br/>"
         "<b>Sol/high:</b> deep review, hard Ascend correctness, HCCL/NPUGraph/perf root cause.<br/>"
         "<b>Sol/xhigh:</b> escalation only.<br/><br/>"
         "Long perf/kernel loop -> <font name='Courier'>/plan</font> + <font name='Courier'>/goal</font> + artifact ledger.", BLUE)
    y -= 140
    card(c, xs[1], y, 96, "DO NOT SPEND A MODEL TURN",
         "Standalone push/status/fetch/switch -> terminal.<br/>Do not send <font name='Courier'>push</font>, <font name='Courier'>continue</font>, or <font name='Courier'>update</font> in a long thread.<br/>Do not expand scope after the objective is solved.", AMBER)

    # Column 3
    y = BODY_TOP
    card(c, xs[2], y, 168, "ASCEND / NPU HARD GATES",
         "Record before version-sensitive diagnosis/benchmark:<br/><br/>"
         "hardware | CANN | torch | torch_npu | sgl-kernel-npu | SGLang commit | graph/eager | dtype/quant | TP/DP/EP | workload | actual backend.<br/><br/>"
         "<b>STOP</b> if baseline/candidate differ by unrelated variables or a silent fallback changes backend.<br/><br/>"
         "CUDA/NCCL/graph/stream assumptions are not automatically valid for Ascend/HCCL/NPUGraph.", RED)
    y -= 178
    card(c, xs[2], y, 118, "STOP RULES",
         "Before ending: objective complete? diff minimal? validation sufficient? handoff/Goal updated if needed?<br/><br/>"
         "No unrelated cleanup/docs/tests/refactors after the objective is solved.<br/><br/>"
         "Tests only when explicitly requested, required by review/CI, or needed as a real regression guard.", GREEN)
    y -= 128
    card(c, xs[2], y, 108, "DAILY UI / QUICK COMMANDS",
         "<b>Default:</b> <font name='Courier'>cd ~/code/sglang &amp;&amp; code .</font> -> WSL: Ubuntu -> Codex sidebar.<br/><br/>"
         "<b>CLI optional:</b> <font name='Courier'>cxl</font> Luna | <font name='Courier'>cx</font> Terra | <font name='Courier'>cxh</font> Sol/high | <font name='Courier'>cxx</font> Sol/xhigh<br/><br/>"
         "Handoff: <font name='Courier'>.codex/scripts/new-handoff.sh &lt;PR|slug&gt;</font>", GRAY)

    c.setStrokeColor(BORDER)
    c.line(M, M + FOOTER_H - 5, PAGE_W - M, M + FOOTER_H - 5)
    draw_para(c, "Chat = working memory. Git = code state. Handoff/Goal files = durable memory. NEW OBJECTIVE = NEW SESSION.", styles["footer"], M, M + 17, PAGE_W - 2 * M)

    c.save()
    print(OUT)


if __name__ == "__main__":
    main()
