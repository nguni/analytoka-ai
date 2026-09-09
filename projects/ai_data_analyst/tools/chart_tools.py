import os
import uuid

import matplotlib.pyplot as plt
import pandas as pd

from tools.data_tools import (
    load_dataset,
    normalize_column_name,
)


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

OUTPUT_DIRECTORY = os.path.join(
    PROJECT_ROOT,
    "outputs"
)

os.makedirs(
    OUTPUT_DIRECTORY,
    exist_ok=True
)


# ============================================================
# SAVE CHART
# ============================================================

def save_chart(fig, title):

    filename = (
        f"chart_{uuid.uuid4().hex[:10]}.png"
    )

    path = os.path.join(
        OUTPUT_DIRECTORY,
        filename
    )

    fig.tight_layout()

    fig.savefig(
        path,
        dpi=180,
        bbox_inches="tight"
    )

    plt.close(fig)

    return {
        "path": path,
        "title": title
    }


# ============================================================
# CREATE CHART
# ============================================================

def create_chart(
    file_path: str,
    chart_type: str,
    x_column: str = None,
    y_column: str = None,
    aggregation: str = "sum",
    period: str = "month",
    title: str = None,
    sheet_name: str = None
) -> dict:

    df = load_dataset(
        file_path=file_path,
        sheet_name=sheet_name
    )

    chart_type = (
        chart_type
        .strip()
        .lower()
    )

    if x_column:
        x_column = normalize_column_name(
            x_column
        )

    if y_column:
        y_column = normalize_column_name(
            y_column
        )

    allowed_aggregations = {
        "sum",
        "mean",
        "median",
        "count",
        "min",
        "max"
    }

    aggregation = aggregation.lower()

    if aggregation not in allowed_aggregations:
        raise ValueError(
            f"Unsupported aggregation: {aggregation}"
        )


    # ========================================================
    # BAR CHART
    # ========================================================

    if chart_type == "bar":

        if not x_column:
            raise ValueError(
                "Bar chart requires x_column."
            )

        if x_column not in df.columns:
            raise ValueError(
                f"Column '{x_column}' was not found."
            )

        if aggregation == "count":

            grouped = (
                df.groupby(
                    x_column,
                    dropna=False
                )
                .size()
                .sort_values(
                    ascending=False
                )
            )

            ylabel = "Count"

        else:

            if not y_column:
                raise ValueError(
                    "Bar chart requires y_column "
                    "unless aggregation='count'."
                )

            if y_column not in df.columns:
                raise ValueError(
                    f"Column '{y_column}' was not found."
                )

            grouped = (
                df.groupby(
                    x_column,
                    dropna=False
                )[y_column]
                .agg(aggregation)
                .sort_values(
                    ascending=False
                )
            )

            ylabel = (
                f"{aggregation.title()} of "
                f"{y_column.replace('_', ' ').title()}"
            )

        chart_title = (
            title
            or
            f"{ylabel} by "
            f"{x_column.replace('_', ' ').title()}"
        )

        fig, ax = plt.subplots(
            figsize=(10, 6)
        )

        grouped.plot(
            kind="bar",
            ax=ax
        )

        ax.set_title(
            chart_title
        )

        ax.set_xlabel(
            x_column
            .replace("_", " ")
            .title()
        )

        ax.set_ylabel(
            ylabel
        )

        ax.tick_params(
            axis="x",
            rotation=45
        )

        return save_chart(
            fig,
            chart_title
        )


    # ========================================================
    # LINE CHART
    # ========================================================

    elif chart_type == "line":

        if not x_column or not y_column:
            raise ValueError(
                "Line chart requires x_column and y_column."
            )

        if x_column not in df.columns:
            raise ValueError(
                f"Column '{x_column}' was not found."
            )

        if y_column not in df.columns:
            raise ValueError(
                f"Column '{y_column}' was not found."
            )

        working_df = df.copy()

        working_df[x_column] = (
            pd.to_datetime(
                working_df[x_column],
                errors="coerce"
            )
        )

        working_df = (
            working_df.dropna(
                subset=[x_column]
            )
        )

        period_mapping = {
            "day": "D",
            "week": "W",
            "month": "M",
            "quarter": "Q",
            "year": "Y"
        }

        if period not in period_mapping:
            raise ValueError(
                "Period must be day, week, month, quarter or year."
            )

        working_df["_period"] = (
            working_df[x_column]
            .dt
            .to_period(
                period_mapping[period]
            )
            .astype(str)
        )

        grouped = (
            working_df
            .groupby("_period")[y_column]
            .agg(aggregation)
            .sort_index()
        )

        chart_title = (
            title
            or
            (
                f"{y_column.replace('_', ' ').title()} "
                f"trend by {period}"
            )
        )

        fig, ax = plt.subplots(
            figsize=(10, 6)
        )

        ax.plot(
            grouped.index,
            grouped.values,
            marker="o"
        )

        ax.set_title(
            chart_title
        )

        ax.set_xlabel(
            period.title()
        )

        ax.set_ylabel(
            y_column
            .replace("_", " ")
            .title()
        )

        ax.tick_params(
            axis="x",
            rotation=45
        )

        return save_chart(
            fig,
            chart_title
        )


    # ========================================================
    # SCATTER
    # ========================================================

    elif chart_type == "scatter":

        if not x_column or not y_column:
            raise ValueError(
                "Scatter plot requires x_column and y_column."
            )

        if (
            x_column not in df.columns
            or
            y_column not in df.columns
        ):
            raise ValueError(
                "One or more requested columns were not found."
            )

        chart_data = (
            df[
                [
                    x_column,
                    y_column
                ]
            ]
            .dropna()
        )

        chart_title = (
            title
            or
            (
                f"{y_column.replace('_', ' ').title()} "
                f"vs {x_column.replace('_', ' ').title()}"
            )
        )

        fig, ax = plt.subplots(
            figsize=(9, 6)
        )

        ax.scatter(
            chart_data[x_column],
            chart_data[y_column]
        )

        ax.set_title(
            chart_title
        )

        ax.set_xlabel(
            x_column
            .replace("_", " ")
            .title()
        )

        ax.set_ylabel(
            y_column
            .replace("_", " ")
            .title()
        )

        return save_chart(
            fig,
            chart_title
        )


    # ========================================================
    # HISTOGRAM
    # ========================================================

    elif chart_type == "histogram":

        column = (
            y_column
            or
            x_column
        )

        if not column:
            raise ValueError(
                "Histogram requires a numeric column."
            )

        if column not in df.columns:
            raise ValueError(
                f"Column '{column}' was not found."
            )

        if not pd.api.types.is_numeric_dtype(
            df[column]
        ):
            raise ValueError(
                f"Column '{column}' must be numeric."
            )

        chart_title = (
            title
            or
            f"Distribution of "
            f"{column.replace('_', ' ').title()}"
        )

        fig, ax = plt.subplots(
            figsize=(9, 6)
        )

        ax.hist(
            df[column].dropna(),
            bins=20
        )

        ax.set_title(
            chart_title
        )

        ax.set_xlabel(
            column
            .replace("_", " ")
            .title()
        )

        ax.set_ylabel(
            "Frequency"
        )

        return save_chart(
            fig,
            chart_title
        )


    # ========================================================
    # BOX PLOT
    # ========================================================

    elif chart_type == "boxplot":

        column = (
            y_column
            or
            x_column
        )

        if not column:
            raise ValueError(
                "Box plot requires a numeric column."
            )

        if column not in df.columns:
            raise ValueError(
                f"Column '{column}' was not found."
            )

        if not pd.api.types.is_numeric_dtype(
            df[column]
        ):
            raise ValueError(
                f"Column '{column}' must be numeric."
            )

        chart_title = (
            title
            or
            f"Box Plot of "
            f"{column.replace('_', ' ').title()}"
        )

        fig, ax = plt.subplots(
            figsize=(8, 5)
        )

        ax.boxplot(
            df[column].dropna()
        )

        ax.set_title(
            chart_title
        )

        ax.set_ylabel(
            column
            .replace("_", " ")
            .title()
        )

        return save_chart(
            fig,
            chart_title
        )


    # ========================================================
    # PIE CHART
    # ========================================================

    elif chart_type == "pie":

        if not x_column:
            raise ValueError(
                "Pie chart requires x_column."
            )

        if x_column not in df.columns:
            raise ValueError(
                f"Column '{x_column}' was not found."
            )

        if aggregation == "count":

            grouped = (
                df[x_column]
                .value_counts(
                    dropna=False
                )
            )

        else:

            if not y_column:
                raise ValueError(
                    "Pie chart requires y_column "
                    "unless aggregation='count'."
                )

            if y_column not in df.columns:
                raise ValueError(
                    f"Column '{y_column}' was not found."
                )

            grouped = (
                df.groupby(
                    x_column,
                    dropna=False
                )[y_column]
                .agg(aggregation)
                .sort_values(
                    ascending=False
                )
            )

        if len(grouped) > 10:
            raise ValueError(
                "Too many categories for a readable pie chart. "
                "Use a bar chart instead."
            )

        chart_title = (
            title
            or
            f"{x_column.replace('_', ' ').title()} Distribution"
        )

        fig, ax = plt.subplots(
            figsize=(8, 8)
        )

        ax.pie(
            grouped.values,
            labels=grouped.index.astype(str),
            autopct="%1.1f%%"
        )

        ax.set_title(
            chart_title
        )

        return save_chart(
            fig,
            chart_title
        )


    # ========================================================
    # CORRELATION HEATMAP
    # ========================================================

    elif chart_type == "correlation_heatmap":

        numeric_df = (
            df.select_dtypes(
                include="number"
            )
        )

        if len(
            numeric_df.columns
        ) < 2:
            raise ValueError(
                "At least two numeric columns are required "
                "for a correlation heatmap."
            )

        correlation = (
            numeric_df.corr()
        )

        chart_title = (
            title
            or
            "Correlation Heatmap"
        )

        fig, ax = plt.subplots(
            figsize=(10, 8)
        )

        image = ax.imshow(
            correlation.values,
            aspect="auto"
        )

        ax.set_xticks(
            range(
                len(
                    correlation.columns
                )
            )
        )

        ax.set_yticks(
            range(
                len(
                    correlation.columns
                )
            )
        )

        ax.set_xticklabels(
            correlation.columns,
            rotation=45,
            ha="right"
        )

        ax.set_yticklabels(
            correlation.columns
        )

        for row in range(
            len(
                correlation.columns
            )
        ):

            for column in range(
                len(
                    correlation.columns
                )
            ):

                value = (
                    correlation
                    .iloc[
                        row,
                        column
                    ]
                )

                ax.text(
                    column,
                    row,
                    f"{value:.2f}",
                    ha="center",
                    va="center"
                )

        fig.colorbar(
            image,
            ax=ax
        )

        ax.set_title(
            chart_title
        )

        return save_chart(
            fig,
            chart_title
        )


    # ========================================================
    # INVALID TYPE
    # ========================================================

    else:

        raise ValueError(
            f"Unsupported chart type: {chart_type}"
        )