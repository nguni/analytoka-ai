"""Analytoka AI: persistent local data analysis workspace."""
import json
from pathlib import Path
import pandas as pd
import streamlit as st
import altair as alt
from agent_groq import run_agent
from workspace import (new_chat, list_chats, save_chat, import_upload, save_frame,
                       transform, apply_change, join_frames)
from tools.cleaning_tools import (profile_data_quality, dataframe_to_excel, trim_text_values,
    remove_duplicates, drop_missing_rows, fill_missing_text, fill_numeric_with_median, remove_empty_columns)
from tools.advanced_tools import advanced_analysis
from reports import markdown_report, pdf_report
from ui import inject_styles, brand, topline, welcome, workflow, dataset_heading, overview_banner, footer

st.set_page_config(page_title="Analytoka AI · Data studio", page_icon="◧", layout="wide")
inject_styles()
if "chats" not in st.session_state:
    st.session_state.chats = {c["id"]: c for c in list_chats()}
if not st.session_state.chats:
    chat = new_chat()
    st.session_state.chats[chat["id"]] = chat
if st.session_state.get("active_chat") not in st.session_state.chats:
    st.session_state.active_chat = next(iter(st.session_state.chats))

with st.sidebar:
    brand()
    if st.button("New chat", type="primary", width="stretch"):
        chat = new_chat()
        st.session_state.chats[chat["id"]] = chat
        st.session_state.active_chat = chat["id"]
        save_chat(chat)
        st.rerun()
    st.markdown('<div class="side-label">YOUR WORKSPACE</div>', unsafe_allow_html=True)
    ids = list(st.session_state.chats)
    chat_titles = {k: st.session_state.chats[k]["title"] for k in ids}
    selected = st.selectbox("Chats", ids, index=ids.index(st.session_state.active_chat),
                            format_func=lambda k, labels=chat_titles: labels[k])
    st.session_state.active_chat = selected
    chat = st.session_state.chats[selected]
    with st.expander("AI settings", expanded=False):
        provider = st.selectbox("AI provider", ["Groq", "Gemini"])
        model = st.text_input("Model", value="openai/gpt-oss-120b" if provider == "Groq" else "gemini-3.6-flash", key=f"model_{provider}")
    with st.expander("Add data", expanded=False):
        files = st.file_uploader("Add CSV or Excel files", type=["csv", "xlsx", "xls"],
                                 accept_multiple_files=True, key=f"uploads_{selected}")
    for uploaded in files:
        try:
            import_upload(chat, uploaded.name, uploaded.getvalue())
        except Exception as error:
            st.error(f"{uploaded.name}: {error}")
    if chat["datasets"]:
        names = list(chat["datasets"])
        active = st.selectbox("Active dataset / worksheet", names,
                             index=names.index(chat["active"]), key=f"dataset_{selected}_{len(names)}")
        if active != chat["active"]:
            for key in ("analysis", "summary", "recommendations"):
                chat.pop(key, None)
        chat["active"] = active
    if st.button("Clear conversation"):
        chat["messages"] = []
        save_chat(chat)
        st.rerun()
    save_chat(chat)
    st.markdown('<div class="side-note"><strong>A space for better questions.</strong><br>Your datasets, conversations, and discoveries. All in one place.</div>', unsafe_allow_html=True)

topline(bool(chat["datasets"]))
if not chat["datasets"]:
    welcome()
    st.markdown('<div class="section-title">Start with a dataset</div><div class="section-note">Your next insight is already in there.</div>', unsafe_allow_html=True)
    incoming = st.file_uploader("Upload a CSV or Excel workbook", type=["csv", "xlsx", "xls"], accept_multiple_files=True, key=f"welcome_upload_{selected}")
    for uploaded in incoming:
        try:
            import_upload(chat, uploaded.name, uploaded.getvalue())
            save_chat(chat)
        except Exception as error:
            st.error(f"{uploaded.name}: {error}")
    if chat["datasets"]:
        st.rerun()
    demo, note = st.columns([1, 2.4])
    with demo:
        if st.button("Try sample data", width="stretch"):
            sample = Path(__file__).parent / "data" / "sample_sales.csv"
            import_upload(chat, sample.name, sample.read_bytes())
            save_chat(chat)
            st.rerun()
    with note:
        st.caption("Just looking around? Take the studio for a spin with a sample dataset.")
    workflow()
    footer()
    st.stop()

@st.cache_data(max_entries=8, show_spinner=False)
def read_frame(path):
    return pd.read_parquet(path)

