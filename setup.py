import subprocess
from pathlib import Path

from setuptools import find_packages, setup
from setuptools.command.develop import develop
from setuptools.command.install import install


def _install_gui_web_npm_deps():
    subprocess.run("cd bigsheets/adapters/ui/gui/web-files && npm i", shell=True)


class PostDevelopCommand(develop):
    def run(self):
        super().run()
        _install_gui_web_npm_deps()


class PostInstallCommand(install):
    def run(self):
        super().run()
        _install_gui_web_npm_deps()


setup(
    name="BigSheets",
    version="1.0b1",
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
        "ordered-set-37",
    ],
    extras_require={
        "test": ["pytest"],
        "build": ["pyinstaller"],
        "coverage": ["coverage"],
    },
    cmdclass={"develop": PostDevelopCommand, "install": PostInstallCommand},
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
    ],
)
