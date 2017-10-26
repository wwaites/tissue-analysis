from setuptools import setup

setup(
    name='tissue-analysis',
    version='1.1',
    packages=['ta'],
    install_requires=['numpy', 'scipy', 'Pillow', 'pytess', 'xlrd'],
    entry_points={
        'console_scripts': [
            'tstats = ta.cmd:main',
            'eplot = ta.plt:main',
            'pmesh = ta.plt:mesh',
            'plattice = ta.mesh:lattice',
            'pentropy = ta.entropy:main',
            'pvoronoi = ta.voronoi:main'
            ]
        }
    )
