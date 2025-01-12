from setuptools import setup, find_packages

setup(
    name="suno2openai",
    version="0.2.1",
    packages=find_packages(),
    install_requires=[
        "aiohttp",
        "fake-useragent",
        "python-dotenv",
    ],
) 