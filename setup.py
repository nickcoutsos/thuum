from setuptools import setup
from thuum import __version__

setup(
    name="thuum",
    version=__version__,
    url="https://github.com/nickcoutsos/thuum",
    packages=[
        "thuum",
    ],
    description=("Simple HTTP Load tester"),
    author="Nick Coutsos",
    author_email="nick@coutsos.com",
    install_requires=[
        "tornado==4",
    ],
    entry_points={
        "console_scripts": [
            "thuum = thuum.__main__:main"
        ]
    }
)
