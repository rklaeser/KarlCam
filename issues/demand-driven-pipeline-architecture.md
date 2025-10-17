# Issue: Implement Demand-Driven Pipeline Architecture with Direct Gemini API

**Status**: Open  
**Priority**: High  
**Type**: Cost Optimization / Architecture Simplification  
**Created**: October 15, 2025  
**Revised**: October 16, 2025 (Architecture Simplification)

## Problem Statement

### Current Cost Structure
- **Cloud Run Costs**: $158/month (60% of total project costs)
- **Always-On Pipeline**: Runs every 10 minutes regardless of user activity
- **Resource Waste**: 2 vCPU + 2GB RAM × 144 executions/day = massive over-provisioning
- **Unused Work**: Collecting 1,300+ images/day even when no users visit the site

## Simplified Solution: Just-In-Time Processing

### Core Principle
**Do work only when requested. No background jobs. No pre-fetching. No complexity.**

### Architecture
```
User Request → Check Cache → If Miss: Fetch + Label → Save + Return
```

### Implementation (Minimal Changes)

#### 1. Single Endpoint Enhancement
Add to existing API service (`/api/public/cameras/{id}/latest`):
```python
async def get_camera_latest(webcam_id):
    # Check cache (simple time-based)
    latest = db.query_latest_image(webcam_id)
    if latest and latest.age_minutes < 30:
        return latest
    
    # Cache miss - fetch fresh
    try:
        image_data = requests.get(webcam.url).content
        fog_analysis = gemini.analyze(image_data)
        
        # Single atomic save
        result = db.save_labeled_image(
            webcam_id=webcam_id,
            image_data=image_data,
            fog_score=fog_analysis.score,
            fog_level=fog_analysis.level
        )
        return result
    except Exception:
        # Any error = return stale data
        return latest or {"error": "No data available"}
```

#### 2. Database Simplification
**Current**: 5 tables (webcams, collection_runs, image_collections, image_labels, system_status)  
**Proposed**: 2 tables
- `webcams`: Camera configurations
- `images`: Combined image + label data (one row per image)

#### 3. Remove Unnecessary Components
**Delete entirely**:
- `/collect` service
- `/label` service  
- Cloud Run job configurations
- Collection run tracking
- Labeler registry pattern
- System status tracking

**Keep only**:
- `/web/api` service (enhanced with direct fetch/label)
- `/web/frontend` (unchanged)
- `/admin` (simplified)

### Cost Impact
- **Current**: $158/month (144 runs/day)
- **Proposed**: ~$5/month (estimated 10-20 actual requests/day)
- **Savings**: 97% reduction

### Why This Is Better

#### Simpler Code
- **Before**: 3 services, job orchestration, state management
- **After**: 1 service, stateless requests

#### Simpler Operations
- **Before**: Monitor jobs, handle failures, coordinate services
- **After**: Standard API monitoring only

#### Simpler Database
- **Before**: Complex relationships, state tracking, multiple labelers
- **After**: Simple cache with timestamp

#### Simpler Error Handling
- **Before**: Retry logic, partial failures, recovery procedures
- **After**: Return stale data or error - let user retry

### Implementation Steps

#### Week 1: Proof of Concept
1. Add Gemini client to API service
2. Implement single endpoint with fetch + label
3. Test in staging

#### Week 2: Migration
1. Deploy enhanced API to production
2. Monitor for 48 hours
3. Turn off Cloud Run jobs
4. Delete unnecessary code

#### Week 3: Cleanup
1. Drop unused database tables
2. Remove job configurations
3. Update documentation

### What We're NOT Doing
- ❌ Background refreshes (adds complexity, race conditions)
- ❌ Pre-warming caches (defeats the purpose)
- ❌ Complex staleness logic (simple time threshold is enough)
- ❌ Multiple labeler support (YAGNI - one labeler works fine)
- ❌ Batch processing optimizations (premature optimization)
- ❌ Request coalescing (unnecessary complexity)

### Risk Mitigation
**Q: What if first user after 30min has slow experience?**  
A: They wait 3-5 seconds. This is acceptable for the massive cost savings.

**Q: What if multiple users request simultaneously?**  
A: Let them. Gemini API handles concurrent requests fine. Minor duplicate work is cheaper than coordination complexity.

**Q: What if Gemini API is down?**  
A: Return stale data with a note. Same as current behavior.

### Success Metrics
- Cost reduction: >95% 
- Code reduction: >50% fewer lines
- Latency: <5s for cache misses, <100ms for hits
- Uptime: Same as current (>99%)

## Decision
This simplified approach removes entire subsystems while maintaining all user-facing functionality. The minor UX tradeoff (occasional 5-second wait) is worth the dramatic reduction in complexity and cost.

---

**Expected Timeline**: 1 week development, 1 week migration  
**Expected Savings**: $1,896/year  
**Risk Level**: Low (simpler architecture = fewer failure modes)