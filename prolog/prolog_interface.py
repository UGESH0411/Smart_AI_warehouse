"""Central point of communication with the Prolog knowledge base.

Uses SWI-Prolog through PySwip when available. If SWI-Prolog/pyswip is missing
the interface transparently falls back to an equivalent pure-Python rule engine
(same facts, same rules) so the application never crashes.
"""
import os

RULES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "warehouse_rules.pl")

_ROBOTS = ["r1", "r2", "r3"]
_PACKAGE_TYPE = {"p1": "fragile", "p2": "heavy", "p3": "normal"}
_CAN_CARRY = {"r1": {"fragile", "normal"}, "r2": {"heavy", "normal"}, "r3": {"normal", "fragile"}}
_PRIORITY = {"p1": "high", "p2": "normal", "p3": "low"}


class PrologInterface:
    def __init__(self):
        self.using_prolog = False
        self._prolog = None
        try:
            from pyswip import Prolog
            self._prolog = Prolog()
            self._prolog.consult(RULES_PATH.replace("\\", "/"))
            list(self._prolog.query("robot(r1)"))   # smoke test
            self.using_prolog = True
        except Exception:
            self._prolog = None
            self.using_prolog = False

    def status_message(self):
        if self.using_prolog:
            return "Connected to SWI-Prolog (warehouse_rules.pl loaded)."
        return ("SWI-Prolog / pyswip not available - using the built-in Python fallback "
                "rule engine (identical facts and rules).")

    def robots_for_package(self, package_id):
        if self.using_prolog:
            res = list(self._prolog.query(f"robots_for_package({package_id}, Robots)"))
            return [str(x) for x in res[0]["Robots"]] if res else []
        ptype = _PACKAGE_TYPE.get(package_id)
        return [r for r in _ROBOTS if ptype in _CAN_CARRY[r]] if ptype else []

    def packages_for_robot(self, robot_id):
        if self.using_prolog:
            res = list(self._prolog.query(f"packages_for_robot({robot_id}, Packages)"))
            return [str(x) for x in res[0]["Packages"]] if res else []
        return [p for p, t in _PACKAGE_TYPE.items() if t in _CAN_CARRY.get(robot_id, set())]

    def high_priority_packages(self):
        if self.using_prolog:
            return [str(r["P"]) for r in self._prolog.query("high_priority_package(P)")]
        return [p for p, pr in _PRIORITY.items() if pr == "high"]

    def is_valid_assignment(self, robot_id, package_id):
        if self.using_prolog:
            return bool(list(self._prolog.query(f"valid_assignment({robot_id}, {package_id})")))
        ptype = _PACKAGE_TYPE.get(package_id)
        return ptype is not None and ptype in _CAN_CARRY.get(robot_id, set())
