from setuptools import setup, find_packages

try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except: long_description = ""

setup(
    name='pcshell', 
    version='21.4.9.1',
    author='Chase M. Allen',
    description="Easily create robust Shell applications in Python with this extension for Click & Prompt-Toolkit; built with Windows OS in mind.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/xSlither/pretty-click-shell",

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Topic :: System :: Shells"
    ],

    install_requires=[
        'click',
        'colorama',
        'pygments',
        'pyreadline',
        'prompt-toolkit==2.0.10'
    ],
    
    packages=find_packages(),
    python_requires=">=3.8"
)