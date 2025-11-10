# Web Deployment Plan - Educational Video Generator

Breaking down web deployment into testable, deliverable stories.

## Overview

**Goal**: Deploy the video generation pipeline as a web application where users can submit prompts and receive generated videos.

**Current state**:
- ✅ Pipeline works locally (after E2E-004 complete)
- ❌ No web interface
- ❌ No job queue for background processing
- ❌ No deployment infrastructure

**Target state**: Users can access a web app, enter a prompt, and get a video (with progress updates)

---

## Deployment Philosophy

**Progressive Enhancement**: Start with simplest solution, add complexity only when needed

```
Gradio MVP (2h) → Background Jobs (1d) → Production API (3-5d) → Scale (future)
```

**Not aiming for**: Netflix-scale infrastructure day 1
**Aiming for**: 10-100 concurrent users with good UX

---

## Story Structure

### Phase 1: MVP Web Interface (Critical Path)
**Goal**: Get a working web demo ASAP for validation

- **WEB-001**: Gradio Web Interface (MVP)
- **WEB-002**: Progress Tracking & Status Updates
- **WEB-003**: Error Handling & User Feedback

### Phase 2: Production Infrastructure (High Priority)
**Goal**: Handle multiple concurrent users reliably

- **WEB-004**: Job Queue System (Celery + Redis)
- **WEB-005**: FastAPI Backend
- **WEB-006**: Simple Frontend UI
- **WEB-007**: File Management & Cleanup

### Phase 3: Deployment & Operations (Medium Priority)
**Goal**: Deploy to cloud, monitor, maintain

- **WEB-008**: Docker Containerization
- **WEB-009**: Cloud Deployment (AWS/GCP/Azure)
- **WEB-010**: Monitoring & Logging
- **WEB-011**: Authentication & Rate Limiting

### Phase 4: Scale & Optimize (Future)
**Goal**: Handle high traffic, reduce costs

- **WEB-012**: Caching & CDN
- **WEB-013**: GPU Acceleration for Manim
- **WEB-014**: Multi-worker Architecture
- **WEB-015**: Cost Optimization

---

## Dependencies Graph

```
E2E-004 (Pipeline Complete) ──┐
                              ↓
                         WEB-001 (Gradio MVP)
                              ↓
                         WEB-002 (Progress)
                              ↓
                         WEB-003 (Errors)
                              ↓
                    ┌─────────┴─────────┐
                    ↓                   ↓
              WEB-004 (Queue)      WEB-007 (Cleanup)
                    ↓
              WEB-005 (FastAPI)
                    ↓
              WEB-006 (Frontend)
                    ↓
        ┌───────────┴───────────┐
        ↓                       ↓
   WEB-008 (Docker)        WEB-011 (Auth)
        ↓
   WEB-009 (Deploy)
        ↓
   WEB-010 (Monitor)
```

**Critical path**: E2E-004 → WEB-001 → WEB-002 → WEB-003 → WEB-004 → WEB-005

---

## Story Overview

### WEB-001: Gradio Web Interface (MVP)
**Priority**: P0 - Critical Path
**Estimate**: 2 hours
**Dependencies**: E2E-004 (pipeline complete)
**Status**: 🔴 Not Started

**Goal**: Single-file web app using Gradio for instant demo

**Deliverable**:
```bash
python examples/web_app.py
# Opens web interface at localhost:7860
# User enters prompt → gets video
```

See: `planning/stories/WEB-001-gradio-mvp.md`

---

### WEB-002: Progress Tracking & Status Updates
**Priority**: P0 - Critical Path
**Estimate**: 3-4 hours
**Dependencies**: WEB-001
**Status**: 🔴 Not Started

**Goal**: Show users what stage the pipeline is in (not just spinning wheel)

**User Experience**:
```
[████████░░░░░░░░░░░░] 40% - Rendering visuals (Act 2/3)...
Estimated time remaining: 1m 30s
```

See: `planning/stories/WEB-002-progress-tracking.md`

