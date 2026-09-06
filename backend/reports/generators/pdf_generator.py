import json
from datetime import datetime
from fpdf import FPDF
from pathlib import Path
from typing import Dict, Any, List

class PDFGenerator(FPDF):
    def __init__(self, title: str):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.report_title = title
        self.add_page()
        
    def header(self):
        # Header text
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, 'VoltGuard', ln=True, align='L')
        self.set_font('helvetica', 'B', 12)
        self.cell(0, 10, 'Physics-Aware ICS/SCADA Security Report', ln=True, align='L')
        self.set_font('helvetica', 'I', 10)
        self.cell(0, 10, self.report_title, ln=True, align='L')
        self.ln(10)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

    def add_section_title(self, title: str):
        self.set_font('helvetica', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 8, title, ln=True, fill=True)
        self.ln(4)

    def add_key_value(self, key: str, value: str):
        self.set_font('helvetica', 'B', 10)
        self.cell(40, 6, key + ":")
        self.set_font('helvetica', '', 10)
        self.multi_cell(0, 6, str(value))

    def add_table_header(self, columns: List[str], widths: List[int]):
        self.set_font('helvetica', 'B', 10)
        for col, width in zip(columns, widths):
            self.cell(width, 8, col, border=1)
        self.ln()

    def add_table_row(self, row: List[str], widths: List[int]):
        self.set_font('helvetica', '', 10)
        for item, width in zip(row, widths):
            self.cell(width, 8, str(item), border=1)
        self.ln()

def generate_report_pdf(metadata: Dict[str, Any], data: Dict[str, Any], output_path: str):
    """
    Generate a professional PDF report.
    """
    title = f"{metadata.get('report_type', 'REPORT').replace('_', ' ')} - {metadata.get('report_id')}"
    pdf = PDFGenerator(title)
    
    # Metadata
    pdf.add_section_title("REPORT METADATA")
    pdf.add_key_value("Report ID", metadata.get('report_id', ''))
    pdf.add_key_value("Generated At", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))
    pdf.add_key_value("Primary Device", metadata.get('primary_device', 'All Devices'))
    pdf.add_key_value("Severity", metadata.get('severity', 'All Severities'))
    pdf.ln(5)

    # Event Details (If specific event)
    if 'event' in data and data['event']:
        evt = data['event']
        pdf.add_section_title("EVENT DETAILS")
        pdf.add_key_value("Event ID", evt.get('id', ''))
        pdf.add_key_value("Timestamp", evt.get('timestamp', ''))
        pdf.add_key_value("Device", evt.get('device', ''))
        pdf.add_key_value("Protocol", evt.get('protocol', ''))
        pdf.add_key_value("Command", evt.get('command', ''))
        pdf.add_key_value("Value", evt.get('command_value', ''))
        pdf.ln(5)

        pdf.add_section_title("PHYSICAL ANALYSIS")
        pdf.add_key_value("Predicted Pressure", f"{evt.get('predicted_pressure', 'N/A')} bar")
        pdf.add_key_value("Predicted Flow", f"{evt.get('predicted_flow', 'N/A')} m3/h")
        pdf.add_key_value("Predicted Temp", f"{evt.get('predicted_temperature', 'N/A')} C")
        pdf.add_key_value("Risk Score", f"{evt.get('risk_score', 'N/A')}")
        pdf.add_key_value("Safety State", f"{evt.get('safety_state', 'N/A')}")
        pdf.ln(5)

        pdf.add_section_title("SECURITY DECISION")
        pdf.add_key_value("Decision", evt.get('decision', 'N/A'))
        pdf.add_key_value("Reason", evt.get('reason', 'N/A'))
        if evt.get('violations'):
            pdf.ln(2)
            pdf.add_key_value("Violations", evt.get('violations', ''))
        if evt.get('explanation'):
            pdf.ln(2)
            pdf.add_key_value("Explanation", evt.get('explanation', ''))
        pdf.ln(5)
        
    elif 'events' in data and data['events']:
        pdf.add_section_title("RECENT EVENTS SUMMARY")
        cols = ["ID", "Time", "Device", "Command", "State", "Decision"]
        widths = [15, 40, 25, 45, 30, 35]
        pdf.add_table_header(cols, widths)
        for evt in data['events']:
            row = [
                str(evt.get('id', '')),
                str(evt.get('timestamp', ''))[:19],
                str(evt.get('device', '')),
                str(evt.get('command', '')) + " " + str(evt.get('command_value', '')),
                str(evt.get('safety_state', '')),
                str(evt.get('decision', ''))
            ]
            pdf.add_table_row(row, widths)
        pdf.ln(5)
    
    # Save PDF
    pdf.output(output_path)
    return output_path
