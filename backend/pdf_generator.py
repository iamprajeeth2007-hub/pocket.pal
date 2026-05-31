import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from typing import List, Dict, Any

def generate_pdf_report(
    expenses: List[Dict[str, Any]],
    limits: List[Dict[str, Any]],
    monthly_income: float,
    health_score_data: Dict[str, Any],
    target_month: str  # YYYY-MM
) -> io.BytesIO:
    """
    Generates a professional financial PDF report using ReportLab.
    Returns a BytesIO stream containing the PDF binary.
    """
    # Parse target month
    try:
        dt = datetime.strptime(target_month, "%Y-%m")
        month_name = dt.strftime("%B %Y")
    except Exception:
        month_name = target_month

    # Filter expenses for target month
    monthly_expenses = [e for e in expenses if e.get("date", "").startswith(target_month)]
    total_expenses = sum(float(e["amount"]) for e in monthly_expenses)
    net_savings = max(0.0, monthly_income - total_expenses)
    savings_pct = (net_savings / monthly_income * 100) if monthly_income > 0 else 0

    # Group expenses by category
    category_totals = {}
    for e in monthly_expenses:
        cat = e["category"]
        category_totals[cat] = category_totals.get(cat, 0.0) + float(e["amount"])

    limit_dict = {l["category"]: float(l["limit_amount"]) for l in limits}

    # Setup document stream
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    story = []
    
    # Styles Setup
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=15
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True
    )
    
    normal_style = ParagraphStyle(
        'NormalText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#334155')
    )

    header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        textColor=colors.white
    )

    bold_cell_style = ParagraphStyle(
        'BoldCell',
        parent=normal_style,
        fontName='Helvetica-Bold'
    )

    # 1. Header Section
    story.append(Paragraph("PocketPal — Monthly Financial Report", title_style))
    story.append(Paragraph(f"Analysis and summary report for <b>{month_name}</b> &bull; Generated on {datetime.now().strftime('%d %b %Y')}", subtitle_style))
    story.append(Spacer(1, 10))

    # 2. Key Metrics Cards (Grid Table)
    score = health_score_data["score"]
    grade = health_score_data["grade"]
    
    metrics_data = [
        [
            Paragraph("<b>Monthly Income</b>", normal_style),
            Paragraph("<b>Total Expenses</b>", normal_style),
            Paragraph("<b>Net Savings</b>", normal_style),
            Paragraph("<b>Financial Health Score</b>", normal_style)
        ],
        [
            Paragraph(f"<font size=14><b>₹{monthly_income:,.2f}</b></font>", bold_cell_style),
            Paragraph(f"<font size=14 color='#EF4444'><b>₹{total_expenses:,.2f}</b></font>", bold_cell_style),
            Paragraph(f"<font size=14 color='#10B981'><b>₹{net_savings:,.2f} ({savings_pct:.1f}%)</b></font>", bold_cell_style),
            Paragraph(f"<font size=14 color='{health_score_data['color']}'><b>{score}/100 ({grade})</b></font>", bold_cell_style)
        ]
    ]
    
    metrics_table = Table(metrics_data, colWidths=[1.8*inch, 1.8*inch, 1.8*inch, 1.8*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 10),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 20))

    # 3. Category Breakdown Section
    story.append(Paragraph("Category Spending & Budget Limits", section_title_style))
    
    cat_rows = [[
        Paragraph("Category", header_style),
        Paragraph("Spent", header_style),
        Paragraph("Budget Limit", header_style),
        Paragraph("Status / Usage", header_style)
    ]]
    
    categories_list = ["Food", "Travel", "Shopping", "Recharge", "Petrol", "Others"]
    for cat in categories_list:
        spent = category_totals.get(cat, 0.0)
        limit = limit_dict.get(cat, 0.0)
        
        limit_text = f"₹{limit:,.2f}" if limit > 0 else "No Limit"
        
        if limit > 0:
            usage_pct = (spent / limit) * 100
            if spent > limit:
                status = f"<font color='#EF4444'><b>Exceeded ({usage_pct:.1f}%)</b></font>"
            else:
                status = f"<font color='#10B981'>Within Limit ({usage_pct:.1f}%)</font>"
        else:
            status = "No Limit Set"
            
        cat_rows.append([
            Paragraph(cat, normal_style),
            Paragraph(f"₹{spent:,.2f}", normal_style),
            Paragraph(limit_text, normal_style),
            Paragraph(status, normal_style)
        ])
        
    cat_table = Table(cat_rows, colWidths=[1.5*inch, 1.8*inch, 1.8*inch, 2.1*inch])
    cat_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(cat_table)
    story.append(Spacer(1, 20))

    # 4. Financial Health Tips
    story.append(Paragraph("Actionable Financial Recommendations", section_title_style))
    tips_content = ""
    for tip in health_score_data["tips"]:
        tips_content += f"&bull; {tip}<br/>"
        
    tips_box = Table([[Paragraph(tips_content, normal_style)]], colWidths=[7.2*inch])
    tips_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EFF6FF')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#BFDBFE')),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(tips_box)
    story.append(Spacer(1, 20))

    # 5. Recent Transactions List
    story.append(Paragraph("Recent Transactions", section_title_style))
    
    tx_rows = [[
        Paragraph("Date", header_style),
        Paragraph("Description", header_style),
        Paragraph("Category", header_style),
        Paragraph("Amount", header_style)
    ]]
    
    sorted_expenses = sorted(monthly_expenses, key=lambda x: x.get("date", ""), reverse=True)[:15]
    if not sorted_expenses:
        tx_rows.append([Paragraph("No transactions recorded for this month.", normal_style), "", "", ""])
    else:
        for tx in sorted_expenses:
            date_str = tx.get("date", "")
            try:
                date_parsed = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d %b %Y")
            except Exception:
                date_parsed = date_str
            tx_rows.append([
                Paragraph(date_parsed, normal_style),
                Paragraph(tx.get("description", ""), normal_style),
                Paragraph(tx.get("category", ""), normal_style),
                Paragraph(f"₹{float(tx['amount']):,.2f}", normal_style)
            ])
            
    tx_table = Table(tx_rows, colWidths=[1.3*inch, 2.6*inch, 1.5*inch, 1.8*inch])
    tx_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#475569')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(tx_table)

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer
