from setuptools import setup


setup(
    name='IlluminateCore',
    version='1.0.0',
    url='https://github.com/tonyhhyip/py-illuminate-core',
    license='MIT',
    author='Tony Yip',
    author_email='tony@opensource.hk',
    description='Dependency Container Injection Core',
    zip_safe=False,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Topic :: Dependency Injection'
    ],
    packages=[
        'illuminate_core',
        'illuminate_core.container',
        'illuminate_core.contract',
        'illuminate_core.events',
        'illuminate_core.kernel',
        'illuminate_core.service',
        'illuminate_core.support',
    ],
    install_requires=[],
    include_package_data=True
)