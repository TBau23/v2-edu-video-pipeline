# ANIM-002: Dynamic Code Execution

**Priority**: P0 - Critical Path
**Estimate**: 1 hour
**Dependencies**: ANIM-001
**Status**: 🔴 Not Started

---

## Goal

Safely execute LLM-generated Manim Scene code and render it to a video file.

---

## Why This Matters

Generated code is useless without execution. This is the bridge between LLM output and actual video files. Must be safe, reliable, and handle errors gracefully.

---

## Current State

- We have code generation (ANIM-001)
- SceneExecutor can render Scene classes
- Need to go from code string → Scene class → rendered video

---

## Tasks

### 1. Code Parsing and Validation (20 min)
- [ ] Extract Scene class definition from code string
- [ ] Validate structure (has Scene class, construct method)
- [ ] Check for required imports
- [ ] Basic safety checks (no obvious dangerous operations)

**What to validate**:
- Code contains `class GeneratedAnimation(Scene):`
- Code contains `def construct(self):`
- Code has `from manim import` or similar
- No obvious red flags (os.system, eval, exec, __import__)

### 2. Dynamic Execution (30 min)
- [ ] Create temporary module from code string
- [ ] Execute code in controlled namespace
- [ ] Extract Scene class from executed module
- [ ] Handle imports and Manim setup

**Execution approaches**:
- **Option A**: `exec()` in namespace
- **Option B**: Write to temp file, import dynamically
- **Option C**: Use `compile()` and `eval()`

**Recommendation**: Option B (temp file) - cleaner, easier to debug

### 3. Integration with SceneExecutor (10 min)
- [ ] Pass Scene class to existing SceneExecutor
- [ ] Use executor's render_scene() method
- [ ] Get output video path
- [ ] Clean up temp files

### 4. Error Handling (20 min)
- [ ] Try/catch around execution
- [ ] Catch ImportError, SyntaxError, RuntimeError
- [ ] Helpful error messages with code snippet
- [ ] Logging for debugging
- [ ] Fallback strategy

---

## Acceptance Criteria

✅ **Must have**:
- Can execute generated Scene code
- Returns path to rendered video file
- Handles syntax errors gracefully
- Handles runtime errors (bad Manim API calls)
- Cleans up temp files
- Logs errors with context

✅ **Nice to have**:
- Timeout for long-running renders
- Memory limit enforcement
- Detailed error reporting

---

## Implementation Approach

### Function Signature

```python
def execute_animation_code(
    code: str,
    output_name: str,
    output_dir: Path,
    quality: str = "low_quality"
) -> Path:
    """Execute generated Manim Scene code and render video.

    Args:
        code: Python code with Scene class definition
        output_name: Name for output file (without extension)
        output_dir: Directory to save rendered video
        quality: Manim quality flag

    Returns:
        Path to rendered video file

    Raises:
        SyntaxError: If code has syntax errors
        RuntimeError: If execution or rendering fails
    """
```

### Execution Flow

```python
def execute_animation_code(code, output_name, output_dir, quality):
    # 1. Validate code structure
    validate_scene_code(code)

    # 2. Write to temporary file
    temp_file = create_temp_file(code)

    try:
        # 3. Import the module dynamically
        module = import_from_path(temp_file)

        # 4. Extract Scene class
        scene_class = module.GeneratedAnimation

        # 5. Use SceneExecutor to render
        executor = SceneExecutor(output_dir, quality)
        output_path = executor.render_scene(
            scene_class,
            output_name=output_name,
            preview=False
        )

        return output_path

    except Exception as e:
        logger.error(f"Animation execution failed: {e}")
        logger.debug(f"Code that failed:\n{code}")
        raise

    finally:
        # 6. Clean up temp file
        temp_file.unlink(missing_ok=True)
```

### Validation Function

```python
def validate_scene_code(code: str) -> None:
    """Validate generated Scene code structure.

    Args:
        code: Python code to validate

    Raises:
        ValueError: If code structure is invalid
    """
    required_patterns = [
        "class GeneratedAnimation",
        "def construct(self)",
        "from manim"
    ]

    for pattern in required_patterns:
        if pattern not in code:
            raise ValueError(f"Generated code missing: {pattern}")

    # Check for dangerous operations
    dangerous = ["os.system", "subprocess", "eval(", "__import__"]
    for danger in dangerous:
        if danger in code:
            raise ValueError(f"Dangerous operation detected: {danger}")
```

---

## Test Strategy

### Unit Test

```python
def test_execute_simple_animation():
    """Test executing generated Scene code."""

    code = '''
from manim import *

class GeneratedAnimation(Scene):
    def construct(self):
        circle = Circle(color=BLUE)
        self.play(FadeIn(circle))
        self.wait(1)
'''

    output_path = execute_animation_code(
        code=code,
        output_name="test_circle",
        output_dir=Path("test_output"),
        quality="low_quality"
    )

    assert output_path.exists()
    assert output_path.suffix == ".mp4"
```

### Error Handling Tests

```python
def test_invalid_syntax():
    """Test handling of syntax errors."""
    code = "this is not valid python"

    with pytest.raises(SyntaxError):
        execute_animation_code(code, "test", Path("output"))


def test_missing_scene_class():
    """Test validation catches missing Scene class."""
    code = '''
from manim import *

def some_function():
    pass
'''

    with pytest.raises(ValueError, match="missing"):
        execute_animation_code(code, "test", Path("output"))
```

---

## Safety Considerations

### Sandboxing Options

**Level 1: Basic validation** (MVP)
- Check for dangerous imports/operations
- No actual sandboxing
- Fast, simple
- **Risk**: Malicious/buggy code could cause issues

**Level 2: Resource limits** (Future)
- Timeout after 30 seconds
- Memory limit (e.g., 2GB)
- Use multiprocessing with limits
- **Trade-off**: More complex, slower

**Level 3: Full sandbox** (Overkill)
- Docker container per render
- Complete isolation
- **Trade-off**: Very complex, much slower

**Recommendation**: Start with Level 1, add Level 2 if needed

### Timeout Implementation

```python
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Render exceeded time limit")

# Set timeout
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(30)  # 30 second timeout

try:
    # Execute render
    render_scene(...)
finally:
    signal.alarm(0)  # Cancel timeout
```

---

## Blockers / Risks

**Risk**: Generated code has infinite loops
- **Mitigation**: Timeout after 30 seconds
- **Fallback**: Kill process, return error

**Risk**: Generated code crashes Manim
- **Mitigation**: Try/catch around render
- **Fallback**: Log error, skip animation

**Risk**: Memory leak from repeated execution
- **Mitigation**: Clean up properly, monitor memory
- **Future**: Use separate process per render

---

## Done When

- [x] Can execute valid Scene code
- [x] Returns path to rendered video
- [x] Validates code structure before execution
- [x] Handles syntax errors gracefully
- [x] Handles runtime errors gracefully
- [x] Cleans up temp files
- [x] Unit tests pass

---

## Follow-up Stories

- **ANIM-003**: Integration with Renderer
- **ANIM-006**: Error Recovery and Retry Logic
