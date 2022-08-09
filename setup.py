import os
from pathlib import Path

from setuptools import setup, find_packages

PKG_NAME = "enr_app"
VERSION = os.getenv("BUILD_VERSION", "0.0.2")

with open('README.md') as f:
    readme = f.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

if __name__ == "__main__":

    print(f"Building wheel {PKG_NAME}-{VERSION}")

    # Dynamically set the __version__ attribute
    cwd = Path(__file__).parent.absolute()
    with open(cwd.joinpath(PKG_NAME, "version.py"), "w", encoding="utf-8") as f:
        f.write(f"__version__ = '{VERSION}'\n")

    setup(
        name=PKG_NAME,
        version=VERSION,
        author="Bruno Lenzi",
        author_email="bruno.lenzi@developpement-durable.gouv.fr",
        description="Tableau de bord des énergies renouvelables - mission connaissance, pôle Grand Est",
        long_description=readme,
        long_description_content_type="text/markdown",
        url="https://github.com/blenzi/enr_app",
        packages=find_packages(),
        classifiers=[
            "Programming Language :: Python",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Operating System :: OS Independent",
        ],
        python_requires='>=3.8',
        install_requires=requirements,
        include_package_data=True,
    )
