from datetime import datetime
from loguru import logger

def generate_bibtex(papers: list[dict]) -> str:
    """
    Generate a BibTeX string from a list of papers.
    """
    bibtex_entries = []
    
    for i, paper in enumerate(papers):
        # Create a citation key: FirstAuthorYEAR
        authors = paper.get("authors") or "Unknown"
        first_author = authors.split(",")[0].split()[-1] if authors != "Unknown" else "Unknown"
        year = datetime.now().year # Fallback year
        
        # Try to extract year from paper data if available (Phase 8 search might add this)
        key = f"{first_author.lower()}{year}_{i}"
        
        entry = (
            f"@article{{{key},\n"
            f"  title = {{{paper.get('title')}}},\n"
            f"  author = {{{authors}}},\n"
            f"  url = {{{paper.get('url')}}},\n"
            f"  note = {{Source: {paper.get('source')}}}\n"
            f"}}"
        )
        bibtex_entries.append(entry)
        
    return "\n\n".join(bibtex_entries)

def sanitize_text_for_pdf(text: str) -> str:
    """
    Sanitize text to be compatible with standard PDF fonts (Latin-1).
    Replaces common Unicode characters with safe equivalents.
    """
    if not text:
        return ""
    
    replacements = {
        "\u2013": "-",    # en dash
        "\u2014": "--",   # em dash
        "\u2018": "'",    # left single quote
        "\u2019": "'",    # right single quote
        "\u201c": '"',    # left double quote
        "\u201d": '"',    # right double quote
        "\u2022": "*",    # bullet
        "\u2026": "...",  # ellipsis
        "\u00a0": " ",    # non-breaking space
    }
    
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
        
    # Fallback: remove any other non-latin-1 characters
    return text.encode("latin-1", errors="replace").decode("latin-1")

def generate_pdf_report(report_data: dict, task_topic: str) -> str:
    """
    Generate a PDF report using fpdf2.
    Returns the path to the generated file.
    """
    try:
        from fpdf import FPDF
        import os

        class PDF(FPDF):
            def header(self):
                self.set_font('helvetica', 'B', 15)
                self.cell(0, 10, 'Autonomous AI Research Report', border=False, align='C', new_x="LMARGIN", new_y="NEXT")
                self.ln(5)

            def footer(self):
                self.set_y(-15)
                self.set_font('helvetica', 'I', 8)
                self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')

        pdf = PDF()
        pdf.add_page()
        effective_width = pdf.epw
        
        # Topic
        pdf.set_font("helvetica", "B", 16)
        pdf.multi_cell(effective_width, 10, f"Topic: {sanitize_text_for_pdf(task_topic)}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)

        # Summary
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(effective_width, 10, "Executive Summary", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 11)
        pdf.multi_cell(effective_width, 7, sanitize_text_for_pdf(report_data.get("summary", "")))
        pdf.ln(5)

        # Key Techniques
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(effective_width, 10, "Key Techniques", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 11)
        for tech in report_data.get("key_techniques", []):
            pdf.multi_cell(effective_width, 7, f"- {sanitize_text_for_pdf(tech)}")
        pdf.ln(5)

        # References
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(effective_width, 10, "References", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 9)
        for ref in report_data.get("references", []):
            pdf.multi_cell(effective_width, 5, f"- {sanitize_text_for_pdf(ref)}")
            
        # Ensure export directory exists
        os.makedirs("./data/exports", exist_ok=True)
        output_name = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = os.path.join("data", "exports", output_name)
        pdf.output(output_path)
        
        return output_path
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return ""

def generate_markdown_report(report_data: dict, topic: str) -> str:
    """
    Generate a formatted Markdown report.
    """
    md = f"# Research Report: {topic}\n\n"
    md += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    
    md += "## Executive Summary\n\n"
    md += report_data.get("summary", "No summary available.") + "\n\n"
    
    if report_data.get("key_techniques"):
        md += "## Key Techniques\n\n"
        for tech in report_data.get("key_techniques", []):
            md += f"- {tech}\n"
        md += "\n"
        
    if report_data.get("comparison_table"):
        md += "## Comparison Table\n\n"
        md += "| Method | Description | Strengths | Limitations |\n"
        md += "|--------|-------------|-----------|-------------|\n"
        for row in report_data.get("comparison_table", []):
            m = row.get("method", "")
            d = row.get("description", "")
            s = row.get("strengths", "")
            l = row.get("limitations", "")
            md += f"| {m} | {d} | {s} | {l} |\n"
        md += "\n"
        
    if report_data.get("future_directions"):
        md += "## Future Directions\n\n"
        for i, dir in enumerate(report_data.get("future_directions", []), 1):
            md += f"{i}. {dir}\n"
        md += "\n"
        
    if report_data.get("references"):
        md += "## References\n\n"
        for i, ref in enumerate(report_data.get("references", []), 1):
            md += f"{i}. {ref}\n"
            
    return md
