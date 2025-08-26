from setuptools import setup, find_packages

setup(
    name="intelligent-test-generator",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@mlb.com",
    description="Intelligent Test Case Generator for Server-Driven UI - Qdrant Hackathon 2025",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        line.strip()
        for line in open("requirements.txt").readlines()
        if not line.startswith("#")
    ],
    entry_points={
        "console_scripts": [
            "test-gen=src.pipeline:main",
        ],
    },
)