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
