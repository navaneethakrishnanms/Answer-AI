"""
Comprehensive tests for API Endpoints
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from tests.test_framework import test, time_test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from fastapi import UploadFile
from io import BytesIO


class TestAPIEndpoints:
    """Test suite for API Endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        from app.main import app
        return TestClient(app)
    
    @pytest.fixture
    def mock_pdf_file(self):
        """Create mock PDF file"""
        return BytesIO(b"Mock PDF content")
    
    @time_test
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        assert 'version' in data
    
    @time_test
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
    
    @time_test
    @patch('app.api.endpoints.EvaluationPipeline')
    def test_upload_endpoint_success(self, mock_pipeline, client, temp_dir):
        """Test successful upload"""
        # Create dummy PDF files
        qp_file = temp_dir / "question_paper.pdf"
        ak_file = temp_dir / "answer_key.pdf"
        sa_file = temp_dir / "student_answers.pdf"
        
        for file in [qp_file, ak_file, sa_file]:
            file.write_bytes(b"Mock PDF content")
        
        # Mock pipeline
        mock_instance = AsyncMock()
        mock_instance.process.return_value = {
            'job_id': 'test_job_123',
            'status': 'processing'
        }
        mock_pipeline.return_value = mock_instance
        
        # Make request
        with open(qp_file, 'rb') as qp, open(ak_file, 'rb') as ak, open(sa_file, 'rb') as sa:
            response = client.post(
                "/api/v1/evaluate",
                files={
                    'question_paper': ('question_paper.pdf', qp, 'application/pdf'),
                    'answer_key': ('answer_key.pdf', ak, 'application/pdf'),
                    'student_answers': ('student_answers.pdf', sa, 'application/pdf')
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert 'job_id' in data
    
    @time_test
    def test_upload_endpoint_missing_files(self, client):
        """Test upload with missing files"""
        response = client.post("/api/v1/evaluate", files={})
        
        assert response.status_code == 422  # Validation error
    
    @time_test
    def test_upload_endpoint_invalid_file_type(self, client, temp_dir):
        """Test upload with invalid file type"""
        # Create dummy text file
        txt_file = temp_dir / "test.txt"
        txt_file.write_text("Not a PDF")
        
        with open(txt_file, 'rb') as f:
            response = client.post(
                "/api/v1/evaluate",
                files={
                    'question_paper': ('test.txt', f, 'text/plain'),
                    'answer_key': ('test.txt', f, 'text/plain'),
                    'student_answers': ('test.txt', f, 'text/plain')
                }
            )
        
        # Should fail validation
        assert response.status_code in [400, 422]
    
    @time_test
    @patch('app.api.endpoints.JobManager')
    def test_status_endpoint_job_exists(self, mock_manager, client):
        """Test status endpoint with existing job"""
        # Mock job manager
        mock_instance = AsyncMock()
        mock_instance.get_job_status.return_value = {
            'job_id': 'test_123',
            'status': 'processing',
            'progress': 50
        }
        mock_manager.return_value = mock_instance
        
        response = client.get("/api/v1/status/test_123")
        
        assert response.status_code == 200
        data = response.json()
        assert data['job_id'] == 'test_123'
        assert data['status'] == 'processing'
    
    @time_test
    @patch('app.api.endpoints.JobManager')
    def test_status_endpoint_job_not_found(self, mock_manager, client):
        """Test status endpoint with non-existent job"""
        # Mock job manager
        mock_instance = AsyncMock()
        mock_instance.get_job_status.return_value = None
        mock_manager.return_value = mock_instance
        
        response = client.get("/api/v1/status/nonexistent")
        
        assert response.status_code == 404
    
    @time_test
    @patch('app.api.endpoints.JobManager')
    def test_result_endpoint_job_completed(self, mock_manager, client):
        """Test result endpoint with completed job"""
        # Mock job manager
        mock_instance = AsyncMock()
        mock_instance.get_job_result.return_value = {
            'job_id': 'test_123',
            'status': 'completed',
            'result': {
                'total_marks': 45.0,
                'sections': {}
            }
        }
        mock_manager.return_value = mock_instance
        
        response = client.get("/api/v1/result/test_123")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'completed'
        assert 'result' in data
    
    @time_test
    @patch('app.api.endpoints.JobManager')
    def test_result_endpoint_job_not_completed(self, mock_manager, client):
        """Test result endpoint with uncompleted job"""
        # Mock job manager
        mock_instance = AsyncMock()
        mock_instance.get_job_result.return_value = {
            'job_id': 'test_123',
            'status': 'processing'
        }
        mock_manager.return_value = mock_instance
        
        response = client.get("/api/v1/result/test_123")
        
        # Should return 202 (Accepted, but not ready)
        assert response.status_code in [200, 202]
    
    @time_test
    def test_cors_headers(self, client):
        """Test CORS headers"""
        response = client.options("/api/v1/evaluate")
        
        # Should have CORS headers
        assert 'access-control-allow-origin' in response.headers or response.status_code == 405


# Register tests with framework
@test("api_endpoints", priority=3, dependencies=["ai_qwen_mapper", "ai_deepseek_evaluator"], 
      category="api")
def test_api():
    """Test API endpoints"""
    print("  Testing API endpoints...")
    from app.main import app
    client = TestClient(app)
    
    response = client.get("/")
    assert response.status_code == 200
    
    return True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
