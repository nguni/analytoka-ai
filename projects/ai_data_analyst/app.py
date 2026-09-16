"""Analytoka AI: persistent local data analysis workspace."""
import json
from html import escape
from pathlib import Path
import pandas as pd
import streamlit as st
import altair as alt
from agent_groq import run_agent
from workspace import (new_chat, list_chats, save_chat as persist_chat, import_upload, save_frame,
                       transform, apply_change, join_frames, add_relationship, generate_question_starters)
from tools.cleaning_tools import (profile_data_quality, dataframe_to_excel, trim_text_values,
    remove_duplicates, drop_missing_rows, fill_missing_text, fill_numeric_with_median, remove_empty_columns)
from tools.advanced_tools import advanced_analysis
from reports import markdown_report, pdf_report
from ui import inject_styles, brand, topline, welcome, workflow, dataset_heading, overview_banner, footer

st.set_page_config(page_title="Analytoka AI · Data studio", page_icon=str(Path(__file__).parent / "assets" / "favicon.svg"), layout="wide")
inject_styles()

is_signed_in = bool(getattr(st.user, "is_logged_in", False))
user_identity = ((getattr(st.user, "email", None) or getattr(st.user, "sub", None))
                 if is_signed_in else None)

def save_chat(chat):
    if is_signed_in:
        chat["owner"] = user_identity
        persist_chat(chat)

if "chats" not in st.session_state:
    saved_chats = list_chats(owner=user_identity) if is_signed_in else []
    st.session_state.chats = {c["id"]: c for c in saved_chats}
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
    st.markdown('<div class="side-label">CONVERSATIONS</div>', unsafe_allow_html=True)
    ids = list(st.session_state.chats)
    chat_titles = {k: st.session_state.chats[k]["title"] for k in ids}
    st.caption(f"{len(ids)} saved conversation{'s' if len(ids) != 1 else ''}" if is_signed_in else "History is not saved in guest mode")
    for chat_id in ids:
        title = chat_titles[chat_id] or "Untitled conversation"
        if st.button(title, key=f"conversation_{chat_id}", type="primary" if chat_id == st.session_state.active_chat else "secondary", width="stretch"):
            st.session_state.active_chat = chat_id
            st.rerun()
    selected = st.session_state.active_chat
    chat = st.session_state.chats[selected]
    chat.setdefault("relationships", [])
    with st.expander("Add data", expanded=False):
        st.caption("Upload one or more spreadsheets. Every worksheet stays available.")
        files = st.file_uploader("Upload spreadsheets (CSV or Excel)", type=["csv", "xlsx", "xls"],
                                 accept_multiple_files=True, key=f"uploads_{selected}")
    for uploaded in files:
        try:
            import_upload(chat, uploaded.name, uploaded.getvalue())
        except Exception as error:
            st.error(f"{uploaded.name}: {error}")
    with st.expander("Assistant settings", expanded=False):
        st.caption("Choose the assistant that will answer your questions.")
        provider = st.selectbox("Choose your AI assistant", ["Groq", "Gemini"])
        model = st.text_input("Advanced model (optional)", value="openai/gpt-oss-120b" if provider == "Groq" else "gemini-3.6-flash", key=f"model_{provider}")
    with st.expander("What can I ask?", expanded=False):
        st.caption("Try questions about performance, trends, unusual results, gaps, comparisons, or recommendations.")
    if chat["datasets"]:
        names = list(chat["datasets"])
        active = st.selectbox("Data to discuss", names,
                             index=names.index(chat["active"]), key=f"dataset_{selected}_{len(names)}")
        if active != chat["active"]:
            for key in ("analysis", "summary", "recommendations"):
                chat.pop(key, None)
        chat["active"] = active
    with st.expander("Conversation options"):
        if st.button("Clear conversation"):
            chat["messages"] = []
            save_chat(chat)
            st.rerun()
    st.markdown('<div class="sidebar-spacer"></div>', unsafe_allow_html=True)
    if is_signed_in:
        account_name = getattr(st.user, "name", None) or user_identity
        st.markdown(f'<div class="account-panel signed-in"><strong>{escape(account_name)}</strong><span>Signed in · conversations are saved to your account.</span></div>', unsafe_allow_html=True)
        if st.button("Sign out", width="stretch", icon=":material/logout:"):
            st.logout()
    else:
        st.markdown('<div class="account-panel"><strong>Working as a guest</strong><span>Your data and questions stay available while this browser session is open.</span></div>', unsafe_allow_html=True)
        if st.button("Sign in or create an account", width="stretch", icon=":material/login:"):
            try:
                st.login()
            except Exception:
                st.warning("Sign-in is not configured yet. Add the Streamlit authentication settings described in the README.")
        st.caption("Sign in to save and return to conversations.")
    save_chat(chat)
    st.markdown('<div class="side-note"><strong>A space for better questions.</strong><br>Your datasets, conversations, and discoveries. All in one place.</div>', unsafe_allow_html=True)

