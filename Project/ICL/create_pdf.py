import os
import re
import sys
from fpdf import FPDF

def clean_unicode(text):
    # Mapping of common unicode characters to ASCII/Latin-1 equivalents
    replacements = [
        ('\u2014', '--'),  # em dash
        ('\u2013', '-'),   # en dash
        ('\u201c', '"'),   # curly double quote left
        ('\u201d', '"'),   # curly double quote right
        ('\u2018', "'"),   # curly single quote left
        ('\u2019', "'"),   # curly single quote right
        ('\u2192', '->'),  # right arrow
        ('\u2248', 'approx.'), # approx sign
        ('\u222b', 'integral'), # integral sign
        ('\u2202', 'd'),   # partial diff
        ('\u221e', 'inf'),  # infinity
        ('\u00b1', '+/-'), # plus-minus
        ('\u2264', '<='),  # less than or equal
        ('\u2265', '>='),  # greater than or equal
        ('\u22c5', '*'),   # center dot
        ('\u2022', '*'),   # bullet
        ('\u250c', '+'),   # box drawing chars
        ('\u2510', '+'),
        ('\u2514', '+'),
        ('\u2518', '+'),
        ('\u2500', '-'),
        ('\u2502', '|'),
        ('\u251c', '+'),
        ('\u2524', '+'),
        ('\u252c', '+'),
        ('\u2534', '+'),
        ('\u253c', '+'),
        ('\u2504', '-'),
        ('\u2506', '|'),
        ('\u254c', '-'),
        ('\u254e', '|'),
        ('\U0001f534', '[P0]'), # red circle
        ('\U0001f7e1', '[P1]'), # yellow circle
        ('\U0001f7e2', '[P2]'), # green circle
        ('\u2b50', '*'),        # star
        ('\u2714', '[OK]'),     # checkmark
        ('\u2718', '[X]'),      # cross
        ('\u26a0', '[!]'),      # warning sign
    ]
    
    cleaned = text
    for unicode_char, ascii_char in replacements:
        cleaned = cleaned.replace(unicode_char, ascii_char)
        
    # Failsafe: drop any characters that cannot be encoded in latin-1
    result = []
    for char in cleaned:
        try:
            char.encode('latin-1')
            result.append(char)
        except UnicodeEncodeError:
            result.append('?') # replace with question mark
    return ''.join(result)

# Define custom PDF class for headers, footers and styling
class ICLPlanPDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_char_spacing(0)

    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(100, 110, 120)
            self.cell(0, 8, "Phase 1: ICL Latent Space Manipulation -- Implementation Plan", align="R")
            self.ln(8)
            self.set_draw_color(220, 225, 230)
            self.set_line_width(0.2)
            self.line(20, self.get_y(), 190, self.get_y())
            self.ln(5)

    def footer(self):
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(100, 110, 120)
            self.cell(0, 10, f"Page {self.page_no()} / {{nb}}", align="C")


def clean_math(text):
    # Standard math symbol cleaning for ASCII-safe PDF output
    replacements = [
        (r'\$\$', ''),
        (r'\$', ''),
        (r'\\alpha', 'alpha'),
        (r'\\beta', 'beta'),
        (r'\\gamma', 'gamma'),
        (r'\\sigma', 'sigma'),
        (r'\\epsilon', 'epsilon'),
        (r'\\theta', 'theta'),
        (r'\\sum', 'sum'),
        (r'\\sqrt', 'sqrt'),
        (r'\\frac\{([^{}]+)\}\{([^{}]+)\}', r'(\1)/(\2)'),
        (r'\\text\{([^{}]+)\}', r'\1'),
        (r'\\left\(', '('),
        (r'\\right\)', ')'),
        (r'\\cdot', ' * '),
        (r'\^(\{[^}]+\}|[0-9a-zA-Z])', r'^\1'),
        (r'_(\{[^}]+\}|[0-9a-zA-Z])', r'_\1'),
    ]
    
    cleaned = text
    for _ in range(3):
        for pattern, repl in replacements:
            cleaned = re.sub(pattern, repl, cleaned)
            
    cleaned = cleaned.replace('{', '').replace('}', '')
    cleaned = cleaned.replace('\\', '')
    return cleaned


