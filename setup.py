from setuptools import setup, find_packages

setup(
    name="CameraCountingDashboard",
    version="1.1.0",
    description="A dashboard with people counting information including a logger and database",
    author="Kyle Kelly",
    author_email="Kyle.kelly@student.unsw.edu.au",
    packages=find_packages(),
    include_package_data=True,  # Ensures non-Python files like config/data files are included
    install_requires=[
        'requests',  # Add other non-standard dependencies here
    ],
    entry_points={
        'console_scripts': [
            'dashboard = main:main',  # Entry point for running `dashboard` from the command line
        ],
    },
    python_requires='>=3.6',  # Adjust this if you support different versions
)