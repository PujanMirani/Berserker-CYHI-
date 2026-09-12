from setuptools import setup, find_packages

setup(
    name="omnix",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "typer",
        "rich",
        "requests",
        "questionary",
        "watchdog",
        "psutil"
    ],
    entry_points={
        "console_scripts": [
            "omnix = omnix.main:app",
        ],
    },
)