def parse_markdown(lines):
    elements = []
    in_code = False
    code_lang = ""
    code_lines = []
    
    in_table = False
    table_lines = []
    
    in_alert = False
    alert_type = ""
    alert_lines = []
    
    for line_raw in lines:
        line = line_raw.rstrip('\r\n')
        
        # Check code block toggle
        if line.strip().startswith('```'):
            if in_code:
                elements.append({
                    'type': 'code',
                    'lang': code_lang,
                    'content': '\n'.join(code_lines)
                })
                in_code = False
                code_lines = []
            else:
                in_code = True
                code_lang = line.strip()[3:].strip()
            continue
            
        if in_code:
            code_lines.append(line)
            continue
            
        # Table detection
        if line.strip().startswith('|'):
            if not in_table:
                in_table = True
                table_lines = []
            table_lines.append(line)
            continue
        elif in_table:
            elements.append({
                'type': 'table',
                'lines': table_lines
            })
            in_table = False
            table_lines = []
            
        # Alert / Blockquote detection
        if line.strip().startswith('>'):
            content = line.strip()[1:].strip()
            if not in_alert:
                in_alert = True
                alert_type = "NOTE"
                alert_lines = []
                if content.startswith('[!'):
                    end_idx = content.find(']')
                    if end_idx != -1:
                        alert_type = content[2:end_idx].upper()
                        content = content[end_idx+1:].strip()
            else:
                if content.startswith('[!'):
                    end_idx = content.find(']')
                    if end_idx != -1:
                        alert_type = content[2:end_idx].upper()
                        content = content[end_idx+1:].strip()
            
            if content or len(alert_lines) > 0:
                alert_lines.append(content)
            continue
        elif in_alert:
            elements.append({
                'type': 'alert',
                'alert_type': alert_type,
                'content': '\n'.join(alert_lines)
            })
            in_alert = False
            alert_lines = []
            
        # Empty lines
        if not line.strip():
            elements.append({'type': 'empty'})
            continue
            
        # Headings
        if line.startswith('# '):
            elements.append({'type': 'h1', 'content': line[2:].strip()})
        elif line.startswith('## '):
            elements.append({'type': 'h2', 'content': line[3:].strip()})
        elif line.startswith('### '):
            elements.append({'type': 'h3', 'content': line[4:].strip()})
        elif line.startswith('#### '):
            elements.append({'type': 'h4', 'content': line[5:].strip()})
        elif line.strip() == '---' or line.strip() == '***':
            elements.append({'type': 'hr'})
        elif line.strip().startswith('- ') or line.strip().startswith('* '):
            indent_level = len(line_raw) - len(line_raw.lstrip())
            content = line.strip()[2:].strip()
            elements.append({'type': 'bullet', 'content': content, 'indent': indent_level})
        elif line.strip() and line.strip()[0].isdigit() and (line.strip().find('. ') != -1 and line.strip().find('. ') < 5):
            idx = line.strip().find('. ')
            indent_level = len(line_raw) - len(line_raw.lstrip())
            content = line.strip()[idx+2:].strip()
            num = line.strip()[:idx]
            elements.append({'type': 'numbered', 'content': content, 'num': num, 'indent': indent_level})
        else:
            elements.append({'type': 'paragraph', 'content': line.strip()})
            
    if in_code:
        elements.append({'type': 'code', 'lang': code_lang, 'content': '\n'.join(code_lines)})
    if in_table:
        elements.append({'type': 'table', 'lines': table_lines})
    if in_alert:
        elements.append({'type': 'alert', 'alert_type': alert_type, 'content': '\n'.join(alert_lines)})
        
    return elements


def post_process_elements(elements):
    processed = []
    current_para = []
    
    for el in elements:
        if el['type'] == 'paragraph':
            current_para.append(el['content'])
        else:
            if current_para:
                processed.append({
                    'type': 'paragraph',
                    'content': ' '.join(current_para)
                })
                current_para = []
            
            if el['type'] != 'empty':
                processed.append(el)
                
    if current_para:
        processed.append({
            'type': 'paragraph',
            'content': ' '.join(current_para)
        })
        
    return processed