@st.cache_data(max_entries=2, show_spinner=False)
def excel_export(path):
    return dataframe_to_excel(read_frame(path))

@st.cache_data(max_entries=4, show_spinner=False)
def pdf_export(text):
    return pdf_report(text)

dataset = chat["datasets"][chat["active"]]
df = read_frame(dataset["path"])
dataset_heading(chat["active"], len(chat["datasets"]))
a, b, c, d = st.columns(4)
a.metric("Rows", f"{len(df):,}")
b.metric("Columns", len(df.columns))
c.metric("Missing cells", int(df.isna().sum().sum()))
d.metric("Duplicate rows", int(df.duplicated().sum()))
preview, clean, combine, analytics, visuals, dictionary, reports, conversation = st.tabs(
    ["Explore", "Clean", "Combine", "Analytics", "Charts", "Data dictionary", "Reports", "Chat"])

with preview:
    overview_banner(df)
    st.markdown('<div class="section-title">Inside your dataset</div><div class="section-note">The details behind the bigger picture.</div>', unsafe_allow_html=True)
    st.dataframe(df.head(1000), hide_index=True, width="stretch")
    st.caption("Preview limited to 1,000 rows; calculations use the full dataset.")
    with st.expander("Field guide · column types and completeness"):
        st.dataframe(pd.DataFrame({"type": df.dtypes.astype(str), "missing": df.isna().sum(), "unique": df.nunique()}), width="stretch")
    if len(df.columns):
        with st.expander("Descriptive statistics · distributions at a glance"):
            st.dataframe(df.describe(include="all").astype(str), width="stretch")

with clean:
    st.subheader("A little cleanup. A lot more confidence.")
    st.caption("Preview every change. Your original dataset stays intact.")
    quality = profile_data_quality(df)
    st.write(f"{quality['missing_values']} missing cells; {quality['duplicate_rows']} duplicate rows.")
    if st.button("Get AI cleaning recommendations"):
        with st.spinner("Reviewing data quality…"):
            advice = run_agent("Inspect data quality and recommend specific cleaning actions by column, explaining tradeoffs. Do not change the data.", dataset["path"], metadata=chat["metadata"], provider=provider, model=model)
            chat["recommendations"] = advice["answer"]
            save_chat(chat)
    if chat.get("recommendations"):
        st.markdown(chat["recommendations"])
    if len(df.columns):
        column = st.selectbox("Column", list(df.columns), key=f"clean_col_{selected}")
        action = st.selectbox("Action", ["Trim text", "Standardize categories", "Category mapping", "Convert to number", "Convert to date", "Fill missing", "Fill median", "Drop missing rows", "Remove empty column", "Remove duplicates", "Cap outliers", "Remove outliers"])
        value = st.text_input("Replacement value / category mapping JSON")
        bulk_action = st.selectbox("Optional whole-table action", ["None", "Trim all text", "Fill missing text", "Fill numeric medians", "Drop rows with any missing value", "Remove empty columns"])
        bulk_functions = {"Trim all text": trim_text_values, "Fill missing text": lambda frame: fill_missing_text(frame, value or "Unknown"), "Fill numeric medians": fill_numeric_with_median, "Drop rows with any missing value": drop_missing_rows, "Remove empty columns": remove_empty_columns}
        st.caption("Category standardization trims spaces and lowercases text. Outlier treatment uses 1.5 × IQR. Type conversion rejects invalid values.")
        if st.button("Preview cleaning"):
            try:
                if bulk_action != "None":
                    candidate, description = bulk_functions[bulk_action](df)
                else:
                    candidate = transform(df, column, action, value)
                    description = f"{action}: {column}"
                st.session_state.clean_preview = (selected, chat["active"], dataset["path"], description, candidate)
            except Exception as error:
                st.error(str(error))
        candidate = st.session_state.get("clean_preview")
        if candidate and candidate[:3] == (selected, chat["active"], dataset["path"]):
            after = candidate[4]
            st.write({"rows_before": len(df), "rows_after": len(after), "missing_before": int(df.isna().sum().sum()), "missing_after": int(after.isna().sum().sum())})
            left, right = st.columns(2)
            left.dataframe(df.head(30))
            right.dataframe(after.head(30))
            if st.button("Apply previewed change"):
                apply_change(chat, after, candidate[3])
                save_chat(chat)
                st.rerun()
    if st.button("Undo last change", disabled=not dataset["undo"]):
        dataset["path"] = dataset["undo"].pop()
        for key in ("analysis", "summary", "recommendations"):
            chat.pop(key, None)
        chat["history"].append({"dataset": chat["active"], "action": "Undo"})
        save_chat(chat)
        st.rerun()
    if st.button("Reset to original", disabled=dataset["path"] == dataset["original"]):
        dataset["undo"].append(dataset["path"])
        dataset["path"] = dataset["original"]
        for key in ("analysis", "summary", "recommendations"):
            chat.pop(key, None)
        chat["history"].append({"dataset": chat["active"], "action": "Reset"})
        save_chat(chat)
        st.rerun()
    st.dataframe(chat["history"])
    st.download_button("Download CSV", df.to_csv(index=False).encode(), "cleaned.csv", "text/csv")
    st.download_button("Download Excel", excel_export(dataset["path"]), "cleaned.xlsx")

