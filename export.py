import io
import pandas as pd
import xlsxwriter
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def export_to_excel(analysis_data):
    """
    Export analysis data to Excel format
    
    Args:
        analysis_data (dict): Dictionary containing analysis data
        
    Returns:
        bytes: Excel file as bytes
    """
    # Create a BytesIO object to store the Excel file
    output = io.BytesIO()
    
    # Create Excel workbook and worksheet
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('Analysis Results')
    
    # Define styles
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#4B8BBE',  # Light blue background for headers
        'font_color': 'white',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': True
    })
    
    metric_format = workbook.add_format({
        'bg_color': '#F0F0F0',
        'border': 1,
        'align': 'left',
        'valign': 'vcenter'
    })
    
    value_format = workbook.add_format({
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'num_format': '#,##0.00'
    })
    
    percent_format = workbook.add_format({
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'num_format': '0.00%'
    })
    
    integer_format = workbook.add_format({
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'num_format': '#,##0'
    })
    
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 14,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    subtitle_format = workbook.add_format({
        'bold': True,
        'font_size': 12,
        'align': 'left',
        'valign': 'vcenter',
        'bg_color': '#EEEEEE'
    })
    
    # Set column widths
    worksheet.set_column('A:A', 25)
    worksheet.set_column('B:D', 15)
    
    # Extract data from analysis_data
    website_url = analysis_data.get('website_url', '')
    budget = analysis_data.get('budget', 0)
    business_type = analysis_data.get('business_type', '')
    
    base_case = analysis_data.get('base_case', {})
    pessimistic_case = analysis_data.get('pessimistic_case', {})
    optimistic_case = analysis_data.get('optimistic_case', {})
    
    # Write title
    row = 0
    worksheet.merge_range('A1:D1', f'Google Ads Budget Analysis for {website_url}', title_format)
    row += 1
    
    # Write input parameters
    worksheet.merge_range(f'A{row+1}:D{row+1}', 'Input Parameters', subtitle_format)
    row += 1
    
    worksheet.write(row, 0, 'Budget (UAH)', metric_format)
    worksheet.write(row, 1, budget, value_format)
    row += 1
    
    worksheet.write(row, 0, 'Business Type', metric_format)
    worksheet.write(row, 1, 'E-commerce' if business_type == 'ecommerce' else 'Services', value_format)
    row += 1
    
    worksheet.write(row, 0, 'Website URL', metric_format)
    worksheet.write(row, 1, website_url, value_format)
    row += 2  # Add an empty row
    
    # Write scenario analysis
    worksheet.merge_range(f'A{row+1}:D{row+1}', 'Scenario Analysis', subtitle_format)
    row += 1
    
    # Headers for scenario table
    headers = ['Metric', 'Pessimistic', 'Expected', 'Optimistic']
    for col, header in enumerate(headers):
        worksheet.write(row, col, header, header_format)
    row += 1
    
    # Scenario data
    metrics = [
        {'name': 'Clicks', 'fields': 'clicks', 'format': integer_format},
        {'name': 'Impressions', 'fields': 'impressions', 'format': integer_format},
        {'name': 'Conversions', 'fields': 'conversions', 'format': integer_format},
        {'name': 'Cost Per Click (UAH)', 'fields': 'avg_cpc', 'format': value_format},
        {'name': 'CTR', 'fields': 'ctr', 'format': percent_format},
        {'name': 'Conversion Rate', 'fields': 'conversion_rate', 'format': percent_format},
        {'name': 'Cost Per Conversion (UAH)', 'fields': 'cost_per_conversion', 'format': value_format},
        {'name': 'Revenue (UAH)', 'fields': 'revenue', 'format': value_format},
        {'name': 'ROI', 'fields': 'roi', 'format': percent_format},
        {'name': 'ROAS', 'fields': 'roas', 'format': value_format}
    ]
    
    for metric in metrics:
        worksheet.write(row, 0, metric['name'], metric_format)
        worksheet.write(row, 1, pessimistic_case.get(metric['fields'], 0), metric['format'])
        worksheet.write(row, 2, base_case.get(metric['fields'], 0), metric['format'])
        worksheet.write(row, 3, optimistic_case.get(metric['fields'], 0), metric['format'])
        row += 1
        
    # Add notes section if available
    notes = analysis_data.get('notes')
    if notes:
        row += 1
        worksheet.merge_range(f'A{row+1}:D{row+1}', 'Notes', subtitle_format)
        row += 1
        worksheet.merge_range(f'A{row+1}:D{row+3}', notes, workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'top',
            'text_wrap': True
        }))
        row += 4
    
    # Add footer
    row += 1
    worksheet.merge_range(f'A{row+1}:D{row+1}', 'Google Ads Budget Analysis Tool | Ukrainian Hryvnia (UAH) Calculator', 
                        workbook.add_format({
                            'align': 'center',
                            'valign': 'vcenter',
                            'font_color': '#666666',
                            'font_size': 8
                        }))
    
    # Close the workbook to write the data
    workbook.close()
    
    # Reset the file pointer to the beginning
    output.seek(0)
    
    return output.getvalue()

