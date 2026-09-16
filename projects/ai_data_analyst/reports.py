"""Portable analytical report exports."""
import io
from xml.sax.saxutils import escape


def markdown_report(chat, df):
    parts = ["# Analytoka AI report", f"Dataset: {chat['active']}",
             f"Rows: {len(df):,} | Columns: {len(df.columns)} | Missing cells: {int(df.isna().sum().sum())}",
             "## Executive summary", chat.get("summary", "Generate an executive summary in the Reports tab."),
             "## Cleaning history"]
    parts.extend(f"- {entry['dataset']}: {entry['action']}" for entry in chat['history'])
    if chat.get("analysis"):
        import json
        parts.extend(["## Calculated analysis", json.dumps(chat["analysis"], indent=2)])
    parts.append("## Conversation")
    for message in chat["messages"]:
        parts.extend([f"### {message['role'].title()}", message["content"]])
    return "\n\n".join(parts)


def pdf_report(markdown):
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    output = io.BytesIO()
    styles = getSampleStyleSheet()
    flow = []
    for line in markdown.splitlines():
        if not line.strip():
            flow.append(Spacer(1, 8))
            continue
        level = len(line) - len(line.lstrip("#"))
        style = styles["Title" if level == 1 else "Heading2" if level else "BodyText"]
        flow.append(Paragraph(escape(line.lstrip("# ")), style))
    SimpleDocTemplate(output, title="Analytoka AI report", leftMargin=48, rightMargin=48).build(flow)
    return output.getvalue()
