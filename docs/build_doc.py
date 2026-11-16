"""Builds the Anatomy Atlas project documentation PDF (A4) with ReportLab."""
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle,
                                Image, PageBreak, KeepTogether, NextPageTemplate, CondPageBreak)
from reportlab.platypus.tableofcontents import TableOfContents

import os
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Anatomy_Atlas_Project_Documentation.pdf")
IMG = os.path.join(HERE, "img") + "/"
INK = colors.HexColor("#1d1f22")
INK2 = colors.HexColor("#4f545c")
INK3 = colors.HexColor("#8b8f97")
RULE = colors.HexColor("#dcd8ce")
ACCENT = colors.HexColor("#1f5fc8")
ACCENT_SOFT = colors.HexColor("#e8effb")
PAPER = colors.HexColor("#f6f4ef")
WARN = colors.HexColor("#9a5b00")
OK = colors.HexColor("#17733f")
W, H = A4
MARGIN = 20 * mm
TEXT_W = W - 2 * MARGIN

# ------------------------------------------------------------------ styles
base = dict(fontName="Helvetica", textColor=INK, leading=14.2, fontSize=10)
S = {
    "body": ParagraphStyle("body", **base, spaceAfter=6),
    "small": ParagraphStyle("small", **{**base, "fontSize": 8.5, "leading": 11.5, "textColor": INK2}),
    "cell": ParagraphStyle("cell", **{**base, "fontSize": 8.8, "leading": 11.6}),
    "cellb": ParagraphStyle("cellb", **{**base, "fontSize": 8.8, "leading": 11.6, "fontName": "Helvetica-Bold"}),
    "cellh": ParagraphStyle("cellh", **{**base, "fontSize": 8.6, "leading": 11, "fontName": "Helvetica-Bold",
                                        "textColor": colors.white}),
    "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=INK, spaceBefore=4,
                         spaceAfter=10),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=12.2, leading=16, textColor=INK, spaceBefore=12,
                         spaceAfter=5),
    "h3": ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=10.2, leading=14, textColor=INK2, spaceBefore=8,
                         spaceAfter=3),
    "bullet": ParagraphStyle("bullet", **base, leftIndent=12, bulletIndent=2, spaceAfter=2.5),
    "caption": ParagraphStyle("caption", **{**base, "fontSize": 8.3, "leading": 10.5, "textColor": INK2},
                              spaceBefore=2, spaceAfter=8),
    "code": ParagraphStyle("code", fontName="Courier", fontSize=8.2, leading=10.6, textColor=INK, leftIndent=6,
                           backColor=PAPER, borderPadding=(5, 6, 5, 6), spaceBefore=4, spaceAfter=8),
    "toc1": ParagraphStyle("toc1", fontName="Helvetica", fontSize=10.5, leading=17, textColor=INK),
    "toc2": ParagraphStyle("toc2", fontName="Helvetica", fontSize=9.4, leading=14, leftIndent=14, textColor=INK2),
    "_": None,
    "lead": ParagraphStyle("lead", **{**base, "fontSize": 10.8, "leading": 15.5}, spaceAfter=8),
}
S.pop("_")
for k in ("h1", "h2", "h3"):
    S[k].keepWithNext = 1


def P(t, s="body"):
    return Paragraph(t, S[s])


def bullets(items, style="bullet"):
    return [Paragraph(i, S[style], bulletText="\u2022") for i in items]


def table(rows, widths, header=True, zebra=True, bold_first=False):
    data = []
    for r_i, r in enumerate(rows):
        cells = []
        for c_i, c in enumerate(r):
            if isinstance(c, str):
                st = "cellh" if (header and r_i == 0) else ("cellb" if (bold_first and c_i == 0) else "cell")
                cells.append(Paragraph(c, S[st]))
            else:
                cells.append(c)
        data.append(cells)
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
          ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
          ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE)]
    if header:
        st += [("BACKGROUND", (0, 0), (-1, 0), INK)]
    if zebra:
        for i in range(1 if header else 0, len(rows)):
            if i % 2 == 0:
                st.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#faf9f6")))
    t.setStyle(TableStyle(st))
    t.spaceBefore, t.spaceAfter = 2, 9
    return t


def figure(path, caption, width=TEXT_W):
    img = Image(path, width=width, height=width * 750 / 1200)
    return KeepTogether([img, P(caption, "caption")])


def fig_pair(a, b, ca, cb):
    w = (TEXT_W - 6 * mm) / 2
    t = Table([[Image(IMG + a, width=w, height=w * 0.625), Image(IMG + b, width=w, height=w * 0.625)],
               [P(ca, "caption"), P(cb, "caption")]], colWidths=[w + 3 * mm, w + 3 * mm])
    t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                           ("TOPPADDING", (0, 0), (-1, -1), 0), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t


# ------------------------------------------------------------------ diagrams
def box(d, x, y, w, h, title, lines, accent=False):
    d.add(Rect(x, y, w, h, rx=5, ry=5, fillColor=ACCENT_SOFT if accent else colors.white,
               strokeColor=ACCENT if accent else INK3, strokeWidth=1.4 if accent else 0.8))
    d.add(String(x + 7, y + h - 14, title, fontName="Helvetica-Bold", fontSize=8.6, fillColor=INK))
    for i, l in enumerate(lines):
        d.add(String(x + 7, y + h - 27 - i * 10.5, l, fontName="Helvetica", fontSize=7.4, fillColor=INK2))


def arrow(d, x1, y1, x2, y2):
    d.add(Line(x1, y1, x2, y2, strokeColor=INK3, strokeWidth=0.9))
    import math
    a = math.atan2(y2 - y1, x2 - x1)
    s = 5
    d.add(Polygon([x2, y2, x2 - s * math.cos(a - 0.45), y2 - s * math.sin(a - 0.45),
                   x2 - s * math.cos(a + 0.45), y2 - s * math.sin(a + 0.45)], fillColor=INK3, strokeColor=INK3))


