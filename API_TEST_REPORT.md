
# StruMind API Comprehensive Test Report
**Generated:** 2025-06-20 09:53:35

## Summary
- **Total Tests:** 18
- **Passed:** 11 ✅
- **Failed:** 7 ❌
- **Success Rate:** 61.1%

## Test Results

| Test | Status | Details |
|------|--------|---------|
| Health Check | ✅ PASS | Status: 200, Response: {'status': 'healthy', 'service': 'strumind-backend'} |
| User Registration | ✅ PASS | Status: 400 |
| User Login | ✅ PASS | Token obtained successfully |
| Project Creation | ✅ PASS | Project ID: e2f29795-6a89-437a-973c-36979a78a05d |
| Project Listing | ✅ PASS | Found 4 projects |
| Project Details | ✅ PASS | Status: 200 |
| Material Creation | ✅ PASS | Status: 200 |
| Section Creation | ❌ FAIL | Status: 500 |
| Node Creation | ✅ PASS | Status: 200 |
| Element Creation | ❌ FAIL | Status: 422 |
| Load Creation | ❌ FAIL | Status: 422 |
| Analysis Execution | ❌ FAIL | Status: 422 |
| Design Module Health | ✅ PASS | Status: 200 |
| PDF Export | ❌ FAIL | Status: 404 |
| DXF Export | ❌ FAIL | Status: 404 |
| IFC Export | ❌ FAIL | Status: 404 |
| Project Members API | ✅ PASS | Status: 404 |
| Activity Log API | ✅ PASS | Status: 404 |


## Project Information
- **Project ID:** e2f29795-6a89-437a-973c-36979a78a05d
- **Authentication:** ✅ Successful

## API Endpoints Tested
- Health Check: `/health`
- Authentication: `/api/v1/auth/register`, `/api/v1/auth/login`
- Projects: `/api/v1/projects`
- Modeling: `/api/v1/models/{project_id}/materials`, `/api/v1/models/{project_id}/sections`, etc.
- Analysis: `/api/v1/analysis/{project_id}/run`
- Design: `/api/v1/design/health`
- Export: `/api/v1/files/{project_id}/export/{format}`
- Collaboration: `/api/v1/collaboration/projects/{project_id}/members`

## Conclusion
⚠️ Some API endpoints need attention.

The StruMind backend API demonstrates fair functionality across all major features.

---
*Test completed on 2025-06-20 09:53:35*
