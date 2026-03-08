"""
PDF Generator — SPEC 6.1
Genera reportes ejecutivos profesionales de Decision Intelligence.
Usa reportlab Platypus para layout multi-página.
"""
import io
from datetime import datetime
from typing import Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle
)
from reportlab.platypus.flowables import Flowable


# ═══════════════════════════════════════════════════════════════
# BRAND
# ═══════════════════════════════════════════════════════════════

DARK_BLUE  = colors.HexColor('#1A1A2E')
GOLD       = colors.HexColor('#D4AF37')
MID_BLUE   = colors.HexColor('#2C3E7A')
LIGHT_GRAY = colors.HexColor('#F5F5F5')
MED_GRAY   = colors.HexColor('#888888')
GREEN_OK   = colors.HexColor('#27AE60')
YELLOW_WARN = colors.HexColor('#F39C12')
RED_CRIT   = colors.HexColor('#E74C3C')

PAGE_W, PAGE_H = A4
MARGIN = 2 * cm


# ═══════════════════════════════════════════════════════════════
# CUSTOM FLOWABLES
# ═══════════════════════════════════════════════════════════════

class HealthScoreBox(Flowable):
    """Caja grande con el Business Health Score."""
    def __init__(self, score: int, label: str, hex_color: str, width: float = 14 * cm):
        super().__init__()
        self.score = score
        self.label = label
        self.color = colors.HexColor(hex_color)
        self.width = width
        self.height = 3.5 * cm

    def draw(self):
        c = self.canv
        # Fondo con borde
        c.setStrokeColor(self.color)
        c.setFillColor(colors.HexColor('#F8F8F8'))
        c.setLineWidth(2)
        c.roundRect(0, 0, self.width, self.height, 8, fill=1, stroke=1)
        # Score
        c.setFillColor(self.color)
        c.setFont('Helvetica-Bold', 40)
        c.drawString(1 * cm, 1.8 * cm, str(self.score))
        # /100
        c.setFont('Helvetica', 14)
        c.setFillColor(MED_GRAY)
        c.drawString(3.2 * cm, 1.9 * cm, '/ 100')
        # Label
        c.setFont('Helvetica-Bold', 18)
        c.setFillColor(self.color)
        c.drawString(6 * cm, 2.1 * cm, self.label)
        # Subtitulo
        c.setFont('Helvetica', 10)
        c.setFillColor(MED_GRAY)
        c.drawString(6 * cm, 1.5 * cm, 'Business Health Score — Evangelista & Co.')


class SectionHeader(Flowable):
    """Encabezado de sección con linea dorada."""
    def __init__(self, title: str, width: float = 17 * cm):
        super().__init__()
        self.title = title
        self.width = width
        self.height = 1.0 * cm

    def draw(self):
        c = self.canv
        c.setFillColor(DARK_BLUE)
        c.setFont('Helvetica-Bold', 13)
        c.drawString(0, 0.3 * cm, self.title)
        c.setStrokeColor(GOLD)
        c.setLineWidth(1.5)
        c.line(0, 0, self.width, 0)


# ═══════════════════════════════════════════════════════════════
# STYLES
# ═══════════════════════════════════════════════════════════════