---

### WEB-003: Error Handling & User Feedback
**Priority**: P0 - Critical Path
**Estimate**: 2-3 hours
**Dependencies**: WEB-001, WEB-002
**Status**: 🔴 Not Started

**Goal**: Graceful error messages, retry logic, helpful feedback

**Examples**:
- "API key invalid - please contact support"
- "Video generation failed at audio synthesis stage - please try again"
- "This topic is too broad - try being more specific"

See: `planning/stories/WEB-003-error-handling.md`

---

### WEB-004: Job Queue System
**Priority**: P1 - High Priority
**Estimate**: 6-8 hours
**Dependencies**: WEB-003
**Status**: 🔴 Not Started

**Goal**: Background processing so web server doesn't block

**Why needed**: Manim rendering takes 2-5 minutes, can't block HTTP request

**Stack**: Celery + Redis (industry standard)

See: `planning/stories/WEB-004-job-queue.md`

---

### WEB-005: FastAPI Backend
**Priority**: P1 - High Priority
**Estimate**: 6-8 hours
**Dependencies**: WEB-004
**Status**: 🔴 Not Started

**Goal**: RESTful API for production use

**Endpoints**:
- `POST /api/generate` - Submit prompt, get job_id
- `GET /api/status/{job_id}` - Check progress
- `GET /api/video/{job_id}` - Download video
- `GET /api/projects` - List user's videos

See: `planning/stories/WEB-005-fastapi-backend.md`

---

### WEB-006: Simple Frontend UI
**Priority**: P1 - High Priority
**Estimate**: 8-10 hours
**Dependencies**: WEB-005
**Status**: 🔴 Not Started

**Goal**: Custom UI (better than Gradio for branding)

**Options**:
- React SPA (modern, flexible)
- Next.js (SSR, SEO-friendly)
- Plain HTML/JS (simplest)

See: `planning/stories/WEB-006-frontend-ui.md`

---

### WEB-007: File Management & Cleanup
**Priority**: P1 - High Priority
**Estimate**: 3-4 hours
**Dependencies**: WEB-004
**Status**: 🔴 Not Started

**Goal**: Don't fill disk with old videos

**Strategy**:
- Delete videos after 24 hours
- Keep last N videos per user
- Archive to S3 for premium users

See: `planning/stories/WEB-007-file-management.md`

---

### WEB-008: Docker Containerization
**Priority**: P2 - Medium Priority
**Estimate**: 4-6 hours
**Dependencies**: WEB-005, WEB-007
**Status**: 🔴 Not Started

**Goal**: Reproducible deployment environment

**Includes**:
- Dockerfile with all dependencies (LaTeX, ffmpeg, Python)
- docker-compose.yml for local development
- Multi-stage build for smaller images

See: `planning/stories/WEB-008-docker.md`

---

### WEB-009: Cloud Deployment
**Priority**: P2 - Medium Priority
**Estimate**: 6-8 hours
**Dependencies**: WEB-008
**Status**: 🔴 Not Started

**Goal**: Deploy to production cloud environment

**Options**:
- Railway/Render (easiest)
- AWS ECS/Fargate (flexible)
- GCP Cloud Run (cost-effective)
- Azure Container Instances

See: `planning/stories/WEB-009-cloud-deployment.md`

---

### WEB-010: Monitoring & Logging
**Priority**: P2 - Medium Priority
**Estimate**: 4-6 hours
**Dependencies**: WEB-009
**Status**: 🔴 Not Started

**Goal**: Know when things break, track usage

**Tools**:
- Sentry (error tracking)
- Datadog/New Relic (APM)
- CloudWatch/GCP Logging (cloud native)

See: `planning/stories/WEB-010-monitoring.md`

---

### WEB-011: Authentication & Rate Limiting
**Priority**: P2 - Medium Priority
**Estimate**: 6-8 hours
**Dependencies**: WEB-005
**Status**: 🔴 Not Started

**Goal**: Control who can use the system and how much

