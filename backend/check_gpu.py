"""
GPU and VRAM Monitoring Script
Checks if Ollama and the system are properly using GPU
"""

import subprocess
import sys
import time
import requests
import json

def check_nvidia_gpu():
    """Check NVIDIA GPU availability"""
    print("="*80)
    print("🎮 GPU AVAILABILITY CHECK")
    print("="*80)
    
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu',
             '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for i, line in enumerate(lines):
                parts = [p.strip() for p in line.split(',')]
                print(f"\n✅ GPU {i}: {parts[0]}")
                print(f"   💾 Total VRAM: {parts[1]} MB")
                print(f"   📊 Used VRAM: {parts[2]} MB")
                print(f"   🆓 Free VRAM: {parts[3]} MB")
                print(f"   ⚡ GPU Usage: {parts[4]}%")
                print(f"   🌡️  Temperature: {parts[5]}°C")
            return True
        else:
            print("❌ nvidia-smi command failed")
            return False
    except FileNotFoundError:
        print("❌ nvidia-smi not found. NVIDIA GPU drivers may not be installed.")
        return False
    except Exception as e:
        print(f"❌ Error checking GPU: {e}")
        return False

def check_ollama_status():
    """Check if Ollama is running and using GPU"""
    print("\n" + "="*80)
    print("🦙 OLLAMA STATUS CHECK")
    print("="*80)
    
    try:
        # Check if Ollama is running
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        
        if response.status_code == 200:
            print("✅ Ollama is running!")
            
            models = response.json().get('models', [])
            print(f"\n📦 Loaded Models: {len(models)}")
            for model in models:
                name = model.get('name', 'Unknown')
                size = model.get('size', 0) / (1024**3)  # Convert to GB
                print(f"   • {name} ({size:.2f} GB)")
            
            return True
        else:
            print("❌ Ollama responded but with error")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama at http://localhost:11434")
        print("   Please start Ollama: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
        return False

def check_ollama_gpu_usage():
    """Verify Ollama is using GPU"""
    print("\n" + "="*80)
    print("🔍 OLLAMA GPU USAGE CHECK")
    print("="*80)
    
    print("\n⏳ Running a test inference to check GPU usage...")
    print("   (Monitor nvidia-smi in another terminal)")
    
    try:
        # Try to generate with a model
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2.5:14b",
                "prompt": "Hello",
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Test inference completed!")
            print("   Check nvidia-smi output to verify GPU usage spike")
            return True
        else:
            print(f"❌ Test failed: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - model might be loading")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def monitor_gpu_realtime():
    """Real-time GPU monitoring"""
    print("\n" + "="*80)
    print("📊 REAL-TIME GPU MONITORING (Press Ctrl+C to stop)")
    print("="*80)
    
    try:
        while True:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu',
                 '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                parts = [p.strip() for p in result.stdout.strip().split(',')]
                gpu_util = parts[0]
                mem_used = parts[1]
                mem_total = parts[2]
                temp = parts[3]
                
                print(f"\r⚡ GPU: {gpu_util}% | 💾 VRAM: {mem_used}/{mem_total} MB | 🌡️  {temp}°C", end='', flush=True)
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n✅ Monitoring stopped")

def check_environment():
    """Check Python environment for GPU libraries"""
    print("\n" + "="*80)
    print("🐍 PYTHON ENVIRONMENT CHECK")
    print("="*80)
    
    # Check CUDA environment variables
    import os
    cuda_visible = os.environ.get('CUDA_VISIBLE_DEVICES', 'Not set')
    print(f"\n🔧 CUDA_VISIBLE_DEVICES: {cuda_visible}")
    
    # Check if torch is installed and has CUDA
    try:
        import torch
        print(f"✅ PyTorch installed: {torch.__version__}")
        print(f"   CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"   CUDA version: {torch.version.cuda}")
            print(f"   GPU count: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
    except ImportError:
        print("ℹ️  PyTorch not installed (not required for Ollama)")

def main():
    """Main function"""
    print("\n" + "🎮 "*20)
    print("GPU & VRAM UTILIZATION CHECK FOR AI EXAM EVALUATOR")
    print("🎮 "*20 + "\n")
    
    # Check GPU
    gpu_available = check_nvidia_gpu()
    
    if not gpu_available:
        print("\n⚠️  WARNING: No GPU detected or nvidia-smi not available")
        print("   Ollama will run on CPU (much slower)")
        return
    
    # Check Ollama
    ollama_running = check_ollama_status()
    
    if not ollama_running:
        print("\n⚠️  Please start Ollama before running evaluations:")
        print("   > ollama serve")
        return
    
    # Check Python environment
    check_environment()
    
    # Test GPU usage
    print("\n" + "="*80)
    print("💡 RECOMMENDATIONS")
    print("="*80)
    print("\n1. ✅ Ollama automatically uses GPU when available")
    print("2. 📊 Monitor GPU usage while running evaluations:")
    print("   > nvidia-smi -l 1")
    print("3. 🚀 For maximum performance:")
    print("   - Keep GPU drivers updated")
    print("   - Close other GPU-intensive applications")
    print("   - Ensure adequate cooling")
    
    # Ask if user wants real-time monitoring
    print("\n" + "="*80)
    choice = input("\n🔍 Start real-time GPU monitoring? (y/n): ").strip().lower()
    
    if choice == 'y':
        monitor_gpu_realtime()
    else:
        print("\n✅ Check complete! Run 'nvidia-smi -l 1' in another terminal to monitor GPU during evaluation.")

if __name__ == "__main__":
    main()