def build_styles():
    base = getSampleStyleSheet()
    styles = {
        'title': ParagraphStyle('title', fontName='Helvetica-Bold', fontSize=28,
                                textColor=DARK_BLUE, alignment=TA_CENTER, spaceAfter=6),
        'subtitle': ParagraphStyle('subtitle', fontName='Helvetica', fontSize=14,
                                   textColor=MID_BLUE, alignment=TA_CENTER, spaceAfter=4),
        'body': ParagraphStyle('body', fontName='Helvetica', fontSize=10,
                               textColor=colors.black, leading=14, spaceAfter=4),
        'body_bold': ParagraphStyle('body_bold', fontName='Helvetica-Bold', fontSize=10,
                                    textColor=DARK_BLUE, leading=14, spaceAfter=4),
        'small': ParagraphStyle('small', fontName='Helvetica', fontSize=8,
                                textColor=MED_GRAY, leading=11),
        'bullet': ParagraphStyle('bullet', fontName='Helvetica', fontSize=10,
                                 textColor=colors.black, leading=14,
                                 leftIndent=12, bulletIndent=0, spaceAfter=3),
        'kpi_value': ParagraphStyle('kpi_value', fontName='Helvetica-Bold', fontSize=14,
                                    textColor=DARK_BLUE, alignment=TA_CENTER),
        'kpi_label': ParagraphStyle('kpi_label', fontName='Helvetica', fontSize=8,
                                    textColor=MED_GRAY, alignment=TA_CENTER),
        'cover_client': ParagraphStyle('cover_client', fontName='Helvetica-Bold', fontSize=20,
                                       textColor=GOLD, alignment=TA_CENTER, spaceAfter=6),
        'cover_date': ParagraphStyle('cover_date', fontName='Helvetica', fontSize=11,
                                     textColor=MED_GRAY, alignment=TA_CENTER),
        'rec_title': ParagraphStyle('rec_title', fontName='Helvetica-Bold', fontSize=11,
                                    textColor=DARK_BLUE, spaceAfter=2),
        'rec_body': ParagraphStyle('rec_body', fontName='Helvetica', fontSize=9,
                                   textColor=colors.black, leading=13, spaceAfter=2),
        'tag': ParagraphStyle('tag', fontName='Helvetica-Bold', fontSize=8,
                              textColor=colors.white, alignment=TA_CENTER),
    }
    return styles


# ═══════════════════════════════════════════════════════════════
# PAGE TEMPLATE WITH HEADER/FOOTER
# ═══════════════════════════════════════════════════════════════

def _make_page_template(doc, page_num: int, total_pages: int, client_name: str):
    def on_page(canvas, document):
        canvas.saveState()
        # Header bar
        canvas.setFillColor(DARK_BLUE)
        canvas.rect(0, PAGE_H - 1.2 * cm, PAGE_W, 1.2 * cm, fill=1, stroke=0)
        canvas.setFillColor(GOLD)
        canvas.setFont('Helvetica-Bold', 11)
        canvas.drawString(MARGIN, PAGE_H - 0.85 * cm, 'SENTINEL Decision Intelligence')
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.white)
        canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 0.85 * cm,
                               f'{client_name}  |  Confidencial')
        # Gold accent line
        canvas.setStrokeColor(GOLD)
        canvas.setLineWidth(2)
        canvas.line(0, PAGE_H - 1.2 * cm, PAGE_W, PAGE_H - 1.2 * cm)
        # Footer
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(MED_GRAY)
        canvas.drawString(MARGIN, 0.7 * cm, '© 2026 Evangelista & Co.  —  Documento Confidencial')
        canvas.drawRightString(PAGE_W - MARGIN, 0.7 * cm,
                               f'Página {document.page}')
        canvas.setStrokeColor(LIGHT_GRAY)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, 1.1 * cm, PAGE_W - MARGIN, 1.1 * cm)
        canvas.restoreState()
    return on_page


# ═══════════════════════════════════════════════════════════════
# TABLE STYLES
# ═══════════════════════════════════════════════════════════════

