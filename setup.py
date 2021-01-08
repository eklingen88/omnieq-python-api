import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='omnieq-api',
    version='1.0.0',
    py_modules=['omnieq'],
    include_package_data=True,
    install_requires=[
        'diskcache',
        'ratelimit',
        # 'pandas_market_calendars',
        'requests',
        'joblib',
    ],
    author="Eric M. Klingensmith",
    author_email="eric.m.klingensmith@gmail.com",
    description="OmniEQ API wrapper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/eklingen88/omnieq-python-api",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
