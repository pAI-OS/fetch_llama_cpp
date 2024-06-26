from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of your README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="fetch_llama_cpp",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "py-cpuinfo",
        "packaging",
    ],
    entry_points={
        'console_scripts': [
            'fetch_llama_cpp = fetch_llama_cpp:fetch',
        ],
    },
    author="Sam Johnston",
    author_email="samj@samj.net",
    description="Fetches the latest and best version of llama.cpp for your system.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/pAI-OS/fetch_llama_cpp",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "Topic :: System :: Installation/Setup",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Information Technology",
    ],
    python_requires='>=3.6',
)
