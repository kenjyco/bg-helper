from setuptools import setup, find_packages


setup(
    name='bg-helper',
    version='0.1.0',
    description='Common CLI background helpers',
    author='Ken',
    author_email='kenjyco@gmail.com',
    license='MIT',
    url='https://github.com/kenjyco/bg-helper',
    download_url='https://github.com/kenjyco/bg-helper/tarball/v0.1.0',
    packages=find_packages(),
    include_package_data=True,
    package_dir={'': '.'},
    package_data={
        '': ['*.ini'],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries',
        'Intended Audience :: Developers',
    ],
    keywords=['background', 'helper']
)