topline(bool(chat["datasets"]))
if not chat["datasets"]:
    welcome()
    st.markdown('<div class="section-title">Start with your data</div><div class="section-note">Upload a spreadsheet and let us find the story inside it.</div>', unsafe_allow_html=True)
    incoming = st.file_uploader("Upload a spreadsheet (CSV or Excel)", type=["csv", "xlsx", "xls"], accept_multiple_files=True, key=f"welcome_upload_{selected}")
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
        st.caption("Just looking around? Try the sample data to see how it works.")
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
a.metric("Records", f"{len(df):,}")
b.metric("Fields", len(df.columns))
c.metric("Data gaps", int(df.isna().sum().sum()))
d.metric("Repeated records", int(df.duplicated().sum()))
conversation, preview, model_view, clean, combine, analytics, visuals, dictionary, reports = st.tabs(
    ["Ask AI", "Explore", "Model", "Improve data", "Combine data", "Business analysis", "Dashboard", "Definitions", "Reports"])

with preview:
    explore_source = st.selectbox(
        "Choose a sheet or source to explore",
        list(chat["datasets"]),
        index=list(chat["datasets"]).index(chat["active"]),
        format_func=lambda name: name.rsplit(" [", 1)[0],
        key=f"explore_source_{selected}",
    )
    explore_df = read_frame(chat["datasets"][explore_source]["path"])
    overview_banner(explore_df)
    st.markdown('<div class="section-title">Inside your dataset</div><div class="section-note">The details behind the bigger picture.</div>', unsafe_allow_html=True)
    st.dataframe(explore_df.head(1000), hide_index=True, width="stretch")
    st.caption("Preview limited to 1,000 rows; calculations use the full dataset.")
    with st.expander("Field guide · column types and completeness"):
        st.dataframe(pd.DataFrame({"type": explore_df.dtypes.astype(str), "missing": explore_df.isna().sum(), "unique": explore_df.nunique()}), width="stretch")
    if len(explore_df.columns):
        with st.expander("Descriptive statistics · distributions at a glance"):
            st.dataframe(explore_df.describe(include="all").astype(str), width="stretch")

