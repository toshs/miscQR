from setuptools import setup

setup(
    name="misqr",
    version="1.0.0",
    install_requires=["reedsolo", "pillow", "numpy"],
    entry_points={
        "console_scripts": [
            "whimq = src.whim:main",
        ],
    }
)
