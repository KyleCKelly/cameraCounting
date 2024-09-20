from setuptools import setup, find_packages

setup(
    name="dashboard",
    version="1.0.0",
    description="A dashboard with people counting information including a logger and database",
    author="Kyle Kelly",
    author_email="Kyle.kelly@student.unsw.edu.au",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'requests',
        'sqlite3'
    ],
    entry_points={
        'console_scripts': [
            'dashboard = main:main',
        ],
    },
)