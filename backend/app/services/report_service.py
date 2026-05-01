from fpdf import FPDF
from datetime import datetime
from typing import List, Dict, Any
import os

class SecurityReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Trusyn Brand Protection - Security Report', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()} | Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 0, 'C')

class ReportService:
    def __init__(self, output_path: str = "storage/reports"):
        self.output_path = output_path
        os.makedirs(self.output_path, exist_ok=True)

    def generate_brand_report(self, brand_name: str, incidents: List[Dict[str, Any]]) -> str:
        """
        Generates a PDF report for a specific brand's incidents.
        """
        pdf = SecurityReport()
        pdf.add_page()
        
        # Summary Section
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, f'Report for: {brand_name}', 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, f'Total Incidents Analyzed: {len(incidents)}', 0, 1)
        pdf.ln(5)

        # Incident List
        pdf.set_font('Arial', 'B', 11)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(80, 10, 'Target URL', 1, 0, 'C', True)
        pdf.cell(40, 10, 'Type', 1, 0, 'C', True)
        pdf.cell(30, 10, 'Status', 1, 0, 'C', True)
        pdf.cell(40, 10, 'Confidence', 1, 1, 'C', True)

        pdf.set_font('Arial', '', 9)
        for inc in incidents:
            # Shorten URL if too long
            url = inc['target_url'][:40] + '...' if len(inc['target_url']) > 40 else inc['target_url']
            pdf.cell(80, 10, url, 1)
            pdf.cell(40, 10, str(inc.get('threat_type', 'N/A')), 1)
            pdf.cell(30, 10, str(inc['status']), 1)
            pdf.cell(40, 10, f"{float(inc.get('confidence_score', 0))*100:.1f}%", 1, 1)

        filename = f"Report_{brand_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(self.output_path, filename)
        pdf.output(filepath)
        
        return filepath

report_service = ReportService()
