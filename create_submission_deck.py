from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parent
SOURCE = Path(r"C:\Users\admin\Downloads\Khacks_4.0_ppt (1).pptx")
OUTPUT = ROOT / "RingTrace_K!_Hacks_4.0_Submission.pptx"


def set_text_shape(shape, text, size=18, bold=False, color=(20, 30, 55), align=PP_ALIGN.LEFT):
    shape.text_frame.clear()
    shape.text_frame.margin_left = Inches(0.12)
    shape.text_frame.margin_right = Inches(0.12)
    shape.text_frame.margin_top = Inches(0.08)
    shape.text_frame.margin_bottom = Inches(0.08)
    shape.text_frame.word_wrap = True
    paragraph = shape.text_frame.paragraphs[0]
    paragraph.text = text
    paragraph.font.name = "Aptos"
    paragraph.font.size = Pt(size)
    paragraph.font.bold = bold
    paragraph.font.color.rgb = RGBColor(*color)
    paragraph.alignment = align


def find_body(slide):
    candidates = [sh for sh in slide.shapes if getattr(sh, "has_text_frame", False)]
    if not candidates:
        return None
    for sh in candidates:
        if sh.text.strip() == "Type Here":
            return sh
    return None


def add_bullet_block(slide, left, top, width, height, items, title=None, accent=(37, 99, 235)):
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor(248, 250, 252)
    box.line.color.rgb = RGBColor(203, 213, 225)
    tf = box.text_frame
    tf.clear()
    tf.margin_left = Inches(0.18)
    tf.margin_right = Inches(0.15)
    tf.margin_top = Inches(0.12)
    tf.margin_bottom = Inches(0.10)
    tf.word_wrap = True
    if title:
        p = tf.paragraphs[0]
        p.text = title
        p.font.name = "Aptos"
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = RGBColor(*accent)
        p.space_after = Pt(8)
    for item in items:
        p = tf.add_paragraph()
        p.text = item
        p.font.name = "Aptos"
        p.font.size = Pt(13)
        p.font.color.rgb = RGBColor(20, 30, 55)
        p.level = 0
        p.text = "• " + p.text
        p.space_after = Pt(5)
    return box


def add_architecture(slide):
    colors = {
        "input": (14, 116, 144),
        "graph": (37, 99, 235),
        "evidence": (79, 70, 229),
        "agents": (220, 38, 38),
        "test": (234, 88, 12),
        "output": (5, 150, 105),
    }
    y = 2.15
    boxes = [
        (0.35, 2.35, "CASE INPUT", "Transactions\nSynthetic presets / API", "input"),
        (2.95, 2.35, "TEMPORAL GRAPH", "Accounts + directed\ntransaction edges", "graph"),
        (5.55, 2.35, "EVIDENCE PACK", "Frozen records\npaths + metrics", "evidence"),
        (8.15, 2.35, "BOUND INVESTIGATION", "Planner → Prosecutor\n→ Defender", "agents"),
        (10.75, 2.35, "CERP + REVIEW", "Stress tests\nHuman workspace", "output"),
    ]
    for x, w, title, body, kind in boxes:
        sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(1.45))
        sh.fill.solid()
        sh.fill.fore_color.rgb = RGBColor(*colors[kind])
        sh.line.color.rgb = RGBColor(*colors[kind])
        tf = sh.text_frame
        tf.clear()
        tf.margin_left = tf.margin_right = Inches(0.12)
        tf.vertical_anchor = 1
        p = tf.paragraphs[0]
        p.text = title
        p.font.name = "Aptos"
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.alignment = PP_ALIGN.CENTER
        p2 = tf.add_paragraph()
        p2.text = body
        p2.font.name = "Aptos"
        p2.font.size = Pt(10)
        p2.font.color.rgb = RGBColor(255, 255, 255)
        p2.alignment = PP_ALIGN.CENTER

    for x1, x2 in [(2.70, 2.95), (5.30, 5.55), (7.90, 8.15), (10.50, 10.75)]:
        line = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x1), Inches(2.68), Inches(x2-x1), Inches(0.38))
        line.fill.solid()
        line.fill.fore_color.rgb = RGBColor(100, 116, 139)
        line.line.fill.background()

    add_bullet_block(
        slide, 0.35, 3.95, 12.60, 2.55,
        [
            "Stress Engine: provenance • chronology • alternative hypotheses • contradictions/gaps • pivotal-evidence sensitivity",
            "Deterministic Claim Validator: rejects fabricated IDs, field mismatches and impossible chronology",
            "Reconciler: separates verified observations, challenged hypotheses, unknowns and sensitivity caveats",
            "Governance: suggestions only—analyst retains final review and no enforcement action is automated",
        ],
        "PROCESSING & CONTROL LAYER",
        accent=(234, 88, 12),
    )


