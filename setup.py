from setuptools import setup, find_packages


with open('README.rst', 'r') as fp:
    long_description = fp.read()

with open('requirements.txt', 'r') as fp:
    requirements = fp.read().splitlines()

setup(
    name='bg-helper',
    version='0.1.21',
    description='CLI helpers for background tasks (shell), docker (databases), git, and SSH',
    long_description=long_description,
    author='Ken',
    author_email='kenjyco@gmail.com',
    license='MIT',
    url='https://github.com/kenjyco/bg-helper',
    download_url='https://github.com/kenjyco/bg-helper/tarball/v0.1.21',
    packages=find_packages(),
    install_requires=requirements,
    include_package_data=True,
    package_dir={'': '.'},
    package_data={
        '': ['*.ini'],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python',
        'Programming Language :: Unix Shell',
        'Topic :: Database',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
    ],
    keywords=['background', 'shell', 'git', 'ssh', 'docker', 'redis', 'mongodb', 'postgres', 'postgresql', 'mysql', 'helper', 'kenjyco']
)
