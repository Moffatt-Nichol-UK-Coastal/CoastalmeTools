from setuptools import setup, find_packages
import os

with open('requirements.txt') as f:
    reqs = f.read().splitlines()

setup(
    name="coastalmetools",
    version="0.1",
    packages=find_packages(),
    install_requires=reqs,
)

# /home/wilfc/CoastalmeTools/venv/bin/pip install --force-reinstall --no-deps ./dist/coastalmetools-0.1-py3-none-any.whl   