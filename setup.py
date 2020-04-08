from setuptools import setup, find_packages
setup(
    name='cortex',
    description='Thought Processing System',
    author_email='benny.fellman@gmail.com',
    author='Benny Fellman',
    version='1.00',
    python_requires='>=3.8.0',
    install_requires=[p.strip() for p in open('requirements.txt', 'r').readlines() if p.strip() and not p.startswith('#')],
    packages=find_packages(),
)