def _stats_table_style():
    return TableStyle([
        ('BACKGROUND',   (0, 0), (-1, 0), DARK_BLUE),
        ('TEXTCOLOR',    (0, 0), (-1, 0), colors.white),
        ('FONTNAME',     (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',     (0, 0), (-1, 0), 9),
        ('ALIGN',        (0, 0), (-1, -1), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_GRAY, colors.white]),
        ('FONTNAME',     (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',     (0, 1), (-1, -1), 9),
        ('GRID',         (0, 0), (-1, -1), 0.3, colors.HexColor('#CCCCCC')),
        ('TOPPADDING',   (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
    ])


def _rec_table_style():
    return TableStyle([
        ('BACKGROUND',   (0, 0), (-1, 0), MID_BLUE),
        ('TEXTCOLOR',    (0, 0), (-1, 0), colors.white),
        ('FONTNAME',     (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',     (0, 0), (-1, 0), 9),
        ('ALIGN',        (0, 0), (0, -1), 'CENTER'),
        ('ALIGN',        (1, 1), (-1, -1), 'LEFT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_GRAY, colors.white]),
        ('FONTNAME',     (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',     (0, 1), (-1, -1), 9),
        ('GRID',         (0, 0), (-1, -1), 0.3, colors.HexColor('#CCCCCC')),
        ('TOPPADDING',   (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
        ('WORDWRAP',     (0, 0), (-1, -1), True),
    ])


# ═══════════════════════════════════════════════════════════════
# PDF GENERATOR CLASS — SPEC 6.1
# ═══════════════════════════════════════════════════════════════

class PDFGenerator:
    """
    Genera reportes ejecutivos PDF de Decision Intelligence.

    Sections:
      1. Cover page
      2. Executive Summary (Health Score + Briefing)
      3. Financial Overview (Monte Carlo stats)
      4. Strategic Recommendations
      5. Risk Analysis
      6. Action Plan (Next Steps)
    """

    def __init__(
        self,
        client_name: str,
        stats: Dict,
        sensitivity=None,
        dashboard: Dict = None,
        strategic_analysis: Dict = None,
        recommendations: List[Dict] = None,
        business_narrative=None,
        industry: str = 'General',
    ):
        self.client_name = client_name
        self.stats = stats
        self.sensitivity = sensitivity
        self.dashboard = dashboard or {}
        self.strategic = strategic_analysis or {}
        self.recommendations = recommendations or []
        self.business_narrative = business_narrative
        self.industry = industry
        self.styles = build_styles()
        self.generated_at = datetime.now().strftime('%d de %B de %Y, %H:%M')

    def generate(self) -> bytes:
        """Genera el PDF y retorna bytes para descarga en Streamlit."""
        buffer = io.BytesIO()
        doc = BaseDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=MARGIN,
            rightMargin=MARGIN,
            topMargin=2.0 * cm,
            bottomMargin=1.8 * cm,
            title=f'Decision Intelligence Report — {self.client_name}',
            author='Evangelista & Co.',
        )

        on_page = _make_page_template(doc, 1, 1, self.client_name)
        frame = Frame(MARGIN, 1.8 * cm, PAGE_W - 2 * MARGIN, PAGE_H - 4.0 * cm, id='main')
        template = PageTemplate(id='main', frames=[frame], onPage=on_page)
        doc.addPageTemplates([template])

        story = []
        story += self._cover_page()
        story += self._executive_summary()
        story += self._financial_overview()
        story += self._strategic_recommendations()
        story += self._risk_analysis()
        story += self._action_plan()
        story += self._appendix_sensitivity()

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    # ──────────────────────────────────────────────────────────────────────
    # SECTIONS
    # ──────────────────────────────────────────────────────────────────────

    def _cover_page(self) -> list:
        s = self.styles
        story = [Spacer(1, 3 * cm)]

        # Gold top bar (visual)
        story.append(HRFlowable(width='100%', thickness=4, color=GOLD, spaceAfter=20))

        story.append(Paragraph('DECISION INTELLIGENCE REPORT', s['title']))
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph(self.client_name, s['cover_client']))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f'Industria: {self.industry}', s['subtitle']))
        story.append(Spacer(1, 1.5 * cm))

        # Health score en portada si existe
        score = self.dashboard.get('health_score')
        level = self.dashboard.get('health_level', {})
        if score is not None:
            story.append(HealthScoreBox(score, level.get('label', ''), level.get('color', '#1A1A2E')))
            story.append(Spacer(1, 0.5 * cm))
            story.append(Paragraph(level.get('message', ''), s['body']))

        story.append(Spacer(1, 2 * cm))
        story.append(HRFlowable(width='100%', thickness=1, color=GOLD, spaceAfter=10))
        story.append(Paragraph(f'Generado el {self.generated_at}', s['cover_date']))
        story.append(Paragraph('Evangelista & Co.  —  Documento Confidencial', s['cover_date']))

        story.append(PageBreak())
        return story

    def _executive_summary(self) -> list:
        s = self.styles
        story = [SectionHeader('1. RESUMEN EJECUTIVO'), Spacer(1, 0.4 * cm)]

        briefing = self.dashboard.get('executive_briefing', [])
        if briefing:
            for i, point in enumerate(briefing, 1):
                story.append(Paragraph(f'<b>{i}.</b> {point}', s['bullet']))
            story.append(Spacer(1, 0.3 * cm))

        # Narrative del Business Translator
        if self.business_narrative:
            if isinstance(self.business_narrative, dict):
                narrative_text = self.business_narrative.get('executive_summary', '')
                confidence = self.business_narrative.get('confidence_level', '')
                if confidence:
                    story.append(Paragraph(f'<i>{confidence}</i>', s['small']))
            else:
                narrative_text = str(self.business_narrative)
            if narrative_text:
                story.append(Paragraph(narrative_text, s['body']))

        # Strategic headline
        sa_summary = self.strategic.get('executive_summary', {})
        if sa_summary.get('headline'):
            story.append(Spacer(1, 0.3 * cm))
            story.append(Paragraph(f'<b>Valoracion estrategica:</b> {sa_summary["headline"]}', s['body_bold']))
            if sa_summary.get('key_message'):
                story.append(Paragraph(sa_summary['key_message'], s['body']))

        # Executive KPIs table
        exec_kpis = self.dashboard.get('executive_kpis', [])
        if exec_kpis:
            story.append(Spacer(1, 0.4 * cm))
            story.append(Paragraph('<b>Indicadores Ejecutivos</b>', s['body_bold']))
            story.append(Spacer(1, 0.2 * cm))

            STATUS_SYMBOLS = {'green': '● BIEN', 'yellow': '◑ ATENCIÓN', 'red': '○ RIESGO'}
            kpi_data = [['Indicador', 'Valor', 'Detalle', 'Estado']]
            for kpi in exec_kpis:
                status_text = STATUS_SYMBOLS.get(kpi['status'], '—')
                kpi_data.append([
                    kpi['name'], kpi['value'], kpi['detail'], status_text
                ])

            kpi_table = Table(kpi_data, colWidths=[5 * cm, 3 * cm, 5.5 * cm, 3 * cm])
            ts = _stats_table_style()
            # Color rows by status
            for row_idx, kpi in enumerate(exec_kpis, 1):
                color_map = {'green': GREEN_OK, 'yellow': YELLOW_WARN, 'red': RED_CRIT}
                cell_color = color_map.get(kpi['status'], MED_GRAY)
                ts.add('TEXTCOLOR', (3, row_idx), (3, row_idx), cell_color)
                ts.add('FONTNAME',  (3, row_idx), (3, row_idx), 'Helvetica-Bold')
            kpi_table.setStyle(ts)
            story.append(kpi_table)

        story.append(PageBreak())
        return story

    def _financial_overview(self) -> list:
        s = self.styles
        story = [SectionHeader('2. PANORAMA FINANCIERO — MONTE CARLO'), Spacer(1, 0.4 * cm)]

        stats = self.stats
        mean = stats.get('mean', 0)
        std  = stats.get('std', 0)
        cv   = abs(std / mean) if mean != 0 else 0

        story.append(Paragraph(
            f'Basado en <b>10,000 simulaciones Monte Carlo</b>. Los resultados representan '
            f'la distribucion de probabilidad de los resultados financieros del negocio.',
            s['body']
        ))
        story.append(Spacer(1, 0.4 * cm))

        # Percentiles table
        perc_data = [
            ['Escenario', 'Probabilidad', 'Resultado', 'Interpretacion'],
            ['P10  (Pesimista)',   '10%', f"${stats.get('p10', 0):,.0f}",
             'El 10% peor de escenarios'],
            ['P25',               '25%', f"${stats.get('p25', 0):,.0f}",
             'Cuartil inferior'],
            ['P50  (Base)',        '50%', f"${stats.get('p50', mean):,.0f}",
             'Resultado mas probable'],
            ['P75',               '75%', f"${stats.get('p75', 0):,.0f}",
             'Cuartil superior'],
            ['P90  (Optimista)',  '10%', f"${stats.get('p90', 0):,.0f}",
             'El 10% mejor de escenarios'],
        ]

        perc_table = Table(perc_data, colWidths=[4 * cm, 2.5 * cm, 3.5 * cm, 6.5 * cm])
        ts = _stats_table_style()
        # Highlight base case row (P50 = row 3)
        ts.add('FONTNAME',   (0, 3), (-1, 3), 'Helvetica-Bold')
        ts.add('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#E8F4FD'))
        perc_table.setStyle(ts)
        story.append(perc_table)
        story.append(Spacer(1, 0.4 * cm))

        # Risk metrics table
        prob_loss = stats.get('prob_loss', 0)
        var_95    = stats.get('var_95', 0)
        cvar_95   = stats.get('cvar_95', 0)

        risk_data = [
            ['Metrica de Riesgo', 'Valor', 'Significado'],
            ['Probabilidad de Perdida', f'{prob_loss:.1%}',
             'Probabilidad de resultado negativo'],
            ['VaR 95%', f'${abs(var_95):,.0f}',
             'Perdida maxima esperada en 95% de escenarios'],
            ['CVaR 95% (Expected Shortfall)', f'${abs(cvar_95):,.0f}',
             'Perdida promedio en el 5% peor de casos'],
            ['Coeficiente de Variacion', f'{cv:.1%}',
             'Volatilidad relativa al resultado esperado'],
        ]
        risk_table = Table(risk_data, colWidths=[5 * cm, 3 * cm, 8.5 * cm])
        risk_table.setStyle(_stats_table_style())
        story.append(risk_table)

        story.append(PageBreak())
        return story

    def _strategic_recommendations(self) -> list:
        s = self.styles
        story = [SectionHeader('3. RECOMENDACIONES ESTRATEGICAS'), Spacer(1, 0.4 * cm)]

        # Strategic Advisor recommendations (Fase 5)
        sa_recs = self.strategic.get('strategic_recommendations', [])
        if sa_recs:
            story.append(Paragraph(
                'Recomendaciones generadas por el Motor de Inteligencia Estrategica (Llama 3.3-70B).',
                s['small']
            ))
            story.append(Spacer(1, 0.3 * cm))

            for rec in sa_recs:
                priority = rec.get('priority', '?')
                title    = rec.get('title', '')
                rationale = rec.get('rationale', '')
                impact   = rec.get('expected_impact', '')
                horizon  = rec.get('implementation_horizon', '')
                conf     = rec.get('confidence', '')
                actions  = rec.get('action_items', [])

                # Rec header
                story.append(Paragraph(f'#{priority} — {title}', s['rec_title']))
                story.append(Paragraph(f'<i>Horizonte: {horizon}  |  Confianza: {conf}</i>', s['small']))
                story.append(Spacer(1, 0.1 * cm))
                story.append(Paragraph(rationale, s['rec_body']))
                if impact:
                    story.append(Paragraph(f'<b>Impacto esperado:</b> {impact}', s['rec_body']))
                if actions:
                    story.append(Paragraph('<b>Plan de accion:</b>', s['rec_body']))
                    for act in actions:
                        story.append(Paragraph(f'• {act}', s['bullet']))
                story.append(HRFlowable(width='100%', thickness=0.5,
                                        color=colors.HexColor('#DDDDDD'), spaceAfter=6))

        # Fallback: Fase 4 recommendations (reglas del YAML)
        elif self.recommendations:
            story.append(Paragraph(
                'Recomendaciones generadas por el Motor de Decision Intelligence (reglas del YAML).',
                s['small']
            ))
            story.append(Spacer(1, 0.3 * cm))

            rec_data = [['#', 'Estrategia', 'Acciones Principales']]
            for rec in self.recommendations:
                actions = rec.get('actions', [])
                actions_text = '\n'.join(
                    f"• {a['action']}" for a in actions[:3] if isinstance(a, dict)
                )
                rec_data.append([
                    str(rec.get('priority', '?')),
                    rec.get('title', ''),
                    actions_text,
                ])

            rec_table = Table(rec_data, colWidths=[1 * cm, 5 * cm, 10.5 * cm])
            rec_table.setStyle(_rec_table_style())
            story.append(rec_table)

        else:
            story.append(Paragraph('No se generaron recomendaciones estrategicas.', s['body']))

        story.append(PageBreak())
        return story

    def _risk_analysis(self) -> list:
        s = self.styles
        story = [SectionHeader('4. ANALISIS DE RIESGOS'), Spacer(1, 0.4 * cm)]

        risk_analysis = self.strategic.get('risk_analysis', {})
        primary_risks = risk_analysis.get('primary_risks', [])
        scenario_analysis = risk_analysis.get('scenario_analysis', {})

        if primary_risks:
            risk_data = [['Riesgo', 'Probabilidad', 'Impacto', 'Mitigacion']]
            for r in primary_risks:
                risk_data.append([
                    r.get('risk', ''),
                    r.get('probability', ''),
                    r.get('impact', ''),
                    r.get('mitigation', ''),
                ])
            risk_table = Table(risk_data,
                               colWidths=[4.5 * cm, 2.5 * cm, 2.5 * cm, 7 * cm])
            risk_table.setStyle(_stats_table_style())
            story.append(risk_table)
            story.append(Spacer(1, 0.5 * cm))

        if scenario_analysis:
            story.append(Paragraph('<b>Analisis de Escenarios</b>', s['body_bold']))
            story.append(Spacer(1, 0.2 * cm))

            scenarios = [
                ('Escenario Pesimista (Bear Case)', scenario_analysis.get('bear_case', ''), RED_CRIT),
                ('Escenario Base (Base Case)',       scenario_analysis.get('base_case', ''), GOLD),
                ('Escenario Optimista (Bull Case)', scenario_analysis.get('bull_case', ''), GREEN_OK),
            ]
            scen_data = [['Escenario', 'Descripcion']]
            for label, desc, _ in scenarios:
                scen_data.append([label, desc])

            scen_table = Table(scen_data, colWidths=[5 * cm, 11.5 * cm])
            ts = _stats_table_style()
            for i, (_, _, c) in enumerate(scenarios, 1):
                ts.add('TEXTCOLOR', (0, i), (0, i), c)
                ts.add('FONTNAME',  (0, i), (0, i), 'Helvetica-Bold')
            scen_table.setStyle(ts)
            story.append(scen_table)

        if not primary_risks and not scenario_analysis:
            stats = self.stats
            story.append(Paragraph(
                f'Probabilidad de perdida: <b>{stats.get("prob_loss", 0):.1%}</b>. '
                f'VaR 95%: <b>${abs(stats.get("var_95", 0)):,.0f}</b>. '
                f'Escenario pesimista P10: <b>${stats.get("p10", 0):,.0f}</b>.',
                s['body']
            ))

        story.append(PageBreak())
        return story

    def _action_plan(self) -> list:
        s = self.styles
        story = [SectionHeader('5. PLAN DE ACCION'), Spacer(1, 0.4 * cm)]

        next_steps = self.strategic.get('next_steps', {})
        highlights = self.dashboard.get('strategic_highlights', [])

        if highlights:
            story.append(Paragraph('<b>Acciones Inmediatas (Executive View)</b>', s['body_bold']))
            for h in highlights:
                story.append(Paragraph(f'{h["icon"]} {h["text"]}', s['bullet']))
            story.append(Spacer(1, 0.4 * cm))

        horizons = [
            ('Esta Semana', next_steps.get('this_week', []), GREEN_OK),
            ('Este Mes',    next_steps.get('this_month', []), GOLD),
            ('Este Trimestre', next_steps.get('this_quarter', []), MID_BLUE),
        ]

        has_steps = any(steps for _, steps, _ in horizons)
        if has_steps:
            story.append(Paragraph('<b>Cronograma de Ejecucion</b>', s['body_bold']))
            story.append(Spacer(1, 0.2 * cm))

            plan_data = [['Horizonte', 'Acciones']]
            for label, steps, _ in horizons:
                if steps:
                    steps_text = '\n'.join(f'• {step}' for step in steps)
                    plan_data.append([label, steps_text])

            if len(plan_data) > 1:
                plan_table = Table(plan_data, colWidths=[3.5 * cm, 13 * cm])
                ts = _stats_table_style()
                for i, (_, _, c) in enumerate(
                    [(l, st, c) for l, st, c in horizons if st], 1
                ):
                    ts.add('TEXTCOLOR', (0, i), (0, i), c)
                    ts.add('FONTNAME',  (0, i), (0, i), 'Helvetica-Bold')
                plan_table.setStyle(ts)
                story.append(plan_table)

        if not has_steps and not highlights:
            story.append(Paragraph(
                'No se generaron pasos de accion especificos. Consulte con su equipo de Evangelista & Co.',
                s['body']
            ))

        story.append(PageBreak())
        return story

    def _appendix_sensitivity(self) -> list:
        s = self.styles
        story = [SectionHeader('APÉNDICE — ANALISIS DE SENSIBILIDAD'), Spacer(1, 0.4 * cm)]

        story.append(Paragraph(
            'Variables con mayor impacto en la varianza del resultado. '
            'Enfocar esfuerzos de gestion de riesgo en estas variables maximiza el impacto.',
            s['body']
        ))
        story.append(Spacer(1, 0.3 * cm))

        if self.sensitivity is not None:
            try:
                import pandas as pd
                if hasattr(self.sensitivity, 'iterrows'):
                    sens_data = [['Variable', 'Importancia', 'Impacto Relativo']]
                    for _, row in self.sensitivity.head(10).iterrows():
                        importance = row.get('importance', 0)
                        bar_len = int(importance * 20)
                        bar = '█' * bar_len + '░' * (20 - bar_len)
                        sens_data.append([
                            row.get('variable', ''),
                            f'{importance:.1%}',
                            bar,
                        ])
                    sens_table = Table(sens_data, colWidths=[6 * cm, 2.5 * cm, 8 * cm])
                    sens_table.setStyle(_stats_table_style())
                    story.append(sens_table)
                elif isinstance(self.sensitivity, dict):
                    sorted_items = sorted(self.sensitivity.items(),
                                          key=lambda x: abs(x[1]), reverse=True)[:10]
                    sens_data = [['Variable', 'Impacto']]
                    for var, impact in sorted_items:
                        sens_data.append([var, f'{impact:.4f}'])
                    sens_table = Table(sens_data, colWidths=[10 * cm, 6.5 * cm])
                    sens_table.setStyle(_stats_table_style())
                    story.append(sens_table)
            except Exception:
                story.append(Paragraph('Datos de sensibilidad no disponibles.', s['body']))
        else:
            story.append(Paragraph('Analisis de sensibilidad no disponible para este reporte.', s['body']))

        story.append(Spacer(1, 1 * cm))
        story.append(HRFlowable(width='100%', thickness=1, color=GOLD))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(
            f'Reporte generado automaticamente por Sentinel Decision Intelligence Platform. '
            f'Evangelista & Co. — {self.generated_at}. Documento Confidencial.',
            s['small']
        ))

        return story
