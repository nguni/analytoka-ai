import re
import pandas as pd


# ============================================================
# 1. COLUMN NORMALIZATION
# ============================================================

def normalize_column_name(column_name: str) -> str:
    """
    Convert column names into a consistent internal format.

    Examples:
    Quantity       -> quantity
    Unit Price     -> unit_price
    Unit_Price     -> unit_price
    SALES REGION   -> sales_region
    """

    column_name = str(column_name).strip().lower()

    column_name = re.sub(
        r"[^a-z0-9]+",
        "_",
        column_name
    )

    column_name = column_name.strip("_")

    return column_name


# ============================================================
# 2. LOAD DATASET
# ============================================================

def load_dataset(
    file_path: str,
    sheet_name: str = None
) -> pd.DataFrame:
    """
    Load a CSV or Excel dataset.

    Excel files can optionally specify a worksheet.
    Column names are normalized internally.
    """

    file_path_lower = file_path.lower()

    if file_path_lower.endswith(".csv"):

        df = pd.read_csv(
            file_path
        )

    elif file_path_lower.endswith((".xlsx", ".xls")):

        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name
        )

    else:

        raise ValueError(
            "Unsupported file type. "
            "Please use CSV or Excel."
        )


    # Normalize column names
    df.columns = [
        normalize_column_name(column)
        for column in df.columns
    ]

    return df


# ============================================================
# 3. INSPECT DATASET
# ============================================================

def inspect_dataset(
    file_path: str,
    sheet_name: str = None
) -> dict:
    """
    Inspect dataset structure.
    """

    df = load_dataset(
        file_path=file_path,
        sheet_name=sheet_name
    )


    return {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": df.columns.tolist(),
        "data_types": (
            df.dtypes
            .astype(str)
            .to_dict()
        ),
        "missing_values": (
            df.isnull()
            .sum()
            .to_dict()
        ),
        "duplicate_rows": int(
            df.duplicated().sum()
        )
    }


# ============================================================
# 4. DATASET SAMPLE
# ============================================================

def get_dataset_sample(
    file_path: str,
    sheet_name: str = None,
    rows: int = 5
) -> dict:
    """
    Return a small sample of the dataset.
    """

    df = load_dataset(
        file_path=file_path,
        sheet_name=sheet_name
    )


    rows = max(
        1,
        min(rows, 20)
    )


    sample = (
        df.head(rows)
        .fillna("")
        .to_dict(
            orient="records"
        )
    )


    return {
        "rows_returned": len(sample),
        "sample": sample
    }


# ============================================================
# 5. COLUMN STATISTICS
# ============================================================

def get_column_statistics(
    file_path: str,
    column: str,
    sheet_name: str = None
) -> dict:
    """
    Return statistics for one column.
    """

    df = load_dataset(
        file_path=file_path,
        sheet_name=sheet_name
    )


    column = normalize_column_name(
        column
    )


    if column not in df.columns:

        raise ValueError(
            f"Column '{column}' was not found. "
            f"Available columns: {df.columns.tolist()}"
        )


    series = df[column]


    result = {
        "column": column,
        "data_type": str(series.dtype),
        "missing_values": int(
            series.isnull().sum()
        ),
        "unique_values": int(
            series.nunique()
        )
    }


    # Numeric statistics
    if pd.api.types.is_numeric_dtype(series):

        result.update(
            {
                "count": int(series.count()),
                "sum": float(series.sum()),
                "mean": float(series.mean()),
                "median": float(series.median()),
                "minimum": float(series.min()),
                "maximum": float(series.max())
            }
        )

    else:

        top_values = (
            series
            .value_counts(dropna=True)
            .head(10)
            .to_dict()
        )

        result["top_values"] = top_values


    return result


# ============================================================
# 6. GROUP AND AGGREGATE
# ============================================================

def group_and_aggregate(
    file_path: str,
    group_by: str,
    metric: str,
    aggregation: str = "sum",
    sheet_name: str = None
) -> dict:
    """
    Group data by one column and aggregate another column.

    Supported aggregations:
    sum
    mean
    median
    min
    max
    count
    """

    df = load_dataset(
        file_path=file_path,
        sheet_name=sheet_name
    )


    group_by = normalize_column_name(
        group_by
    )

    metric = normalize_column_name(
        metric
    )


    if group_by not in df.columns:

        raise ValueError(
            f"Group column '{group_by}' was not found. "
            f"Available columns: {df.columns.tolist()}"
        )


    if metric not in df.columns:

        raise ValueError(
            f"Metric column '{metric}' was not found. "
            f"Available columns: {df.columns.tolist()}"
        )


    allowed_aggregations = {
        "sum",
        "mean",
        "median",
        "min",
        "max",
        "count"
    }


    aggregation = aggregation.lower()


    if aggregation not in allowed_aggregations:

        raise ValueError(
            f"Unsupported aggregation '{aggregation}'. "
            f"Use one of: "
            f"{sorted(allowed_aggregations)}"
        )


    grouped = (
        df.groupby(
            group_by,
            dropna=False
        )[metric]
        .agg(aggregation)
        .sort_values(
            ascending=False
        )
    )


    results = {}

    for key, value in grouped.items():

        key_string = (
            "Missing"
            if pd.isna(key)
            else str(key)
        )


        if isinstance(
            value,
            (int, float)
        ):

            results[key_string] = float(value)

        else:

            results[key_string] = value


    return {
        "group_by": group_by,
        "metric": metric,
        "aggregation": aggregation,
        "results": results
    }


# ============================================================
# 7. SORT AND RANK
# ============================================================

def sort_and_rank(
    file_path: str,
    column: str,
    sheet_name: str = None,
    ascending: bool = False,
    limit: int = 10
) -> dict:
    """
    Sort rows by a column and return the top records.
    """

    df = load_dataset(
        file_path=file_path,
        sheet_name=sheet_name
    )


    column = normalize_column_name(
        column
    )


    if column not in df.columns:

        raise ValueError(
            f"Column '{column}' was not found. "
            f"Available columns: {df.columns.tolist()}"
        )


    limit = max(
        1,
        min(limit, 50)
    )


    sorted_df = (
        df.sort_values(
            by=column,
            ascending=ascending
        )
        .head(limit)
    )


    return {
        "sorted_by": column,
        "ascending": ascending,
        "limit": limit,
        "records": (
            sorted_df
            .fillna("")
            .to_dict(
                orient="records"
            )
        )
    }