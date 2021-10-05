
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="lora-multihop",
    version="0.0.1",
    author="Marvin Rausch",
    author_email="",
    description="ad-hoc routing protocol with tcp interface",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    project_urls={},
    classifiers=[],
    package_dir={"": "src"},
    packages=['ipc', 'protocol', 'util'],
    python_requires=">=3.6",
)