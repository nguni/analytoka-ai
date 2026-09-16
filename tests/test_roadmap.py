import io
import sys
from pathlib import Path
from types import SimpleNamespace
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "projects" / "ai_data_analyst"))
import workspace
from tools.advanced_tools import advanced_analysis
from tools.data_tools import load_dataset

@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setattr(workspace, "ROOT", tmp_path)
    return tmp_path

def test_growth_calendar_gaps_and_zero(root):
    path = workspace.save_frame(pd.DataFrame({"date": ["2024-01-01", "2024-03-01", "2024-04-01", "2024-05-01", "2025-01-01"], "sales": [10, 20, 0, 30, 15]}))
    rows = advanced_analysis(path, "growth", "sales", date_column="date")["rows"]
    assert rows[1]["sales"] is None
    assert rows[2]["mom_percent"] is None
    assert rows[4]["mom_percent"] is None
    assert rows[12]["yoy_percent"] == 50

def test_target_ratio_and_pivot(root):
    path = workspace.save_frame(pd.DataFrame({"team": ["a", "b"], "sales": [20, 5], "target": [10, 0]}))
    result = advanced_analysis(path, "target", "sales", group="team", target="target")["rows"]
    assert result[0]["attainment_percent"] == 200
    assert result[1]["attainment_percent"] is None
    assert advanced_analysis(path, "ratio", "sales", denominator="target")["rows"][0]["ratio_percent"] == 250
    assert len(advanced_analysis(path, "pivot", "sales", group="team", target="target")["rows"]) == 2

def test_cleaning_preserves_original_and_types(root):
    df = pd.DataFrame({"name": [" A ", None], "date": ["2024-01-01", None]})
    chat = workspace.new_chat()
    original = workspace.save_frame(df)
    chat["active"] = "data"
    chat["datasets"]["data"] = {"path": original, "original": original, "undo": []}
    changed = workspace.transform(df, "date", "Convert to date")
    workspace.apply_change(chat, changed, "date conversion")
    assert pd.api.types.is_datetime64_any_dtype(pd.read_parquet(chat["datasets"]["data"]["path"])["date"])
    pd.testing.assert_frame_equal(pd.read_parquet(original), df)
    assert chat["datasets"]["data"]["undo"] == [original]
    assert workspace.transform(df, "name", "Standardize categories")["name"].iloc[0] == "a"

def test_storage_round_trip(root):
    chat = workspace.new_chat()
    chat["messages"] = [{"role": "user", "content": "hello"}]
    workspace.save_chat(chat)
    assert workspace.list_chats() == [chat]

def test_import_all_sheets_and_same_name_changes(root):
    output = io.BytesIO()
    with pd.ExcelWriter(output) as writer:
        pd.DataFrame({"x": [1]}).to_excel(writer, sheet_name="one", index=False)
        pd.DataFrame({"x": [2]}).to_excel(writer, sheet_name="two", index=False)
    chat = workspace.new_chat()
    workspace.import_upload(chat, "book.xlsx", output.getvalue())
    workspace.import_upload(chat, "book.xlsx", output.getvalue())
    assert len(chat["datasets"]) == 2
    workspace.import_upload(chat, "file.csv", b"x\n1\n")
    workspace.import_upload(chat, "file.csv", b"x\n2\n")
    assert len(chat["datasets"]) == 4

def test_join_cardinality_and_null_guard():
    with pytest.raises(pd.errors.MergeError):
        workspace.join_frames(pd.DataFrame({"id": [1]}), pd.DataFrame({"id": [1, 1]}), "id", "id", "left")
    with pytest.raises(ValueError):
        workspace.join_frames(pd.DataFrame({"id": [None]}), pd.DataFrame({"id": [None]}), "id", "id", "left")

def test_excel_defaults_and_column_collision(root):
    path = root / "data.xlsx"
    pd.DataFrame({"Amount": [3]}).to_excel(path, index=False)
    assert load_dataset(str(path))["amount"].iloc[0] == 3
    path = workspace.save_frame(pd.DataFrame({"A B": [1], "a-b": [2]}))
    with pytest.raises(ValueError, match="collide"):
        load_dataset(path)