**Features**:
- API key authentication
- Rate limiting (e.g., 10 videos/day per user)
- Usage tracking
- Basic billing integration

See: `planning/stories/WEB-011-auth-rate-limiting.md`

---

## MVP Milestone

**Definition of MVP**: Working web demo where user submits prompt and gets video

**Required stories**: WEB-001, WEB-002, WEB-003

**Estimated time**: 7-9 hours

**Test case**:
```
1. Open web app in browser
2. Enter prompt: "Explain Newton's First Law"
3. See progress updates
4. Get playable MP4 video in 3-5 minutes
5. Try again with different prompt
```

**Success criteria**:
- ✅ Web interface loads
- ✅ Can submit prompt
- ✅ Progress updates visible
- ✅ Video downloads/plays
- ✅ Errors show helpful messages
- ✅ Can generate multiple videos

---

## Production Milestone

**Definition**: Deployed web app that can handle 10+ concurrent users

**Required stories**: All WEB-001 through WEB-011

**Test case**: Stress test with 10 simultaneous prompts

---

## Key Design Decisions

### Decision 1: Gradio vs Custom UI for MVP

**Question**: Start with Gradio or build custom UI?

**✅ DECISION**: Start with Gradio, migrate later if needed

**Why**:
- 2 hours vs 2 weeks
- Validate concept first
- Can always build custom UI later (WEB-006)
- Gradio good enough for internal demos

**Migration path**: Gradio → FastAPI → Custom UI

---

### Decision 2: Job Queue Architecture

**Question**: How to handle long-running video generation?

**✅ DECISION**: Celery + Redis

**Why**:
- Industry standard
- Mature, well-documented
- Scales well
- Python-native

**Alternatives considered**:
- RQ (simpler, less features)
- AWS SQS (cloud lock-in)
- No queue (blocks web server ❌)

---

### Decision 3: File Storage

**Question**: Where to store generated videos?

**✅ DECISION**: Local disk (MVP) → S3 (production)

**Why**:
- Local disk simple for MVP
- S3 for production (cheap, scalable, CDN-ready)
- Keep intermediate files temporarily for debugging

**Cleanup strategy**:
- Delete local files after 24 hours
- Archive to S3 for premium users
- Keep only final video, delete intermediates

---

### Decision 4: Deployment Platform

**Question**: Where to host?

**✅ DECISION**: Docker + flexible deployment (choose based on budget/expertise)

**Options ranked**:
1. **Railway/Render** - Easiest, push Docker image, done ($10-50/mo)
2. **AWS Fargate** - More control, scales better ($20-100/mo)
3. **GCP Cloud Run** - Cost-effective, serverless ($10-50/mo)
4. **Bare metal/VPS** - Cheapest if you manage it ($5-20/mo)

**Recommendation**: Start with Railway, migrate to AWS if needed

---

### Decision 5: Concurrent Job Limits

**Question**: How many videos to render simultaneously?

**✅ DECISION**: 2-4 concurrent Manim renders (test-based)

**Why**:
- Manim is CPU-intensive
- 2-4 workers per 4-core machine
- Use queue for overflow

**Implementation**:
```python
# Celery config
CELERYD_CONCURRENCY = 2  # Max 2 videos at once
```

---

## Resource Requirements

### Development Machine
- 4+ CPU cores
- 8GB+ RAM
- 50GB disk space (for testing)

### Production Server (10-50 users)
- 8 CPU cores (for 2-4 concurrent renders)
- 16GB RAM
- 100GB SSD (with cleanup)
- 100GB/month bandwidth

### Estimated Costs (monthly)
- **MVP (Railway)**: $20-30
- **Small scale (100 videos/day)**: $50-100
- **Medium scale (1000 videos/day)**: $200-500
- **API costs (OpenAI)**: $0.10-0.20 per video × volume

---

## Risk Assessment

**High Risk**:
- Manim rendering slow → User abandons before completion
  - Mitigation: Progress updates, email notification option