prs = Presentation(SOURCE)

# Slide 1
slide = prs.slides[0]
set_text_shape(
    [sh for sh in slide.shapes if getattr(sh, "has_text_frame", False)][1],
    "Team Name        :  Twilight\n"
    "College Name    :  Saveetha Engineering College\n"
    "Problem Track   :  Agentic AI / FinTech\n"
    "Project             :  RingTrace",
    size=22,
)

# Slide 2
slide = prs.slides[1]
body = find_body(slide)
body.left, body.top = Inches(0.45), Inches(1.35)
body.width, body.height = Inches(12.35), Inches(5.25)
set_text_shape(body,
    "Suspicious transaction alerts are starting points, not investigations or proof of wrongdoing.\n\n"
    "When activity spans accounts and time, analysts must reconstruct fund flows, verify source records, "
    "consider legitimate explanations and document uncertainty. Fragmented evidence and unconstrained AI "
    "narratives can hide gaps or turn graph patterns into unsupported conclusions.\n\n"
    "RingTrace addresses the post-alert investigation gap: systematically test why a case was flagged, "
    "what the records establish, which explanations remain plausible, and when the conclusion depends on "
    "pivotal evidence.",
    size=21,
)

# Slide 3
slide = prs.slides[2]
body = find_body(slide)
body.left, body.top = Inches(0.45), Inches(1.35)
body.width, body.height = Inches(12.35), Inches(5.25)
set_text_shape(body,
    "An evidence-grounded, adversarial investigation prototype for financial-crime analysts.\n\n"
    "A temporal graph assembles the case; a frozen evidence pack preserves provenance; a Prosecutor develops "
    "a testable suspicious hypothesis; and a Defender checks legitimate alternatives.\n\n"
    "A stress-test engine examines provenance, chronology, contradictions, missing context and pivotal-evidence "
    "sensitivity. A deterministic validator rejects unsupported or inconsistent claims. The Reconciler produces "
    "a transparent Case Evidence Robustness Profile (CERP) for human review.\n\n"
    "Outcome: ESCALATE FOR REVIEW • REQUEST MORE INFORMATION • REVIEW DISMISSAL • INSUFFICIENT EVIDENCE",
    size=19,
)

# Slide 4
slide = prs.slides[3]
for sh in list(slide.shapes):
    if getattr(sh, "has_text_frame", False) and sh.text.strip() == "Type Here":
        slide.shapes._spTree.remove(sh._element)
add_architecture(slide)

# Slide 5
slide = prs.slides[4]
body = find_body(slide)
body.left, body.top = Inches(0.35), Inches(1.55)
body.width, body.height = Inches(12.55), Inches(5.10)
set_text_shape(body,
    "FEASIBILITY\n"
    "• Implemented FastAPI backend, temporal graph engine, adversarial workflow, evidence pack and analyst UI\n"
    "• Synthetic circular, payroll, fan-in and planted-defect cases provide end-to-end demonstrations\n"
    "• 14 automated tests pass, including fabricated IDs, chronology violations and pivot sensitivity\n\n"
    "UNIQUE SELLING POINTS\n"
    "• Facts are separated from interpretations\n"
    "• Mandatory counter-hypothesis challenge\n"
    "• Deterministic validation beneath AI-generated text\n"
    "• CERP replaces a deceptive single risk score with traceable evidence dimensions\n"
    "• Human-in-the-loop: no autonomous account blocking or regulatory reporting",
    size=17,
)

