#!/usr/bin/env python3
"""C 类离线流程记录判题器。"""

from __future__ import annotations

import argparse
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
STEPS = ["power", "seed", "tune", "auth", "transmit", "log"]
MODEL_SPECS = {
    "R-700": {"voltage": Decimal("12.0"), "factor": Decimal("0.5"), "offset": Decimal("121")},
    "T-50": {"voltage": Decimal("9.0"), "factor": Decimal("0.25"), "offset": Decimal("118")},
}


def exact_keys(value: Any, keys: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == keys


def one_decimal_literal(raw: str, field: str) -> str | None:
    pattern = rf'"{re.escape(field)}"\s*:\s*(-?\d+\.\d)(?=\s*[,}}])'
    matches = re.findall(pattern, raw)
    return matches[0] if len(matches) == 1 else None


def load_runtime(number: int) -> dict[str, Any]:
    return json.loads((ROOT / f"runtime_c{number}.json").read_text(encoding="utf-8"))


def verify(number: int, submission_dir: Path) -> tuple[bool, str]:
    answer_path = submission_dir / f"answer_c{number}.json"
    if not answer_path.is_file():
        return False, f"C-{number}: E_MISSING"
    try:
        raw = answer_path.read_text(encoding="utf-8")
        answer = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False, f"C-{number}: E_JSON"

    runtime = load_runtime(number)
    observations = {item["kind"]: item["value"] for item in runtime["observations"]}
    if not exact_keys(answer, {"task", "execution", "submission"}):
        return False, f"C-{number}: E_SCHEMA"
    if answer["task"] != runtime["task_id"] or not isinstance(answer["execution"], list):
        return False, f"C-{number}: E_SCHEMA"
    execution = answer["execution"]
    if len(execution) != len(STEPS):
        return False, f"C-{number}: E_SEQUENCE position={min(len(execution), len(STEPS)) + 1}"
    for index, (entry, expected_step) in enumerate(zip(execution, STEPS), 1):
        if not isinstance(entry, dict) or entry.get("step") != expected_step:
            return False, f"C-{number}: E_SEQUENCE position={index}"

    model = runtime["device_model"]
    spec = MODEL_SPECS[model]

    power = execution[0]
    if not exact_keys(power, {"step", "request"}) or not exact_keys(power["request"], {"model", "voltage"}):
        return False, f"C-{number}: E_POWER"
    if power["request"]["model"] != model or isinstance(power["request"]["voltage"], bool):
        return False, f"C-{number}: E_POWER"
    voltage_literal = one_decimal_literal(raw, "voltage")
    if voltage_literal is None:
        return False, f"C-{number}: E_VOLTAGE_PRECISION"
    try:
        voltage = Decimal(voltage_literal)
    except InvalidOperation:
        return False, f"C-{number}: E_POWER"
    if voltage != spec["voltage"] or Decimal(str(power["request"]["voltage"])) != spec["voltage"]:
        return False, f"C-{number}: E_POWER"

    seed = execution[1]
    expected_seed = observations["crystal_seed"]
    if not exact_keys(seed, {"step", "response"}) or not exact_keys(seed["response"], {"freq_seed"}):
        return False, f"C-{number}: E_SEED"
    if isinstance(seed["response"]["freq_seed"], bool) or seed["response"]["freq_seed"] != expected_seed:
        return False, f"C-{number}: E_SEED"

    tune = execution[2]
    if not exact_keys(tune, {"step", "request"}) or not exact_keys(tune["request"], {"freq"}):
        return False, f"C-{number}: E_FREQUENCY"
    if isinstance(tune["request"]["freq"], bool) or not isinstance(tune["request"]["freq"], (int, float)):
        return False, f"C-{number}: E_FREQUENCY"
    freq_literal = one_decimal_literal(raw, "freq")
    if freq_literal is None:
        return False, f"C-{number}: E_PRECISION"
    expected_freq = Decimal(expected_seed) * spec["factor"] + spec["offset"]
    if Decimal(freq_literal) != expected_freq or Decimal(str(tune["request"]["freq"])) != expected_freq:
        return False, f"C-{number}: E_FREQUENCY"

    auth = execution[3]
    auth_code = observations["authorization_token"]
    if not exact_keys(auth, {"step", "response"}) or not exact_keys(auth["response"], {"code"}):
        return False, f"C-{number}: E_AUTH"
    if auth["response"]["code"] != auth_code:
        return False, f"C-{number}: E_AUTH"

    transmit = execution[4]
    ack = observations["transmission_ack"]
    if not exact_keys(transmit, {"step", "request", "response"}):
        return False, f"C-{number}: E_TRANSMIT"
    if not exact_keys(transmit["request"], {"code", "coord"}) or not exact_keys(transmit["response"], {"ack"}):
        return False, f"C-{number}: E_TRANSMIT"
    if transmit["request"] != {"code": auth_code, "coord": runtime["return_coordinate"]}:
        return False, f"C-{number}: E_TRANSMIT"
    if transmit["response"]["ack"] != ack:
        return False, f"C-{number}: E_TRANSMIT"

    log = execution[5]
    done_code = observations["completion_receipt"]
    if not exact_keys(log, {"step", "request", "response"}):
        return False, f"C-{number}: E_LOG"
    if not exact_keys(log["request"], {"ack"}) or not exact_keys(log["response"], {"done_code"}):
        return False, f"C-{number}: E_LOG"
    if log["request"]["ack"] != ack or log["response"]["done_code"] != done_code:
        return False, f"C-{number}: E_LOG"

    if not exact_keys(answer["submission"], {"done_code"}):
        return False, f"C-{number}: E_SUBMISSION"
    if answer["submission"]["done_code"] != done_code:
        return False, f"C-{number}: E_SUBMISSION"

    return True, f"C-{number}: OK"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=int, choices=range(1, 4))
    parser.add_argument("--submission-dir", type=Path, default=Path("."))
    args = parser.parse_args()
    numbers = [args.task] if args.task else [1, 2, 3]
    results = [verify(number, args.submission_dir) for number in numbers]
    for _, message in results:
        print(message)
    raise SystemExit(0 if all(ok for ok, _ in results) else 1)


if __name__ == "__main__":
    main()
