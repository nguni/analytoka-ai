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


def list_chats():
    with connect() as db:
        return [json.loads(row[0]) for row in db.execute("SELECT body FROM chats ORDER BY rowid DESC")]


def new_chat():
    return {"id": uuid.uuid4().hex, "title": "New Chat", "messages": [], "datasets": {}, "active": None, "metadata": "", "history": []}


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
