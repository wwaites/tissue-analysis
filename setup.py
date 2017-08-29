from setuptools import setup

setup(
    name='tissue-analysis',
    version='1.0',
    packages=['ta'],
    install_requires=['scipy'],
    entry_points={
        'console_scripts': [
            'clusters = ta.clusters:main'
            ]
        }
    )