with combine:
    st.subheader("See how it all connects.")
    st.caption("Bring related tables together to reveal the complete picture.")
    others = [name for name in chat["datasets"] if name != chat["active"]]
    if not others:
        st.info("Add another file or a workbook with multiple worksheets to combine data.")
    else:
        other = st.selectbox("Other dataset", others)
        right_df = read_frame(chat["datasets"][other]["path"])
        mode = st.radio("Combine method", ["Join by key", "Append rows"], horizontal=True)
        if mode == "Join by key" and len(df.columns) and len(right_df.columns):
            left_key = st.selectbox("Left key", list(df.columns))
            right_key = st.selectbox("Right key", list(right_df.columns))
            how = st.selectbox("Join type", ["left", "inner", "outer", "right"])
            validation = st.selectbox("Relationship", ["many_to_one", "one_to_one", "one_to_many"])
        if st.button("Create combined dataset"):
            try:
                if mode == "Append rows":
                    if set(df.columns) != set(right_df.columns):
                        raise ValueError("Append requires matching column names")
                    combined = pd.concat([df, right_df], ignore_index=True)
                else:
                    combined = join_frames(df, right_df, left_key, right_key, how, validation)
                path = save_frame(combined)
                label = f"Combined {len(chat['datasets']) + 1}"
                chat["datasets"][label] = {"original": path, "path": path, "undo": []}
                for key in ("analysis", "summary", "recommendations"):
                    chat.pop(key, None)
                chat["active"] = label
                save_chat(chat)
                st.success(f"Created {label}: {len(combined):,} rows. Select it in the sidebar.")
            except Exception as error:
                st.error(str(error))

with analytics:
    st.subheader("Go beyond the headline number.")
    st.caption("Compare performance, follow growth, and measure what matters.")
    numeric = list(df.select_dtypes(include="number").columns)
    if not numeric:
        st.info("A numeric column is required for business analytics.")
    else:
        operation = st.selectbox("Analysis", ["compare", "growth", "pivot", "target", "ratio"])
        metric = st.selectbox("Metric", numeric)
        group = st.selectbox("Group / pivot rows", [None] + list(df.columns))
        date = st.selectbox("Date column", list(df.columns)) if operation == "growth" else None
        target = st.selectbox("Pivot columns" if operation == "pivot" else "Target column", list(df.columns) if operation == "pivot" else numeric) if operation in {"target", "pivot"} else None
        denominator = st.selectbox("Denominator", numeric) if operation == "ratio" else None
        aggregation = st.selectbox("Aggregation", ["sum", "mean", "median", "count", "min", "max"])
        if st.button("Calculate"):
            try:
                result = advanced_analysis(dataset["path"], operation, metric, group, date, target, denominator, aggregation)
                chat["analysis"] = result
                save_chat(chat)
            except Exception as error:
                st.error(str(error))
        if chat.get("analysis"):
            result = chat["analysis"]
            st.dataframe(result["rows"])
            st.caption(f"Showing up to 500 of {result['total_result_rows']} result rows. Undefined ratios are blank.")
            if "linear_trend_per_month" in result:
                st.write({k: result[k] for k in ["linear_trend_per_month", "invalid_dates_excluded"]})
            st.download_button("Export analysis JSON", json.dumps(result, indent=2), "analysis.json")

