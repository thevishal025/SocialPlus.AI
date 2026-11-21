import os
import io
import json
import csv
from typing import Dict, Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

import html
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


class ReportGenerator:
    """Generates professional reports in PDF, HTML, CSV, Excel, and JSON formats."""

    @staticmethod
    def generate_pdf(data: Dict[str, Any], output_path: str) -> str:
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=14
        )
        h2_style = ParagraphStyle(
            "H2Heading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=12,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#334155")
        )
        body_bold = ParagraphStyle(
            "BodyBold",
            parent=body_style,
            fontName="Helvetica-Bold"
        )

        elements = []

        # Title & Subtitle
        elements.append(Paragraph("SocialPlus.ai — Intelligence Report", title_style))
        platform_name = str(data.get("platform", "General")).upper()
        gen_date = str(data.get("created_at", "N/A"))
        elements.append(Paragraph(
            f"<b>Platform:</b> {platform_name} &nbsp;|&nbsp; <b>Date:</b> {gen_date} &nbsp;|&nbsp; <b>Title:</b> {data.get('title', 'Analysis')}",
            subtitle_style
        ))
        elements.append(Spacer(1, 10))

        # KPI Summary Table
        summary = data.get("summary", {})
        total_comments = data.get("comment_count", 0)
        sent_dist = summary.get("sentiment_distribution", {})
        avg_conf = summary.get("average_confidence", 0.0)
        avg_rating = summary.get("average_rating")

        kpi_data = [
            [
                Paragraph("<b>Total Comments</b>", body_style),
                Paragraph("<b>Dominant Sentiment</b>", body_style),
                Paragraph("<b>Avg Confidence</b>", body_style),
                Paragraph("<b>Avg Rating</b>", body_style)
            ],
            [
                Paragraph(f"<font size=12><b>{total_comments}</b></font>", body_style),
                Paragraph(f"<font size=12 color='#059669'><b>Positive ({sent_dist.get('Positive', 0)}%)</b></font>", body_style),
                Paragraph(f"<font size=12><b>{int(avg_conf * 100)}%</b></font>", body_style),
                Paragraph(f"<font size=12><b>{f'{avg_rating} / 5' if avg_rating else 'N/A'}</b></font>", body_style)
            ]
        ]
        kpi_table = Table(kpi_data, colWidths=[130, 150, 120, 120])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 14))

        # Sentiment Breakdown
        elements.append(Paragraph("Sentiment Breakdown", h2_style))
        sent_rows = [
            [Paragraph("<b>Category</b>", body_bold), Paragraph("<b>Percentage</b>", body_bold), Paragraph("<b>Count</b>", body_bold)]
        ]
        sent_counts = summary.get("sentiment_counts", {})
        for cat in ["Positive", "Negative", "Neutral", "Mixed", "Sarcastic"]:
            pct = sent_dist.get(cat, 0.0)
            cnt = sent_counts.get(cat, 0)
            sent_rows.append([
                Paragraph(cat, body_style),
                Paragraph(f"{pct}%", body_style),
                Paragraph(str(cnt), body_style)
            ])
        sent_table = Table(sent_rows, colWidths=[200, 150, 150])
        sent_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(sent_table)
        elements.append(Spacer(1, 14))

        # Emotion & Intent Overview
        elements.append(Paragraph("Emotional & Intent Intelligence", h2_style))
        emo_dist = summary.get("emotion_distribution", {})
        intent_dist = summary.get("intent_distribution", {})

        top_emotions = ", ".join([f"{k} ({v.get('percentage')}%)" for k, v in list(emo_dist.items())[:5]])
        top_intents = ", ".join([f"{k} ({v.get('percentage')}%)" for k, v in list(intent_dist.items())[:5]])

        ei_rows = [
            [Paragraph("<b>Top Detected Emotions:</b>", body_bold), Paragraph(top_emotions or "None", body_style)],
            [Paragraph("<b>Top Comment Intents:</b>", body_bold), Paragraph(top_intents or "None", body_style)]
        ]
        ei_table = Table(ei_rows, colWidths=[160, 360])
        ei_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(ei_table)
        elements.append(Spacer(1, 14))

        # Moderation Intelligence
        elements.append(Paragraph("Auto-Moderation & Safety Analysis", h2_style))
        mod_dist = summary.get("moderation_distribution", {})
        mod_rows = [
            [Paragraph("<b>Status</b>", body_bold), Paragraph("<b>Count</b>", body_bold), Paragraph("<b>Share</b>", body_bold)]
        ]
        for st in ["Safe", "Review Required", "Suspicious", "Spam", "Toxic"]:
            cnt = mod_dist.get(st, 0)
            share = round((cnt / total_comments * 100), 1) if total_comments > 0 else 0
            mod_rows.append([Paragraph(st, body_style), Paragraph(str(cnt), body_style), Paragraph(f"{share}%", body_style)])
        mod_table = Table(mod_rows, colWidths=[180, 160, 160])
        mod_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(mod_table)
        elements.append(Spacer(1, 14))

        # Product Aspects Breakdown (if present)
        aspects_data = data.get("aspects", {}).get("aspects", [])
        if aspects_data:
            elements.append(Paragraph("Product Aspect Feedback", h2_style))
            asp_rows = [
                [Paragraph("<b>Aspect</b>", body_bold), Paragraph("<b>Mentions</b>", body_bold), Paragraph("<b>Positive %</b>", body_bold), Paragraph("<b>Negative %</b>", body_bold)]
            ]
            for asp in aspects_data[:6]:
                asp_rows.append([
                    Paragraph(html.escape(str(asp["aspect"])), body_style),
                    Paragraph(str(asp["mentions"]), body_style),
                    Paragraph(f"{asp['positive_pct']}%", body_style),
                    Paragraph(f"{asp['negative_pct']}%", body_style)
                ])
            asp_table = Table(asp_rows, colWidths=[180, 100, 110, 110])
            asp_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(asp_table)
            elements.append(Spacer(1, 14))

        # Key Representative Comments
        elements.append(Paragraph("Representative Feedback Samples", h2_style))
        sample_rows = [[Paragraph("<b>Author</b>", body_bold), Paragraph("<b>Sentiment</b>", body_bold), Paragraph("<b>Comment Text</b>", body_bold)]]
        
        comments = data.get("comments", [])
        for c in comments[:5]:
            raw_t = c.get("text", "")
            truncated = (raw_t[:120] + "...") if len(raw_t) > 120 else raw_t
            clean_t = html.escape(truncated)
            author_clean = html.escape(c.get("author", "Anonymous")[:18])
            sample_rows.append([
                Paragraph(author_clean, body_style),
                Paragraph(c.get("sentiment", "Neutral"), body_style),
                Paragraph(clean_t, body_style)
            ])
        sample_table = Table(sample_rows, colWidths=[110, 80, 310])
        sample_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(sample_table)

        doc.build(elements)
        return output_path

    @staticmethod
    def generate_html(data: Dict[str, Any]) -> str:
        summary = data.get("summary", {})
        sent_dist = summary.get("sentiment_distribution", {})
        comments = data.get("comments", [])
        aspects = data.get("aspects", {}).get("aspects", [])
        emojis = data.get("emojis", {}).get("top_emojis", [])

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>SocialPlus.ai Report - {data.get('title', 'Analysis')}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f8fafc; color: #1e293b; margin: 0; padding: 40px; }}
    .container {{ max-width: 1000px; margin: 0 auto; background: #fff; padding: 36px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; }}
    h1 {{ font-size: 26px; color: #0f172a; margin-bottom: 6px; }}
    .subtitle {{ color: #64748b; font-size: 14px; margin-bottom: 28px; }}
    .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 30px; }}
    .kpi-card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; text-align: center; }}
    .kpi-val {{ font-size: 24px; font-weight: bold; color: #0f172a; margin-top: 6px; }}
    .kpi-label {{ font-size: 12px; color: #64748b; text-transform: uppercase; font-weight: 600; }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 24px; font-size: 13px; }}
    th, td {{ border: 1px solid #e2e8f0; padding: 10px 14px; text-align: left; }}
    th {{ background: #f1f5f9; font-weight: 600; color: #334155; }}
    .badge {{ display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
    .badge-pos {{ background: #dcfce7; color: #15803d; }}
    .badge-neg {{ background: #fee2e2; color: #b91c1c; }}
    .badge-neu {{ background: #f1f5f9; color: #475569; }}
    .badge-mix {{ background: #fef3c7; color: #b45309; }}
    .badge-sar {{ background: #f3e8ff; color: #7e22ce; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>SocialPlus.ai Intelligence Report</h1>
    <div class="subtitle">Platform: {data.get('platform', 'N/A').upper()} | Date: {data.get('created_at', 'N/A')} | Title: {data.get('title', 'Analysis')}</div>

    <div class="kpi-grid">
      <div class="kpi-card"><div class="kpi-label">Comments Analyzed</div><div class="kpi-val">{data.get('comment_count', 0)}</div></div>
      <div class="kpi-card"><div class="kpi-label">Positive Sentiment</div><div class="kpi-val" style="color:#16a34a">{sent_dist.get('Positive', 0)}%</div></div>
      <div class="kpi-card"><div class="kpi-label">Negative Sentiment</div><div class="kpi-val" style="color:#dc2626">{sent_dist.get('Negative', 0)}%</div></div>
      <div class="kpi-card"><div class="kpi-label">Avg Confidence</div><div class="kpi-val">{int(summary.get('average_confidence', 0.8) * 100)}%</div></div>
    </div>

    <h2>Sentiment Distribution</h2>
    <table>
      <thead><tr><th>Category</th><th>Percentage</th><th>Count</th></tr></thead>
      <tbody>
        <tr><td>Positive</td><td>{sent_dist.get('Positive', 0)}%</td><td>{summary.get('sentiment_counts', {}).get('Positive', 0)}</td></tr>
        <tr><td>Negative</td><td>{sent_dist.get('Negative', 0)}%</td><td>{summary.get('sentiment_counts', {}).get('Negative', 0)}</td></tr>
        <tr><td>Neutral</td><td>{sent_dist.get('Neutral', 0)}%</td><td>{summary.get('sentiment_counts', {}).get('Neutral', 0)}</td></tr>
        <tr><td>Mixed</td><td>{sent_dist.get('Mixed', 0)}%</td><td>{summary.get('sentiment_counts', {}).get('Mixed', 0)}</td></tr>
        <tr><td>Sarcastic</td><td>{sent_dist.get('Sarcastic', 0)}%</td><td>{summary.get('sentiment_counts', {}).get('Sarcastic', 0)}</td></tr>
      </tbody>
    </table>

    <h2>Analyzed Comments Explorer (Sample)</h2>
    <table>
      <thead><tr><th>Author</th><th>Sentiment</th><th>Emotion</th><th>Intent</th><th>Status</th><th>Comment</th></tr></thead>
      <tbody>
"""
        for c in comments[:100]:
            sent = c.get("sentiment", "Neutral")
            cls_map = {"Positive": "badge-pos", "Negative": "badge-neg", "Neutral": "badge-neu", "Mixed": "badge-mix", "Sarcastic": "badge-sar"}
            b_class = cls_map.get(sent, "badge-neu")
            html_content += f"""
        <tr>
          <td><b>{c.get('author', 'Anonymous')}</b></td>
          <td><span class="badge {b_class}">{sent}</span></td>
          <td>{c.get('primary_emotion', 'Neutral')}</td>
          <td>{c.get('intent', 'Feedback')}</td>
          <td>{c.get('moderation_status', 'Safe')}</td>
          <td>{c.get('text', '')}</td>
        </tr>
"""
        html_content += """
      </tbody>
    </table>
  </div>
</body>
</html>
"""
        return html_content

    @staticmethod
    def generate_csv(data: Dict[str, Any]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "ID", "Author", "Comment Text", "Platform", "Date", "Likes", "Rating",
            "Sentiment", "Sentiment Confidence", "Primary Emotion", "Intent",
            "Spam Probability", "Toxicity Score", "Moderation Status"
        ])
        for c in data.get("comments", []):
            writer.writerow([
                c.get("id"),
                c.get("author"),
                c.get("text"),
                c.get("platform"),
                c.get("date"),
                c.get("likes", 0),
                c.get("rating"),
                c.get("sentiment"),
                c.get("sentiment_confidence"),
                c.get("primary_emotion"),
                c.get("intent"),
                c.get("spam_probability"),
                c.get("toxicity_score"),
                c.get("moderation_status")
            ])
        return output.getvalue()

    @staticmethod
    def generate_excel(data: Dict[str, Any], output_path: str) -> str:
        wb = openpyxl.Workbook()

        # Sheet 1: Summary
        ws_sum = wb.active
        ws_sum.title = "Executive Summary"
        ws_sum.append(["SocialPlus.ai Intelligence Report"])
        ws_sum.append(["Platform", data.get("platform", "").upper()])
        ws_sum.append(["Title", data.get("title", "")])
        ws_sum.append(["Created At", data.get("created_at", "")])
        ws_sum.append(["Total Comments", data.get("comment_count", 0)])
        ws_sum.append([])

        summary = data.get("summary", {})
        ws_sum.append(["Sentiment Category", "Percentage", "Count"])
        sent_dist = summary.get("sentiment_distribution", {})
        sent_cnt = summary.get("sentiment_counts", {})
        for cat in ["Positive", "Negative", "Neutral", "Mixed", "Sarcastic"]:
            ws_sum.append([cat, f"{sent_dist.get(cat, 0)}%", sent_cnt.get(cat, 0)])

        # Sheet 2: Comments Data
        ws_comments = wb.create_sheet(title="Comments Intelligence")
        headers = [
            "ID", "Author", "Comment Text", "Platform", "Date", "Likes", "Rating",
            "Sentiment", "Sentiment Confidence", "Primary Emotion", "Intent",
            "Spam Probability", "Toxicity Score", "Moderation Status"
        ]
        ws_comments.append(headers)

        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")

        for col_num in range(1, len(headers) + 1):
            cell = ws_comments.cell(row=1, column=col_num)
            cell.font = header_font
            cell.fill = header_fill

        for c in data.get("comments", []):
            ws_comments.append([
                c.get("id"),
                c.get("author"),
                c.get("text"),
                c.get("platform"),
                c.get("date"),
                c.get("likes", 0),
                c.get("rating"),
                c.get("sentiment"),
                c.get("sentiment_confidence"),
                c.get("primary_emotion"),
                c.get("intent"),
                c.get("spam_probability"),
                c.get("toxicity_score"),
                c.get("moderation_status")
            ])

        wb.save(output_path)
        return output_path

