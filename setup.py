from setuptools import setup

setup(
    name='omnieq-api',
    version='0.1',
    py_modules=['omnieq'],
    include_package_data=True,
    install_requires=[
        'diskcache',
        'ratelimit',
        'pandas_market_calendars',
        'requests',
        'joblib',
    ],
)