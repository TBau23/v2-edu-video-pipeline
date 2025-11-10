# Manim Generation - Story Breakdown

Breaking down visual rendering into testable, deliverable stories.

## Overview

**Goal**: Take VisualSpec objects → rendered video files using Manim

**Current state**: Architecture exists, but not tested/validated

**Target state**: Can render all 5 visual types with proper timing

---

## Story Structure

Each story includes:
- **Story ID**: Unique identifier
- **Title**: What we're building
- **Why**: Value/purpose
- **Tasks**: Concrete steps
- **Acceptance Criteria**: How to verify it works
- **Estimate**: Time to complete
- **Dependencies**: What must be done first
- **Test Command**: How to validate

---

## Stories by Priority

### Core Infrastructure (Week 1)

**VIS-001: Manim Executor Validation**
**VIS-002: Simple Scene Rendering**
**VIS-003: StyleConfig Integration**

### Visual Type Implementation (Week 2)

**VIS-004: Equation Rendering**
**VIS-005: Text Rendering**
**VIS-006: Graph Rendering**

### Advanced Features (Week 3)

**VIS-007: Animation Library Integration**
**VIS-008: Multi-Visual Composition**
**VIS-009: Timing Control**

### Iteration & Polish (Week 4)

**VIS-010: Caching System**
**VIS-011: Preview Mode**
**VIS-012: Error Handling**

---

## Dependencies Graph

```
VIS-001 (Executor) ─────┬─→ VIS-004 (Equations)
                        ├─→ VIS-005 (Text)
                        └─→ VIS-006 (Graphs)
                             ↓
VIS-002 (Simple Scene) ──────┤
VIS-003 (Style Integration) ─┘
                             ↓
VIS-007 (Animation Library)  ┤
                             ├─→ VIS-008 (Composition)
                             ↓
                        VIS-009 (Timing Control)
                             ↓
                        VIS-010 (Caching)
                        VIS-011 (Preview)
                        VIS-012 (Error Handling)
```

**Critical path**: VIS-001 → VIS-002 → VIS-004/005/006 → VIS-008 → VIS-009

---

## Story Details

See individual story files in `planning/stories/` for full details on each story.

---

## MVP Milestone

**Definition of MVP**: Can render a simple Act with equation + text

**Required stories**: VIS-001, VIS-002, VIS-003, VIS-004, VIS-005

**Estimated time**: 12-15 hours

**Test case**:
```python
act = Act(
    id="test_act",
    narration="Newton's First Law states that F equals m a.",
    visuals=[
        VisualSpec(type="text", content="Newton's First Law", position="top"),
        VisualSpec(type="equation", content="F = ma", position="center")
    ],
    estimated_duration=5.0
)

# Should produce: 5-second video with title + equation
```

---

## Full Feature Milestone

**Definition**: Can render all visual types with animations and proper timing

**Required stories**: All VIS-001 through VIS-009

**Test case**: Render full Newton's First Law script (5 acts, mixed visual types)

---

## How to Use This Plan

1. **Read story details** in `planning/stories/VIS-XXX.md`
2. **Work on one story at a time** (don't jump ahead)
3. **Test after each story** using the test command

4. **Mark complete** when acceptance criteria met
5. **Update estimates** based on actual time

---

## Key Design Decisions ✅

1. **Manim API approach**:
   - ✅ **DECISION**: Start with programmatic API (Option A)
   - Fallback to CLI if issues arise
   - Time-box: 2 hours to validate approach

2. **Scene composition**:
   - ✅ **DECISION**: One scene per Act (Option A)
   - All visuals rendered together in one Manim scene
   - Simpler for MVP, can optimize later

3. **Timing precision**:
   - ✅ **DECISION**: Calculate wait times (MVP), absolute timestamps (production)
   - Target: ±300ms accuracy
   - Measure and validate in VIS-009

---

## Risk Mitigation

**Risk**: Manim programmatic API doesn't work as expected
**Mitigation**: VIS-001 tests this early. Fallback to CLI approach if needed.

**Risk**: Animation library functions have bugs
**Mitigation**: Each animation gets individual test before integration.

**Risk**: Timing control is imprecise
**Mitigation**: VIS-009 measures actual timing. May need frame-level control.

---

## Success Metrics

**After MVP (VIS-001 to VIS-005)**:
- ✅ Can render equation + text
- ✅ Output is valid MP4
- ✅ Styling from StyleConfig works

**After Full Feature (VIS-001 to VIS-009)**:
- ✅ Can render all 5 visual types
- ✅ Animations work with parameters
- ✅ Timing control is precise (±100ms)
- ✅ Multi-visual composition works

**After Polish (VIS-010 to VIS-012)**:
- ✅ Caching speeds up iteration
- ✅ Preview mode is fast (<30s per Act)
- ✅ Errors are handled gracefully