def architecture():
    d = Drawing(TEXT_W, 250)
    bw, bh = 108, 70
    xs = [0, 120.5, 241, 361.5]
    y1 = 165
    box(d, xs[0], y1, bw, bh, "Z-Anatomy .blend", ["~290 MB, whole body", "BodyParts3D meshes", "Wikipedia text", "TA2 Latin table"])
    box(d, xs[1], y1, bw, bh, "export.py (bpy)", ["pip bpy, Python 3.11", "classify tissue, depth", "assign region", "one node per structure"], accent=True)
    box(d, xs[2], y1, bw, bh, "compress.sh", ["gltf-transform", "Draco compression", "weld + simplify", "keeps nodes separate"])
    box(d, xs[3], y1, bw + 12, bh, "Region bundles", ["10 x <region>.glb (18.5 MB)", "10 x content.json (3.9 MB)", "metadata.json (1.3 MB)", "manifest.json"])
    for i in range(3):
        arrow(d, xs[i] + bw, y1 + bh / 2, xs[i + 1] - 2, y1 + bh / 2)
    box(d, xs[1], 70, bw, 58, "depth_tags.csv", ["per-structure layer", "overrides, both sides", "reviewed by faculty"])
    arrow(d, xs[1] + bw / 2, 128, xs[1] + bw / 2, y1 - 2)
    y2 = 40
    box(d, xs[2], y2, bw, 88, "Web viewer (web/)", ["Vite + React + TS", "React Three Fiber", "Zustand state", "loads regions in turn", "renders on demand"], accent=True)
    box(d, xs[3], y2, bw + 12, 88, "GitHub Pages", ["Actions build on push", "public static site", "no login needed", "nalla-perumal-aayush", ".github.io/anatomy-atlas"])
    arrow(d, xs[3] + (bw + 12) / 2, y1, xs[2] + bw - 10, y2 + 88 + 2)
    arrow(d, xs[2] + bw, y2 + 44, xs[3] - 2, y2 + 44)
    d.add(String(xs[3] + 4, y1 - 13, "copied into web/public", fontName="Helvetica", fontSize=7, fillColor=INK3))
    d.add(String(0, 12, "No Blender application is installed or opened at any step.", fontName="Helvetica-Oblique",
                 fontSize=7.6, fillColor=INK2))
    return d


def roadmap():
    d = Drawing(TEXT_W, 150)
    phases = [("Phase 1-2", "Baseline", "Done", "Upper limb, then\nwhole body, deployed"),
              ("Phase 3", "Feedback setup", "Next", "Forms, logging,\ntester guide"),
              ("Phase 4", "Pilot round 1", "Planned", "15 students, 2 faculty,\nneurosurgeon"),
              ("Phase 5", "Fix and review", "Planned", "Weekly releases,\nreviewed badges"),
              ("Phase 6", "Next level", "Later", "Quizzes, AI tutor,\nmobile, by feedback")]
    n = len(phases)
    gap = 6
    w = (TEXT_W - gap * (n - 1)) / n
    y = 50
    for i, (ph, name, status, desc) in enumerate(phases):
        x = i * (w + gap)
        done = status == "Done"
        nxt = status == "Next"
        fill = colors.HexColor("#e3f1e8") if done else (ACCENT_SOFT if nxt else colors.white)
        stroke = OK if done else (ACCENT if nxt else INK3)
        d.add(Rect(x, y, w, 72, rx=5, ry=5, fillColor=fill, strokeColor=stroke, strokeWidth=1.2))
        d.add(String(x + 7, y + 58, ph, fontName="Helvetica", fontSize=7.4, fillColor=INK2))
        d.add(String(x + 7, y + 45, name, fontName="Helvetica-Bold", fontSize=8.8, fillColor=INK))
        for j, l in enumerate(desc.split("\n")):
            d.add(String(x + 7, y + 30 - j * 10, l, fontName="Helvetica", fontSize=7.3, fillColor=INK2))
        d.add(String(x + 7, y - 14, status, fontName="Helvetica-Bold", fontSize=8, fillColor=stroke))
        if i < n - 1:
            arrow(d, x + w, y + 36, x + w + gap - 1, y + 36)
    d.add(Line(0, 22, TEXT_W, 22, strokeColor=RULE, strokeWidth=0.6))
    d.add(String(0, 8, "Gate between phases: the previous phase's exit check is met (see section 8). Dates are not fixed.",
                 fontName="Helvetica-Oblique", fontSize=7.6, fillColor=INK2))
    return d


# ------------------------------------------------------------------ page templates
class Doc(BaseDocTemplate):
    def afterFlowable(self, f):
        if isinstance(f, Paragraph) and f.style.name in ("h1", "h2"):
            text = f.getPlainText()
            level = 0 if f.style.name == "h1" else 1
            key = "h%d" % id(f)
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=level, closed=False)
            self.notify("TOCEntry", (level, text, self.page, key))


