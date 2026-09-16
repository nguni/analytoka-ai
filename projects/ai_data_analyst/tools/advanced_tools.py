"""Deterministic business analytics; undefined ratios remain null."""
import json
import numpy as np
import pandas as pd
from tools.data_tools import load_dataset, normalize_column_name


def advanced_analysis(file_path, operation, metric, group=None, date_column=None,
                      target=None, denominator=None, aggregation="sum", sheet_name=None):
    """Compare groups, pivot, compute monthly growth, targets and ratio KPIs."""
    df = load_dataset(file_path, sheet_name)
    metric, group, date_column, target, denominator = [
        normalize_column_name(c) if c else None
        for c in (metric, group, date_column, target, denominator)]
    if aggregation not in {"sum", "mean", "median", "count", "min", "max"}:
        raise ValueError("Unsupported aggregation")
    def aggregate(series):
        return series.sum(min_count=1) if aggregation == "sum" else series.agg(aggregation)
    if operation == "growth":
        dates = pd.to_datetime(df[date_column], errors="coerce")
        invalid = int(dates.isna().sum())
        values = df.assign(_month=dates.dt.to_period("M")).dropna(subset=["_month"])
        monthly = values.groupby("_month")[metric].apply(aggregate)
        if monthly.empty:
            raise ValueError("No valid dates")
        monthly = monthly.reindex(pd.period_range(monthly.index.min(), monthly.index.max(), freq="M"))
        result = monthly.rename(metric).to_frame()
        for lag, name in [(1, "mom_percent"), (12, "yoy_percent")]:
            previous = monthly.shift(lag).replace(0, np.nan)
            result[name] = (monthly - previous) / previous.abs() * 100
        valid = monthly.dropna()
        slope = float(np.polyfit(np.flatnonzero(monthly.notna()), valid, 1)[0]) if len(valid) > 1 else None
        result.index = result.index.astype(str)
        result = result.rename_axis("month").reset_index()
        extra = {"invalid_dates_excluded": invalid, "linear_trend_per_month": slope}
    elif operation == "pivot":
        result = df.pivot_table(index=group, columns=target, values=metric, aggfunc=aggregate).reset_index()
        result.columns = result.columns.astype(str)
        extra = {}
    elif operation in {"compare", "target", "ratio"}:
        columns = list(dict.fromkeys([metric] + ([target] if operation == "target" else [denominator] if operation == "ratio" else [])))
        result = df.groupby(group, dropna=False)[columns].agg(aggregate).reset_index() if group else pd.DataFrame([{c: aggregate(df[c]) for c in columns}])
        if operation == "compare":
            total = result[metric].sum(min_count=1)
            result["share_percent"] = result[metric] / (total if total != 0 else np.nan) * 100
            result = result.sort_values(metric, ascending=False)
            result["difference_from_leader"] = result[metric] - result[metric].max()
        else:
            base = result[target if operation == "target" else denominator].replace(0, np.nan)
            result["attainment_percent" if operation == "target" else "ratio_percent"] = result[metric] / base * 100
            if operation == "target":
                result["variance"] = result[metric] - result[target]
        extra = {}
    else:
        raise ValueError("Choose compare, growth, pivot, target or ratio")
    return {"operation": operation, "rows": json.loads(result.head(500).to_json(orient="records", date_format="iso")),
            "total_result_rows": len(result), "truncated": len(result) > 500, **extra}
