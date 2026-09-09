import pandas as pd

from tools.data_tools import (
    load_dataset,
    normalize_column_name,
)


# ============================================================
# 1. FULL EXPLORATORY DATA ANALYSIS
# ============================================================

def exploratory_analysis(
    file_path: str,
    sheet_name: str = None
) -> dict:

    df = load_dataset(
        file_path=file_path,
        sheet_name=sheet_name
    )

    numeric_columns = (
        df.select_dtypes(
            include="number"
        ).columns.tolist()
    )

    categorical_columns = [
        column
        for column in df.columns
        if column not in numeric_columns
    ]

    missing = (
        df.isnull()
        .sum()
    )

    missing_columns = {
        column: int(value)
        for column, value in missing.items()
        if value > 0
    }

    numeric_summary = {}

    for column in numeric_columns:

        series = df[column]

        numeric_summary[column] = {
            "count": int(series.count()),
            "mean": (
                float(series.mean())
                if series.count()
                else None
            ),
            "median": (
                float(series.median())
                if series.count()
                else None
            ),
            "minimum": (
                float(series.min())
                if series.count()
                else None
            ),
            "maximum": (
                float(series.max())
                if series.count()
                else None
            ),
            "std": (
                float(series.std())
                if series.count() > 1
                else None
            )
        }

    categorical_summary = {}

    for column in categorical_columns:

        value_counts = (
            df[column]
            .value_counts(
                dropna=True
            )
            .head(10)
            .to_dict()
        )

        categorical_summary[column] = {
            "unique_values": int(
                df[column].nunique()
            ),
            "top_values": {
                str(key): int(value)
                for key, value
                in value_counts.items()
            }
        }

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "missing_values": missing_columns,
        "duplicate_rows": int(
            df.duplicated().sum()
        ),
        "numeric_summary": numeric_summary,
        "categorical_summary": categorical_summary
    }


# ============================================================
# 2. CORRELATION ANALYSIS
# ============================================================

def correlation_analysis(
    file_path: str,
    sheet_name: str = None,
    threshold: float = 0.3
) -> dict:

    df = load_dataset(
        file_path=file_path,
        sheet_name=sheet_name
    )

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
            "for correlation analysis."
        )

    correlation_matrix = (
        numeric_df.corr()
    )

    relationships = []

    columns = (
        correlation_matrix
        .columns
        .tolist()
    )

    for i in range(
        len(columns)
    ):

        for j in range(
            i + 1,
            len(columns)
        ):

            column_a = columns[i]
            column_b = columns[j]

            correlation = (
                correlation_matrix.loc[
                    column_a,
                    column_b
                ]
            )

            if pd.isna(
                correlation
            ):
                continue

            if abs(
                correlation
            ) >= threshold:

                relationships.append(
                    {
                        "column_1": column_a,
                        "column_2": column_b,
                        "correlation": round(
                            float(correlation),
                            4
                        )
                    }
                )

    relationships = sorted(
        relationships,
        key=lambda item: abs(
            item["correlation"]
        ),
        reverse=True
    )

    return {
        "numeric_columns": columns,
        "threshold": threshold,
        "relationships": relationships
    }


# ============================================================
# 3. OUTLIER DETECTION
# ============================================================

def detect_outliers(
    file_path: str,
    column: str,
    sheet_name: str = None
) -> dict:

    df = load_dataset(
        file_path=file_path,
        sheet_name=sheet_name
    )

    column = normalize_column_name(
        column
    )

    if column not in df.columns:

        raise ValueError(
            f"Column '{column}' was not found."
        )

    if not pd.api.types.is_numeric_dtype(
        df[column]
    ):

        raise ValueError(
            f"Column '{column}' is not numeric."
        )

    series = (
        df[column]
        .dropna()
    )

    q1 = float(
        series.quantile(
            0.25
        )
    )

    q3 = float(
        series.quantile(
            0.75
        )
    )

    iqr = q3 - q1

    lower_bound = (
        q1 - 1.5 * iqr
    )

    upper_bound = (
        q3 + 1.5 * iqr
    )

    outlier_mask = (
        (df[column] < lower_bound)
        |
        (df[column] > upper_bound)
    )

    outliers = (
        df[outlier_mask]
        .head(50)
    )

    return {
        "column": column,
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "outlier_count": int(
            outlier_mask.sum()
        ),
        "outlier_percentage": round(
            (
                outlier_mask.sum()
                /
                len(df)
                *
                100
            )
            if len(df)
            else 0,
            2
        ),
        "sample_outliers": (
            outliers
            .fillna("")
            .to_dict(
                orient="records"
            )
        )
    }


# ============================================================
# 4. DISTRIBUTION ANALYSIS
# ============================================================

def analyze_distribution(
    file_path: str,
    column: str,
    sheet_name: str = None
) -> dict:

    df = load_dataset(
        file_path=file_path,
        sheet_name=sheet_name
    )

    column = normalize_column_name(
        column
    )

    if column not in df.columns:

        raise ValueError(
            f"Column '{column}' was not found."
        )

    if not pd.api.types.is_numeric_dtype(
        df[column]
    ):

        raise ValueError(
            f"Column '{column}' is not numeric."
        )

    series = (
        df[column]
        .dropna()
    )

    return {
        "column": column,
        "count": int(
            series.count()
        ),
        "mean": float(
            series.mean()
        ),
        "median": float(
            series.median()
        ),
        "std": float(
            series.std()
        ),
        "minimum": float(
            series.min()
        ),
        "maximum": float(
            series.max()
        ),
        "q1": float(
            series.quantile(
                0.25
            )
        ),
        "q3": float(
            series.quantile(
                0.75
            )
        ),
        "skewness": float(
            series.skew()
        )
    }


# ============================================================
# 5. TIME SERIES ANALYSIS
# ============================================================

def analyze_time_series(
    file_path: str,
    date_column: str,
    metric: str,
    aggregation: str = "sum",
    period: str = "month",
    sheet_name: str = None
) -> dict:

    df = load_dataset(
        file_path=file_path,
        sheet_name=sheet_name
    )

    date_column = normalize_column_name(
        date_column
    )

    metric = normalize_column_name(
        metric
    )

    if date_column not in df.columns:

        raise ValueError(
            f"Date column '{date_column}' was not found."
        )

    if metric not in df.columns:

        raise ValueError(
            f"Metric '{metric}' was not found."
        )

    allowed_aggregations = {
        "sum",
        "mean",
        "median",
        "min",
        "max",
        "count"
    }

    if aggregation not in allowed_aggregations:

        raise ValueError(
            "Unsupported aggregation."
        )

    df = df.copy()

    df[date_column] = pd.to_datetime(
        df[date_column],
        errors="coerce"
    )

    df = df.dropna(
        subset=[
            date_column
        ]
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

    df["_period"] = (
        df[date_column]
        .dt
        .to_period(
            period_mapping[
                period
            ]
        )
        .astype(str)
    )

    result = (
        df.groupby(
            "_period"
        )[metric]
        .agg(
            aggregation
        )
        .sort_index()
    )

    records = [
        {
            "period": str(
                index
            ),
            "value": float(
                value
            )
        }
        for index, value
        in result.items()
    ]

    return {
        "date_column": date_column,
        "metric": metric,
        "period": period,
        "aggregation": aggregation,
        "results": records
    }