def on_cover(c, d):
    c.saveState()
    c.setFillColor(INK)
    c.rect(0, H - 118 * mm, W, 118 * mm, stroke=0, fill=1)
    c.setFillColor(colors.HexColor("#9fb7e6"))
    c.setFont("Helvetica", 10)
    c.drawString(MARGIN, H - 38 * mm, "PROJECT DOCUMENTATION")
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 34)
    c.drawString(MARGIN, H - 58 * mm, "Anatomy Atlas")
    c.setFont("Helvetica", 15)
    c.drawString(MARGIN, H - 70 * mm, "A web-based 3D anatomy atlas for first-year medical students")
    c.setFont("Helvetica", 10.5)
    c.setFillColor(colors.HexColor("#c9d3e6"))
    c.drawString(MARGIN, H - 86 * mm, "Baseline release: whole body, 3,153 structures, 10 regions, 7 depth layers")
    c.drawString(MARGIN, H - 93 * mm, "Status: live on GitHub Pages, ready for a closed pilot")
    # details block
    y = H - 140 * mm
    rows = [("Author", "Nalla Perumal Aayush C"),
            ("Affiliation", "B.Tech Robotics and Artificial Intelligence, School of Electrical and Electronics Engineering, SASTRA Deemed to be University"),
            ("Document version", "1.0, 16 November 2026"),
            ("Live site", "https://nalla-perumal-aayush.github.io/anatomy-atlas/"),
            ("Source code", "https://github.com/Nalla-Perumal-Aayush/anatomy-atlas"),
            ("Licence", "Models and text: CC BY-SA 4.0 (derived from Z-Anatomy and BodyParts3D)")]
    for k, v in rows:
        c.setFillColor(INK3)
        c.setFont("Helvetica", 8.5)
        c.drawString(MARGIN, y, k.upper())
        c.setFillColor(INK)
        c.setFont("Helvetica", 10.5)
        words, line, lines = v.split(), "", []
        for w_ in words:
            if c.stringWidth(line + " " + w_, "Helvetica", 10.5) > TEXT_W - 45 * mm:
                lines.append(line)
                line = w_
            else:
                line = (line + " " + w_).strip()
        lines.append(line)
        for i, l in enumerate(lines):
            c.drawString(MARGIN + 45 * mm, y - i * 13, l)
        y -= 13 * len(lines) + 9
    try:
        c.drawImage(IMG + "cover.jpg", MARGIN, 18 * mm, width=TEXT_W, height=TEXT_W * 0.42,
                    preserveAspectRatio=True, anchor="c", mask=None)
    except Exception:
        pass
    c.restoreState()


def on_page(c, d):
    c.saveState()
    c.setStrokeColor(RULE)
    c.setLineWidth(0.5)
    c.line(MARGIN, H - 13 * mm, W - MARGIN, H - 13 * mm)
    c.setFont("Helvetica", 7.8)
    c.setFillColor(INK3)
    c.drawString(MARGIN, H - 11 * mm, "Anatomy Atlas: project documentation v1.1")
    c.drawRightString(W - MARGIN, H - 11 * mm, "16 November 2026")
    c.line(MARGIN, 13 * mm, W - MARGIN, 13 * mm)
    c.drawString(MARGIN, 9 * mm, "github.com/Nalla-Perumal-Aayush/anatomy-atlas")
    c.drawRightString(W - MARGIN, 9 * mm, "Page %d" % d.page)
    c.restoreState()


doc = Doc(OUT, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=20 * mm, bottomMargin=19 * mm,
          title="Anatomy Atlas: Project Documentation", author="Nalla Perumal Aayush C",
          subject="Baseline release documentation", creator="Anatomy Atlas project")