def export_to_pdf(analysis_data):
    """
    Export analysis data to PDF format
    
    Args:
        analysis_data (dict): Dictionary containing analysis data
        
    Returns:
        bytes: PDF file as bytes
    """
    # Create a BytesIO object to store the PDF
    buffer = io.BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Create a custom style for the title
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        alignment=1,  # Center alignment
        spaceAfter=12
    )
    
    # Create a custom style for section headers
    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        alignment=0,  # Left alignment
        spaceBefore=12,
        spaceAfter=6,
        backColor=colors.lightgrey,
        borderPadding=5
    )
    
    # Create a list of flowables for the document
    elements = []
    
    # Extract data
    website_url = analysis_data.get('website_url', '')
    budget = analysis_data.get('budget', 0)
    business_type = analysis_data.get('business_type', '')
    
    base_case = analysis_data.get('base_case', {})
    pessimistic_case = analysis_data.get('pessimistic_case', {})
    optimistic_case = analysis_data.get('optimistic_case', {})
    
    # Add title
    elements.append(Paragraph(f'Google Ads Budget Analysis for {website_url}', title_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add input parameters section
    elements.append(Paragraph('Input Parameters', section_header_style))
    
    input_data = [
        ['Parameter', 'Value'],
        ['Budget (UAH)', f"{budget:,.2f}"],
        ['Business Type', 'E-commerce' if business_type == 'ecommerce' else 'Services'],
        ['Website URL', website_url]
    ]
    
    # Create the input parameters table
    input_table = Table(input_data, colWidths=[2.5*inch, 3*inch])
    input_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (1, 0), 12),
        ('BACKGROUND', (0, 1), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT')
    ]))
    
    elements.append(input_table)
    elements.append(Spacer(1, 0.25*inch))
    
    # Add scenario analysis section
    elements.append(Paragraph('Scenario Analysis', section_header_style))
    
    # Create the scenario data
    scenario_data = [
        ['Metric', 'Pessimistic', 'Expected', 'Optimistic']
    ]
    
    metrics = [
        {'name': 'Clicks', 'field': 'clicks', 'format': lambda x: f"{int(x):,}"},
        {'name': 'Impressions', 'field': 'impressions', 'format': lambda x: f"{int(x):,}"},
        {'name': 'Conversions', 'field': 'conversions', 'format': lambda x: f"{int(x):,}"},
        {'name': 'Cost Per Click (UAH)', 'field': 'avg_cpc', 'format': lambda x: f"{x:,.2f}"},
        {'name': 'CTR', 'field': 'ctr', 'format': lambda x: f"{x*100:.2f}%"},
        {'name': 'Conversion Rate', 'field': 'conversion_rate', 'format': lambda x: f"{x*100:.2f}%"},
        {'name': 'Cost Per Conversion (UAH)', 'field': 'cost_per_conversion', 'format': lambda x: f"{x:,.2f}"},
        {'name': 'Revenue (UAH)', 'field': 'revenue', 'format': lambda x: f"{x:,.2f}"},
        {'name': 'ROI', 'field': 'roi', 'format': lambda x: f"{x*100:.2f}%"},
        {'name': 'ROAS', 'field': 'roas', 'format': lambda x: f"{x:.2f}x"}
    ]
    
    for metric in metrics:
        row = [
            metric['name'],
            metric['format'](pessimistic_case.get(metric['field'], 0)),
            metric['format'](base_case.get(metric['field'], 0)),
            metric['format'](optimistic_case.get(metric['field'], 0))
        ]
        scenario_data.append(row)
    
    # Create the scenario table
    scenario_table = Table(scenario_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    scenario_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT')
    ]))
    
    elements.append(scenario_table)
    elements.append(Spacer(1, 0.25*inch))
    
    # Add notes section if available
    notes = analysis_data.get('notes')
    if notes:
        elements.append(Paragraph('Notes', section_header_style))
        elements.append(Paragraph(notes, styles['Normal']))
        elements.append(Spacer(1, 0.25*inch))
    
    # Add disclaimer
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey
    )
    
    disclaimer_text = """
    Note: These projections are estimates based on industry averages and the parameters you've provided.
    Actual campaign performance may vary based on numerous factors including ad quality, targeting, 
    market conditions, and competition. For best results, continuously monitor and optimize your 
    campaigns based on real performance data.
    """
    
    elements.append(Paragraph(disclaimer_text, disclaimer_style))
    
    # Add footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        alignment=1,  # Center alignment
        fontSize=8,
        textColor=colors.grey
    )
    
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph('Google Ads Budget Analysis Tool | Ukrainian Hryvnia (UAH) Calculator', footer_style))
    
    # Build the PDF document
    doc.build(elements)
    
    # Get the value of the BytesIO buffer
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data