"""Workspace storage, reversible transformations and metadata retrieval."""
import hashlib
import io
import json
import os
import re
import sqlite3
import uuid
from pathlib import Path
import pandas as pd

ROOT = Path(os.getenv("ANALYTOKA_DATA_DIR", Path(__file__).parent / ".workspace"))


def connect():
    ROOT.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(ROOT / "chats.sqlite3")
    db.execute("CREATE TABLE IF NOT EXISTS chats (id TEXT PRIMARY KEY, body TEXT NOT NULL)")
    return db


def save_chat(chat):
    with connect() as db:
        db.execute("INSERT OR REPLACE INTO chats VALUES (?, ?)", (chat["id"], json.dumps(chat)))


def list_chats(owner=None):
    with connect() as db:
        chats = [json.loads(row[0]) for row in db.execute("SELECT body FROM chats ORDER BY rowid DESC")]
    if owner is None:
        return chats
    return [chat for chat in chats if chat.get("owner") == owner]


def new_chat():
    return {"id": uuid.uuid4().hex, "title": "New Chat", "messages": [], "datasets": {}, "relationships": [], "active": None, "metadata": "", "history": []}


def save_frame(df):
    ROOT.mkdir(parents=True, exist_ok=True)
    path = ROOT / (uuid.uuid4().hex + ".parquet")
    df.to_parquet(path, index=False)
    return str(path)


def read_upload(name, data):
    if len(data) > 200 * 1024 * 1024:
        raise ValueError("Files must be 200 MB or smaller")
    if name.lower().endswith(".csv"):
        return {name: pd.read_csv(io.BytesIO(data))}
    with pd.ExcelFile(io.BytesIO(data)) as book:
        return {f"{name} / {sheet}": pd.read_excel(book, sheet_name=sheet) for sheet in book.sheet_names}


def import_upload(chat, name, data):
    digest = hashlib.sha256(data).hexdigest()
    if digest in chat.setdefault("uploads", []):
        return
    frames = read_upload(name, data)
    for label, frame in frames.items():
        key = f"{label} [{digest[:8]}]"
        path = save_frame(frame)
        chat["datasets"][key] = {"original": path, "path": path, "undo": []}
        chat["active"] = key
    for key in ("analysis", "summary", "recommendations"):
        chat.pop(key, None)
    chat["uploads"].append(digest)
    chat["relationships"] = infer_relationships(chat["datasets"])


def _relationship_candidates(left_name, left_frame, right_name, right_frame):
    candidates = []
    for left_column in left_frame.columns:
        left_values = left_frame[left_column].dropna()
        if left_values.empty:
            continue
        for right_column in right_frame.columns:
            right_values = right_frame[right_column].dropna()
            if right_values.empty:
                continue
            left_key = normalize_column(left_column)
            right_key = normalize_column(right_column)
            if left_key != right_key and left_key not in {"id", "key"} and right_key not in {"id", "key"}:
                continue
            comparable_left = set(left_values.astype(str).head(10000))
            comparable_right = set(right_values.astype(str).head(10000))
            overlap = len(comparable_left & comparable_right) / max(1, min(len(comparable_left), len(comparable_right)))
            if overlap < 0.5:
                continue
            left_unique = left_values.nunique() == len(left_values)
            right_unique = right_values.nunique() == len(right_values)
            if left_unique and not right_unique:
                one_name, one_column, many_name, many_column = left_name, left_column, right_name, right_column
            elif right_unique and not left_unique:
                one_name, one_column, many_name, many_column = right_name, right_column, left_name, left_column
            else:
                one_name, one_column, many_name, many_column = left_name, left_column, right_name, right_column
            candidates.append({
                "one": one_name,
                "one_column": str(one_column),
                "many": many_name,
                "many_column": str(many_column),
                "cardinality": "one-to-many" if left_unique != right_unique else "many-to-many",
                "confidence": round(min(0.99, overlap + (0.2 if left_key == right_key else 0)), 2),
                "source": "suggested",
            })
    return candidates


def normalize_column(column):
    return re.sub(r"[^a-z0-9]+", "_", str(column).strip().casefold()).strip("_")


def infer_relationships(datasets):
    relationships = []
    names = list(datasets)
    for left_index, left_name in enumerate(names):
        left_frame = pd.read_parquet(datasets[left_name]["path"])
        for right_name in names[left_index + 1:]:
            right_frame = pd.read_parquet(datasets[right_name]["path"])
            candidates = _relationship_candidates(left_name, left_frame, right_name, right_frame)
            if candidates:
                relationships.append(max(candidates, key=lambda item: item["confidence"]))
    return relationships


