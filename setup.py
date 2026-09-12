from setuptools import setup, find_packages

setup(
    name="berserker",
    version="1.0.0",
    description="Hackathon toolkit for CI/CD and log correlation",
    packages=find_packages(),
    py_modules=["main"],
    install_requires=[
        "rich>=13.0.0",
        "questionary>=2.0.0",
        "requests>=2.30.0",
    ],
    entry_points={
        "console_scripts": [
            "berserker=main:main",
        ],
    },
)
