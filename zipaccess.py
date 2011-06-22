#!/usr/bin/env python
"""
zipaccess
=========

Patches functions [modules]:file+open, and os.path:exists+isfile
to enable accessing files inside zip archives using standard file functions.

Package:
  http://pypi.python.org/pypi/zipaccess
Project:
  https://github.com/iki/zipaccess
Issues:
  https://github.com/iki/zipaccess/issues
Updates:
  https://github.com/iki/zipaccess/commits/master.atom
Install via `pip <http://www.pip-installer.org>`_:
  ``pip install zipaccess``
Install via `easy_install <http://peak.telecommunity.com/DevCenter/EasyInstall>`_:
  ``easy_install zipaccess``
Sources via `git <http://git-scm.com/>`_:
  ``git clone https://github.com/iki/zipaccess``
Sources via `hg-git <https://github.com/schacon/hg-git>`_:
  ``hg clone git://github.com/iki/zipaccess``


Usage
-----

Use as a class. Do not instantiate it::

    class AnyZipAccess(zipaccess.ZipAccess):
        any_zip = True  # custom modifications here

    AnyZipAccess.enable()

Or use as a module::

    zipaccess.enable()
    zipaccess.addzip('data.zip')

Optionally, register zipaccess.ZipAccess as os.zipaccess::

    zipaccess.enable(register=True)

so other modules can easily use::

    try:
        os.zipaccess.enable(locals())
    except AttributeError:
        pass


Note on `Google App Engine <http://code.google.com/appengine>`_ (GAE)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On GAE, the __builtin__ module changes are not reflected, even in the local name space.

To use zip access in any GAE module, you need to enable it for that module locals::

    try:
        import zipaccess
        zipaccess.enable(locals())
    except ImportError:
        pass

Alternatively, only enable zip access locally, if it was already registered::

    try:
        os.zipaccess.enable(locals())
    except AttributeError:
        pass

Or enable it for target modules externally::

    zipaccess.enable([
        'babel.core',
        'babel.localedata',
        'tipfy.template',
        'werkzeug.debug.tbtools',
        ])
    # It imports all the modules though, which may be not what you want.
    # If you know, how to hook on module import, let me kindly know.

Note, that os.path.isfile and os.path.exists are patched globally. Even on GAE,
they apply for all modules of given instance. If some modules do support
zip files, they usually first check if regular file exists, and if not, they
split the path and check if the zipfile exists.
With zip access enabled, the regular file check will succeed, which is ok
as long as consequently used file() or open() functions are patched too.

Example:

    The tipfy.debugger.get_loader() function checks if templates are located
    in a regular directory or in a zip file (``lib/dist.zip`` usually).
    Then it returns tipfy.template.Loader or tipfy.template.ZipLoader accordingly.
    With zipaccess enabled, the standard tipfy.template.Loader will be used,
    and therefore ``zipaccess.enable('tipfy.template')`` is needed to make it work.

    See https://github.com/moraes/tipfy/blob/master/tipfy/debugger/__init__.py#L26.

"""
__docformat__ = 'restructuredtext en'
__version__ = '0.1rc1'
__all__ = 'ZipAccess add enable hasfile getfile file open'.split()

import sys
import os
import logging

from os.path import basename, isabs, abspath, realpath, join, sep, isfile, exists

_ = realpath(basename(__file__))
if _ != abspath(_):
    realpath = lambda x: abspath(realpath(x))
    # On some outdated Unixes, realpath() might not return an absolute path.

_exists = exists
_isfile = isfile
_open = open
_file = file

def exists(path):
    return exists._zipaccess.hasfile(path) and True or exists._exists(path)

def isfile(path):
    return isfile._zipaccess.hasfile(path) and True or isfile._isfile(path)

def open(name, mode='r', buffering=-1, **options):
    return (
        open._zipaccess.getfile(name, mode, buffering, **options) or
        open._open(name, mode, buffering, **options)
        )

# def file(name, mode='r', buffering=-1, **options):
#     return (
#         file._zipaccess.getfile(name, mode, buffering, **options) or
#         file._file(name, mode, buffering, **options)
#         )

class file(file):
    def __init__(self, name, mode='r', buffering=-1, **options):
        self.__target__ = (
        file._zipaccess.getfile(name, mode, buffering, **options) or
        file._file(name, mode, buffering, **options)
        )
    def __getattribute__(self, name):
        if name == '__target__':
            return object.__getattribute__(self, name)
        else:
            return getattr(object.__getattribute__(self, '__target__'), name)

exists._exists = _exists
isfile._isfile = _isfile
open._open = _open
file._file = _file


