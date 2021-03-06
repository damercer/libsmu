[![appveyor status](https://ci.appveyor.com/api/projects/status/p30uj8rqulrxsqvs/branch/master?svg=true)](https://ci.appveyor.com/project/analogdevicesinc/libsmu/branch/master)
[![travis-ci status](https://travis-ci.org/analogdevicesinc/libsmu.svg?branch=master)](https://travis-ci.org/analogdevicesinc/libsmu)
[![coverity status](https://scan.coverity.com/projects/analogdevicesinc-libsmu/badge.svg)](https://scan.coverity.com/projects/analogdevicesinc-libsmu)

### libsmu

libsmu contains abstractions for streaming data to and from USB-connected
analog interface devices, currently supporting the Analog Devices' ADALM1000.
Building off of LibUSB for cross-platform operation, it offers the sourcing of
repeated waveforms, configuration of hardware, and measuring of signals.

Python bindings are also provided in the form of the pysmu module. See
instructions below for how to build them.

#### Building

Build dependencies are cmake, pkgconfig, boost (headers only), and libusb-1.0.

Bindings for Python are enabled by default. To be able to build libsmu with 
Python bindings, use the following steps, before compiling the library:

Install pip and setup tools for Python:
```
$ sudo apt-get install python-setuptools python-pip
```

Install Cython
```
$ sudo pip install cython
```

To build and install the library and command line application use the following
steps:

Clone the repo:
```
$ git clone https://github.com/analogdevicesinc/libsmu.git
```

Configure via cmake:
```
$ mkdir build && cd build && cmake ..
```

Compile:
```
$ make
```

Install:
```
$ sudo make install
```

##### Docs

Doxygen-based documentation is available at
https://analogdevicesinc.github.io/libsmu/.

This can also be built locally if enabled using the following cmake option
before running make:

```
cmake -DWITH_DOC=ON ..
```

After make is run, the generated documentation files can then be found in the
html subdir of the build directory.

##### Testing

The [Google Test framework](https://github.com/google/googletest) is used to
run various streaming tests. Make sure it's installed on the host system and then use the
following to build and run tests:

```
cmake -DBUILD_TESTS=ON ..
make check
```

Note that at least one device should be inserted to the system for the checks
to run properly.

##### Python

Bindings for python (2.7, 3.4, and 3.5) are available and can be enabled
explicitly via the following cmake command (they're enabled by default):

```
$ cmake -DBUILD_PYTHON=ON ..
```

Note that this will build only one versions of python for the first supported
implementation it finds installed on the system. To build them for other
versions it's easiest to build them manually via the setup.py script in the
regular python manner if libsmu has already been built and/or installed on the
host machine.


##### Linux

By default, libsmu is installed into various directories inside /usr. However,
if it's installed somewhere such as /usr/local the runtime linker cache often
needs to be regenerated otherwise runtime linking errors will occur.

Regenerate runtime linker cache:
```
$ sudo ldconfig
```

If the same errors still happen, make sure the directory the libsmu library is
installed to is in the sourced files for /etc/ld.so.conf before running
ldconfig.

In addition, the udev rules file (53-adi-m1k-usb.rules) is installed by default
to give regular users access to devices supported by libsmu. Udev has to be
forced to reload its rules files in order to use the new file without rebooting
the system.

Reload udev rules files:
```
$ sudo udevadm control --reload-rules
```

Finally, for python support on Debian/Ubuntu derived distros users will have to
export PYTHONPATH or perform a similar method since hand-built modules are
installed to the site-packages directory (which isn't in the standard search
list) while distro provided modules are placed in dist-packages.

Add pysmu module directory to python search path:
```
$ export PYTHONPATH=/usr/lib/python2.7/site-packages:${PYTHONPATH}
```

Note the command will have to be altered for targets with different bitness or
python versions.

##### OS X

For systems running OS X, first install [homebrew](http://brew.sh). Then use
brew to install libusb, cmake, boost, pkg-config, and optionally python to
build the python bindings. In addition, cython needs to be installed via pip to
generate the python extension.

Note that libusb is built for both 32 and 64 bit architectures since the
current build system for libsmu builds universal binaries by default.

```
brew install libusb --universal
brew install cmake boost pkg-config python
pip install cython
```

After the above dependencies are installed, the command line instructions in
the previous sections should work on OS X as well.

##### Windows

On Windows, it's easiest to use the provided installers,
[libsmu-setup-x86.exe](https://github.com/analogdevicesinc/libsmu/releases/latest) and
[libsmu-setup-x64.exe](https://github.com/analogdevicesinc/libsmu/releases/latest)
that install either 32 or 64 bit support, respectively. During the
install process options are provided to install python and Visual Studio
development support.
