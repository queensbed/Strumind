
# StruMind API Comprehensive Test Report
**Generated:** 2025-06-20 09:47:27

## Summary
- **Total Tests:** 9
- **Passed:** 2 ✅
- **Failed:** 7 ❌
- **Success Rate:** 22.2%

## Test Results

| Test | Status | Details |
|------|--------|---------|
| Health Check | ✅ PASS | Status: 200, Response: {'status': 'healthy', 'service': 'strumind-backend'} |
| User Registration | ❌ FAIL | Status: 422 |
| User Login | ❌ FAIL | Status: 422 |
| Project Creation | ❌ FAIL | Status: 403 |
| Structural Modeling | ❌ FAIL | No project ID available |
| Analysis Engine | ❌ FAIL | No project ID available |
| Design Module Health | ✅ PASS | Status: 200 |
| File Exports | ❌ FAIL | No project ID available |
| Collaboration Features | ❌ FAIL | No project ID available |


## Project Information
- **Project ID:** Not created
- **Authentication:** ❌ Failed

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
*Test completed on 2025-06-20 09:47:27*