class ZipAccess(object):
    """Access files inside zip archives using standard file functions.
    """

    log = logging     # Logger object. Disabled if False. Defaults to logging module.
    zipsep = '/'      # Zip files always use '/', independently on OS path sep.
    zipmodes = dict(  # Maps file modes to ZipFile.open modes.
        r = 'rU',
        rb = 'r',
        )

    any_zip = False   # Allow access to any zip files.
    register = False  # Register this class as os.zipaccess.

    zips = {}         # Dictionary of zip files with access enabled:
                      #     Key: zip file name
                      #     Value: True (enabled), False (failed), ZipFile

    file = file       # Patched functions or classes.
    exists, isfile, open = map(staticmethod, (
        exists, isfile, open))

    zipfile = None    # ZipFile class. Import lazily.

    def __init__(self):
        """Use as a class. Do not instantiate it.
        """
        raise RuntimeError('%s: %s' % (
            self.__class__.__name__, self.__init__.__doc__))

    @classmethod
    def enable(cls, for_modules=True, any_zip=None, register=None):
        """Enables access to files inside zip archives using standard file functions.

        Patches functions [for_modules]:file+open, and os.path:exists+isfile.

        For_modules is expected to be True (enable globally), or False (do not enable),
        or module object/name/list to import and enable zip access from.

        If any_zip is True, then access to all zip files is enabled.
        If it's False (default), then zip files have to be added via addzip().

        If register is True, then the class is registered as os.zipaccess,
        so other modules can easily use::

            try:
                os.zipaccess.enable(locals())
            except AttributeError:
                pass
        """
        if any_zip is not None:
            cls.any_zip = any_zip

        if register is not None:
            cls.register = register

        if modules:
            cls._patch(cls.file, modules, 'file', _zipaccess=cls)
            cls._patch(cls.open, modules, 'open', _zipaccess=cls)
            cls._patch(cls.exists, os.path, 'exists', _zipaccess=cls)
            cls._patch(cls.isfile, os.path, 'isfile', _zipaccess=cls)

            if cls.register:
                cls._patch(cls, os, 'zipaccess')

    @classmethod
    def _patch(cls, *args, **argd):
        """Placeholder to import patch lazily."""
        import monkeypatch
        cls._patch = staticmethod(monkeypatch.patch)
        return monkeypatch.patch(*args, **argd)

    @classmethod
    def addzip(cls, path):
        """Adds path to set of zip files with access enabled.
        """
        if not path.lower().endswith('.zip'):
            raise ValueError('path is expected to have a .zip extension: %s' % path)

        path = realpath(path)

        if cls.zips.get(path, None):
            cls.log.info('zip access enable: %s' % path)
            cls.zips[path] = True

    @classmethod
    def delzip(cls, path):
        """Removes path from set of zip files with access enabled.
        """
        del cls.zips[path]

    @classmethod
    def hasfile(cls, path):
        """Returns (ZipFile, inner file name) if file is in a zip file,
        or False if it isn't.
        """
        path = realpath(path)
        pos = path.lower().find('.zip%s' % sep)

        if pos == -1:
            return False

        zip_name, name = path[:pos+4], path[pos+5:]
        zip_file = cls.zips.get(zip_name, None)

        if zip_file is None and cls.all and _isfile(zip_name):
            zip_file = True

        if not zip_file or not name:
            cls.log.warning('zip access fail: %s: %s' % (
               zip_name, name or 'no file name specified'))
            return False

        elif zip_file is True:
            cls.log.info('zip access init: %s' % zip_name)

            # Import lazily.
            zipfile = cls.zipfile is None and setattr(cls, 'zipfile', __import__('zipfile')) or cls.zipfile

            try:
                cls.zips[zip_name] = zip_file = zipfile.ZipFile(zip_name)
            except (IOError, zipfile.BadZipFile):
                cls.zips[zip_name] = False
                cls.log.exception('zip access fail: %s' % zip_name)
                return False

        if sep != cls.zipsep:
            name = name.replace(sep, cls.zipsep)

        if name in zip_file.NameToInfo:
            # cls.log.debug('zip access test: %s: %s' % (zip_name, name))
            return zip_file, name
        else:
            cls.log.warning('zip access miss: %s: %s' % (zip_name, name))
            return False

    @classmethod
    def getfile(cls, name, mode='r', buffering=-1, **options):
        """Returns file-like object if file is in a zip file,
        or False if it isn't.

        Uses ZipFile.open() if available (Python 2.6 and newer).
        """
        zip_file = cls.hasfile(name)
        if zip_file is False:
            return False

        zip_file, name = zip_file

        if mode not in ('r', 'rb'):
            cls.log.error("zip access fail: %s: %s: requires mode 'r' or 'rb', not %r" % (
                zip_file.filename, name, mode))
            return False

        cls.log.debug('zip access open: %s: %s' % (zip_file.filename, name))

        try:
            # Use ZipFile.open() if available (Python 2.6 and newer).
            return zip_file.open(name, cls.zipmodes[mode], **options)

        except AttributeError:
            # Poor man workaround if ZipFile.open() is missing (Python 2.5 and older).

            # Initialize lazily.
            try:
                StringInput = cls.StringInput
            except AttributeError:
                from StringIO import StringIO

                class StringInput(StringIO):
                    """Read only StringIO"""
                    def __init__(self, buf='', mode='r', name=None):
                        self.name = name or self.__class__.__name__
                        if mode == 'r' and '\r' in buf:
                            buf = buf.replace('\r\n', '\n')
                        StringIO.__init__(self, buf)

                    def write(self, *args, **argd):
                        raise IOError('file is not writable: %s' % self.name)

                    truncate = writelines = write

                cls.StringInput = StringInput

            return StringInput(zip_file.read(name), mode, name)

        except:
            cls.log.exception('zip access fail: %s: %s' % (zip_name, name))
            return False


[ setattr(func, '_zipaccess', ZipAccess) for func in (exists, isfile, open, file) ]

enable = ZipAccess.enable
addzip = ZipAccess.addzip
delzip = ZipAccess.delzip
hasfile = ZipAccess.hasfile
getfile = ZipAccess.getfile


if __name__ == '__main__':
    import doctest
    doctest.testmod()