# Slide 6
slide = prs.slides[5]
body = find_body(slide)
body.left, body.top = Inches(0.35), Inches(1.55)
body.width, body.height = Inches(12.55), Inches(5.10)
set_text_shape(body,
    "TARGET USERS\n"
    "AML operations teams • Financial-crime investigators • FinTech risk/compliance teams • AML technology vendors\n\n"
    "MARKET POSITION\n"
    "A decision-support layer after alert generation and before enforcement action. Integrates with existing "
    "case-management, graph-detection and bank-regulated data environments.\n\n"
    "BUSINESS MODEL\n"
    "B2B SaaS pilot: annual licence by monitored alert volume and analyst seats; optional integration fees and "
    "validation support; regional deployment options for sensitive compliance environments.\n\n"
    "VALUE METRICS\n"
    "Review time • unsupported-claim rejection • evidence-gap recall • false-positive resolution • analyst override rate",
    size=17,
)

# Slide 7
slide = prs.slides[6]
body = find_body(slide)
body.left, body.top = Inches(0.35), Inches(1.55)
body.width, body.height = Inches(12.55), Inches(5.10)
set_text_shape(body,
    "KEY RESEARCH & REFERENCES\n"
    "1. Co-Investigator AI — Agentic AI for AML Compliance Narratives. arXiv:2509.08380\n"
    "2. Explainable AML Triage with LLMs — Evidence Retrieval and Counterfactual Checks. arXiv:2604.19755\n"
    "3. LLM reasoning over financial transaction graphs. arXiv:2507.14785\n"
    "4. From Tasks to Teams: M-SAEA risk-first framework for multi-agent LLM systems in finance.\n"
    "   ACL Anthology 2026 Findings, https://aclanthology.org/2026.findings-acl.1934/\n"
    "5. A Survey of Intelligent Anti-Money Laundering Techniques — DOI:10.19678/j.issn.1000-3428.0260981\n\n"
    "POSITIONING\n"
    "RingTrace makes no claim that individual agents or evidence citations are unique. Its defensible contribution "
    "is an integrated, experimentally testable case-level robustness workflow.",
    size=14,
)

# Slide 8
slide = prs.slides[7]
for sh in list(slide.shapes):
    if getattr(sh, "has_text_frame", False):
        if sh.text.strip() in {"ROLE", "NAME", "STREAM / DEPT", "YEAR", "COLLEGE"}:
            sh.left = sh.left

table = slide.shapes.add_table(5, 5, Inches(0.45), Inches(2.15), Inches(12.45), Inches(4.50)).table
columns = [2.20, 2.20, 2.30, 1.10, 4.65]
for i, width in enumerate(columns):
    table.columns[i].width = Inches(width)
headers = ["ROLE", "NAME", "STREAM / DEPT", "YEAR", "COLLEGE"]
rows = [
    ("Graph & Data", "Member 1 — add name", "Add department", "Add year", "Saveetha Engineering College"),
    ("Agent & Tool Design", "Member 2 — add name", "Add department", "Add year", "Saveetha Engineering College"),
    ("Validation & Evaluation", "Member 3 — add name", "Add department", "Add year", "Saveetha Engineering College"),
    ("Backend, UI & Demo", "Member 4 — add name", "Add department", "Add year", "Saveetha Engineering College"),
]
for c, text in enumerate(headers):
    cell = table.cell(0, c)
    cell.text = text
    cell.fill.solid()
    cell.fill.fore_color.rgb = RGBColor(30, 64, 175)
    for p in cell.text_frame.paragraphs:
        p.font.name = "Aptos"
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.alignment = PP_ALIGN.CENTER
for r, row in enumerate(rows, start=1):
    for c, text in enumerate(row):
        cell = table.cell(r, c)
        cell.text = text
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(248, 250, 252) if r % 2 else RGBColor(239, 246, 255)
        for p in cell.text_frame.paragraphs:
            p.font.name = "Aptos"
            p.font.size = Pt(11)
            p.font.color.rgb = RGBColor(20, 30, 55)
            p.alignment = PP_ALIGN.CENTER

prs.save(OUTPUT)
print(OUTPUT)