def parse_table_lines(lines):
    rows = []
    for line in lines:
        line_strip = line.strip()
        if not line_strip:
            continue
        parts = [p.strip() for p in line_strip.split('|')]
        if parts[0] == '':
            parts = parts[1:]
        if len(parts) > 0 and parts[-1] == '':
            parts = parts[:-1]
            
        is_sep = True
        for p in parts:
            p_clean = p.replace(':', '').replace('-', '').replace(' ', '')
            if p_clean != '':
                is_sep = False
                break
        if is_sep:
            continue
            
        rows.append([clean_math(p) for p in parts])
    return rows


def write_rich_line(pdf, text, base_font="Helvetica", base_size=10, base_style=""):
    # Split on ** for bold
    parts_bold = text.split("**")
    for i, part_bold in enumerate(parts_bold):
        is_bold = (i % 2 == 1)
        
        # Split on "*" for italic
        parts_italic = part_bold.split("*")
        for j, part_italic in enumerate(parts_italic):
            is_italic = (j % 2 == 1)
            
            style = ""
            if is_bold and is_italic:
                style = "BI"
            elif is_bold:
                style = "B"
            elif is_italic:
                style = "I"
            else:
                style = base_style
                
            pdf.set_font(base_font, style=style, size=base_size)
            # Remove any trailing double underscores or simple markdown link syntax if needed
            # For simplicity, we just output the text part
            pdf.write(5, part_italic)


