"""
Setup script for PyChat
"""
from setuptools import setup, find_packages

setup(
    name="pychat",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        'console_scripts': [
            'pychat-cli=pychat.interfaces.cli_interface:main',
            'pychat-gui=pychat.interfaces.gui_interface:main',
        ],
    },
    author="PyChat Team",
    author_email="example@example.com",
    description="A simple, lightweight chat application built with Python 3",
    keywords="chat, messaging, python",
    python_requires=">=3.6",
)
