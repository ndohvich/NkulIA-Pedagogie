"""Export PDF d'une fiche de cours VALIDÉE (issue #14).

Gabarit : en-tête établissement + enseignant (issus du profil, issue
#7), identité visuelle NkulIA (vert forêt / latérite / or), un bloc par
champ avec son étiquette de provenance, pied de page numéroté.

La règle « seul `valide` s'exporte » est appliquée ici ET dans la route :
ce module refuse de produire un PDF définitif pour un autre statut,
même s'il était un jour appelé depuis un autre endroit.
"""

from __future__ import annotations

from datetime import datetime
from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer

from app.db.models import GeneratedDocument, Teacher
from app.generation import lifecycle

FOREST = colors.HexColor("#1F5D42")
FOREST_DEEP = colors.HexColor("#123825")
LATERITE = colors.HexColor("#B44B26")
GOLD = colors.HexColor("#B5842A")
SLATE = colors.HexColor("#334155")

PROVENANCE_LABEL = {
    "reference": ("Référence", FOREST),
    "deduction": ("Déduction", colors.HexColor("#1E5A8A")),
    "ai_recommendation": ("Recommandation IA", GOLD),
    "missing_information": ("Information manquante", colors.HexColor("#64748B")),
}

VOCABULARY = {
    "ua_ue": {
        "titre_unite_apprentissage": "Unité d'Apprentissage",
        "titre_unite_enseignement": "Unité d'Enseignement",
    },
    "chapitre_lecon": {
        "titre_unite_apprentissage": "Chapitre",
        "titre_unite_enseignement": "Leçon",
    },
}

_LABELS = {
    "titre_module": "Module",
    "duree": "Durée",
    "type_seance": "Type de séance",
    "digitalisation": "Digitalisation",
    "savoirs_essentiels": "Savoirs essentiels",
    "actions": "Actions",
    "objectifs": "Objectifs",
    "prerequis": "Prérequis",
    "situation_probleme": "Situation-problème",
    "activites": "Activités",
}


class NotValidated(RuntimeError):
    """Export refusé : la fiche n'est pas au statut « validé »."""


def _styles() -> dict[str, ParagraphStyle]:
    return {
        "title": ParagraphStyle(
            "title", fontName="Helvetica-Bold", fontSize=18, textColor=FOREST_DEEP, leading=22
        ),
        "meta": ParagraphStyle(
            "meta", fontName="Helvetica", fontSize=9, textColor=SLATE, leading=12
        ),
        "label": ParagraphStyle(
            "label", fontName="Helvetica-Bold", fontSize=10.5, textColor=FOREST_DEEP, leading=14
        ),
        "tag": ParagraphStyle("tag", fontName="Helvetica", fontSize=7.5, leading=10),
        "body": ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=10,
            textColor=SLATE,
            leading=14,
            alignment=TA_LEFT,
        ),
        "missing": ParagraphStyle(
            "missing", fontName="Helvetica-Oblique", fontSize=10, textColor=LATERITE, leading=14
        ),
    }


def _text(value: str) -> str:
    """Échappe le XML de ReportLab et conserve les retours à la ligne."""
    return escape(value, quote=False).replace("\n", "<br/>")


def _label_for(field: str, track_schema: str) -> str:
    return VOCABULARY.get(track_schema, {}).get(field) or _LABELS.get(field, field)


def render_course_sheet_pdf(document: GeneratedDocument, teacher: Teacher) -> bytes:
    if document.status != lifecycle.VALIDE:
        raise NotValidated("Seule une fiche validée peut être exportée en PDF.")

    unit = document.teaching_unit
    source = unit.learning_unit.module.source_document
    styles = _styles()
    institution = teacher.institution.name if teacher.institution else "Établissement non renseigné"
    teacher_line = f"{teacher.first_name} {teacher.last_name}"
    extras = " · ".join(v for v in (teacher.function, teacher.grade, teacher.specialty) if v)
    validated = document.validated_at or datetime.now()

    def on_page(canvas: Canvas, doc: SimpleDocTemplate) -> None:
        width, height = A4
        canvas.saveState()
        canvas.setFillColor(FOREST_DEEP)
        canvas.rect(0, height - 1.6 * cm, width, 1.6 * cm, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 13)
        canvas.drawString(2 * cm, height - 1.05 * cm, "Nkul")
        canvas.setFillColor(GOLD)
        canvas.drawString(
            2 * cm + canvas.stringWidth("Nkul", "Helvetica-Bold", 13), height - 1.05 * cm, "IA"
        )
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(width - 2 * cm, height - 1.05 * cm, institution[:70])
        canvas.setStrokeColor(GOLD)
        canvas.setLineWidth(1.2)
        canvas.line(2 * cm, 1.5 * cm, width - 2 * cm, 1.5 * cm)
        canvas.setFillColor(SLATE)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(
            2 * cm, 1.0 * cm, f"Fiche validée le {validated:%d/%m/%Y} — {teacher_line}"
        )
        canvas.drawRightString(width - 2 * cm, 1.0 * cm, f"Page {doc.page}")
        canvas.restoreState()

    buffer = BytesIO()
    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2.6 * cm,
        bottomMargin=2.2 * cm,
        title=f"Fiche de cours — {unit.title}",
        author=teacher_line,
        subject="Fiche de cours NkulIA",
    )

    story: list = [
        Paragraph("Fiche de cours", styles["title"]),
        Spacer(1, 4),
        Paragraph(_text(f"{teacher_line}" + (f" — {extras}" if extras else "")), styles["meta"]),
        Paragraph(_text(f"Source : {source.filename}"), styles["meta"]),
        Spacer(1, 14),
    ]

    for item in document.fields:
        label, color = PROVENANCE_LABEL[item.provenance]
        edited = " · modifié par l'enseignant" if item.edited_by_teacher else ""
        header = Paragraph(
            f"{_text(_label_for(item.field, source.track_schema))} "
            f'<font name="Helvetica" size="7.5" color="{color.hexval().replace("0x", "#")}">'
            f"[{label}{edited}]</font>",
            styles["label"],
        )
        if item.value and item.value.strip():
            body = Paragraph(_text(item.value), styles["body"])
        else:
            body = Paragraph(
                "Information absente du référentiel — non renseignée.", styles["missing"]
            )
        story.append(KeepTogether([header, Spacer(1, 2), body, Spacer(1, 10)]))

    pdf.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return buffer.getvalue()
