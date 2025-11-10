# Planning Directory

Organization of project planning, stories, and work breakdown.

## Structure

```
planning/
  README.md                      # This file
  MANIM_GENERATION_PLAN.md       # Overall plan for visual rendering
  stories/                       # Individual user stories
    VIS-001-manim-executor.md
    VIS-004-equation-rendering.md
    VIS-007-animation-library.md
    ...
```

## How to Use

### 1. Read the Plan
Start with `MANIM_GENERATION_PLAN.md` to understand:
- What we're building (visual rendering)
- Why it's broken into stories
- Dependencies between stories
- MVP vs full feature milestones

### 2. Pick a Story
Stories are prioritized:
- **P0 (Critical Path)**: Must be done for MVP
- **P1 (High Priority)**: Important for quality
- **P2 (Nice to Have)**: Polish and optimization

Start with lowest-numbered P0 story that has no blockers.

### 3. Work the Story
Each story has:
- **Goal**: What we're building
- **Why**: Value proposition
- **Tasks**: Concrete steps (checkboxes)
- **Acceptance Criteria**: How to verify success
- **Test Command**: How to validate
- **Estimate**: Time to complete

### 4. Mark Progress
Update story status:
- 🔴 Not Started
- 🟡 In Progress
- 🟢 Complete

Check off tasks as you complete them.

### 5. Update Estimates
After completing a story:
- Record actual time taken
- Update future estimates if needed
- Note any blockers or issues encountered

## Story Naming Convention

`VIS-XXX-description`

- **VIS**: Visual rendering work
- **XXX**: Three-digit number (001, 002, etc.)
- **description**: Kebab-case short description

Examples:
- `VIS-001-manim-executor.md`
- `VIS-004-equation-rendering.md`
- `VIS-007-animation-library.md`

## Current Stories

### Week 1: Core Infrastructure
- [🔴] **VIS-001**: Manim Executor Validation (3-4h)
- [ ] **VIS-002**: Simple Scene Rendering (2-3h)
- [ ] **VIS-003**: StyleConfig Integration (2-3h)

### Week 2: Visual Types
- [🔴] **VIS-004**: Equation Rendering (2-3h)
- [ ] **VIS-005**: Text Rendering (1-2h)
- [ ] **VIS-006**: Graph Rendering (3-4h)

### Week 3: Advanced Features
- [🔴] **VIS-007**: Animation Library Integration (6-8h)
- [ ] **VIS-008**: Multi-Visual Composition (4-6h)
- [ ] **VIS-009**: Timing Control (4-6h)

### Week 4: Polish
- [ ] **VIS-010**: Caching System (3-4h)
- [ ] **VIS-011**: Preview Mode (3-4h)
- [ ] **VIS-012**: Error Handling (2-3h)

**Total estimated time**: 35-50 hours

## MVP Definition

**Stories required**: VIS-001, VIS-002, VIS-003, VIS-004, VIS-005

**Estimated time to MVP**: 12-18 hours

**MVP test case**:
```python
act = Act(
    id="mvp_test",
    narration="Newton's First Law states that F equals m a.",
    visuals=[
        VisualSpec(type="text", content="Newton's First Law", position="top"),
        VisualSpec(type="equation", content="F = ma", position="center")
    ]
)
# Should render: Title text + equation, 5 seconds
```

## Working on a Story

### Before Starting
1. Read the story completely
2. Check dependencies are complete
3. Understand acceptance criteria
4. Set up test environment

### While Working
1. Check off tasks as completed
2. Take notes on issues/blockers
3. Update estimates if significantly off
4. Test frequently (don't wait until end)

### After Completing
1. Run test command, verify passes
2. Mark story as complete (🟢)
3. Document any follow-up work needed
4. Move to next story in dependency order

## Tips for Success

### Start Small
Don't try to do everything at once. VIS-001 is intentionally simple (just render a circle). Get that working before moving on.

### Test Early, Test Often
Every story has a test command. Run it frequently. Don't wait until you think you're "done."

### Document Blockers
If you hit a blocker (e.g., LaTeX not installed, Manim API doesn't work), document it in the story. This helps future work.

### Update Estimates
First estimates are always wrong. That's okay. Update them based on actual experience so future planning is better.

### Ask for Help
If stuck for >30 minutes, document what you tried and ask for help. Don't waste hours debugging alone.

## Example Workflow

**Monday**:
- Read VIS-001
- Set up test environment
- Work through tasks
- Get circle rendering working
- Mark complete, move to VIS-002

**Tuesday**:
- Work on VIS-002 (simple scene)
- Work on VIS-003 (style integration)
- Both should build on VIS-001

**Wednesday-Thursday**:
- VIS-004 (equations)
- VIS-005 (text)
- Test MVP together

**Friday**:
- MVP test: render title + equation
- Demo working output
- Plan next week (animations)

## Questions?

See:
- `MANIM_GENERATION_PLAN.md` for overall architecture
- Individual story files for task details
- `../DEVELOPMENT_SPEC.md` for full project scope
- `../PROJECT_STATUS.md` for what's been built so far
