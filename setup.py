from setuptools import setup, find_packages
import os
import sys

# Add the package directory to the path to import __version__
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from chatrixcd import __version__

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="chatrixcd",
    version=__version__,
    author="ChatrixCD Contributors",
    description="A Matrix bot for CI/CD automation with Semaphore UI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CJFWeatherhead/ChatrixCD",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "chatrixcd=chatrixcd.main:main",
        ],
    },
)
