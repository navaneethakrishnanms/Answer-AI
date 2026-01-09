"""
Comprehensive setup verification script for AI Exam Evaluator
Checks all dependencies, configurations, and service connectivity
"""

import sys
import os
from pathlib import Path
import importlib

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text:^60}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ {text}{Colors.RESET}")

def check_python_version():
    """Check Python version"""
    print_header("Python Environment")
    version = sys.version_info
    print_info(f"Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 10:
        print_success("Python version is compatible (3.10+)")
        return True
    else:
        print_error("Python 3.10+ is required")
        return False

def check_required_packages():
    """Check if all required packages are installed"""
    print_header("Required Packages")
    
    packages = {
        'fastapi': 'FastAPI framework',
        'uvicorn': 'ASGI server',
        'sqlalchemy': 'Database ORM',
        'pydantic': 'Data validation',
        'requests': 'HTTP client',
        'fitz': 'PyMuPDF (PDF processing)',
        'torch': 'PyTorch (GPU support)',
        'yaml': 'YAML parser',
        'aiohttp': 'Async HTTP client',
    }
    
    all_installed = True
    
    for package, description in packages.items():
        try:
            mod = importlib.import_module(package)
            version = getattr(mod, '__version__', 'unknown')
            print_success(f"{description:30} - v{version}")
        except ImportError:
            print_error(f"{description:30} - NOT INSTALLED")
            all_installed = False
    
    return all_installed

def check_gpu_availability():
    """Check GPU availability"""
    print_header("GPU & CUDA")
    
    try:
        import torch
        
        if torch.cuda.is_available():
            print_success(f"CUDA is available")
            print_info(f"  GPU: {torch.cuda.get_device_name(0)}")
            print_info(f"  CUDA Version: {torch.version.cuda}")
            print_info(f"  Device Count: {torch.cuda.device_count()}")
            print_info(f"  Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
            return True
        else:
            print_warning("CUDA not available - will use CPU (slower)")
            return False
    except ImportError:
        print_error("PyTorch not installed")
        return False

def check_directories():
    """Check required directories"""
    print_header("Directory Structure")
    
    base_dir = Path("C:/Projects/Paper_AI/backend")
    required_dirs = [
        base_dir / "uploads",
        base_dir / "results",
        base_dir / "temp",
        base_dir / "logs",
        base_dir / "app",
        base_dir / "app/api",
        base_dir / "app/services",
        base_dir / "app/config",
    ]
    
    all_exist = True
    
    for dir_path in required_dirs:
        if dir_path.exists():
            print_success(f"{dir_path.name:20} - exists")
        else:
            print_warning(f"{dir_path.name:20} - missing (will create)")
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print_success(f"  Created: {dir_path}")
            except Exception as e:
                print_error(f"  Failed to create: {e}")
                all_exist = False
    
    return all_exist

def check_config_file():
    """Check configuration file"""
    print_header("Configuration")
    
    config_path = Path("C:/Projects/Paper_AI/backend/app/config/config.yaml")
    
    if not config_path.exists():
        print_error(f"Config file not found: {config_path}")
        return False
    
    print_success(f"Config file exists: {config_path}")
    
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check key sections
        required_sections = ['ocr', 'ollama', 'storage', 'exam_rules']
        for section in required_sections:
            if section in config:
                print_success(f"  Section '{section}' - present")
            else:
                print_error(f"  Section '{section}' - missing")
        
        return True
    except Exception as e:
        print_error(f"Failed to parse config: {e}")
        return False

def check_ollama_service():
    """Check Ollama service connectivity"""
    print_header("Ollama Service")
    
    try:
        import requests
        
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print_success("Ollama service is running")
            
            data = response.json()
            models = data.get('models', [])
            
            print_info(f"  Available models: {len(models)}")
            
            # Check for required models
            required_models = ['qwen', 'deepseek']
            for req_model in required_models:
                found = any(req_model in model['name'].lower() for model in models)
                if found:
                    matching = [m['name'] for m in models if req_model in m['name'].lower()]
                    print_success(f"  {req_model.capitalize()} model: {matching[0]}")
                else:
                    print_warning(f"  {req_model.capitalize()} model not found")
            
            return True
        else:
            print_error(f"Ollama service returned status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Ollama service is not running")
        print_info("  Start Ollama and ensure it's accessible at http://localhost:11434")
        return False
    except Exception as e:
        print_error(f"Error checking Ollama: {e}")
        return False

def check_environment_variables():
    """Check environment variables"""
    print_header("Environment Variables")
    
    env_vars = {
        'OCR_API_KEY': 'OCR.Space API Key',
        'OLLAMA_HOST': 'Ollama Host (optional)',
    }
    
    all_set = True
    
    for var, description in env_vars.items():
        value = os.getenv(var)
        if value:
            masked = value[:8] + '...' if len(value) > 8 else value
            print_success(f"{description:30} - {masked}")
        else:
            if var == 'OCR_API_KEY':
                print_error(f"{description:30} - NOT SET")
                all_set = False
            else:
                print_warning(f"{description:30} - not set (will use default)")
    
    return all_set

def main():
    """Run all verification checks"""
    print_header("AI Exam Evaluator - Setup Verification")
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Packages", check_required_packages),
        ("GPU/CUDA", check_gpu_availability),
        ("Directories", check_directories),
        ("Configuration", check_config_file),
        ("Environment Variables", check_environment_variables),
        ("Ollama Service", check_ollama_service),
    ]
    
    results = []
    
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Error in {name}: {e}")
            results.append((name, False))
    
    # Summary
    print_header("Verification Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        if result:
            print_success(f"{name:30} - PASSED")
        else:
            print_error(f"{name:30} - FAILED")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} checks passed{Colors.RESET}\n")
    
    if passed == total:
        print_success("All checks passed! System is ready.")
        print_info("\nYou can start the server with:")
        print(f"  {Colors.CYAN}python -m uvicorn app.main:app --reload{Colors.RESET}")
        return 0
    else:
        print_warning(f"\n{total - passed} check(s) failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
