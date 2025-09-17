from setuptools import setup, find_packages

setup(
    name="mlb-intelligent-test-generator",
    version="0.1.0",
    author="Douglas Mason",
    author_email="douglas.mason@mlb.com",
    description="MLB Intelligent Test Generator - AI-powered test generation for Server-Driven UI components",
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
            "test-gen=pipeline:main",
        ],
    },
)