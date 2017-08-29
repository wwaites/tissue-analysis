from setuptools import setup

setup(
    name='tissue-analysis',
    version='1.0',
    packages=['ta'],
    install_requires=['numpy', 'scipy'],
    entry_points={
        'console_scripts': [
            'tstats = ta.cmd:main'
            ]
        }
    )
