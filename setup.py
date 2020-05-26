from pathlib import Path

from setuptools import find_packages, setup

test_requires = ["pytest"]

setup(
    name="BigSheets",
    version="1.0a1",
    url="https://github.com/bustawin/bigsheets",
    project_urls={
        "Documentation": "https://github.com/bustawin/bigsheets",
        "Code": "https://github.com/bustawin/bigsheets",
        "Issue tracker": "https://github.com/bustawin/bigsheets/issues/",
    },
    license="Private",
    author="Xavier Bustamante",
    author_email="xavier@bustawin.com",
    description="Sheets",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    long_description=Path("README.rst").read_text("utf8"),
    install_requires=[
        "pywebview",
        "python-decouple",
        "punq",
        "zipstream_new",
        "more_itertools",
        "ordered-set-37"
    ],
    extras_require={"test": test_requires, "build": ["pyinstaller"]},
    tests_require=test_requires,
    setup_requires=["pytest-runner"],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
    ],
)
