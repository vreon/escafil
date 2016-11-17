from setuptools import setup

setup(
    name = 'escafil',
    packages = ['escafil'],
    version = '0.0.1',
    description = 'A minimal Kubernetes API client',
    author = 'Jesse Dubay',
    author_email = 'jesse@jessedubay.com',
    keywords = ['kubernetes'],
    install_requires=[
        'requests>=2,<3',
    ],
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
)