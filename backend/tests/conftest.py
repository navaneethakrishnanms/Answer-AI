"""Pytest configuration and fixtures"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil
from typing import Generator

# Set event loop policy for Windows
if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for tests"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.fixture
def sample_pdf_path(temp_dir: Path) -> Path:
    """Create sample PDF for testing"""
    # Create a minimal PDF file
    pdf_path = temp_dir / "sample.pdf"
    
    # Minimal PDF content
    pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000052 00000 n 
0000000101 00000 n 
trailer<</Size 4/Root 1 0 R>>
startxref
190
%%EOF"""
    
    pdf_path.write_bytes(pdf_content)
    return pdf_path

@pytest.fixture
def sample_question_paper() -> str:
    """Sample question paper text"""
    return """
SECTION A

A1. What is artificial intelligence? [2 marks]

A2. Explain the following concepts: [4 marks]
    (i) Machine Learning
    (ii) Deep Learning

A3. Describe neural networks in detail. [4 marks]

SECTION B

B1. What is supervised learning? [6 marks]
    (i) Define classification
    (ii) Define regression

B2. Explain unsupervised learning. [7 marks]

B3. Describe reinforcement learning. [7 marks]

SECTION C

C1. Compare CNN and RNN. [7 marks]

C2. What are transformers? [6 marks]
    (i) Explain attention mechanism
    (ii) Describe positional encoding

C3. Discuss transfer learning. [7 marks]
"""

@pytest.fixture
def sample_answer_key() -> str:
    """Sample answer key"""
    return """
SECTION A
A1. AI is the simulation of human intelligence in machines. [2 marks]
A2. (i) ML is a subset of AI that learns from data. [2 marks]
    (ii) DL uses neural networks with multiple layers. [2 marks]

SECTION B
B1. (i) Classification assigns labels to data. [3 marks]
    (ii) Regression predicts continuous values. [3 marks]

SECTION C
C1. CNN processes spatial data, RNN processes sequential data. [7 marks]
"""

@pytest.fixture
def sample_student_answers() -> str:
    """Sample student answers"""
    return """
Student ID: TEST12345

SECTION A
A1. AI is about making computers smart

A2. (i) Machine learning helps computers learn from examples
    (ii) Deep learning uses many layers of neural networks

SECTION B
B1. (i) Classification puts things into categories
    (ii) Regression finds patterns in numbers

SECTION C
C1. CNN works with images and RNN works with sequences
"""

@pytest.fixture
def mock_ollama_response():
    """Mock Ollama API response"""
    return {
        "message": {
            "content": """{
                "student_id": "TEST12345",
                "sections": {
                    "A": {
                        "section_id": "A",
                        "questions": [],
                        "max_marks": 10
                    }
                },
                "student_answers": {},
                "answer_key": {},
                "metadata": {}
            }"""
        }
    }