with model_view:
    st.subheader("How your data connects")
    st.caption("Suggested links are based on matching fields and values. Review them before combining data.")
    relationships = chat.get("relationships", [])
    if relationships:
        relationship_rows = [
            {
                "From": f"{item['one']} · {item['one_column']}",
                "To": f"{item['many']} · {item['many_column']}",
                "Relationship": item["cardinality"],
                "Confidence": f"{item['confidence']:.0%}",
                "How found": "Suggested automatically" if item.get("source") == "suggested" else "Added by you",
            }
            for item in relationships
        ]
        st.dataframe(pd.DataFrame(relationship_rows), hide_index=True, width="stretch")
        st.markdown("**Model canvas**")
        connected_names = set()
        model_links = []
        for item in relationships:
            connected_names.update((item["one"], item["many"]))
            model_links.append(
                f'<div class="model-link"><div class="model-node"><strong>{escape(item["one"].rsplit(" [", 1)[0])}</strong><small class="model-field model-key">key · {escape(item["one_column"])}</small></div>'
                f'<div class="model-arrow"><b>&rarr;</b><small>{escape(item["cardinality"])}<br>{escape(item["one_column"])} = {escape(item["many_column"])}</small></div>'
                f'<div class="model-node"><strong>{escape(item["many"].rsplit(" [", 1)[0])}</strong><small class="model-field model-key">key · {escape(item["many_column"])}</small></div></div>'
            )
        for name in chat["datasets"]:
            if name not in connected_names:
                columns = list(pd.read_parquet(chat["datasets"][name]["path"]).columns)
                fields = "".join(f'<small class="model-field">{escape(str(column))}</small>' for column in columns[:8])
                model_links.append(f'<div class="model-node model-unlinked"><strong>{escape(name.rsplit(" [", 1)[0])}</strong>{fields}</div>')
        st.markdown(f'<div class="model-map">{"".join(model_links)}</div>', unsafe_allow_html=True)
    else:
        st.info("No likely relationships found yet. Add another spreadsheet or create one below.")

    if len(chat["datasets"]) >= 2:
        st.markdown("**Create a relationship**")
        model_left, model_right = st.columns(2)
        source_names = list(chat["datasets"])
        one_name = model_left.selectbox("First source", source_names, key=f"model_one_{selected}")
        many_name = model_right.selectbox("Second source", [name for name in source_names if name != one_name], key=f"model_many_{selected}")
        one_frame = pd.read_parquet(chat["datasets"][one_name]["path"])
        many_frame = pd.read_parquet(chat["datasets"][many_name]["path"])
        relation_left, relation_right, relation_kind = st.columns(3)
        one_column = relation_left.selectbox("Matching field", list(one_frame.columns), key=f"model_one_col_{selected}")
        many_column = relation_right.selectbox("Matching field in second source", list(many_frame.columns), key=f"model_many_col_{selected}")
        cardinality = relation_kind.selectbox("How records connect", ["one-to-many", "one-to-one", "many-to-many"], key=f"model_cardinality_{selected}")
        if st.button("Add relationship", key=f"add_relationship_{selected}"):
            add_relationship(chat, one_name, one_column, many_name, many_column, cardinality)
            save_chat(chat)
            st.rerun()

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
    st.subheader("Your business dashboard")
    st.caption("The dashboard adapts to your data. Use the filters to focus the story.")

    numeric = list(df.select_dtypes(include="number").columns)
    date_candidates = []
    for column in df.columns:
        if column in numeric:
            continue
        parsed = pd.to_datetime(df[column], errors="coerce", format="mixed")
        if parsed.notna().sum() >= 2 and parsed.notna().mean() >= 0.8:
            date_candidates.append(column)

    categorical = [
        column for column in df.columns
        if column not in numeric and column not in date_candidates
        and 1 < df[column].nunique(dropna=True) <= 30
    ][:3]
    filtered_df = df.copy()

    with st.container(border=True):
        st.markdown("**Focus the view**")
        filter_columns = st.columns(min(3, max(1, len(date_candidates) + len(categorical))))
        filter_index = 0
        if date_candidates:
            date_column = filter_columns[filter_index].selectbox("Time period", date_candidates, key=f"dashboard_date_{selected}")
            filter_index += 1
            parsed_dates = pd.to_datetime(df[date_column], errors="coerce", format="mixed")
            valid_dates = parsed_dates.dropna()
            start_date = valid_dates.min().date()
            end_date = valid_dates.max().date()
            chosen_dates = st.date_input("From and to", (start_date, end_date), min_value=start_date, max_value=end_date, key=f"dashboard_range_{selected}")
            if isinstance(chosen_dates, tuple) and len(chosen_dates) == 2:
                filtered_df = filtered_df.loc[parsed_dates.dt.date.between(chosen_dates[0], chosen_dates[1])]
        for column in categorical:
            if filter_index >= len(filter_columns):
                break
            values = sorted(df[column].dropna().astype(str).unique().tolist())
            selected_values = filter_columns[filter_index].multiselect(column.replace("_", " ").title(), values, default=values, key=f"dashboard_filter_{selected}_{column}")
            filter_index += 1
            if selected_values:
                filtered_df = filtered_df[filtered_df[column].astype(str).isin(selected_values)]

    if len(filtered_df) == 0:
        st.warning("No data matches these filters. Try widening the view.")
    else:
        st.caption(f"Showing {len(filtered_df):,} of {len(df):,} records")
        kpi_columns = st.columns(min(4, max(1, len(numeric) + 1)))
        kpi_columns[0].metric("Records in view", f"{len(filtered_df):,}", border=True)
        for index, column in enumerate(numeric[:3], start=1):
            value = filtered_df[column].sum()
            label = column.replace("_", " ").title()
            kpi_columns[index].metric(label, f"{value:,.2f}" if isinstance(value, float) else f"{value:,}", border=True)

        chart_config = dict(
            background="#f7f7f2",
            axis=alt.AxisConfig(gridColor="#e2e5dd", domainColor="#d5dcd2", labelColor="#697681", titleColor="#294b53"),
            view=alt.ViewConfig(strokeWidth=0),
        )
        chart_columns = st.columns(2)
        if date_candidates and numeric:
            trend_date = date_candidates[0]
            trend_metric = numeric[0]
            trend_df = filtered_df[[trend_date, trend_metric]].copy()
            trend_df[trend_date] = pd.to_datetime(trend_df[trend_date], errors="coerce", format="mixed")
            trend_df = trend_df.dropna().groupby(pd.Grouper(key=trend_date, freq="MS"))[trend_metric].sum().reset_index()
            trend_chart = alt.Chart(trend_df).mark_line(point=True, color="#d86d42").encode(
                x=alt.X(f"{trend_date}:T", title="Time"),
                y=alt.Y(f"{trend_metric}:Q", title=trend_metric.replace("_", " ").title()),
                tooltip=[alt.Tooltip(f"{trend_date}:T", title="Time"), alt.Tooltip(f"{trend_metric}:Q", title=trend_metric.replace("_", " ").title(), format=",.2f")],
            ).properties(height=300, title="How the main measure changed over time").configure(**chart_config)
            with chart_columns[0]:
                st.altair_chart(trend_chart, width="stretch")
        if categorical and numeric:
            group_column = categorical[0]
            group_metric = numeric[0]
            group_df = filtered_df.groupby(group_column, dropna=False)[group_metric].sum().nlargest(10).reset_index()
            group_chart = alt.Chart(group_df).mark_bar(color="#294b53").encode(
                x=alt.X(f"{group_metric}:Q", title=group_metric.replace("_", " ").title()),
                y=alt.Y(f"{group_column}:N", sort="-x", title=group_column.replace("_", " ").title()),
                tooltip=[group_column, alt.Tooltip(group_metric, format=",.2f")],
            ).properties(height=300, title=f"Top {group_column.replace('_', ' ').title()} by {group_metric.replace('_', ' ').title()}").configure(**chart_config)
            with chart_columns[1 if date_candidates and numeric else 0]:
                st.altair_chart(group_chart, width="stretch")
        elif len(numeric) >= 2:
            scatter = alt.Chart(filtered_df.head(5000)).mark_circle(color="#d86d42", opacity=0.65).encode(
                x=alt.X(f"{numeric[0]}:Q", title=numeric[0].replace("_", " ").title()),
                y=alt.Y(f"{numeric[1]}:Q", title=numeric[1].replace("_", " ").title()),
                tooltip=numeric[:2],
            ).properties(height=300, title="How two measures move together").configure(**chart_config)
            with chart_columns[0]:
                st.altair_chart(scatter, width="stretch")

        st.markdown("**Data behind the charts**")
        st.dataframe(filtered_df.head(500), hide_index=True, width="stretch")

        with st.expander("Build a custom chart or KPI"):
            st.caption("Use this when you already know exactly what you want to compare.")
            custom_columns = st.columns(3)
            custom_x = custom_columns[0].selectbox("Compare by", list(filtered_df.columns), key=f"custom_x_{selected}")
            custom_y = custom_columns[1].selectbox("Measure", [None] + numeric, key=f"custom_y_{selected}")
            custom_kind = custom_columns[2].selectbox("View as", ["Bar", "Line", "Area", "Scatter", "Histogram", "Box plot"], key=f"custom_kind_{selected}")
            if st.button("Show custom view", key=f"custom_chart_{selected}"):
                chart_df = filtered_df.head(5000).copy()
                if custom_kind == "Histogram":
                    custom_chart = alt.Chart(chart_df).mark_bar(color="#294b53").encode(x=alt.X(custom_x, bin=True, title=custom_x.replace("_", " ").title()), y="count()")
                elif custom_kind == "Scatter" and custom_y:
                    custom_chart = alt.Chart(chart_df).mark_circle(color="#d86d42").encode(x=alt.X(custom_x, title=custom_x.replace("_", " ").title()), y=alt.Y(custom_y, title=custom_y.replace("_", " ").title()))
                elif custom_kind == "Box plot" and custom_y:
                    custom_chart = alt.Chart(chart_df).mark_boxplot().encode(x=alt.X(custom_x, title=custom_x.replace("_", " ").title()), y=alt.Y(custom_y, title=custom_y.replace("_", " ").title()))
                elif custom_y:
                    mark_methods = {"Bar": "mark_bar", "Line": "mark_line", "Area": "mark_area"}
                    custom_chart = getattr(alt.Chart(chart_df), mark_methods[custom_kind])().encode(
                        x=alt.X(custom_x, title=custom_x.replace("_", " ").title()),
                        y=alt.Y(custom_y, aggregate="sum", title=custom_y.replace("_", " ").title()),
                    )
                else:
                    st.info("Choose a numeric measure for this view.")
                    custom_chart = None
                if custom_chart is not None:
                    st.altair_chart(custom_chart.properties(height=320).configure(**chart_config), width="stretch")

            if numeric:
                st.markdown("**Create a KPI for your view**")
                kpi_metric = st.selectbox("Measure", numeric, key=f"custom_kpi_metric_{selected}")
                kpi_operation = st.selectbox("Calculate", ["Total", "Average", "Highest", "Lowest"], key=f"custom_kpi_operation_{selected}")
                if st.button("Calculate", key=f"custom_kpi_{selected}"):
                    series = filtered_df[kpi_metric].dropna()
                    operation = {"Total": "sum", "Average": "mean", "Highest": "max", "Lowest": "min"}[kpi_operation]
                    st.metric(f"{kpi_operation} {kpi_metric.replace('_', ' ').title()}", f"{getattr(series, operation)():,.2f}", border=True)

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
    st.subheader("Ask a business question")
    st.caption("Use everyday language. You do not need to know formulas, charts, or code.")
    suggested_questions = generate_question_starters(df)
    question = None
    if not chat["messages"]:
        selected_question = st.pills("Questions based on this data", suggested_questions, label_visibility="visible")
        if selected_question:
            question = selected_question
    for message in chat["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            for chart in message.get("charts", []):
                if Path(chart["path"]).is_file():
                    st.image(chart["path"], caption=chart.get("title"))
    typed_question = st.chat_input("Ask anything about your data")
    if typed_question:
        question = typed_question
    if question:
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