def add_relationship(chat, one, one_column, many, many_column, cardinality="one-to-many"):
    relationship = {
        "one": one,
        "one_column": one_column,
        "many": many,
        "many_column": many_column,
        "cardinality": cardinality,
        "confidence": 1.0,
        "source": "manual",
    }
    chat.setdefault("relationships", [])
    chat["relationships"] = [
        item for item in chat["relationships"]
        if not (item["one"] == one and item["one_column"] == one_column and item["many"] == many and item["many_column"] == many_column)
    ] + [relationship]
    return relationship


def transform(df, column, action, value=""):
    result = df.copy()
    if action == "Remove duplicates":
        return result.drop_duplicates().reset_index(drop=True)
    s = result[column]
    if action == "Trim text":
        result[column] = s.map(lambda v: v.strip() if isinstance(v, str) else v)
    elif action == "Standardize categories":
        result[column] = s.astype("string").str.strip().str.casefold()
    elif action == "Category mapping":
        mapping = json.loads(value)
        if not isinstance(mapping, dict):
            raise ValueError("Enter a JSON object mapping old categories to new ones")
        result[column] = s.replace(mapping)
    elif action == "Convert to number":
        result[column] = pd.to_numeric(s, errors="raise")
    elif action == "Convert to date":
        result[column] = pd.to_datetime(s, errors="raise")
    elif action == "Fill missing":
        result[column] = s.fillna(float(value) if pd.api.types.is_numeric_dtype(s) else value)
    elif action == "Fill median":
        median = s.median()
        if pd.isna(median):
            raise ValueError("No numeric values available for a median")
        result[column] = s.fillna(median)
    elif action == "Drop missing rows":
        result = result.dropna(subset=[column])
    elif action == "Remove empty column":
        if not s.isna().all():
            raise ValueError("Column is not empty")
        result = result.drop(columns=[column])
    elif action in {"Cap outliers", "Remove outliers"}:
        q1, q3 = s.quantile([.25, .75])
        low, high = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
        if action == "Cap outliers":
            result[column] = s.clip(low, high)
        else:
            result = result[s.isna() | s.between(low, high)]
    else:
        raise ValueError("Unknown cleaning action")
    return result


def apply_change(chat, frame, description):
    dataset = chat["datasets"][chat["active"]]
    dataset["undo"].append(dataset["path"])
    dataset["path"] = save_frame(frame)
    for key in ("analysis", "summary", "recommendations"):
        chat.pop(key, None)
    chat["history"].append({"dataset": chat["active"], "action": description})


def join_frames(left, right, left_key, right_key, how, validate="many_to_one"):
    # Null keys must not match one another as they do in pandas.merge by default.
    if left[left_key].isna().any() or right[right_key].isna().any():
        raise ValueError("Resolve missing join keys before combining datasets")
    return left.merge(right, left_on=left_key, right_on=right_key, how=how, validate=validate,
                      suffixes=("_left", "_right"))


def retrieve_metadata(question, metadata, limit=8):
    terms = set(re.findall(r"\w+", question.casefold()))
    lines = [line for line in metadata.splitlines() if line.strip()]
    ranked = sorted(enumerate(lines), key=lambda item: (-len(terms & set(re.findall(r"\w+", item[1].casefold()))), item[0]))
    return "\n".join(line[:1000] for _, line in ranked[:limit])


def generate_question_starters(frame):
    """Create plain-language questions from the active source's fields."""
    numeric = list(frame.select_dtypes(include="number").columns)
    categorical = [
        column for column in frame.columns
        if column not in numeric and 1 < frame[column].nunique(dropna=True) <= 30
    ]
    date_columns = []
    for column in frame.columns:
        if column in numeric:
            continue
        parsed = pd.to_datetime(frame[column], errors="coerce", format="mixed")
        if parsed.notna().sum() >= 2 and parsed.notna().mean() >= 0.8:
            date_columns.append(column)

    def label(column):
        return str(column).replace("_", " ").strip().lower()

    starters = ["What are the most important things I should know about this information?"]
    if numeric and categorical:
        starters.append(f"Which {label(categorical[0])} is performing best for {label(numeric[0])}?")
        starters.append(f"How does {label(numeric[0])} differ across {label(categorical[0])}?")
    elif numeric:
        starters.append(f"What is the overall {label(numeric[0])}, and are there any unusual results?")
    if date_columns and numeric:
        starters.append(f"How has {label(numeric[0])} changed over {label(date_columns[0])}?")
    if categorical:
        starters.append(f"What patterns can you find in {label(categorical[0])}?")
    if frame.isna().any().any():
        starters.append("Are there information gaps that could affect my decisions?")
    return starters[:5]