frame = Frame(MARGIN, 19 * mm, TEXT_W, H - 39 * mm, id="f", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
doc.addPageTemplates([PageTemplate("cover", [Frame(0, 0, W, H, id="c")], onPage=on_cover),
                      PageTemplate("body", [frame], onPage=on_page)])

story = [NextPageTemplate("body"), PageBreak()]

# ------------------------------------------------------------------ contents
story.append(Paragraph("Contents", ParagraphStyle("ctitle", parent=S["h1"])))
toc = TableOfContents()
toc.levelStyles = [S["toc1"], S["toc2"]]
toc.dotsMinLevel = 0
story += [toc, PageBreak()]

# ------------------------------------------------------------------ 1 summary
story.append(P("1. Summary", "h1"))
story.append(P("Anatomy Atlas is a free 3D anatomy atlas that runs in the web browser. A first-year medical student can "
               "peel the human body layer by layer, from skin down to bone, click any structure, and read its name, "
               "Latin term, nerve supply and description. The baseline covers the whole body and is live on GitHub "
               "Pages, where anyone with the link can open it without an account.", "lead"))
story.append(P("The work so far took the project from an idea to a deployed baseline in two build phases: first the "
               "right upper limb as a proof of concept, then the whole body. The next phase is to collect structured "
               "feedback from students and faculty, correct the content, and only then decide which larger features to "
               "build."))
story.append(P("Baseline at a glance", "h3"))
story.append(table([
    ["Item", "Value"],
    ["Structures", "3,153 (1,348 right, 1,347 left, 458 midline)"],
    ["Regions", "10: thorax, abdomen, pelvis and perineum, neck, head, both upper limbs, both lower limbs, brain and spinal cord"],
    ["Depth layers", "7: skin, superficial fascia, deep fascia, superficial muscles, deep muscles, nerves and vessels, bones/organs/brain"],
    ["Descriptions", "2,816 structures (89%), 386 of them borrowed from the parent structure"],
    ["Latin names", "2,840 structures (90%)"],
    ["Nerve supply", "278 of 513 muscles (54%)"],
    ["Download size", "18.5 MB models + 3.9 MB text + 1.3 MB metadata, loaded region by region"],
    ["Hosting", "GitHub Pages, auto-deployed on every push to main"],
    ["Content review", "Not yet reviewed by faculty; every panel shows a \"Not yet reviewed\" badge"],
], [38 * mm, TEXT_W - 38 * mm], bold_first=True))
story.append(Spacer(1, 6))
story.append(P("What is done, what is next, what comes later", "h3"))
story.append(table([
    ["Done", "Next (section 8)", "Later (section 9)"],
    ["Whole-body export pipeline without the Blender app<br/>3D viewer with peeling, search and info panels<br/>"
     "Public deployment on GitHub Pages<br/>Headless browser testing of all main features",
     "Feedback form wired (done)<br/>Failed-search logging<br/>Tester guide and task sheet<br/>Closed pilot with students, "
     "faculty and a neurosurgeon<br/>Faculty review of layers and text",
     "Quizzes and self-test mode<br/>AI tutor over reviewed content<br/>Mobile app or offline PWA<br/>Cross-sections, "
     "pins and annotations"],
], [TEXT_W / 3] * 3, zebra=False))
story.append(PageBreak())

# ------------------------------------------------------------------ 2 background
story.append(P("2. Background and goals", "h1"))
story.append(P("First-year MBBS students learn anatomy mainly from textbooks and limited time at the dissection table. "
               "Commercial 3D atlases exist, such as Anatomy 3D Atlas, which was the reference for this project, but "
               "most lock the full body behind a payment. The aim here is a free, web-based atlas that matches how "
               "dissection proceeds: from the surface inwards."))
story.append(P("Goals for the baseline", "h2"))
story += bullets([
    "Let a student remove the body layer by layer and see what lies beneath, for any region.",
    "Make every structure clickable, with its name, Latin term, layer and a description.",
    "Run in an ordinary browser on a laptop or phone, with nothing to install and no login.",
    "Use openly licensed anatomical data so the project can be shared and built on.",
    "Keep the pipeline reproducible so corrections from reviewers can be applied and redeployed quickly.",
])
story.append(P("Constraints", "h2"))
story += bullets([
    "Solo, personal project with no fixed timeline; progress is gated by milestones.",
    "Web first. A mobile app or other platforms will be decided after the web version is tested.",
    "The developer has no Blender experience, so the 3D data pipeline must run as plain Python scripts.",
    "Content must be checked by medical college students, anatomy professors and a neurosurgeon before wider release.",
])
story.append(P("Intended users", "h2"))
story.append(table([
    ["User", "What they need from the atlas"],
    ["First-year medical students", "Revise structures before and after dissection; find a structure by name; see its layer and relations"],
    ["Anatomy faculty", "Check correctness; use it to demonstrate layers in class; flag errors quickly"],
    ["Clinical reviewers (neurosurgeon)", "Check nervous system detail, which is the weakest part of the open data"],
], [50 * mm, TEXT_W - 50 * mm], bold_first=True))
story.append(PageBreak())

# ------------------------------------------------------------------ 3 what has been built
story.append(P("3. What has been built", "h1"))
story.append(P("3.1 Features of the baseline viewer", "h2"))
story.append(table([
    ["Feature", "How it works"],
    ["Layer peeling", "Seven depth layers. Choosing a layer hides everything above it. An optional \"Ghost peeled\" mode keeps removed layers visible as faint outlines."],
    ["Regions", "Ten region bundles load one after another (thorax first, brain last). Each can be shown, hidden or viewed alone with \"Only\"."],
    ["Systems", "Six toggles: skin; muscles and fascia; nerves, brain and spinal cord; heart, vessels and lymph nodes; organs and sense organs; bones and joints."],
    ["Selection and info panel", "Click a structure to highlight it in blue. The panel shows name, Latin term, tissue, layer, region and side, nerve supply for muscles, the groups it belongs to, and its description with a link to the source."],
    ["Search", "Matches English and Latin names. Picking a result switches on its region and system, peels to its layer, ghosts the layers above, and turns the camera to the side the structure lies on."],
    ["Group search", "Z-Anatomy groups (for example Heart, 17 parts) can be isolated as a set. Nerve groups that hold the muscles a nerve supplies are labelled \"Muscles supplied by\" so they are not mistaken for the nerve."],
    ["Structure actions", "Hide, isolate, ghost and zoom to, with a list of hidden structures and a show-all reset. Keyboard: Esc deselects, H hides."],
    ["Views", "Anterior, posterior, lateral and medial presets, plus free orbit, pan and zoom."],
    ["Error reporting", "A \"Report an error\" button on every structure opens the project's Google Form with the structure and its layer filled in; responses collect in a Google Sheet. A \"Send feedback\" link opens the same form blank."],
    ["Credits and status", "An About panel with full licence credits. Every description carries a \"Not yet reviewed\" badge until faculty sign it off."],
], [36 * mm, TEXT_W - 36 * mm], bold_first=True))

story.append(P("3.2 Coverage by region", "h2"))
story.append(table([
    ["Region", "Structures", "Model size", "Text size"],
    ["Thorax", "426", "3.43 MB", "0.42 MB"], ["Abdomen", "225", "2.14 MB", "0.29 MB"],
    ["Pelvis and perineum", "189", "0.73 MB", "0.17 MB"], ["Neck", "208", "1.29 MB", "0.23 MB"],
    ["Head", "618", "3.46 MB", "0.63 MB"], ["Right upper limb", "278", "1.15 MB", "0.44 MB"],
    ["Left upper limb", "279", "1.14 MB", "0.44 MB"], ["Right lower limb", "347", "1.63 MB", "0.52 MB"],
    ["Left lower limb", "347", "1.63 MB", "0.52 MB"], ["Brain and spinal cord", "236", "1.93 MB", "0.28 MB"],
    ["<b>Total</b>", "<b>3,153</b>", "<b>18.53 MB</b>", "<b>3.94 MB</b>"],
], [60 * mm, 35 * mm, 35 * mm, TEXT_W - 130 * mm]))

layers_block = [P("3.3 The seven depth layers", "h2"), P("Layers 1 to 6 peel the same way everywhere. Layer 7 holds bones, organs and the brain together, because "
               "in the trunk the organs sit inside the ribcage. To see the organs, the student peels to layer 7 and "
               "switches off Bones and joints."), table([
    ["Layer", "Contents", "Structures"],
    ["1. Skin", "Skin regions of the whole body", "242"],
    ["2. Superficial fascia", "Cutaneous nerves, superficial veins, superficial lymph nodes", "112"],
    ["3. Deep fascia", "Deep fascia, retinacula, aponeuroses", "60"],
    ["4. Superficial muscles", "Facial muscles, platysma, trapezius, pectoralis major, superficial limb muscles", "162"],
    ["5. Deep muscles", "Deeper muscle layers, bursae, tendon sheaths", "461"],
    ["6. Nerves and vessels", "Named nerves, arteries, veins, deep lymph nodes", "965"],
    ["7. Bones, organs and brain", "Bones, cartilage, ligaments, joint capsules, viscera, heart, sense organs, brain and spinal cord", "1,151"],
], [42 * mm, TEXT_W - 67 * mm, 25 * mm], bold_first=True)]
story.append(KeepTogether(layers_block))
story.append(CondPageBreak(70 * mm))

story.append(P("3.4 Screens from the baseline", "h2"))
story.append(P("All screenshots were taken from the production build in a headless Chrome browser during testing.", "small"))
story.append(Spacer(1, 4))
story.append(fig_pair("b1_body_skin.jpg", "b2_superficial_muscles.jpg",
                      "Figure 1. Whole body at layer 1 (skin).", "Figure 2. Peeled to layer 4 (superficial muscles)."))
story.append(fig_pair("b3_bones_organs.jpg", "b4_organs_no_bones.jpg",
                      "Figure 3. Layer 7: bones, organs and brain.", "Figure 4. Layer 7 with bones switched off."))
story.append(fig_pair("b5_brain_lateral.jpg", "s_liver.jpg",
                      "Figure 5. Brain and spinal cord on their own, lateral view.",
                      "Figure 6. Search \"liver\": peeled to its layer, layers above ghosted, info panel open."))
story.append(fig_pair("s_facial_nerve.jpg", "s_biceps_femoris.jpg",
                      "Figure 7. Search \"facial nerve\": the head in context with its own description.",
                      "Figure 8. A hamstring muscle: the camera turns to the back of the thigh."))
story.append(CondPageBreak(105 * mm))

# ------------------------------------------------------------------ 4 architecture
story.append(P("4. Architecture", "h1"))
story.append(P("The system has two halves. An offline Python pipeline converts the Z-Anatomy Blender file into compact "
               "web files, and a static web viewer loads those files in the browser. There is no server-side code, "
               "which keeps hosting free and simple."))
story.append(architecture())
story.append(P("Figure 9. Data flow from the source file to the public site.", "caption"))

story.append(P("4.1 Data source and licensing", "h2"))
story.append(table([
    ["Source", "Used for", "Licence"],
    ["Z-Anatomy (github.com/Z-Anatomy)", "Whole-body models grouped by system and region, definitions, TA2 Latin table", "CC BY-SA 4.0"],
    ["BodyParts3D (Database Center for Life Science, Japan)", "Base meshes inside Z-Anatomy", "CC BY-SA 2.1 Japan"],
    ["Wikipedia (through Z-Anatomy)", "Structure descriptions", "CC BY-SA 3.0"],
    ["Brainder, University of Washington, University of Dundee", "Brain, white matter and cranial nerve detail inside Z-Anatomy", "Open licences; a few organ models are non-commercial only"],
], [55 * mm, TEXT_W - 90 * mm, 35 * mm]))
story.append(P("Because of the share-alike terms, the converted models are released under CC BY-SA 4.0. The project "
               "code can carry its own licence. Z-Anatomy includes a few non-commercial models (inner ear, kidney); "
               "these do not matter for a personal project but must be replaced before any commercial use. The "
               "Z-Anatomy project appears to be inactive, so this project keeps its own frozen snapshot of the data."))

story.append(P("4.2 Export pipeline", "h2"))
story.append(P("The pipeline uses Blender's engine as an ordinary Python package (<font face='Courier'>pip install bpy</font>, "
               "version 5.0.1, Python 3.11). It opens the .blend file directly, so nobody has to install or learn "
               "Blender. One run of <font face='Courier'>pipeline/export.py</font> takes under a minute."))
story.append(table([
    ["Step", "What happens"],
    ["Select", "Keeps meshes and curves inside Z-Anatomy's nine system collections whose names end in .r, .l or have no suffix. Labels (.j, .i, .t) and muscle attachment areas (.er, .or) are skipped."],
    ["Classify tissue", "From the material names and the system: skin, fascia, muscle, bursa, tendon sheath, nerve, artery, vein, lymph node, bone, cartilage, ligament, capsule, organ, heart, brain/spinal cord, sense organ."],
    ["Assign region", "From Z-Anatomy's \"Main divisions\". The trunk is split by the height of each structure's centre: thorax above 1.20 m, abdomen 0.99 to 1.20 m, pelvis below. Brain and spinal cord form their own bundle. Structures with no division are placed by height."],
    ["Assign depth", "Per-structure overrides from depth_tags.csv first; then name rules for superficial muscles (layer 4) and for cutaneous nerves and superficial veins (layer 2); then a default per tissue."],
    ["Bake geometry", "Nerve and vessel tubes are rebuilt at lower resolution (source bevel 4 and resolution 12, exported at 2 and 5), cutting their vertex count about four times. Each structure becomes one named node in world space."],
    ["Colour", "Materials are replaced by a flat palette per kind (muscle, tendon, nerve, artery, vein, lobes of the brain and so on), so tendons and cartilage keep their own colour."],
    ["Text and names", "Descriptions come from Z-Anatomy's text blocks, trimmed to 30 paragraphs. A muscle head without its own text borrows the parent muscle's. Latin names come from TA2.csv. Nerve supply is read from the nerve groups Z-Anatomy files muscles under."],
    ["Write", "One raw .glb and one content.json per region, plus metadata.json, manifest.json and a report.txt listing gaps."],
    ["Compress", "compress.sh runs gltf-transform with Draco, welding and light simplification, keeping every structure as a separate clickable node."],
], [28 * mm, TEXT_W - 28 * mm], bold_first=True))

story.append(P("4.3 Web viewer", "h2"))
story.append(table([
    ["Part", "Choice", "Reason"],
    ["Build", "Vite, React 18, TypeScript", "Fast builds, static output with relative paths that work from any folder"],
    ["3D", "Three.js through React Three Fiber and drei", "Mature WebGL stack with orbit controls and glTF loading"],
    ["State", "Zustand", "One small store for layers, systems, regions, selection and camera requests"],
    ["Model loading", "GLTFLoader with Draco (WebAssembly, or JavaScript on strict hosts)", "Draco gave the smallest files: 18.5 MB against 27 MB with meshopt"],
    ["Rendering", "Render on demand", "The scene is redrawn only when something changes, which saves battery and heat"],
    ["Styling", "Plain CSS", "Few screens; no framework needed"],
], [26 * mm, 62 * mm, TEXT_W - 88 * mm], bold_first=True))
story.append(P("Each structure's draw state (solid, ghost or hidden, plus selection and hover) is cached, so a change "
               "only touches the structures it affects. Hidden and ghosted structures are excluded from mouse picking."))

story.append(P("4.4 Deployment", "h2"))
story.append(P("The repository includes a GitHub Actions workflow (<font face='Courier'>.github/workflows/deploy.yml</font>). "
               "On every push to main it installs dependencies with Node 22, builds the viewer and publishes "
               "<font face='Courier'>web/dist</font> to GitHub Pages. The first build took 29 seconds and the deploy 9 "
               "seconds. GitHub Pages allows sites up to 1 GB with a soft bandwidth limit of 100 GB a month; one full "
               "first visit downloads about 24 MB and browsers cache it for later visits."))
story.append(PageBreak())

# ------------------------------------------------------------------ 5 decisions
story.append(P("5. Key decisions and why", "h1"))
story.append(table([
    ["Decision", "Alternatives considered", "Why this choice"],
    ["Use Z-Anatomy as the data source", "Raw BodyParts3D OBJ files; buying commercial models", "Already grouped by system and region, cleaned, with extra neuro models and text. Free and shareable."],
    ["Run Blender as a Python package (bpy)", "Learning Blender; converting the FBX download", "No 3D software to learn. The FBX route would have lost the collection grouping that drives regions and layers."],
    ["Start with the right upper limb", "Whole body at once", "Proved the pipeline and viewer on a manageable 325 structures before scaling up."],
    ["Seven layers, organs with bones at layer 7", "Separate organ layer after bones", "In the limbs bones are deepest, in the trunk organs are inside the ribs. One shared deepest layer plus a bones toggle works for both."],
    ["Split the trunk by height", "Hand-tagging every trunk structure", "Quick and good enough for loading in parts. Long structures land in one region, noted as a limitation."],
    ["Draco compression", "meshopt, quantisation only", "Smallest files, and a pure JavaScript decoder exists for hosts that block WebAssembly."],
    ["Load regions one by one", "One whole-body file", "The body appears within seconds and keeps building; a single file would be slow to first view."],
    ["Search shows structures in context", "Leave peeling as the user set it", "A deep structure found by search was framed but invisible under the skin. Peeling to its layer and ghosting above fixed this."],
    ["Exact structure beats group in search", "Prefer groups", "Searching \"facial nerve\" was isolating the face muscles it supplies, which was misleading."],
    ["GitHub Pages hosting", "Netlify, Cloudflare Pages", "Free, tied to the repository, deploys automatically on push, no extra account."],
], [42 * mm, 46 * mm, TEXT_W - 88 * mm], bold_first=True))

# ------------------------------------------------------------------ 6 testing
story.append(P("6. Testing completed", "h1"))
story.append(P("The viewer was tested in headless Chrome with software rendering, which is far slower than a real "
               "graphics card, so it is a demanding check. The whole body loaded in about 61 seconds in that setting. "
               "Each round covered loading every region, peeling all layers, system and region toggles, search and "
               "group search, the info panel and the report dialog, with screenshots inspected after each change. No "
               "browser console errors were recorded in the final runs."))
story.append(P("Issues found during testing and fixed", "h2"))
story.append(table([
    ["Issue", "Fix"],
    ["The .glb model format was refused by the private preview host", "Added a build that ships models as base64 JSON and uses Draco's JavaScript decoder"],
    ["Selection highlight too faint on thin nerves", "The selected structure's own colour is now tinted blue as well as glowing"],
    ["\"Part of\" listed a structure as part of itself", "Self-references are filtered out"],
    ["Clicks timed out with 3,000 structures redrawn every frame", "Switched to rendering on demand and caching draw state per structure"],
    ["Searching a deep structure showed only skin", "Search now peels to the structure's layer and ghosts the layers above"],
    ["Camera stayed at the front for posterior structures", "Zoom now looks from the side the structure lies on, measured from its region's centre"],
    ["\"Facial nerve (VII\" lost its closing bracket and its own text", "Name clean-up now only removes brackets that wrap the whole name"],
    ["Search for \"liver\" and \"facial nerve\" isolated a group", "Exact structure matches win; groups are picked only when they match better"],
    ["Long Wikipedia articles (over 350 paragraphs)", "Trimmed to the first 30 paragraphs with a link to the full article; text size fell from 7.8 MB to 3.9 MB"],
], [72 * mm, TEXT_W - 72 * mm]))
story.append(P("The live GitHub Pages site was later checked on Android phones: it works, with a slow first load.", "small"))
story.append(CondPageBreak(90 * mm))

# ------------------------------------------------------------------ 7 limitations
story.append(P("7. Known limitations and gaps", "h1"))
story.append(table([
    ["Gap", "Effect", "Proposed fix"],
    ["Content not reviewed", "Descriptions come from Wikipedia and may hold errors, including translation errors in Z-Anatomy", "Faculty review region by region; reviewed badge per entry"],
    ["Superficial or deep muscle split is rule-based", "Some muscles may sit in the wrong layer", "Professor checks layers 4 and 5; overrides go in depth_tags.csv"],
    ["Lateral and medial cords of the brachial plexus missing", "Only the posterior cord is modelled", "Model them, or source them from another open dataset"],
    ["235 of 513 muscles lack nerve supply", "Mostly trunk and head muscles", "Fill a nerve supply table with faculty, merge in the pipeline"],
    ["337 structures lack a description", "Mostly small ligaments, lymph node groups and skin regions", "Write short entries or borrow from parent groups"],
    ["Trunk split by height", "Aorta, oesophagus and erector spinae sit in one region only", "Allow a structure to belong to several regions"],
    ["No single \"Heart\" structure", "The heart is 17 parts; search finds it as a group", "Acceptable; could add a named heart group label"],
    ["Slow first load on phones", "Works on the Android phones tested, but the first visit takes a while", "Lite mode loading one region, if pilot users ask for it"],
    ["Brain lobe colours are faint", "Lobes are hard to tell apart", "Adjust palette and review with the neurosurgeon"],
], [44 * mm, 60 * mm, TEXT_W - 104 * mm], bold_first=True))

# ------------------------------------------------------------------ 8 next steps
story.append(KeepTogether([P("8. What needs to be done next", "h1"),
    P("The next phase is a closed pilot, not a public launch. Content that has not been reviewed should not reach "
      "a full batch of students, and a small group gives feedback that can be acted on."),
    roadmap(), P("Figure 10. Phases from baseline to the next level.", "caption")]))
story.append(P("8.1 Feedback setup", "h2"))
story.append(table([
    ["Task", "Owner", "Notes"],
    ["Google Form for error reports (done)", "Developer", "Fields: structure, layer, what is wrong, role; responses go to a Google Sheet"],
    ["Report button pre-fills the form (done, live)", "Developer", "Structure name, side, id and layer are filled in automatically"],
    ["Add a general feedback button and an end-of-pilot survey", "Developer", "Include a standard usability questionnaire (SUS)"],
    ["Log searches that return nothing", "Developer", "Privacy-friendly counter such as GoatCounter or Umami; no personal data"],
    ["Write a tester guide and task sheet", "Developer", "Short tasks such as \"find the median nerve and name its layer\""],
    ["Check the live site on Android phones (done)", "Developer", "Works; first load is slow. Lite mode only if pilot users ask"],
    ["Ask about ethics approval and consent", "Developer with institution", "Needed if pilot results may later be published"],
], [70 * mm, 30 * mm, TEXT_W - 100 * mm]))
story.append(P("8.2 Pilot plan", "h2"))
story.append(table([
    ["Round", "Who", "What they do", "Exit check"],
    ["Round 1, about two weeks", "10 to 15 first-year students, two anatomy professors, one neurosurgeon",
     "Students follow the task sheet, then use the atlas alongside dissection. Professors review content region by region. The neurosurgeon reviews the nervous system.",
     "Round 1 reports triaged and fixed; reviewed regions carry the badge"],
    ["Round 2", "A full first-year batch", "Free use through a term with the error button and survey",
     "Usability score and error rate acceptable; priorities for the next level agreed"],
], [30 * mm, 42 * mm, TEXT_W - 112 * mm, 40 * mm]))
story.append(P("8.3 Handling feedback", "h2"))
story += bullets([
    "Keep one sheet with a status for each report: new, accepted, fixed, won't fix.",
    "Apply fixes in the pipeline (depth_tags.csv, export rules or text), re-export, and push. The site redeploys in under a minute.",
    "Release in weekly batches with a short changelog so testers see their reports acted on.",
    "Mark entries as reviewed (reviewed_by and reviewed_on in the content files) when a professor signs them off.",
])
story.append(CondPageBreak(100 * mm))

# ------------------------------------------------------------------ 9 future scope
story.append(P("9. Features yet to be included", "h1"))
story.append(P("These are candidates for the next level. Their order should follow the pilot feedback, especially the "
               "failed-search log and the survey."))
story.append(table([
    ["Feature", "Description", "Depends on"],
    ["Quizzes and self-test", "Pin-the-structure questions, a labels-hidden mode, flashcards and progress per region", "Reviewed content"],
    ["AI tutor", "Answers questions from the reviewed descriptions using retrieval, and turns commands such as \"show the brachial plexus without muscles\" into viewer actions", "Reviewed content, a small backend (FastAPI) and a hosted model"],
    ["Mobile app or offline PWA", "Installable app with offline region packs for students with weak connections", "Phone performance results"],
    ["Cross-sections", "Clipping planes to view the body in axial, sagittal and coronal slices", "None"],
    ["Pins and labels", "Floating labels and student annotations saved on the device", "None"],
    ["Curriculum mapping", "Link structures to NMC CBME competency codes so students see where each topic sits in the syllabus", "Faculty input"],
    ["Lite mode", "Load one region at a time and lower detail on phones", "Phone test results"],
    ["Complete the data", "Missing brachial plexus cords, nerve supply for all muscles, descriptions for the remaining 337 structures", "Faculty review"],
    ["Accessibility and languages", "Keyboard navigation for all controls, screen reader labels, and possibly regional languages", "User demand"],
], [36 * mm, TEXT_W - 86 * mm, 50 * mm], bold_first=True))

# ------------------------------------------------------------------ 10 maintenance
story.append(P("10. How to run and maintain", "h1"))
story.append(P("Rebuild the data", "h3"))
story.append(P("python3.11 -m venv bpyenv &amp;&amp; bpyenv/bin/pip install bpy numpy<br/>"
               "cd pipeline<br/>"
               "../bpyenv/bin/python export.py --blend /path/to/Z-Anatomy/Startup.blend \\<br/>"
               "&nbsp;&nbsp;--out ../build/body --tags depth_tags.csv --ta2 TA2.csv&nbsp;&nbsp;&nbsp;# --only head,neck for some regions<br/>"
               "cd .. &amp;&amp; (cd tools &amp;&amp; npm install)<br/>"
               "pipeline/compress.sh $PWD/build/body $PWD/build/body/draco draco<br/>"
               "cp build/body/draco/* web/public/models/body/", "code"))
story.append(P("Run and deploy the viewer", "h3"))
story.append(P("cd web &amp;&amp; npm install<br/>"
               "npm run dev&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# local development server<br/>"
               "npm run build&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# static site in web/dist<br/>"
               "git push origin main&nbsp;# GitHub Actions rebuilds and redeploys the live site", "code"))
story.append(KeepTogether([P("Common changes", "h3"), table([
    ["To change", "Edit"],
    ["A structure's layer", "pipeline/depth_tags.csv (name, depth, note); applies to both sides"],
    ["Which muscles count as superficial", "SUPERFICIAL_MUSCLE in pipeline/export.py"],
    ["Region boundaries in the trunk", "Z_THORAX and Z_ABDOMEN in pipeline/export.py"],
    ["Colours", "PALETTE in pipeline/export.py"],
    ["Feedback form link", "FEEDBACK_FORM_URL in web/src/config.ts"],
    ["Layer names and hints", "LAYERS in web/src/config.ts"],
], [55 * mm, TEXT_W - 55 * mm], bold_first=True)]))
story.append(CondPageBreak(110 * mm))

# ------------------------------------------------------------------ appendices
story.append(P("Appendix A. Repository structure", "h1"))
story.append(P("anatomy-atlas/<br/>"
               "&nbsp;&nbsp;.github/workflows/deploy.yml&nbsp;&nbsp;&nbsp;build and publish to GitHub Pages<br/>"
               "&nbsp;&nbsp;pipeline/<br/>"
               "&nbsp;&nbsp;&nbsp;&nbsp;export.py&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;whole-body exporter (bpy)<br/>"
               "&nbsp;&nbsp;&nbsp;&nbsp;compress.sh&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Draco or meshopt compression<br/>"
               "&nbsp;&nbsp;&nbsp;&nbsp;depth_tags.csv&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;layer overrides (for review)<br/>"
               "&nbsp;&nbsp;&nbsp;&nbsp;TA2.csv&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Terminologia Anatomica 2 table<br/>"
               "&nbsp;&nbsp;&nbsp;&nbsp;inventory.py, inspect_*.py&nbsp;&nbsp;helpers used to explore the .blend<br/>"
               "&nbsp;&nbsp;build/body/&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;last export: metadata, manifest, text, report.txt<br/>"
               "&nbsp;&nbsp;web/<br/>"
               "&nbsp;&nbsp;&nbsp;&nbsp;src/&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;App, Viewer, Sidebar, InfoPanel, store, loader, config<br/>"
               "&nbsp;&nbsp;&nbsp;&nbsp;public/models/body/&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;10 region models and text, metadata, manifest<br/>"
               "&nbsp;&nbsp;&nbsp;&nbsp;public/draco/&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Draco decoders<br/>"
               "&nbsp;&nbsp;&nbsp;&nbsp;scripts/b64.mjs&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;base64 packing for strict hosts<br/>"
               "&nbsp;&nbsp;tools/&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;gltf-transform setup and headless screenshot tests<br/>"
               "&nbsp;&nbsp;README.md, LICENSES.md", "code"))

story.append(P("Appendix B. Structure metadata fields", "h1"))
story.append(table([
    ["Field", "Meaning", "Example"],
    ["id", "Stable identifier, side suffix _r or _l", "median_nerve_r"],
    ["name / source_name", "Display name / original Z-Anatomy object name", "Median nerve / Median nerve.r"],
    ["side", "right, left or midline", "right"],
    ["region", "Region bundle the structure loads with", "upper_limb_r"],
    ["system", "Toggle group: skin, muscular, nervous, vascular, organs, skeletal", "nervous"],
    ["tissue", "Finer type used for colour and default layer", "nerve"],
    ["depth, depth_note", "Layer 1 to 7 and any reviewer note", "6"],
    ["groups", "Z-Anatomy collections the structure belongs to", "Infraclavicular part of brachial plexus"],
    ["content_ref, content_shared_from", "Key into the region's text file; parent whose text is borrowed", "median_nerve"],
    ["innervation", "For muscles, the nerve groups they are filed under", "Radial nerve"],
    ["latin, ta2_id", "Latin term and Terminologia Anatomica 2 identifier", "Nervus medianus"],
], [42 * mm, TEXT_W - 92 * mm, 50 * mm], bold_first=True))

story.append(P("Appendix C. Credits", "h1"))
story += bullets([
    "Models: \"Z-Anatomy, the libre 3D atlas of anatomy\", CC BY-SA 4.0, based on \"BodyParts3D, The Database Center for Life Science\", CC BY-SA 2.1 Japan.",
    "Additional models inside Z-Anatomy: Brainder and White matter (University of Washington); Cranial Nerves and Foramina (University of Dundee, CC BY 4.0).",
    "Descriptions: Z-Anatomy definitions based on Wikipedia, CC BY-SA 3.0.",
    "Latin names: Terminologia Anatomica 2 table distributed with Z-Anatomy.",
    "Software: Three.js, React Three Fiber, drei, React, Vite, Zustand, gltf-transform, Draco, Blender (bpy).",
    "Reference product for the concept: Anatomy 3D Atlas.",
])

doc.multiBuild(story)
print("wrote", OUT)
