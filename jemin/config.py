import json, os

DEFAULTS = {
    "DT_S": 0.01,
    "LPF_ALPHA": 0.2,
    "THRESH_G": 3.5,
    "HOLD_MS": 12,
    "THRESH_JERK": 200.0,
    "INHIBIT_MS": 2000,
    "PRE_MS": 1000,
    "POST_MS": 2000,
    "BUFFER_SEC": 3
}

def load_config(path="config.json"):
    cfg = DEFAULTS.copy()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            user = json.load(f)
        cfg.update(user or {})
    # 간단 검증/보정
    cfg["DT_S"] = max(0.001, float(cfg["DT_S"]))
    cfg["BUFFER_SEC"] = max(1, int(cfg["BUFFER_SEC"]))
    return cfg
