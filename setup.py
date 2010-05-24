##############################################################################
## File:  setup.py
##
## Copyright (C) 2010, Apache License 2.0
## The Institute for System Programming of the Russian Academy of Sciences
##
## Distutils setup scripts for building and installing Sedna Python driver.
## See INSTALL file for details on installation.
## See 'examples' folder for examples on using Sedna Python Driver.
##############################################################################


from distutils.core import setup, Extension
from distutils.spawn import find_executable
from distutils.command.build_ext import build_ext as _build_ext
from distutils.command.clean import clean as _clean
from distutils.dir_util import remove_tree
from distutils import log
import config
import sys
import os
import subprocess

temp_build_dir = os.path.join(os.getcwd(), 'build', 'cdriver.build') # temporary directory to build C driver

def grumble(str, err = 1):
    """ Prints specified error and exits """
    sys.stderr.write('%s Try to build C-driver manually and restart setup. See INSTALL file for details on installation.\n' % str)
    sys.exit(err)

# List containing needed Sedna C driver files (except lib, which is platform-specific)
cdriver_needed = ['libsedna.h', 'sp_defs.h']

def check_for_driver_swig(src_path, bin_path):
    """ check if we've got everything to swig C driver """
    for f in cdriver_needed:
        full_name = os.path.join(src_path, f)
        if not os.path.exists(full_name):
            log.warn("source file %s not found" % full_name)
            return False

    # search for library, but in a different directory
    full_lib_name = os.path.join(bin_path, sedna_library_name)
    if not os.path.exists(full_lib_name):
        log.warn("library file %s not found" % full_lib_name)
        return False

    return True

# Depending on platform select sedna library name
if sys.platform == 'win32':
     sedna_library = 'libsednamd' # Win32, static, /MD version
     sedna_library_name = 'libsednamd.lib'
     make_command = "nmake"
     cmake_generator = 'NMake Makefiles'
     lib_target = "sedna_md"
else:
     sedna_library = 'sedna_pic'      # *nix, static, fpic version
     sedna_library_name = 'libsedna_pic.a'
     make_command = "make"
     cmake_generator = 'Unix Makefiles'
     lib_target = "sedna_pic"

sys.stdout.write("config sedna binaries path -> %s\n" % config.SEDNA_BIN_PATH)
sys.stdout.write("config sedna sources path -> %s\n" % config.SEDNA_SRC_PATH)
sys.stdout.write("platform -> %s\n" % sys.platform)

# check if driver_path exists
if not os.path.exists(config.SEDNA_BIN_PATH) and not os.path.exists(config.SEDNA_SRC_PATH):
    grumble("error: you should have defined either driver binaries or Sedna sources path.")
    sys.exit(1)

# driver_bin_path constains path to Sedna library
# driver_src_path constains path to Sedna headers
driver_bin_path = driver_src_path = os.path.join(config.SEDNA_BIN_PATH, 'driver', 'c')

if not os.path.exists(config.SEDNA_BIN_PATH) or not check_for_driver_swig(driver_src_path, driver_bin_path):
    driver_src_path = os.path.join(config.SEDNA_SRC_PATH, 'driver', 'c')
    driver_bin_path = os.path.join(temp_build_dir, 'driver', 'c') # use temporary directory

class build_ext(_build_ext):
    """ Extends build_ext command by building sedna driver if needed """

    def check_build_prereq(self):
        """" Checks if we've got everything for the driver """
        if not os.path.exists(os.path.join(driver_src_path, 'CMakeLists.txt')):
            grumble("error: can't build Sedna C API library -- Sedna source directory doesn't look correct.")
            sys.exit(1)

        # try to find cmake
        if not find_executable('cmake'):
            grumble("error: can't build Sedna C API library -- cmake not found.")
            sys.exit(1)
        else:
            log.info("Found cmake command...")

        if not find_executable(make_command):
            grumble("error: can't build Sedna C API library -- %s not found." % make_command)
            sys.exit(1)
        else:
            log.info("Found %s command..." % make_command)

    def run(self):
        """ This method overrides common build_ext """

        # Check if sedna library exists
        # If not, try to build it from sources
        if not check_for_driver_swig(driver_src_path, driver_bin_path):
            log.warn("can't locate sedna Sedna C API library files. Will try to build Sedna C driver from scratch.")

            # check prereqs
            self.check_build_prereq()

            # create temporary directory to build C driver
            if os.path.exists(temp_build_dir):
                remove_tree(temp_build_dir)

            os.mkdir(temp_build_dir)

            # run cmake to configure Sedna sources
            p = subprocess.Popen(['cmake', '-G', cmake_generator, '-DCMAKE_BUILD_TYPE=Release', config.SEDNA_SRC_PATH], cwd=temp_build_dir)
            p.wait()
            if p.returncode != 0:
                grumble("error: driver configuration.", 2)

            # run make to build sedna driver
            p = subprocess.Popen([make_command, lib_target], cwd=temp_build_dir)
            p.wait()
            if p.returncode != 0:
                grumble("error: driver make error.", 3)

            # check if we've got all we need for the driver
            if not check_for_driver_swig(driver_src_path, driver_bin_path):
                grumble("error: driver hasn't been built.", 4)

        log.debug("sedna C library dir -> %s" % driver_bin_path)
        log.debug("sedna C library headers dir -> %s" % driver_src_path)
        log.debug("sedna C library name -> %s" % sedna_library_name)

        return _build_ext.run(self) # call python standard clean

class clean(_clean):
    """ Extends clean command by removing sedna temp build driver dir """
    def run(self):
        """ This method overrides common clean """

        if self.all and os.path.exists(temp_build_dir):
            remove_tree(temp_build_dir)

        return _clean.run(self) # call standard clean

# SWIG extension module definition
libsedna = Extension('_libsedna',
                     sources = ['libsedna.i'],
                     swig_opts=['-threads', '-I'+ driver_src_path],
                     include_dirs = [driver_src_path],
                     library_dirs = [driver_bin_path],
                     libraries = [sedna_library])

# Sedna Python driver module definition
setup (name = 'sedna',
       version = '0.2',
       description = 'Sedna XML Database Python Driver',
       ext_modules  = [libsedna],
       author='Modis Team',
       author_email='modis@ispras.ru',
       url='http://modis.ispras.ru/sedna',
       py_modules = ['libsedna', 'sedna'],
       cmdclass = {'build_ext': build_ext, 'clean': clean},
       license = 'Apache 2.0')
