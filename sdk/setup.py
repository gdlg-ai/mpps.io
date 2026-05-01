from setuptools import setup

setup(
    name="mpps",
    version="0.5.0",
    description="Python SDK for mpps.io tamper-proof receipts for AI agent work",
    author="GlideLogic Corp.",
    url="https://github.com/gdlg-ai/mpps.io",
    license="MIT",
    py_modules=["mpps"],
    install_requires=["requests>=2.28.0"],
    python_requires=">=3.8",
)
