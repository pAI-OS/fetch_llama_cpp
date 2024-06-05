import requests
import platform
import re
import subprocess
import cpuinfo
import zipfile
import tarfile
import os
from pathlib import Path

# Downloads the best binary distribution of llama.cpp for your system and graphics card (if present)

# GitHub API URL for the latest release
GITHUB_API_URL = "https://api.github.com/repos/ggerganov/llama.cpp/releases/latest"
DOWNLOAD_DIR = Path("downloads")
EXTRACT_DIR = Path("llama.cpp")

# CUDA version to driver version mapping
CUDA_DRIVER_MAP = {
    "12.5.0": {"linux": "555.42.02", "windows": "555.85"},
    "12.4.1": {"linux": "550.54.15", "windows": "551.78"},
    "12.4.0": {"linux": "550.54.14", "windows": "551.61"},
    "12.3.1": {"linux": "545.23.08", "windows": "546.12"},
    "12.3.0": {"linux": "545.23.06", "windows": "545.84"},
    "12.2.2": {"linux": "535.104.05", "windows": "537.13"},
    "12.2.1": {"linux": "535.86.09", "windows": "536.67"},
    "12.2.0": {"linux": "535.54.03", "windows": "536.25"},
    "12.1.1": {"linux": "530.30.02", "windows": "531.14"},
    "12.1.0": {"linux": "530.30.02", "windows": "531.14"},
    "12.0.1": {"linux": "525.85.12", "windows": "528.33"},
    "12.0.0": {"linux": "525.60.13", "windows": "527.41"},
    "11.8.0": {"linux": "520.61.05", "windows": "520.06"},
    "11.7.1": {"linux": "515.48.07", "windows": "516.31"}
}

def get_latest_release():
    print("Fetching the latest release information from GitHub...")
    response = requests.get(GITHUB_API_URL)
    response.raise_for_status()
    print("Latest release information fetched successfully.")
    return response.json()

def get_system_info():
    print("Detecting system information...")
    system = platform.system().lower()
    arch = platform.machine().lower()
    print(f"System: {system}, Architecture: {arch}")
    return system, arch

def get_cuda_version_from_nvidia_smi():
    try:
        print("Checking CUDA version using nvidia-smi...")
        result = subprocess.run(['nvidia-smi'], stdout=subprocess.PIPE, text=True)
        match = re.search(r'CUDA Version: (\d+\.\d+)', result.stdout)
        if match:
            cuda_version = match.group(1)
            print(f"Detected CUDA version: {cuda_version}")
            return cuda_version
    except FileNotFoundError:
        print("nvidia-smi not found. No NVIDIA GPU detected.")
        return None
    return None

def get_driver_version_from_nvidia_smi():
    try:
        print("Checking driver version using nvidia-smi...")
        result = subprocess.run(['nvidia-smi'], stdout=subprocess.PIPE, text=True)
        match = re.search(r'Driver Version: (\d+\.\d+)', result.stdout)
        if match:
            driver_version = float(match.group(1))
            print(f"Detected driver version: {driver_version}")
            return driver_version
    except FileNotFoundError:
        print("nvidia-smi not found. No NVIDIA GPU detected.")
        return None
    return None

def check_nvidia_gpu():
    cuda_version = get_cuda_version_from_nvidia_smi()
    driver_version = get_driver_version_from_nvidia_smi()
    has_gpu = cuda_version is not None
    print(f"NVIDIA GPU detected: {has_gpu}, CUDA version: {cuda_version}, Driver version: {driver_version}")
    return has_gpu, 'nvidia', cuda_version, driver_version

def check_amd_gpu():
    try:
        print("Checking for AMD GPU using lspci...")
        result = subprocess.run(['lspci'], stdout=subprocess.PIPE, text=True)
        if 'AMD' in result.stdout:
            print("AMD GPU detected.")
            return True, 'amd', None
    except FileNotFoundError:
        print("lspci not found. No AMD GPU detected.")
        return False, None, None
    print("No AMD GPU detected.")
    return False, None, None

def check_avx_support():
    print("Checking CPU for AVX support...")
    info = cpuinfo.get_cpu_info()
    avx = 'avx' in info['flags']
    avx2 = 'avx2' in info['flags']
    avx512 = 'avx512f' in info['flags']
    print(f"AVX: {avx}, AVX2: {avx2}, AVX512: {avx512}")
    return avx, avx2, avx512

def get_available_cuda_versions(assets):
    print("Extracting available CUDA versions from assets...")
    cuda_versions = set()
    for asset in assets:
        match = re.search(r'cu(\d+\.\d+\.\d+)', asset['name'])
        if match:
            cuda_versions.add(match.group(1))
    sorted_versions = sorted(cuda_versions, reverse=True)
    print(f"Available CUDA versions: {sorted_versions}")
    return sorted_versions

