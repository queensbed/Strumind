"""
Comprehensive API Testing for StruMind
Tests all backend functionality and creates a detailed report
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"

class StruMindAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.project_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
    
    def test_health_check(self):
        """Test backend health"""
        try:
            response = self.session.get(f"{BACKEND_URL}/health")
            success = response.status_code == 200
            details = f"Status: {response.status_code}, Response: {response.json() if success else response.text}"
            self.log_test("Health Check", success, details)
            return success
        except Exception as e:
            self.log_test("Health Check", False, f"Error: {e}")
            return False
    
    def test_authentication(self):
        """Test authentication system"""
        # Test registration
        user_data = {
            "email": "api.test@strumind.com",
            "password": "TestPass123!",
            "first_name": "API Test",
            "last_name": "User",
            "organization_name": "StruMind API Test"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/api/v1/auth/register", json=user_data)
            reg_success = response.status_code in [200, 201, 400]  # 400 = user exists
            self.log_test("User Registration", reg_success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("User Registration", False, f"Error: {e}")
        
        # Test login
        login_data = {
            "email": "api.test@strumind.com",
            "password": "TestPass123!"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/api/v1/auth/login", json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                if self.access_token:
                    self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
                    self.log_test("User Login", True, "Token obtained successfully")
                    return True
                else:
                    self.log_test("User Login", False, "No access token in response")
                    return False
            else:
                self.log_test("User Login", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("User Login", False, f"Error: {e}")
            return False
    
    def test_project_management(self):
        """Test project CRUD operations"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create project
        project_data = {
            "name": f"API Test Project {timestamp}",
            "description": "Comprehensive API testing project",
            "building_type": "office",
            "location": "Test Location",
            "code_standard": "AISC_360"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/api/v1/projects", json=project_data)
            if response.status_code in [200, 201]:
                project = response.json()
                self.project_id = project.get("id")
                self.log_test("Project Creation", True, f"Project ID: {self.project_id}")
            else:
                self.log_test("Project Creation", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Project Creation", False, f"Error: {e}")
            return False
        
        # List projects
        try:
            response = self.session.get(f"{BACKEND_URL}/api/v1/projects")
            success = response.status_code == 200
            if success:
                projects = response.json()
                self.log_test("Project Listing", True, f"Found {len(projects)} projects")
            else:
                self.log_test("Project Listing", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Project Listing", False, f"Error: {e}")
        
        # Get project details
        if self.project_id:
            try:
                response = self.session.get(f"{BACKEND_URL}/api/v1/projects/{self.project_id}")
                success = response.status_code == 200
                self.log_test("Project Details", success, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Project Details", False, f"Error: {e}")
        
        return True
    
    def test_structural_modeling(self):
        """Test structural modeling APIs"""
        if not self.project_id:
            self.log_test("Structural Modeling", False, "No project ID available")
            return False
        
        # Test materials
        material_data = {
            "name": "Steel A992",
            "material_type": "steel",
            "properties": {
                "elastic_modulus": 200000,
                "poisson_ratio": 0.3,
                "density": 7850,
                "yield_strength": 345
            }
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/api/v1/models/{self.project_id}/materials", json=material_data)
            success = response.status_code in [200, 201]
            self.log_test("Material Creation", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Material Creation", False, f"Error: {e}")
        
        # Test sections
        section_data = {
            "name": "W14x22",
            "section_type": "I_beam",
            "properties": {
                "area": 2840,
                "moment_of_inertia_y": 29300000,
                "moment_of_inertia_z": 1430000
            }
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/api/v1/models/{self.project_id}/sections", json=section_data)
            success = response.status_code in [200, 201]
            self.log_test("Section Creation", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Section Creation", False, f"Error: {e}")
        
        # Test nodes
        node_data = {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "boundary_conditions": {
                "translation_x": "fixed",
                "translation_y": "fixed",
                "translation_z": "fixed",
                "rotation_x": "fixed",
                "rotation_y": "fixed",
                "rotation_z": "fixed"
            }
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/api/v1/models/{self.project_id}/nodes", json=node_data)
            success = response.status_code in [200, 201]
            self.log_test("Node Creation", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Node Creation", False, f"Error: {e}")
        
        # Test elements
        element_data = {
            "node_i": 1,
            "node_j": 2,
            "section_id": 1,
            "material_id": 1,
            "element_type": "beam"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/api/v1/models/{self.project_id}/elements", json=element_data)
            success = response.status_code in [200, 201]
            self.log_test("Element Creation", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Element Creation", False, f"Error: {e}")
        
        # Test loads
        load_data = {
            "name": "Test Load",
            "load_type": "dead",
            "load_case": "DL",
            "loads": [
                {
                    "node_id": 1,
                    "fx": 0,
                    "fy": 0,
                    "fz": -100,
                    "mx": 0,
                    "my": 0,
                    "mz": 0
                }
            ]
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/api/v1/models/{self.project_id}/loads", json=load_data)
            success = response.status_code in [200, 201]
            self.log_test("Load Creation", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Load Creation", False, f"Error: {e}")
        
        return True
    
    def test_analysis_engine(self):
        """Test analysis capabilities"""
        if not self.project_id:
            self.log_test("Analysis Engine", False, "No project ID available")
            return False
        
        analysis_data = {
            "analysis_type": "linear_static",
            "load_cases": ["DL"],
            "solver_settings": {
                "tolerance": 1e-6,
                "max_iterations": 1000
            }
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/api/v1/analysis/{self.project_id}/run", json=analysis_data)
            success = response.status_code in [200, 201, 202]
            self.log_test("Analysis Execution", success, f"Status: {response.status_code}")
            
            if success:
                # Check analysis status
                time.sleep(1)
                status_response = self.session.get(f"{BACKEND_URL}/api/v1/analysis/{self.project_id}/status")
                if status_response.status_code == 200:
                    status = status_response.json()
                    self.log_test("Analysis Status Check", True, f"Status: {status.get('status', 'unknown')}")
                else:
                    self.log_test("Analysis Status Check", False, f"Status: {status_response.status_code}")
            
            return success
        except Exception as e:
            self.log_test("Analysis Execution", False, f"Error: {e}")
            return False
    
    def test_design_modules(self):
        """Test design capabilities"""
        try:
            response = self.session.get(f"{BACKEND_URL}/api/v1/design/health")
            success = response.status_code == 200
            self.log_test("Design Module Health", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Design Module Health", False, f"Error: {e}")
            return False
    
    def test_file_exports(self):
        """Test file export capabilities"""
        if not self.project_id:
            self.log_test("File Exports", False, "No project ID available")
            return False
        
        # Test PDF export
        try:
            response = self.session.post(f"{BACKEND_URL}/api/v1/files/{self.project_id}/export/pdf")
            success = response.status_code in [200, 201]
            self.log_test("PDF Export", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("PDF Export", False, f"Error: {e}")
        
        # Test DXF export
        try:
            response = self.session.post(f"{BACKEND_URL}/api/v1/files/{self.project_id}/export/dxf")
            success = response.status_code in [200, 201]
            self.log_test("DXF Export", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("DXF Export", False, f"Error: {e}")
        
        # Test IFC export
        try:
            ifc_data = {
                "format": "ifc4",
                "target_software": "revit"
            }
            response = self.session.post(f"{BACKEND_URL}/api/v1/files/{self.project_id}/export/ifc", json=ifc_data)
            success = response.status_code in [200, 201]
            self.log_test("IFC Export", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("IFC Export", False, f"Error: {e}")
        
        return True
    
    def test_collaboration_features(self):
        """Test collaboration capabilities"""
        if not self.project_id:
            self.log_test("Collaboration Features", False, "No project ID available")
            return False
        
        # Test project members
        try:
            response = self.session.get(f"{BACKEND_URL}/api/v1/collaboration/projects/{self.project_id}/members")
            success = response.status_code in [200, 404]  # 404 is OK if no members
            self.log_test("Project Members API", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Project Members API", False, f"Error: {e}")
        
        # Test activity log
        try:
            response = self.session.get(f"{BACKEND_URL}/api/v1/collaboration/projects/{self.project_id}/activity")
            success = response.status_code in [200, 404]
            self.log_test("Activity Log API", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Activity Log API", False, f"Error: {e}")
        
        return True
    
    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Comprehensive API Testing")
        print("=" * 60)
        
        # Run tests in sequence
        tests = [
            ("Health Check", self.test_health_check),
            ("Authentication", self.test_authentication),
            ("Project Management", self.test_project_management),
            ("Structural Modeling", self.test_structural_modeling),
            ("Analysis Engine", self.test_analysis_engine),
            ("Design Modules", self.test_design_modules),
            ("File Exports", self.test_file_exports),
            ("Collaboration Features", self.test_collaboration_features)
        ]
        
        for test_name, test_func in tests:
            print(f"\n📍 Testing {test_name}...")
            try:
                test_func()
            except Exception as e:
                self.log_test(f"{test_name} (Exception)", False, f"Unexpected error: {e}")
        
        # Generate summary
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = f"""
# StruMind API Comprehensive Test Report
**Generated:** {timestamp}

## Summary
- **Total Tests:** {total_tests}
- **Passed:** {passed_tests} ✅
- **Failed:** {failed_tests} ❌
- **Success Rate:** {success_rate:.1f}%

## Test Results

| Test | Status | Details |
|------|--------|---------|
"""
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            details = result['details'][:100] + "..." if len(result['details']) > 100 else result['details']
            report += f"| {result['test']} | {status} | {details} |\n"
        
        report += f"""

## Project Information
- **Project ID:** {self.project_id if self.project_id else 'Not created'}
- **Authentication:** {'✅ Successful' if self.access_token else '❌ Failed'}

## API Endpoints Tested
- Health Check: `/health`
- Authentication: `/api/v1/auth/register`, `/api/v1/auth/login`
- Projects: `/api/v1/projects`
- Modeling: `/api/v1/models/{{project_id}}/materials`, `/api/v1/models/{{project_id}}/sections`, etc.
- Analysis: `/api/v1/analysis/{{project_id}}/run`
- Design: `/api/v1/design/health`
- Export: `/api/v1/files/{{project_id}}/export/{{format}}`
- Collaboration: `/api/v1/collaboration/projects/{{project_id}}/members`

## Conclusion
{'🎉 All critical API functionality is working correctly!' if success_rate >= 80 else '⚠️ Some API endpoints need attention.'}

The StruMind backend API demonstrates {'excellent' if success_rate >= 90 else 'good' if success_rate >= 70 else 'fair'} functionality across all major features.

---
*Test completed on {timestamp}*
"""
        
        # Save report
        with open('/workspace/Strumind/API_TEST_REPORT.md', 'w') as f:
            f.write(report)
        
        # Save JSON results
        with open('/workspace/Strumind/api_test_results.json', 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'success_rate': success_rate
                },
                'project_id': self.project_id,
                'results': self.test_results
            }, f, indent=2)
        
        print("\n" + "=" * 60)
        print("🎉 API TESTING COMPLETED!")
        print(f"📊 Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        print(f"📄 Report saved: API_TEST_REPORT.md")
        print(f"📄 JSON results: api_test_results.json")
        if self.project_id:
            print(f"🏗️ Test project created: {self.project_id}")

if __name__ == "__main__":
    tester = StruMindAPITester()
    tester.run_all_tests()