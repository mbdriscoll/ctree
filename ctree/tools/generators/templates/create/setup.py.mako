from distutils.core import setup

setup(
    name='${specializer_name}',
    version='0.95a',

    packages=[
        '${specializer_name}',
    ],

    package_data={
        '${specializer_name}': ['defaults.cfg'],
    },

    install_requires=[
        'ctree',
    ]
)
