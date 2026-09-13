from setuptools import setup, find_packages

setup(
    name="berserker",
    version="1.0.0",
    description="Berserker Hackathon Toolkit",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "typer",
        "rich",
        "requests",
        "questionary",
        "watchdog",
        "psutil",
        "prompt_toolkit>=3.0.0",
        "google-genai>=0.3.0",
    ],
    entry_points={
        "console_scripts": [
            "griffith = omnix.triage:app",
            "omnix = omnix.main:app",
            "berserker = berserker_cli.cli:main",
        ],
    },
)
