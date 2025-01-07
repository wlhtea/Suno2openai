from setuptools import setup, find_packages

setup(
    name="suno_ai",  # 你的项目名称
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "aiohttp",
        "fake-useragent",
        # 其他依赖项...
    ],
) 