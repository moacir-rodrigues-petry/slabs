"""
Setup script for PyChat
"""
from setuptools import setup, find_packages

setup(
    name="pychat",
    version="0.3.0",  # Updated for Phase 3
    packages=find_packages(),
    install_requires=[
        "pillow>=9.0.0",  # For handling images in tkinter
        "emoji>=2.0.0",   # For emoji support
    ],
    entry_points={
        'console_scripts': [
            'pychat-cli=pychat.interfaces.cli_interface:main',
            'pychat-gui=pychat.interfaces.gui_interface:main',
        ],
    },
    author="PyChat Team",
    author_email="example@example.com",
    description="A simple, lightweight chat application built with Python 3",
    keywords="chat, messaging, python, gui",
    python_requires=">=3.6",
)