def test_agent_memory_and_forced_dataset(root, monkeypatch):
    import agent_groq as agent
    calls = []
    responses = [SimpleNamespace(content=None, tool_calls=[SimpleNamespace(id="t1", function=SimpleNamespace(name="inspect_dataset", arguments='{"file_path":"wrong", "sheet_name":"wrong"}'))]), SimpleNamespace(content="done", tool_calls=None)]
    def create(**kwargs):
        calls.append([dict(m) for m in kwargs["messages"]])
        return SimpleNamespace(choices=[SimpleNamespace(message=responses.pop(0))])
    monkeypatch.setattr(agent, "get_client", lambda provider: SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    observed = {}
    monkeypatch.setitem(agent.tool_registry, "inspect_dataset", lambda **kw: observed.update(kw) or {"rows": 1})
    result = agent.run_agent("and last year?", "current.parquet", history=[{"role": "user", "content": "sales"}], metadata="sales: invoiced revenue")
    assert result["answer"] == "done"
    assert observed == {"file_path": "current.parquet", "sheet_name": None}
    assert calls[0][1]["content"] == "sales"
    assert "invoiced revenue" in calls[0][0]["content"]

def test_metadata_retrieval():
    assert workspace.retrieve_metadata("revenue", "employees: people\nrevenue: net sales", 1) == "revenue: net sales"

def test_app_startup_without_key(root):
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "projects/ai_data_analyst/app.py")).run(timeout=30)
    assert not app.exception

def test_app_loaded_workspace(root):
    from streamlit.testing.v1 import AppTest
    chat = workspace.new_chat()
    workspace.import_upload(chat, "sample.csv", b"region,sales,target,date\nEast,10,12,2024-01-01\nWest,20,15,2024-02-01\n")
    workspace.save_chat(chat)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "projects/ai_data_analyst/app.py")).run(timeout=30)
    assert not app.exception
    next(b for b in app.button if b.label == "Calculate").click().run(timeout=30)
    assert not app.exception
    next(b for b in app.button if b.label == "Preview cleaning").click().run(timeout=30)
    assert not app.exception
    next(b for b in app.button if b.label == "Apply previewed change").click().run(timeout=30)
    assert not app.exception
    next(b for b in app.button if b.label == "Undo last change").click().run(timeout=30)
    assert not app.exception

def test_agent_recovers_from_malformed_arguments(monkeypatch):
    import agent_groq as agent
    responses = [SimpleNamespace(content=None, tool_calls=[SimpleNamespace(id="t", function=SimpleNamespace(name="inspect_dataset", arguments='[]'))]), SimpleNamespace(content="recovered", tool_calls=None)]
    def create(**kwargs):
        return SimpleNamespace(choices=[SimpleNamespace(message=responses.pop(0))])
    monkeypatch.setattr(agent, "get_client", lambda provider: SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    monkeypatch.setitem(agent.tool_registry, "inspect_dataset", lambda **kw: {"rows": 2})
    assert agent.run_agent("inspect", "current.parquet")["answer"] == "recovered"

def test_groq_tool_schemas_allow_null_sheet_name():
    import agent_groq as agent

    for tool in agent.tools:
        properties = tool["function"]["parameters"]["properties"]
        assert properties["sheet_name"]["type"] == ["string", "null"]

def test_gemini_missing_key_does_not_require_secrets_file(monkeypatch):
    import agent_groq as agent

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    result = agent.run_agent("inspect", "current.parquet", provider="Gemini")
    assert result["error"] is True
    assert "Set GEMINI_API_KEY" in result["answer"]
    assert "No secrets found" not in result["answer"]

def test_outliers_and_conversion_failure():
    df = pd.DataFrame({"value": [1, 2, 2, 3, 100, None]})
    result = workspace.transform(df, "value", "Cap outliers")
    assert result["value"].max() < 100
    assert result["value"].isna().sum() == 1
    assert df["value"].max() == 100
    with pytest.raises(ValueError):
        workspace.transform(pd.DataFrame({"x": ["oops"]}), "x", "Convert to number")

def test_app_dataset_switch_and_new_chat(root):
    from streamlit.testing.v1 import AppTest
    chat = workspace.new_chat()
    workspace.import_upload(chat, "one.csv", b"x,value\na,1\n")
    workspace.import_upload(chat, "two.csv", b"x,value\nb,2\n")
    chat["summary"] = "stale summary"
    workspace.save_chat(chat)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "projects/ai_data_analyst/app.py")).run(timeout=60)
    assert not app.exception
    box = next(s for s in app.selectbox if s.label == "Active dataset / worksheet")
    box.select(list(chat["datasets"])[0]).run(timeout=60)
    assert not app.exception
    assert "summary" not in app.session_state.chats[chat["id"]]
    next(b for b in app.button if b.label == "New chat").click().run(timeout=60)
    assert not app.exception
    assert app.session_state.active_chat != chat["id"]
