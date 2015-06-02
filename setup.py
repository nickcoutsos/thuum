from setuptools import setup

def read_requirements(path):
    with open(path) as f:
        requirements = f.readlines()
    return requirements

setup(
    name="thuum",
    version="0.1.1",
    url="https://github.com/nickcoutsos/thuum",
    packages=[
        "thuum",
    ],
    description=("Simple HTTP Load tester"),
    author="Nick Coutsos",
    author_email="nick@coutsos.com",
    install_requires=read_requirements("requirements.txt"),
    entry_points={
        "console_scripts": [
            "thuum = thuum.__main__:main"
        ]
    }
)
