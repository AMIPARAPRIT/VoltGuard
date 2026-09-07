import json
from datetime import datetime
from fpdf import FPDF
from pathlib import Path
from typing import Dict, Any, List

def clean_txt(text: Any) -> str:
    if text is None:
        return "N/A"
    s = str(text)
    return s.replace("—", "-").replace("–", "-").replace("°", "deg ")

class PDFGenerator(FPDF):
    def __init__(self, title: str):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.report_title = clean_txt(title)
        self.add_page()
        
    def header(self):
        # Professional Industrial Header
        self.set_font('helvetica', 'B', 16)
        self.set_text_color(15, 23, 42) # Dark navy
        self.cell(0, 8, 'VoltGuard', ln=True, align='L')
        
        self.set_font('helvetica', 'B', 11)
        self.set_text_color(56, 189, 248) # Accent cyan
        self.cell(0, 6, 'Physics-Aware ICS/SCADA Security & Audit Report', ln=True, align='L')
        
        self.set_font('helvetica', 'I', 9)
        self.set_text_color(100, 116, 139) # Muted gray
        self.cell(0, 5, self.report_title, ln=True, align='L')
        
        # Horizontal rule
        self.set_draw_color(226, 232, 240)
        self.set_line_width(0.5)
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(6)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f'VoltGuard Audit Report | Page {self.page_no()}', align='C')

    def add_section_title(self, title: str):
        self.set_font('helvetica', 'B', 11)
        self.set_fill_color(241, 245, 249) # Light gray slate
        self.set_text_color(30, 41, 59)
        self.cell(0, 7, clean_txt(f"  {title}"), ln=True, fill=True)
        self.ln(3)

    def add_key_value(self, key: str, value: Any, width: int = 45):
        self.set_font('helvetica', 'B', 9)
        self.set_text_color(71, 85, 105)
        curr_x = self.get_x()
        self.cell(width, 6, clean_txt(key + ":"))
        self.set_font('helvetica', '', 9)
        self.set_text_color(15, 23, 42)
        rem_w = self.w - self.r_margin - (curr_x + width)
        if rem_w < 20:
            rem_w = 100
        self.multi_cell(rem_w, 6, clean_txt(value if value is not None else 'N/A'))

    def add_table_header(self, columns: List[str], widths: List[int]):
        self.set_font('helvetica', 'B', 9)
        self.set_fill_color(226, 232, 240)
        self.set_text_color(30, 41, 59)
        for col, width in zip(columns, widths):
            self.cell(width, 7, clean_txt(col), border=1, fill=True, align='C')
        self.ln()

    def add_table_row(self, row: List[str], widths: List[int], is_alert: bool = False):
        self.set_font('helvetica', '', 8)
        if is_alert:
            self.set_text_color(225, 29, 72)
        else:
            self.set_text_color(30, 41, 59)
            
        for item, width in zip(row, widths):
            str_item = clean_txt(item)
            if len(str_item) > width // 2:
                str_item = str_item[:width // 2 - 2] + ".."
            self.cell(width, 6, str_item, border=1, align='C')
        self.ln()


def generate_report_pdf(metadata: Dict[str, Any], data: Dict[str, Any], output_path: str) -> str:
    """
    Generates an authoritative, publication-quality PDF report.
    """
    report_type_clean = metadata.get('report_type', 'REPORT').replace('_', ' ')
    title = f"{report_type_clean} - {metadata.get('report_id')}"
    pdf = PDFGenerator(title)
    
    # Section 1: System Summary Metrics
    if 'system_summary' in data:
        ss = data['system_summary']
        pdf.add_section_title("SYSTEM SUMMARY & OPERATIONAL STATUS")
        pdf.set_font('helvetica', '', 9)
        cols = ["Monitored Devices", "Total Events", "Active Alerts", "Blocked Commands", "Critical Violations"]
        widths = [38, 38, 38, 38, 38]
        pdf.add_table_header(cols, widths)
        row = [
            str(ss.get('device_count', 0)),
            str(ss.get('event_count', 0)),
            str(ss.get('alert_count', 0)),
            str(ss.get('blocked_count', 0)),
            str(ss.get('critical_count', 0))
        ]
        pdf.add_table_row(row, widths)
        pdf.ln(4)

    # Section 2: Report Metadata
    pdf.add_section_title("REPORT METADATA & FILTERS")
    pdf.add_key_value("Report ID", metadata.get('report_id', ''))
    pdf.add_key_value("Report Type", report_type_clean)
    pdf.add_key_value("Generated Timestamp", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))
    pdf.add_key_value("Primary Device Filter", metadata.get('primary_device') or 'All Monitored Devices')
    pdf.add_key_value("Severity Filter", metadata.get('severity') or 'All Severities')
    pdf.ln(4)

    # Section 3: Targeted Incident / Security Event Analysis
    if 'event' in data and data['event']:
        evt = data['event']
        pdf.add_section_title("PRIMARY EVENT / INCIDENT DETAILS")
        pdf.add_key_value("Event ID", f"#{evt.get('id')}")
        pdf.add_key_value("Timestamp", evt.get('timestamp', ''))
        pdf.add_key_value("Target Device", evt.get('device', ''))
        pdf.add_key_value("Protocol", str(evt.get('protocol', '')).upper())
        pdf.add_key_value("Source -> Destination IP", f"{evt.get('source_ip', 'N/A')} -> {evt.get('destination_ip', 'N/A')}")
        pdf.add_key_value("Command Issued", f"{evt.get('command')} = {evt.get('command_value')}")
        pdf.ln(4)

        # Physical Analysis Table
        pdf.add_section_title("PHYSICAL CONSEQUENCE & AUTHORITATIVE LIMITS")
        cols = ["Parameter", "Predicted Value", "Safety Limit", "Unit", "Status"]
        widths = [40, 38, 38, 30, 44]
        pdf.add_table_header(cols, widths)
        
        limits = data.get('system_summary', {}).get('safety_limits', {})
        p_val = evt.get('predicted_pressure')
        p_lim = limits.get('max_pressure', 80.0)
        p_stat = "EXCEEDED" if (p_val is not None and p_val > p_lim) else "NORMAL"
        
        f_val = evt.get('predicted_flow')
        f_lim = limits.get('max_flow', 500.0)
        f_stat = "EXCEEDED" if (f_val is not None and f_val > f_lim) else "NORMAL"

        t_val = evt.get('predicted_temperature')
        t_lim = limits.get('max_temperature', 120.0)
        t_stat = "EXCEEDED" if (t_val is not None and t_val > t_lim) else "NORMAL"

        pdf.add_table_row(["Pressure", f"{p_val:.2f}" if p_val is not None else "N/A", f"{p_lim:.1f}", "bar", p_stat], widths, is_alert=(p_stat=="EXCEEDED"))
        pdf.add_table_row(["Flow Rate", f"{f_val:.2f}" if f_val is not None else "N/A", f"{f_lim:.1f}", "L/min", f_stat], widths, is_alert=(f_stat=="EXCEEDED"))
        pdf.add_table_row(["Temperature", f"{t_val:.2f}" if t_val is not None else "N/A", f"{t_lim:.1f}", "deg C", t_stat], widths, is_alert=(t_stat=="EXCEEDED"))
        pdf.ln(4)

        # Risk & Safety State
        pdf.add_key_value("Calculated Risk Score", f"{evt.get('risk_score', 0):.1f} / 100.0")
        pdf.add_key_value("Assessed Safety State", evt.get('safety_state', 'SAFE'))
        pdf.ln(4)

        # Security Decision
        pdf.add_section_title("RUST DECISION ENGINE POLICY EVALUATION")
        pdf.add_key_value("Security Decision", evt.get('decision', 'N/A'))
        pdf.add_key_value("Decision Reason", evt.get('reason', 'N/A'))
        if evt.get('violations'):
            pdf.add_key_value("Safety Violations", str(evt.get('violations')))
        if evt.get('explanation'):
            pdf.add_key_value("Physics Explanation", str(evt.get('explanation')))
        pdf.ln(4)

    # Section 4: Incident Timeline
    if 'timeline' in data and data['timeline']:
        pdf.add_section_title("CHRONOLOGICAL INCIDENT TIMELINE")
        cols = ["Stage / Event Step", "Timestamp", "Audit Details"]
        widths = [45, 45, 100]
        pdf.add_table_header(cols, widths)
        for item in data['timeline']:
            pdf.add_table_row([
                str(item.get('stage', '')),
                str(item.get('timestamp', ''))[:19],
                str(item.get('details', ''))
            ], widths)
        pdf.ln(4)

    # Section 5: Simulation Runs (If Simulation Report)
    if 'simulations' in data and data['simulations']:
        pdf.add_section_title("INDUSTRIAL SIMULATION RUNS")
        cols = ["ID", "Time", "Scenario", "Device", "Command", "Risk", "Decision"]
        widths = [15, 35, 30, 25, 35, 20, 30]
        pdf.add_table_header(cols, widths)
        for sim in data['simulations']:
            pdf.add_table_row([
                str(sim.get('id', '')),
                str(sim.get('timestamp', ''))[:19],
                str(sim.get('scenario', '')),
                str(sim.get('device_id', '')),
                f"{sim.get('command')} {sim.get('command_value')}",
                f"{sim.get('risk_score', 0):.0f}",
                str(sim.get('decision', ''))
            ], widths, is_alert=(sim.get('decision') in ('BLOCK', 'BLOCK_CRITICAL')))
        pdf.ln(4)

    # Section 6: Events Table (If Events List Report)
    if 'events' in data and data['events'] and not ('event' in data and data['event']):
        pdf.add_section_title("SECURITY EVENTS LOG")
        cols = ["ID", "Time", "Device", "Command", "Safety State", "Decision"]
        widths = [15, 40, 30, 45, 30, 30]
        pdf.add_table_header(cols, widths)
        for evt in data['events']:
            pdf.add_table_row([
                str(evt.get('id', '')),
                str(evt.get('timestamp', ''))[:19],
                str(evt.get('device', '')),
                f"{evt.get('command')} {evt.get('command_value')}",
                str(evt.get('safety_state', '')),
                str(evt.get('decision', ''))
            ], widths, is_alert=(evt.get('decision') in ('BLOCK', 'BLOCK_CRITICAL')))
        pdf.ln(4)

    # Save PDF output
    pdf.output(output_path)
    return output_path
