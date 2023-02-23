import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="categories",
    version="0.5",
    author="tg: n0v_it",
    author_email="kolzazanovikov@gmail.com",
    description="Category Module",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/n0vit/Modules.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