def select_best_asset(assets, system, arch, gpu_vendor, driver_version, avx, avx2, avx512):
    print("Selecting the best asset for the system...")
    patterns = {
        'linux': {
            'nvidia': re.compile(r'.*ubuntu-x64.*\.zip'),
            'amd': re.compile(r'.*ubuntu-x64.*\.zip'),
            'none': re.compile(r'.*ubuntu-x64.*\.zip')
        },
        'darwin': {
            'none': re.compile(r'.*macos-(arm64|x64)\.zip')
        },
        'windows': {
            'nvidia': re.compile(r'.*win-cuda-cu(\d+\.\d+\.\d+)-x64\.zip'),
            'amd': re.compile(r'.*win-amd-x64\.zip'),
            'none': re.compile(r'.*win-(avx|avx2|avx512|noavx|openblas|rpc|sycl|vulkan)-x64\.zip')
        }
    }
    
    available_cuda_versions = get_available_cuda_versions(assets)
    
    # Sort CUDA versions in descending order to try the latest first
    available_cuda_versions.sort(reverse=True)
    
    for cuda_version in available_cuda_versions:
        required_driver_version = float(CUDA_DRIVER_MAP.get(cuda_version, {}).get(system, float('inf')))
        print(f"Checking CUDA version {cuda_version} which requires driver version {required_driver_version}")
        if driver_version >= required_driver_version:
            print(f"Driver version {driver_version} is sufficient for CUDA version {cuda_version}")
            for asset in assets:
                #print(f"Checking asset: {asset['name']}")
                if patterns[system][gpu_vendor].match(asset['name']):
                    asset_cuda_version = re.search(r'cu(\d+\.\d+\.\d+)', asset['name'])
                    if asset_cuda_version and asset_cuda_version.group(1) == cuda_version:
                        print(f"Selected asset: {asset['name']} for CUDA version {cuda_version}")
                        return asset['browser_download_url']
                else:
                    #print(f"Asset {asset['name']} does not match pattern {patterns[system][gpu_vendor]}")
                    pass
        else:
            print(f"Driver version {driver_version} is not sufficient for CUDA version {cuda_version}")
    
    # If no compatible CUDA version is found, fall back to CPU-only option
    print("No compatible CUDA version found. Falling back to CPU-only option.")
    for asset in assets:
        print(f"Checking CPU-only asset: {asset['name']}")
        if patterns[system]['none'].match(asset['name']):
            print(f"Selected CPU-only asset: {asset['name']}")
            return asset['browser_download_url']
        else:
            print(f"CPU-only asset {asset['name']} does not match pattern {patterns[system]['none']}")
    
    print("No suitable asset found.")
    return None

def download_and_extract(url, download_dir, extract_dir):
    print(f"Downloading asset from {url}...")
    
    # Ensure the download directory exists
    download_dir.mkdir(parents=True, exist_ok=True)
    
    response = requests.get(url)
    response.raise_for_status()
    
    filename = url.split('/')[-1]
    file_path = download_dir / filename
    
    with open(file_path, 'wb') as file:
        file.write(response.content)
    print(f"Downloaded asset to {file_path}")
    
    # Ensure the extraction directory exists
    extract_dir.mkdir(parents=True, exist_ok=True)
    
    if file_path.suffix == '.zip':
        print("Extracting zip file...")
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    elif file_path.suffix in ['.tar', '.gz', '.bz2']:
        print("Extracting tar file...")
        with tarfile.open(file_path, 'r:*') as tar_ref:
            tar_ref.extractall(extract_dir)
    print("Extraction complete.")

def run_binary_with_version(extract_dir):
    binary_name = "main.exe" if platform.system().lower() == "windows" else "main"
    binary_path = extract_dir / binary_name
    try:
        print(f"Running {binary_name} with '--version' to verify...")
        result = subprocess.run([str(binary_path), '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(result.stderr)
    except Exception as e:
        print(f"Failed to run {binary_name}: {e}")

def main():
    print("Starting the download process...")
    release_info = get_latest_release()
    system, arch = get_system_info()
    has_gpu, gpu_vendor, cuda_version, driver_version = check_nvidia_gpu()
    
    if not has_gpu:
        has_gpu, gpu_vendor, _ = check_amd_gpu()
    
    avx, avx2, avx512 = check_avx_support()
    
    asset_url = select_best_asset(
        release_info['assets'], system, arch, gpu_vendor, driver_version, avx, avx2, avx512
    )
    
    if asset_url:
        download_and_extract(asset_url, DOWNLOAD_DIR, EXTRACT_DIR)
    else:
        print("No suitable binary found for your system.")
    
    print("Download process completed.")

    # Run the extracted binary with '--version'
    run_binary_with_version(EXTRACT_DIR)

if __name__ == "__main__":
    main()