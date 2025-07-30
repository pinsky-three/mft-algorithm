from setuptools import setup, find_packages

setup(
    name="mft-backtrader",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "backtrader",
        "pandas",
        "numpy",
    ],
    author="MFT Algorithm Team",
    description="Backtrader integration for MFT Algorithm",
    python_requires=">=3.8",
)