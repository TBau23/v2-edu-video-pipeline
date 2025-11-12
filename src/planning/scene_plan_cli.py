"""Command-line helpers for inspecting and validating ScenePlan conversions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable, List

from pydantic import ValidationError

from src.primitives.models import Act, Script, VisualSpec

from .scene_plan import ScenePlan, summarize_plan
from .scene_plan_converter import (
    scene_plan_from_visual_spec,
    scene_plans_from_act,
    scene_plans_from_script,
)


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _parse_visual_spec(data: Any) -> VisualSpec:
    return VisualSpec.model_validate(data)


def _parse_act(data: Any) -> Act:
    return Act.model_validate(data)


def _parse_script(data: Any) -> Script:
    return Script.model_validate(data)


def _infer_and_convert(data: Any) -> List[ScenePlan]:
    if isinstance(data, list):
        # treat as list of visual specs
        plans: List[ScenePlan] = []
        for index, item in enumerate(data):
            visual = _parse_visual_spec(item)
            scene_id = f"visual_{index:02d}"
            plans.append(scene_plan_from_visual_spec(visual, scene_id=scene_id))
        return plans

    if isinstance(data, dict):
        if "acts" in data:
            script = _parse_script(data)
            return scene_plans_from_script(script)
        if "visuals" in data and "id" in data:
            act = _parse_act(data)
            return scene_plans_from_act(act)
        if "type" in data and "content" in data:
            visual = _parse_visual_spec(data)
            return [scene_plan_from_visual_spec(visual, scene_id="visual_00")]

    raise ValueError(
        "Unsupported input format. Provide a VisualSpec, Act, Script, or list of VisualSpecs."
    )


def _dump_plans(plans: Iterable[ScenePlan], output_path: Path) -> None:
    as_dict = [plan.model_dump(mode="json") for plan in plans]
    output_path.write_text(json.dumps(as_dict, indent=2), encoding="utf-8")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate and summarize ScenePlan conversions from existing specs."
    )
    parser.add_argument("input", type=Path, help="Path to JSON file containing specs")
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the generated ScenePlans as JSON",
    )

    args = parser.parse_args(argv)

    try:
        data = _load_json(args.input)
        plans = _infer_and_convert(data)
    except (ValidationError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
        return 2

    for plan in plans:
        print(summarize_plan(plan))

    if args.output:
        _dump_plans(plans, args.output)
        print(f"Wrote {len(plans)} plans to {args.output}")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
