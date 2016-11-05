from __future__ import print_function

from setuptools import setup, find_packages


setup(name='axibot',
      version='0.0.1.dev',
      description='Software for AxiDraw pen plotting robot',
      long_description='',
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3.5',
      ],
      keywords='axidraw cam plotter',
      url='https://github.com/storborg/axibot',
      author='Scott Torborg',
      author_email='storborg@gmail.com',
      license='GPL',
      packages=find_packages(),
      install_requires=[
          'pyserial',
          'svg.path',
          'colormath',
          # Required for server
          # XXX put these in extras
          #'aiohttp',
          #'aiohttp_mako',
          # Required for debug tool
          # XXX put these in extras
          #'matplotlib',
      ],
      setup_requires=['pytest-runner'],
      tests_require=['pytest'],
      include_package_data=True,
      zip_safe=False,
      entry_points="""\
      [console_scripts]
      axibot = axibot.cmd:main
      axibot-debug = axibot.debug:main
      """)
