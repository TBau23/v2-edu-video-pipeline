# codex-test1 Experiment Plan

> **Branch context:** All exploratory work for this initiative lives on the `codex-test1` branch so the primary `work` branch remains untouched until the experiment is validated.

## Goals
- Improve determinism and quality of generated educational animations.
- Prototype structured planning pipeline separating specification, layout, and timeline stages.
- Define metrics and tooling to evaluate animation composition before rendering.

## Hypothesis
A multi-stage pipeline that consumes a structured scene graph specification, applies deterministic layout and timeline compilation, and leverages parameterized animation templates will reduce visual collisions, incoherent motion, and inconsistent pacing in automatically generated videos.

## Deliverables
1. **Specification Schema**
   - A typed schema (Pydantic or dataclasses) for a `ScenePlan` describing nodes, anchors, constraints, and timeline beats.
   - Validator to ensure plans are complete, consistent, and within supported capabilities.
   - Conversion utilities from current `VisualSpec` to new schema for backward compatibility during experimentation.

2. **Layout Engine Prototype**
   - Deterministic placement logic assigning bounding boxes to scene graph nodes based on anchors and constraints.
   - Collision detection that rejects or adjusts conflicting placements.
   - Debug visualization (matplotlib or ASCII) to inspect computed layout without rendering via Manim.

3. **Timeline Compiler**
   - Build a timeline representation enumerating entrance, interaction, and exit beats with absolute timings.
   - Support sequencing/staggering helpers (e.g., `enter_after`, `overlap`, `hold`) and easing presets.
   - Provide dry-run simulator to verify object states over time and detect conflicting motions.

4. **Template-driven Animation Library**
   - Refactor or wrap existing animation primitives to expose structured slots (e.g., `main_object`, `comparison_object`, `annotation`).
   - Metadata per template: footprint, default durations, supported modifiers.
   - Mapping from timeline beats to concrete Manim calls using template metadata and layout output.

5. **Evaluation & Instrumentation**
   - Frame sampling heuristics for overlap detection and motion sanity checks post-render.
   - Logging/reporting pipeline capturing validation failures, layout warnings, and simulation anomalies.

6. **Integration Plan**
   - Strategy to gradually integrate pipeline into existing video generation flow.
   - Fallback path to legacy renderer while new pipeline matures.

## Milestones
1. **M1 – Schema + Validators (Week 1)**
   - Draft schema and converters.
   - Implement validation CLI for inspecting sample lessons.

2. **M2 – Layout + Debugger (Week 1-2)**
   - Layout prototype with visualization.
   - Collision rejection handling.

3. **M3 – Timeline Compiler (Week 2)**
   - Timeline data structures and dry-run simulator.

4. **M4 – Template Library (Week 2-3)**
   - Wrap top 3 frequently used animation primitives with metadata-driven interfaces.

5. **M5 – Instrumented End-to-End Test (Week 3)**
   - Run a single lesson through new pipeline, collect metrics vs. legacy output.

## Risks & Mitigations
- **Spec Complexity**: Schema may become unwieldy.
  - Mitigation: Start with minimal viable set of constraints; iterate with real examples.
- **Timeline Conflicts**: Hard to resolve automatically.
  - Mitigation: Provide planner-level hints (priority, locking) and fail fast with actionable errors.
- **Template Coverage**: Existing animations may not map cleanly.
  - Mitigation: Focus on high-impact templates first and maintain hybrid mode.

## Next Steps
1. Inventory existing `VisualSpec` usage to inform schema design.
2. Implement `ScenePlan` schema and validation tooling.
3. Prototype layout engine with simple auto-layout strategies (grid, stack, overlay).

## Progress
- [x] Implemented initial `ScenePlan` schema with validation
- [x] Added conversion utilities and CLI for inspecting generated plans

## Tools
- `python -m src.planning.scene_plan_cli examples/scene_plan_sample.json`

