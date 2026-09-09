import io
import os
import tempfile

import pandas as pd


# ============================================================
# 1. DATA QUALITY PROFILE
# ============================================================

def profile_data_quality(df: pd.DataFrame) -> dict:

    total_rows = len(df)

    missing_by_column = (
        df.isnull()
        .sum()
        .to_dict()
    )

    blank_by_column = {}

    for column in df.columns:

        if pd.api.types.is_object_dtype(df[column]):

            blank_count = (
                df[column]
                .astype(str)
                .str.strip()
                .eq("")
                .sum()
            )

            blank_by_column[column] = int(blank_count)

        else:

            blank_by_column[column] = 0


    duplicate_rows = int(
        df.duplicated().sum()
    )


    return {
        "rows": total_rows,
        "columns": len(df.columns),
        "missing_values": int(
            df.isnull()
            .sum()
            .sum()
        ),
        "missing_by_column": missing_by_column,
        "blank_by_column": blank_by_column,
        "duplicate_rows": duplicate_rows
    }


# ============================================================
# 2. REMOVE DUPLICATES
# ============================================================

def remove_duplicates(df: pd.DataFrame):

    before = len(df)

    cleaned_df = (
        df.drop_duplicates()
        .reset_index(drop=True)
    )

    removed = (
        before - len(cleaned_df)
    )

    return (
        cleaned_df,
        f"Removed {removed} duplicate row(s)."
    )


# ============================================================
# 3. DROP ROWS WITH MISSING VALUES
# ============================================================

def drop_missing_rows(df: pd.DataFrame):

    before = len(df)

    cleaned_df = (
        df.dropna()
        .reset_index(drop=True)
    )

    removed = (
        before - len(cleaned_df)
    )

    return (
        cleaned_df,
        f"Removed {removed} row(s) containing missing values."
    )


# ============================================================
# 4. FILL MISSING TEXT
# ============================================================

def fill_missing_text(
    df: pd.DataFrame,
    value: str = "Unknown"
):

    cleaned_df = df.copy()

    total_filled = 0


    for column in cleaned_df.columns:

        if (
            pd.api.types.is_object_dtype(
                cleaned_df[column]
            )
            or
            pd.api.types.is_string_dtype(
                cleaned_df[column]
            )
        ):

            count = int(
                cleaned_df[column]
                .isnull()
                .sum()
            )

            cleaned_df[column] = (
                cleaned_df[column]
                .fillna(value)
            )

            total_filled += count


    return (
        cleaned_df,
        f"Filled {total_filled} missing text value(s) with '{value}'."
    )


# ============================================================
# 5. FILL NUMERIC WITH MEDIAN
# ============================================================

def fill_numeric_with_median(
    df: pd.DataFrame
):

    cleaned_df = df.copy()

    total_filled = 0


    for column in cleaned_df.select_dtypes(
        include="number"
    ).columns:

        missing_count = int(
            cleaned_df[column]
            .isnull()
            .sum()
        )


        if missing_count > 0:

            median = (
                cleaned_df[column]
                .median()
            )

            cleaned_df[column] = (
                cleaned_df[column]
                .fillna(median)
            )

            total_filled += missing_count


    return (
        cleaned_df,
        f"Filled {total_filled} missing numeric value(s) using column medians."
    )


# ============================================================
# 6. TRIM TEXT VALUES
# ============================================================

def trim_text_values(
    df: pd.DataFrame
):

    cleaned_df = df.copy()

    changed = 0


    for column in cleaned_df.columns:

        if (
            pd.api.types.is_object_dtype(
                cleaned_df[column]
            )
            or
            pd.api.types.is_string_dtype(
                cleaned_df[column]
            )
        ):

            original = (
                cleaned_df[column]
                .copy()
            )


            cleaned_df[column] = (
                cleaned_df[column]
                .apply(
                    lambda value:
                    value.strip()
                    if isinstance(value, str)
                    else value
                )
            )


            changed += int(
                (
                    original.fillna("")
                    !=
                    cleaned_df[column].fillna("")
                )
                .sum()
            )


    return (
        cleaned_df,
        f"Trimmed whitespace from {changed} text value(s)."
    )


# ============================================================
# 7. REMOVE COMPLETELY EMPTY COLUMNS
# ============================================================

def remove_empty_columns(
    df: pd.DataFrame
):

    cleaned_df = df.copy()

    empty_columns = [
        column
        for column in cleaned_df.columns
        if cleaned_df[column].isnull().all()
    ]


    cleaned_df = (
        cleaned_df.drop(
            columns=empty_columns
        )
    )


    return (
        cleaned_df,
        (
            f"Removed {len(empty_columns)} completely empty "
            f"column(s): {empty_columns}"
        )
    )


# ============================================================
# 8. SAVE WORKING DATASET
# ============================================================

def save_working_dataset(
    df: pd.DataFrame,
    original_extension: str,
    sheet_name: str = None
):

    if original_extension == ".csv":

        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".csv"
        )

        temp_file.close()

        df.to_csv(
            temp_file.name,
            index=False
        )

        return temp_file.name


    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".xlsx"
    )

    temp_file.close()


    safe_sheet_name = (
        sheet_name
        if sheet_name
        else "Data"
    )


    with pd.ExcelWriter(
        temp_file.name,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name=safe_sheet_name
        )


    return temp_file.name


# ============================================================
# 9. EXPORT CLEANED CSV
# ============================================================

def dataframe_to_csv(
    df: pd.DataFrame
):

    return df.to_csv(
        index=False
    ).encode("utf-8")


# ============================================================
# 10. EXPORT CLEANED EXCEL
# ============================================================

def dataframe_to_excel(
    df: pd.DataFrame,
    sheet_name: str = "Cleaned Data"
):

    output = io.BytesIO()


    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name=sheet_name
        )


    output.seek(0)

    return output.getvalue()