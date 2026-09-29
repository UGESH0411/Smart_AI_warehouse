from ai_assistant.api_client import load_config
from ai_assistant.tools import WarehouseToolAdapter, local_answer, openai_tool_specs
from warehouse.grid import WarehouseGrid


class DummyTab:
    def __init__(self):
        self.grid = WarehouseGrid(10, 10)
        self.plan = None
        self.run_mode = None
        self.ai_metrics = None
        self.human_metrics = None

    def is_running(self):
        return self.run_mode is not None

    def run_ai(self):
        self.run_mode = "AI"

    def reset_run(self):
        self.grid.reset_run_state()


def test_env_config_defaults_without_key(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    cfg = load_config(str(tmp_path))
    assert cfg.api_key == ""
    assert cfg.model == "openrouter/free"


def test_tools_read_real_grid_state():
    tab = DummyTab()
    r = tab.grid.add_robot(1, 1)
    p = tab.grid.add_package(2, 3, priority="high")
    adapter = WarehouseToolAdapter(tab)
    assert adapter.get_robot_status(r.robot_id)["position"] == [1, 1]
    assert adapter.get_order_status(p.package_id)["priority"] == "high"
    assert adapter.get_pending_orders()[0]["order_id"] == p.package_id


def test_invalid_ids_are_safe():
    adapter = WarehouseToolAdapter(DummyTab())
    assert "error" in adapter.get_robot_status("R999")
    assert "error" in adapter.get_order_status("P999")


def test_offline_fallback_uses_actual_state():
    tab = DummyTab()
    tab.grid.add_robot(1, 1)
    tab.grid.add_robot(2, 2)
    adapter = WarehouseToolAdapter(tab)
    assert "2 robots" in local_answer("How many robots are there?", adapter)


def test_tool_registry_has_expected_safe_functions():
    names = {item["function"]["name"] for item in openai_tool_specs()}
    assert "get_robot_status" in names
    assert "get_astar_statistics" in names
    assert "start_simulation" in names
    assert "reset_simulation" in names
    assert all(name != "execute_python" for name in names)
