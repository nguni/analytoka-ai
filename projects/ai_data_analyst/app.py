import os
import tempfile
import uuid

import pandas as pd
import streamlit as st

from agent_groq import run_agent

from tools.cleaning_tools import (
    profile_data_quality,
    remove_duplicates,
    drop_missing_rows,
    fill_missing_text,
    fill_numeric_with_median,
    trim_text_values,
    remove_empty_columns,
    save_working_dataset,
    dataframe_to_csv,
    dataframe_to_excel,
)


# ============================================================
# 1. PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Analytoka AI",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# 2. CUSTOM STYLING
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 0px;
    }

    .subtitle {
        font-size: 18px;
        opacity: 0.75;
        margin-top: 0px;
        margin-bottom: 25px;
    }

    .welcome-box {
        padding: 24px;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        margin-top: 10px;
        margin-bottom: 25px;
    }

    .welcome-title {
        font-size: 25px;
        font-weight: 600;
        margin-bottom: 10px;
    }

    .footer {
        text-align: center;
        padding: 30px 10px 15px 10px;
        margin-top: 45px;
        border-top: 1px solid rgba(128, 128, 128, 0.2);
        font-size: 13px;
        opacity: 0.7;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 3. HELPER FUNCTIONS
# ============================================================

def show_footer():

    st.markdown(
        """
        <div class="footer">
            © 2026 John Muthoka. All rights reserved.<br>
            <strong>Analytoka AI</strong> — AI Data Analyst Agent<br>
            Designed & Developed by John Muthoka
        </div>
        """,
        unsafe_allow_html=True
    )


def create_new_chat():

    chat_id = str(
        uuid.uuid4()
    )

    st.session_state.chats[
        chat_id
    ] = {
        "title": "New Chat",
        "messages": [],
        "original_file_path": None,
        "working_file_path": None,
        "file_name": None,
        "sheet_name": None,
        "previous_file": None,
        "cleaned_df": None,
        "cleaning_history": []
    }

    st.session_state.active_chat = (
        chat_id
    )

    return chat_id


def get_active_chat():

    return st.session_state.chats[
        st.session_state.active_chat
    ]


def generate_chat_title(
    question: str
):

    words = (
        question
        .strip()
        .split()
    )

    title = " ".join(
        words[:6]
    )

    if len(words) > 6:
        title += "..."

    return title


# ============================================================
# 4. SESSION STATE
# ============================================================

if "chats" not in st.session_state:

    st.session_state.chats = {}


if "active_chat" not in st.session_state:

    st.session_state.active_chat = None


if not st.session_state.chats:

    create_new_chat()


active_chat = (
    get_active_chat()
)


# ============================================================
# 5. APPLICATION HEADER
# ============================================================

st.markdown(
    '<p class="main-title">📊 Analytoka AI</p>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <p class="subtitle">
        AI-Powered Data Analyst Agent
    </p>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 6. SIDEBAR
# ============================================================

with st.sidebar:

    st.title(
        "📊 Analytoka AI"
    )

    st.caption(
        "Your AI Data Analyst"
    )

    st.divider()

    st.header(
        "💬 Chats"
    )


    # --------------------------------------------------------
    # NEW CHAT
    # --------------------------------------------------------

    if st.button(
        "➕ New Chat",
        width="stretch"
    ):

        create_new_chat()

        st.rerun()


    # --------------------------------------------------------
    # CHAT LIST
    # --------------------------------------------------------

    for chat_id, chat in (
        st.session_state
        .chats
        .items()
    ):

        button_type = (
            "primary"
            if chat_id
            ==
            st.session_state.active_chat
            else "secondary"
        )

        if st.button(
            chat["title"],
            key=f"chat_{chat_id}",
            width="stretch",
            type=button_type
        ):

            st.session_state.active_chat = (
                chat_id
            )

            st.rerun()


    st.divider()

    st.header(
        "📁 Data Workspace"
    )


    # ========================================================
    # FILE UPLOADER
    # ========================================================

    uploaded_file = st.file_uploader(
        "Upload your dataset",
        type=[
            "xlsx",
            "xls",
            "csv"
        ],
        key=(
            f"upload_"
            f"{st.session_state.active_chat}"
        )
    )


    if uploaded_file is not None:

        extension = (
            os.path.splitext(
                uploaded_file.name
            )[1]
            .lower()
        )

        new_file = (
            active_chat[
                "previous_file"
            ]
            !=
            uploaded_file.name
        )


        # ----------------------------------------------------
        # NEW FILE
        # ----------------------------------------------------

        if new_file:

            active_chat[
                "messages"
            ] = []

            active_chat[
                "sheet_name"
            ] = None

            active_chat[
                "cleaned_df"
            ] = None

            active_chat[
                "cleaning_history"
            ] = []

            active_chat[
                "previous_file"
            ] = uploaded_file.name


        # ----------------------------------------------------
        # SAVE UPLOAD
        # ----------------------------------------------------

        if (
            new_file
            or
            active_chat[
                "original_file_path"
            ]
            is None
        ):

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=extension
            ) as temp_file:

                temp_file.write(
                    uploaded_file.getvalue()
                )

                temp_path = (
                    temp_file.name
                )


            active_chat[
                "original_file_path"
            ] = temp_path

            active_chat[
                "working_file_path"
            ] = temp_path

            active_chat[
                "file_name"
            ] = uploaded_file.name


        st.success(
            f"✓ {uploaded_file.name}"
        )


        # ----------------------------------------------------
        # EXCEL WORKSHEET
        # ----------------------------------------------------

        if extension in [
            ".xlsx",
            ".xls"
        ]:

            try:

                excel_file = (
                    pd.ExcelFile(
                        active_chat[
                            "original_file_path"
                        ]
                    )
                )

                sheet_names = (
                    excel_file
                    .sheet_names
                )

                default_index = 0


                if (
                    active_chat[
                        "sheet_name"
                    ]
                    in sheet_names
                ):

                    default_index = (
                        sheet_names.index(
                            active_chat[
                                "sheet_name"
                            ]
                        )
                    )


                selected_sheet = (
                    st.selectbox(
                        "Select worksheet",
                        options=sheet_names,
                        index=default_index,
                        key=(
                            f"sheet_"
                            f"{st.session_state.active_chat}"
                        )
                    )
                )


                # --------------------------------------------
                # SHEET CHANGED
                # --------------------------------------------

                if (
                    active_chat[
                        "sheet_name"
                    ]
                    is not None
                    and
                    active_chat[
                        "sheet_name"
                    ]
                    !=
                    selected_sheet
                ):

                    active_chat[
                        "messages"
                    ] = []

                    active_chat[
                        "cleaned_df"
                    ] = None

                    active_chat[
                        "cleaning_history"
                    ] = []

                    active_chat[
                        "working_file_path"
                    ] = active_chat[
                        "original_file_path"
                    ]


                active_chat[
                    "sheet_name"
                ] = selected_sheet


                st.caption(
                    f"{len(sheet_names)} worksheet(s)"
                )


            except Exception as error:

                st.error(
                    f"Unable to read workbook: {error}"
                )


        else:

            active_chat[
                "sheet_name"
            ] = None


    st.divider()


    # --------------------------------------------------------
    # CLEAR CHAT
    # --------------------------------------------------------

    if st.button(
        "🗑️ Clear Chat",
        width="stretch"
    ):

        active_chat[
            "messages"
        ] = []

        st.rerun()


    st.divider()

    st.caption(
        "© 2026 John Muthoka"
    )

    st.caption(
        "Designed & Developed by John Muthoka"
    )


# ============================================================
# 7. REFRESH ACTIVE CHAT
# ============================================================

active_chat = (
    get_active_chat()
)


# ============================================================
# 8. WELCOME SCREEN
# ============================================================

if active_chat["original_file_path"] is None:

    st.markdown(
        """
<div class="welcome-box">
<div class="welcome-title">👋 Hey there, I'm Analytoka AI</div>

<p>
I'm your AI-powered <strong>Data Analyst Agent</strong>.
Upload an Excel or CSV dataset and I'll help you explore,
clean, analyze, visualize and uncover meaningful insights
from your data.
</p>

<p>
You don't need to write SQL, Python or complex formulas.
Simply upload your data and ask me questions using
natural language.
</p>
</div>
        """,
        unsafe_allow_html=True
    )

    st.info(
        "👈 Upload an Excel or CSV dataset from the sidebar to get started."
    )

    # ========================================================
    # CAPABILITIES
    # ========================================================

    st.markdown("## ✨ What can I do?")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
### 🔎 Explore
Understand your dataset structure, columns, data types,
distributions and descriptive statistics.
            """
        )

    with col2:
        st.markdown(
            """
### 🧹 Clean
Identify and handle missing values, duplicate records,
blank fields and common data-quality problems.
            """
        )

    with col3:
        st.markdown(
            """
### 📊 Analyze
Ask business questions and let Analytoka AI calculate metrics,
comparisons and performance indicators.
            """
        )

    col4, col5, col6 = st.columns(3)

    with col4:
        st.markdown(
            """
### 📈 Visualize
Generate bar charts, line charts, scatter plots,
histograms, box plots and heatmaps.
            """
        )

    with col5:
        st.markdown(
            """
### 🧠 Discover
Identify trends, correlations, outliers, patterns
and important observations hidden in your data.
            """
        )

    with col6:
        st.markdown(
            """
### 💬 Ask Naturally
Interact with your dataset conversationally
without writing SQL or Python.
            """
        )

    st.divider()

    st.markdown("### 💡 Things you can ask me")

    examples1, examples2 = st.columns(2)

    with examples1:
        st.markdown(
            """
- *Analyze this dataset and give me the key insights.*
- *Which region generated the highest revenue?*
- *What are the top-performing products?*
- *Are there any unusual values or outliers?*
            """
        )

    with examples2:
        st.markdown(
            """
- *Plot the monthly revenue trend.*
- *Show revenue by region as a bar chart.*
- *Analyze correlations and create a heatmap.*
- *What data-quality problems should I fix?*
            """
        )

    show_footer()

    st.stop()


# ============================================================
# 9. LOAD DATA
# ============================================================

original_file_path = (
    active_chat[
        "original_file_path"
    ]
)

working_file_path = (
    active_chat[
        "working_file_path"
    ]
)

extension = (
    os.path.splitext(
        original_file_path
    )[1]
    .lower()
)


try:

    if (
        active_chat[
            "cleaned_df"
        ]
        is not None
    ):

        df = (
            active_chat[
                "cleaned_df"
            ]
            .copy()
        )


    elif extension == ".csv":

        df = (
            pd.read_csv(
                original_file_path
            )
        )


    else:

        df = (
            pd.read_excel(
                original_file_path,
                sheet_name=(
                    active_chat[
                        "sheet_name"
                    ]
                )
            )
        )


except Exception as error:

    st.error(
        f"Unable to read dataset: {error}"
    )

    show_footer()

    st.stop()


# ============================================================
# 10. DATASET HEADER
# ============================================================

st.markdown(
    f"## {active_chat['title']}"
)

st.caption(
    f"📁 Dataset: {active_chat['file_name']}"
)


if active_chat[
    "sheet_name"
]:

    st.caption(
        f"📄 Worksheet: {active_chat['sheet_name']}"
    )


if (
    active_chat[
        "cleaned_df"
    ]
    is not None
):

    st.success(
        "🧹 Analytoka AI is currently working with your cleaned dataset."
    )

else:

    st.info(
        "📊 Analytoka AI is currently working with your original dataset."
    )


# ============================================================
# 11. DATA QUALITY SUMMARY
# ============================================================

quality = (
    profile_data_quality(
        df
    )
)


m1, m2, m3, m4 = (
    st.columns(4)
)


with m1:

    st.metric(
        "Rows",
        f"{quality['rows']:,}"
    )


with m2:

    st.metric(
        "Columns",
        f"{quality['columns']:,}"
    )


with m3:

    st.metric(
        "Missing Values",
        f"{quality['missing_values']:,}"
    )


with m4:

    st.metric(
        "Duplicates",
        f"{quality['duplicate_rows']:,}"
    )


# ============================================================
# 12. DATA TABS
# ============================================================

(
    preview_tab,
    structure_tab,
    stats_tab,
    quality_tab,
    cleaning_tab
) = st.tabs(
    [
        "📋 Preview",
        "🔎 Structure",
        "📈 Statistics",
        "⚠️ Data Quality",
        "🧹 Data Cleaning"
    ]
)


# ============================================================
# 13. PREVIEW
# ============================================================

with preview_tab:

    st.subheader(
        "Dataset Preview"
    )

    st.caption(
        "Showing the first 100 rows."
    )

    st.dataframe(
        df.head(100),
        width="stretch",
        hide_index=True
    )


# ============================================================
# 14. STRUCTURE
# ============================================================

with structure_tab:

    st.subheader(
        "Dataset Structure"
    )

    structure_rows = []


    for column in df.columns:

        structure_rows.append(
            {
                "Column": column,

                "Data Type": str(
                    df[column].dtype
                ),

                "Missing": int(
                    df[column]
                    .isnull()
                    .sum()
                ),

                "Unique Values": int(
                    df[column]
                    .nunique(
                        dropna=True
                    )
                )
            }
        )


    structure_df = (
        pd.DataFrame(
            structure_rows
        )
    )


    st.dataframe(
        structure_df,
        width="stretch",
        hide_index=True
    )


# ============================================================
# 15. STATISTICS
# ============================================================

with stats_tab:

    st.subheader(
        "Descriptive Statistics"
    )


    numeric_df = (
        df.select_dtypes(
            include="number"
        )
    )


    if numeric_df.empty:

        st.info(
            "No numeric columns were detected."
        )


    else:

        st.dataframe(
            numeric_df
            .describe()
            .transpose(),
            width="stretch"
        )


# ============================================================
# 16. DATA QUALITY
# ============================================================

with quality_tab:

    st.subheader(
        "Data Quality Report"
    )


    quality_rows = []


    for column in df.columns:

        missing = int(
            df[column]
            .isnull()
            .sum()
        )


        missing_percentage = (
            missing
            /
            len(df)
            *
            100
            if len(df)
            else 0
        )


        quality_rows.append(
            {
                "Column": column,

                "Missing": missing,

                "Missing %": round(
                    missing_percentage,
                    2
                ),

                "Blank": (
                    quality[
                        "blank_by_column"
                    ]
                    .get(
                        column,
                        0
                    )
                ),

                "Unique": int(
                    df[column]
                    .nunique(
                        dropna=True
                    )
                ),

                "Data Type": str(
                    df[column].dtype
                )
            }
        )


    quality_df = (
        pd.DataFrame(
            quality_rows
        )
    )


    st.dataframe(
        quality_df,
        width="stretch",
        hide_index=True
    )


    q1, q2 = (
        st.columns(2)
    )


    with q1:

        st.metric(
            "Duplicate Rows",
            quality[
                "duplicate_rows"
            ]
        )


    with q2:

        st.metric(
            "Total Missing Values",
            quality[
                "missing_values"
            ]
        )


    if (
        quality[
            "missing_values"
        ]
        == 0
        and
        quality[
            "duplicate_rows"
        ]
        == 0
    ):

        st.success(
            "✓ No obvious missing-value or duplicate issues detected."
        )


# ============================================================
# 17. DATA CLEANING
# ============================================================

with cleaning_tab:

    st.subheader(
        "🧹 Data Cleaning Workspace"
    )

    st.caption(
        "Choose the cleaning operations you want Analytoka AI "
        "to apply to the working copy."
    )

    st.warning(
        "Your original uploaded dataset is never modified."
    )


    before1, before2 = (
        st.columns(2)
    )


    with before1:

        st.metric(
            "Current Rows",
            f"{len(df):,}"
        )


    with before2:

        st.metric(
            "Current Missing Values",
            f"{int(df.isnull().sum().sum()):,}"
        )


    st.divider()


    # --------------------------------------------------------
    # CLEANING OPTIONS
    # --------------------------------------------------------

    remove_dupes = (
        st.checkbox(
            "Remove duplicate rows"
        )
    )


    trim_spaces = (
        st.checkbox(
            "Trim leading/trailing spaces from text"
        )
    )


    remove_empty = (
        st.checkbox(
            "Remove completely empty columns"
        )
    )


    fill_text = (
        st.checkbox(
            "Fill missing text values"
        )
    )


    text_fill_value = (
        st.text_input(
            "Text replacement value",
            value="Unknown",
            disabled=not fill_text
        )
    )


    fill_numeric = (
        st.checkbox(
            "Fill missing numeric values using median"
        )
    )


    drop_missing = (
        st.checkbox(
            "Drop rows that still contain missing values"
        )
    )


    st.divider()


    # --------------------------------------------------------
    # APPLY CLEANING
    # --------------------------------------------------------

    if st.button(
        "🧹 Apply Cleaning",
        type="primary"
    ):

        cleaned_df = (
            df.copy()
        )

        new_history = []


        if remove_dupes:

            cleaned_df, message = (
                remove_duplicates(
                    cleaned_df
                )
            )

            new_history.append(
                message
            )


        if trim_spaces:

            cleaned_df, message = (
                trim_text_values(
                    cleaned_df
                )
            )

            new_history.append(
                message
            )


        if remove_empty:

            cleaned_df, message = (
                remove_empty_columns(
                    cleaned_df
                )
            )

            new_history.append(
                message
            )


        if fill_text:

            cleaned_df, message = (
                fill_missing_text(
                    cleaned_df,
                    text_fill_value
                )
            )

            new_history.append(
                message
            )


        if fill_numeric:

            cleaned_df, message = (
                fill_numeric_with_median(
                    cleaned_df
                )
            )

            new_history.append(
                message
            )


        if drop_missing:

            cleaned_df, message = (
                drop_missing_rows(
                    cleaned_df
                )
            )

            new_history.append(
                message
            )


        if not new_history:

            st.warning(
                "Select at least one cleaning action."
            )


        else:

            active_chat[
                "cleaned_df"
            ] = cleaned_df


            active_chat[
                "cleaning_history"
            ].extend(
                new_history
            )


            working_path = (
                save_working_dataset(
                    cleaned_df,
                    extension,
                    active_chat[
                        "sheet_name"
                    ]
                )
            )


            active_chat[
                "working_file_path"
            ] = working_path


            st.success(
                "✓ Cleaning completed successfully."
            )

            st.rerun()


    # --------------------------------------------------------
    # RESET ORIGINAL
    # --------------------------------------------------------

    if (
        active_chat[
            "cleaned_df"
        ]
        is not None
    ):

        if st.button(
            "↩️ Reset to Original"
        ):

            active_chat[
                "cleaned_df"
            ] = None


            active_chat[
                "working_file_path"
            ] = active_chat[
                "original_file_path"
            ]


            active_chat[
                "cleaning_history"
            ] = []


            st.rerun()


    # --------------------------------------------------------
    # CLEANING HISTORY
    # --------------------------------------------------------

    if active_chat[
        "cleaning_history"
    ]:

        st.divider()

        st.subheader(
            "📜 Cleaning History"
        )


        for index, item in enumerate(
            active_chat[
                "cleaning_history"
            ],
            start=1
        ):

            st.write(
                f"**{index}.** {item}"
            )


    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    if (
        active_chat[
            "cleaned_df"
        ]
        is not None
    ):

        st.divider()

        st.subheader(
            "⬇️ Download Cleaned Data"
        )


        cleaned_df = (
            active_chat[
                "cleaned_df"
            ]
        )


        csv_data = (
            dataframe_to_csv(
                cleaned_df
            )
        )


        excel_data = (
            dataframe_to_excel(
                cleaned_df,
                active_chat[
                    "sheet_name"
                ]
                or
                "Cleaned Data"
            )
        )


        download1, download2 = (
            st.columns(2)
        )


        with download1:

            st.download_button(
                "⬇️ Download CSV",
                data=csv_data,
                file_name=(
                    "Analytoka AI_cleaned_dataset.csv"
                ),
                mime="text/csv",
                width="stretch"
            )


        with download2:

            st.download_button(
                "⬇️ Download Excel",
                data=excel_data,
                file_name=(
                    "Analytoka AI_cleaned_dataset.xlsx"
                ),
                mime=(
                    "application/"
                    "vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                width="stretch"
            )


# ============================================================
# 18. AI ANALYST
# ============================================================

st.divider()

st.markdown(
    "## 🤖 Ask Analytoka AI"
)


if (
    active_chat[
        "cleaned_df"
    ]
    is not None
):

    st.caption(
        "I'm analyzing your cleaned working dataset."
    )


else:

    st.caption(
        "I'm analyzing your original dataset."
    )


# ============================================================
# 19. SUGGESTED QUESTIONS
# ============================================================

example1, example2, example3 = (
    st.columns(3)
)


with example1:

    st.info(
        "💡 Perform a full exploratory analysis."
    )


with example2:

    st.info(
        "📈 Plot the monthly revenue trend."
    )


with example3:

    st.info(
        "🔗 Analyze correlations and show a heatmap."
    )


# ============================================================
# 20. CHAT HISTORY
# ============================================================

for message in (
    active_chat[
        "messages"
    ]
):

    with st.chat_message(
        message[
            "role"
        ]
    ):

        st.markdown(
            message[
                "content"
            ]
        )


        # ----------------------------------------------------
        # HISTORICAL CHARTS
        # ----------------------------------------------------

        for chart in (
            message.get(
                "charts",
                []
            )
        ):

            chart_path = (
                chart.get(
                    "path"
                )
            )


            if (
                chart_path
                and
                os.path.exists(
                    chart_path
                )
            ):

                st.image(
                    chart_path,
                    caption=(
                        chart.get(
                            "title"
                        )
                    ),
                    width="stretch"
                )


# ============================================================
# 21. CHAT INPUT
# ============================================================

question = (
    st.chat_input(
        "Ask Analytoka AI about your data..."
    )
)


# ============================================================
# 22. RUN AGENT
# ============================================================

if question:

    # --------------------------------------------------------
    # GENERATE CHAT TITLE
    # --------------------------------------------------------

    if (
        active_chat[
            "title"
        ]
        ==
        "New Chat"
    ):

        active_chat[
            "title"
        ] = (
            generate_chat_title(
                question
            )
        )


    # --------------------------------------------------------
    # SAVE USER MESSAGE
    # --------------------------------------------------------

    active_chat[
        "messages"
    ].append(
        {
            "role": "user",
            "content": question
        }
    )


    # --------------------------------------------------------
    # SHOW USER MESSAGE
    # --------------------------------------------------------

    with st.chat_message(
        "user"
    ):

        st.markdown(
            question
        )


    # --------------------------------------------------------
    # RUN Analytoka AI AGENT
    # --------------------------------------------------------

    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "Analytoka AI is analyzing your data..."
        ):

            analysis_file = (
                active_chat[
                    "working_file_path"
                ]
            )


            result = (
                run_agent(
                    question=question,
                    file_path=analysis_file,
                    sheet_name=(
                        active_chat[
                            "sheet_name"
                        ]
                    )
                )
            )


        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        if isinstance(
            result,
            dict
        ):

            answer = (
                result.get(
                    "answer",
                    "Analysis completed."
                )
            )


            charts = (
                result.get(
                    "charts",
                    []
                )
            )


        else:

            answer = str(
                result
            )

            charts = []


        # ----------------------------------------------------
        # DISPLAY ANSWER
        # ----------------------------------------------------

        st.markdown(
            answer
        )


        # ----------------------------------------------------
        # DISPLAY CHARTS
        # ----------------------------------------------------

        for chart in charts:

            chart_path = (
                chart.get(
                    "path"
                )
            )


            if (
                chart_path
                and
                os.path.exists(
                    chart_path
                )
            ):

                st.image(
                    chart_path,
                    caption=(
                        chart.get(
                            "title"
                        )
                    ),
                    width="stretch"
                )


    # --------------------------------------------------------
    # SAVE AI RESPONSE
    # --------------------------------------------------------

    active_chat[
        "messages"
    ].append(
        {
            "role": "assistant",
            "content": answer,
            "charts": charts
        }
    )


    st.rerun()


# ============================================================
# 23. FOOTER
# ============================================================

show_footer()