with visuals:
    st.subheader("Give your numbers a point of view.")
    st.caption("Choose a perspective. Explore the story in your data.")
    if len(df.columns):
        x = st.selectbox("X axis", list(df.columns))
        y = st.selectbox("Y axis", [None] + numeric)
        kind = st.selectbox("Chart", ["Auto", "Bar", "Line", "Area", "Scatter", "Histogram", "Box plot"])
        chosen = kind
        if chosen == "Auto":
            if y is None:
                chosen = "Histogram" if x in numeric else "Bar"
            elif x in numeric:
                chosen = "Scatter"
            else:
                dates = pd.to_datetime(df[x].head(100).astype(str), errors="coerce")
                chosen = "Line" if len(dates) and dates.notna().mean() > .9 else "Bar"
        try:
            chart_df = df.head(5000).copy()
            chart_df.columns = [f"c{i}" for i in range(len(df.columns))]
            xc = f"c{list(df.columns).index(x)}"
            yc = f"c{list(df.columns).index(y)}" if y else None
            base = alt.Chart(chart_df)
            if chosen == "Histogram":
                chart = base.mark_bar().encode(x=alt.X(xc, type="quantitative", bin=True, title=x), y="count()")
            elif chosen in {"Line", "Area"}:
                chart_df[xc] = pd.to_datetime(chart_df[xc], errors="raise")
                base = alt.Chart(chart_df)
                chart = (base.mark_line() if chosen == "Line" else base.mark_area()).encode(x=alt.X(xc, type="temporal", title=x), y=alt.Y(yc, type="quantitative", aggregate="sum", title=y) if yc else alt.Y("count()"))
            elif chosen == "Scatter":
                if not yc:
                    raise ValueError("Choose a Y axis for a scatter plot")
                chart = base.mark_circle().encode(x=alt.X(xc, type="quantitative", title=x), y=alt.Y(yc, type="quantitative", title=y))
            elif chosen == "Box plot":
                if not yc:
                    raise ValueError("Choose a numeric Y axis")
                chart = base.mark_boxplot().encode(x=alt.X(xc, type="nominal", title=x), y=alt.Y(yc, type="quantitative", title=y))
            else:
                chart = base.mark_bar().encode(x=alt.X(xc, type="nominal", title=x), y=alt.Y(yc, type="quantitative", aggregate="sum", title=y) if yc else alt.Y("count()"))
            st.altair_chart(chart.properties(height=340).configure(background="#f7f7f2").configure_range(category=["#294b53", "#dc784c", "#a7bfae", "#caa46d", "#71899a"]).configure_axis(gridColor="#e2e5dd", domainColor="#d5dcd2", labelColor="#697681", titleColor="#294b53").configure_view(strokeWidth=0).interactive(), width="stretch")
            st.caption(f"{chosen} chart · first {min(len(df), 5000):,} rows. Chat-generated charts use the full dataset.")
        except Exception as error:
            st.info(str(error))

with dictionary:
    st.subheader("Every field has a meaning.")
    st.caption("Describe columns, units, business definitions and KPI rules. Relevant lines are retrieved for each AI question.")
    metadata = st.text_area("Data dictionary", chat["metadata"], height=220, key=f"metadata_{selected}")
    if st.button("Save dictionary"):
        chat["metadata"] = metadata
        save_chat(chat)
        st.success("Saved")

with reports:
    st.subheader("Make your findings travel.")
    st.caption("A clear summary, ready to share with the people who need it.")
    if st.button("Generate executive summary"):
        with st.spinner("Analyzing…"):
            response = run_agent("Produce an executive summary with verified key metrics, trends, data quality limitations and practical next steps.", dataset["path"], metadata=chat["metadata"], provider=provider, model=model)
            chat["summary"] = response["answer"]
            save_chat(chat)
    if chat.get("summary"):
        st.markdown(chat["summary"])
    report = markdown_report(chat, df)
    st.download_button("Download report (Markdown)", report, "analytoka-report.md")
    st.download_button("Download report (PDF)", pdf_export(report), "analytoka-report.pdf", "application/pdf")
    st.download_button("Export conversation", json.dumps(chat["messages"], indent=2), "conversation.json")

with conversation:
    st.subheader("What are you curious about?")
    st.caption("Ask a question, follow a thought, or dig a little deeper.")
    for message in chat["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            for chart in message.get("charts", []):
                if Path(chart["path"]).is_file():
                    st.image(chart["path"], caption=chart.get("title"))
    if question := st.chat_input("Ask about your data"):
        history = [{"role": m["role"], "content": f"[Dataset: {m.get('dataset', 'previous')}] {m['content']}"} for m in chat["messages"]]
        with st.spinner("Analyzing…"):
            response = run_agent(question, dataset["path"], history=history, metadata=chat["metadata"], provider=provider, model=model)
        chat["messages"].extend([
            {"role": "user", "content": question, "dataset": chat["active"]},
            {"role": "assistant", "content": response["answer"], "charts": response.get("charts", []), "dataset": chat["active"]}])
        if chat["title"] == "New Chat":
            chat["title"] = " ".join(question.split()[:7])
        save_chat(chat)
        st.rerun()

footer()