def main():
    md_path = r"C:/Users/pdutta/.gemini/antigravity/brain/f4ee6842-b127-4185-8494-b0145933fecf/implementation_plan.md"
    pdf_out = r"d:\pratyay\LLNL\Project\ICL\ICL_Implementation_Plan.pdf"
    
    if not os.path.exists(md_path):
        print(f"Error: markdown plan file not found at {md_path}")
        sys.exit(1)
        
    with open(md_path, 'r', encoding='utf-8') as f:
        md_lines = [clean_unicode(line) for line in f.readlines()]
        
    raw_elements = parse_markdown(md_lines)
    elements = post_process_elements(raw_elements)
    
    # Initialize PDF
    pdf = ICLPlanPDF(orientation='P', unit='mm', format='A4')
    pdf.alias_nb_pages()
    
    # ========== PAGE 1: COVER PAGE ==========
    pdf.add_page()
    pdf.set_auto_page_break(False)
    
    # Left vertical decorative bar
    pdf.set_fill_color(26, 26, 46) # Deep Navy
    pdf.rect(0, 0, 25, 297, style='F')
    
    # Cyan accent strip
    pdf.set_fill_color(0, 212, 170) # Cyan
    pdf.rect(25, 0, 2, 297, style='F')
    
    # Title content
    pdf.set_left_margin(40)
    pdf.set_y(40)
    
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(26, 26, 46)
    pdf.multi_cell(150, 12, "Phase 1: Systematic Problem Identification in ICL")
    pdf.ln(3)
    
    pdf.set_font("Helvetica", "", 18)
    pdf.set_text_color(100, 110, 120)
    pdf.cell(0, 10, "In-Context Learning as Latent Space Manipulation")
    pdf.ln(20)
    
    # Divider line
    pdf.set_draw_color(0, 212, 170)
    pdf.set_line_width(1)
    pdf.line(40, pdf.get_y(), 180, pdf.get_y())
    pdf.ln(15)
    
    # Metadata
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(26, 26, 46)
    pdf.cell(0, 8, "Author:")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(60, 70, 80)
    pdf.cell(0, 8, "Pratyay Dutta")
    pdf.ln(5)
    pdf.set_font("Helvetica", "I", 11)
    pdf.set_text_color(100, 110, 120)
    pdf.cell(0, 8, "Department of Computer Science, University of California, Riverside")
    pdf.ln(5)
    pdf.cell(0, 8, "Lawrence Livermore National Laboratory")
    pdf.ln(12)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(26, 26, 46)
    pdf.cell(0, 8, "Advisor:")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(60, 70, 80)
    pdf.cell(0, 8, "Prof. Bir Bhanu")
    pdf.ln(15)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(26, 26, 46)
    pdf.cell(0, 8, "Status:")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(26, 26, 46)
    # Status badge background
    x_pos = pdf.get_x()
    y_pos = pdf.get_y()
    pdf.set_fill_color(240, 248, 255)
    pdf.rect(x_pos - 1, y_pos, 115, 8, style='F')
    pdf.set_text_color(0, 140, 255)
    pdf.cell(0, 8, " Phase 1: Problem Identification & Diagnostic Experimentation")
    pdf.ln(15)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(26, 26, 46)
    pdf.cell(0, 8, "Date:")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(60, 70, 80)
    pdf.cell(0, 8, "June 2026")
    
    # ========== MAIN CONTENT PAGE SETUP ==========
    pdf.set_auto_page_break(True, margin=20)
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    pdf.add_page()
    
    # Set default text color
    pdf.set_text_color(45, 55, 72)
    
    for el in elements:
        t = el['type']
        
        # Check page break logic to prevent single headings at the bottom of pages
        if t in ['h1', 'h2', 'h3'] and pdf.get_y() > 250:
            pdf.add_page()
            
        if t == 'h1':
            pdf.ln(8)
            pdf.set_font("Helvetica", "B", 18)
            pdf.set_text_color(26, 26, 46) # Deep Navy
            pdf.cell(0, 10, el['content'])
            pdf.ln(10)
            # Draw horizontal rule under H1
            pdf.set_draw_color(26, 26, 46)
            pdf.set_line_width(0.5)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(5)
            
        elif t == 'h2':
            pdf.ln(6)
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(26, 26, 46)
            pdf.cell(0, 8, el['content'])
            pdf.ln(10)
            
        elif t == 'h3':
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(0, 140, 255) # Deep Blue Accent
            pdf.cell(0, 6, el['content'])
            pdf.ln(8)
            
        elif t == 'h4':
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 10.5)
            pdf.set_text_color(124, 58, 237) # Purple
            pdf.cell(0, 6, el['content'])
            pdf.ln(7)
            
        elif t == 'paragraph':
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(45, 55, 72)
            # Write rich text paragraph (supporting bold/italic)
            write_rich_line(pdf, el['content'], base_font="Helvetica", base_size=10)
            pdf.ln(6)
            
        elif t == 'bullet':
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(45, 55, 72)
            
            # Bullet point indent
            indent = 8 + (el['indent'] * 2)
            pdf.set_x(20 + indent)
            
            # Draw bullet circle
            curr_y = pdf.get_y()
            pdf.set_fill_color(0, 140, 255)
            pdf.circle(pdf.get_x() - 4, curr_y + 2.2, 0.8, style='F')
            
            # Render bullet text
            write_rich_line(pdf, el['content'], base_font="Helvetica", base_size=10)
            pdf.ln(6)
            
        elif t == 'numbered':
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(45, 55, 72)
            
            # Number indent
            indent = 8 + (el['indent'] * 2)
            pdf.set_x(20 + indent)
            
            # Write number prefix
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(26, 26, 46)
            pdf.write(5, f"{el['num']}. ")
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(45, 55, 72)
            
            # Render item text
            write_rich_line(pdf, el['content'], base_font="Helvetica", base_size=10)
            pdf.ln(6)
            
        elif t == 'hr':
            pdf.ln(3)
            pdf.set_draw_color(220, 225, 230)
            pdf.set_line_width(0.3)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(5)
            
        elif t == 'code':
            pdf.ln(2)
            code_text = el['content']
            # Determine background box dimensions
            pdf.set_font("Courier", "", 8.5)
            pdf.set_text_color(40, 45, 55)
            
            # Render block in multi_cell inside a gray fill rectangle
            lines_count = len(code_text.split('\n'))
            box_h = (lines_count * 4) + 6
            
            # If box exceeds page boundary, let's wrap it in normal cells or add page break
            if pdf.get_y() + box_h > 270:
                pdf.add_page()
                
            y_start = pdf.get_y()
            pdf.set_fill_color(245, 247, 249) # Light Gray
            pdf.set_draw_color(218, 222, 229)
            pdf.set_line_width(0.25)
            pdf.rect(20, y_start, 170, box_h, style='FD')
            
            pdf.set_y(y_start + 3)
            pdf.set_x(23)
            # Use multi_cell to write code lines, keeping spaces
            pdf.multi_cell(164, 4, code_text, border=0, align='L', fill=False)
            
            pdf.set_y(y_start + box_h)
            pdf.ln(4)
            
        elif t == 'alert':
            pdf.ln(3)
            alert_type = el['alert_type']
            alert_text = el['content']
            
            # Setup alert box styles
            if alert_type == "IMPORTANT":
                border_color = (124, 58, 237) # Purple
                bg_color = (250, 245, 255)
                title = "IMPORTANT"
            elif alert_type == "WARNING":
                border_color = (245, 158, 11) # Orange
                bg_color = (255, 251, 235)
                title = "WARNING"
            elif alert_type == "CAUTION":
                border_color = (239, 68, 68) # Red
                bg_color = (254, 242, 242)
                title = "CAUTION"
            else: # NOTE or TIP
                border_color = (0, 140, 255) # Blue
                bg_color = (240, 249, 255)
                title = alert_type
                
            # Render using FPDF cells
            pdf.set_font("Helvetica", "B", 9)
            
            # Estimate height needed
            # Set font to measure height
            pdf.set_font("Helvetica", "I", 9.5)
            # Get text height by rendering it off-screen or calculating
            # We can use multi_cell to write it
            lines_count = len(alert_text.split('\n')) + 1.5
            box_h = (lines_count * 5) + 6
            
            if pdf.get_y() + box_h > 270:
                pdf.add_page()
                
            y_start = pdf.get_y()
            # Draw background box
            pdf.set_fill_color(*bg_color)
            pdf.rect(20, y_start, 170, box_h, style='F')
            
            # Draw left thick border
            pdf.set_fill_color(*border_color)
            pdf.rect(20, y_start, 2, box_h, style='F')
            
            # Write alert header
            pdf.set_y(y_start + 3)
            pdf.set_x(25)
            pdf.set_font("Helvetica", "B", 9.5)
            pdf.set_text_color(*border_color)
            pdf.cell(0, 5, title)
            pdf.ln(5.5)
            
            # Write alert text
            pdf.set_x(25)
            pdf.set_font("Helvetica", "I", 9.5)
            pdf.set_text_color(60, 70, 80)
            
            # Write contents rstrip / lstrip lines
            cleaned_alert_lines = [ln.strip() for ln in alert_text.split('\n') if ln.strip()]
            cleaned_alert_text = '\n'.join(cleaned_alert_lines)
            
            pdf.multi_cell(160, 4.8, cleaned_alert_text, border=0, align='L', fill=False)
            
            pdf.set_y(y_start + box_h)
            pdf.ln(4)
            
        elif t == 'table':
            pdf.ln(2)
            table_rows = parse_table_lines(el['lines'])
            if not table_rows:
                continue
                
            # Estimate height of table
            table_h = len(table_rows) * 10
            if pdf.get_y() + table_h > 270:
                pdf.add_page()
                
            pdf.set_font("Helvetica", "", 9.5)
            pdf.set_text_color(45, 55, 72)
            
            # Use pdf.table for automatic clean layout
            with pdf.table(
                first_row_as_headings=True, 
                align="CENTER", 
                text_align="LEFT",
                line_height=5.5
            ) as table:
                for row_idx, r_data in enumerate(table_rows):
                    row = table.row()
                    for cell_idx, cell_text in enumerate(r_data):
                        # Style headers differently
                        if row_idx == 0:
                            pdf.set_font("Helvetica", "B", 9.5)
                            pdf.set_text_color(26, 26, 46)
                        else:
                            pdf.set_font("Helvetica", "", 9)
                            pdf.set_text_color(45, 55, 72)
                        row.cell(cell_text)
            pdf.ln(4)

    pdf.output(pdf_out)
    print(f"PDF successfully created and saved to: {pdf_out}")


if __name__ == "__main__":
    main()
