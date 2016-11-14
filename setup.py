from __future__ import print_function

from setuptools import setup, find_packages


setup(name='axibot',
      version='0.0.2',
      description='Software for AxiDraw pen plotting robot',
      long_description='',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Environment :: Console',
          'Environment :: Web Environment',
          'Topic :: Artistic Software',
          'Topic :: Multimedia :: Graphics',
          'Topic :: Printing',
      ],
      keywords='eibotboard axidraw cam motion pen drawing plotter',
      url='https://github.com/storborg/axibot',
      author='Scott Torborg',
      author_email='storborg@gmail.com',
      license='GPL',
      packages=find_packages(),
      install_requires=[
          'pyserial',
          'svg.path',
          'colormath',
      ],
      setup_requires=['pytest-runner'],
      tests_require=['pytest'],
      extras_require={
          'server': ['aiohttp', 'aiohttp_mako'],
          'debug': ['matplotlib'],
      },
      include_package_data=True,
      zip_safe=False,
      entry_points="""\
      [console_scripts]
      axibot = axibot.cmd:main
      axibot-debug = axibot.debug:main [debug]
      """)
