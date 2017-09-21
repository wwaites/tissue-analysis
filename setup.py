from setuptools import setup

setup(
    name='tissue-analysis',
    version='1.0',
    packages=['ta'],
    install_requires=['numpy', 'scipy', 'Pillow'],
    entry_points={
        'console_scripts': [
            'tstats = ta.cmd:main',
            'eplot = ta.plt:main',
            'pmesh = ta.plt:mesh',
            ]
        }
    )