- Concurrent users overload server → Everything crashes
  - Mitigation: Job queue, rate limiting, auto-scaling
- Disk fills up → System fails
  - Mitigation: Automated cleanup, S3 archival

**Medium Risk**:
- Users submit malicious prompts → Inappropriate content
  - Mitigation: Content moderation, LLM safety filters
- API costs spiral out of control → Budget blown
  - Mitigation: Rate limiting, usage caps, monitoring

**Low Risk**:
- Gradio UI too simple → Users want custom branding
  - Mitigation: Build custom UI (WEB-006)
- Need authentication → Add later
  - Mitigation: WEB-011 adds auth when needed

---

## Success Metrics

**After MVP (WEB-001 to WEB-003)**:
- ✅ Can generate video via web interface
- ✅ Progress updates work
- ✅ Error messages helpful
- ✅ >80% success rate

**After Production Infrastructure (WEB-004 to WEB-007)**:
- ✅ Can handle 10 concurrent users
- ✅ No server crashes
- ✅ <5 minute wait time (p95)
- ✅ Disk usage stays under control

**After Deployment (WEB-008 to WEB-011)**:
- ✅ Deployed to public URL
- ✅ Uptime >99%
- ✅ Monitoring catches errors
- ✅ Can track usage/costs

---

## Migration Path

```
Week 1: Gradio MVP
  - Get working demo
  - Test with 5-10 users
  - Validate concept

Week 2: Add Job Queue
  - Handle concurrent users
  - Better progress tracking
  - Test with 20-50 users

Week 3-4: Production API
  - FastAPI backend
  - Optional: Custom UI
  - Deployment infrastructure

Week 5+: Scale & Polish
  - Monitoring
  - Authentication
  - Optimization
  - Cost reduction
```

---

## Implementation Notes

### Gradio Quick Start
```python
import gradio as gr
from src.pipeline.orchestrator import VideoPipeline

def generate_video(prompt):
    pipeline = VideoPipeline(Path("projects"))
    result = pipeline.generate(prompt=prompt)
    return result.video_path

demo = gr.Interface(
    fn=generate_video,
    inputs=gr.Textbox(label="Topic"),
    outputs=gr.Video(label="Video")
)
demo.launch()
```

### Celery Quick Start
```python
from celery import Celery

celery = Celery('tasks', broker='redis://localhost:6379')

@celery.task(bind=True)
def generate_video_task(self, prompt):
    # Update progress
    self.update_state(state='PROGRESS', meta={'stage': 'script'})
    # ... run pipeline ...
    return video_path
```

### FastAPI Quick Start
```python
from fastapi import FastAPI, BackgroundTasks

app = FastAPI()

@app.post("/api/generate")
async def generate(prompt: str, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    background_tasks.add_task(run_pipeline, job_id, prompt)
    return {"job_id": job_id}
```

---

## How to Use This Plan

1. **Start with WEB-001** (Gradio MVP) - validate the concept
2. **Demo to users** - get feedback
3. **If valuable, continue** to WEB-004 (job queue)
4. **Deploy** when ready (WEB-008, WEB-009)
5. **Iterate** based on usage

**Don't build everything at once!** Gradio MVP is enough to validate demand.

---

## Next Steps

**Immediate**:
1. Finish E2E-004 (pipeline orchestrator) if not done
2. Create WEB-001 (Gradio interface)
3. Test with real prompts
4. Get user feedback

**After validation**:
- Build production infrastructure (WEB-004 to WEB-007)
- Deploy (WEB-008, WEB-009)
- Add polish (WEB-010, WEB-011)

**Total time to production**: 2-4 weeks (with testing)

---

## Questions to Answer

Before starting, decide:
1. **Who is the target user?** (internal team, students, general public)
2. **Expected usage?** (10 videos/day vs 1000 videos/day)
3. **Budget?** ($20/month vs $500/month)
4. **Timeline?** (demo next week vs production in 2 months)
5. **Authentication needed?** (open to public vs protected)

These answers will inform which stories to prioritize.
