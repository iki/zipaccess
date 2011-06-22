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
Sources via `git <http://git-scm.com/>`_:
  ``git clone https://github.com/iki/zipaccess``
Sources via `hg-git <https://github.com/schacon/hg-git>`_:
  ``hg clone git://github.com/iki/zipaccess``


Usage
-----

Use as a class. Do not instaniate it::

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

On GAE, __builtin__ changes are not reflected, even in the current module.

To use zip access in any GAE module, you need to enable it for that module locals::

    try:
        import zipaccess
        zipaccess.enable(locals())
    except ImportError:
        pass

Alternatively, only enable zip access, if it was already registered::

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
    # It imports all the modules though, which may not be what you want.
    # If you know, how to hook on module import, let me kindly know.

Note, that os.path.isfile and os.path.exists are patched globally. Even on GAE,
they apply for all modules of given instance. If some modules do support
zip files, they usually first check if regular file exists, and if not, they
split the path and check if the zipfile exists.
With zipaccess.enabled() the regular file check will succeed, which is ok
as long as file/open functions used later are patched too.

Example:

    In tipfy.debugger.get_loader() the file/zip check is performed,
    and tipfy.template.Loader or tipfy.template.ZipLoader is used accordingly.
    With zipaccess enabled, the standard tipfy.template.Loader will be used,
    and therefore ``zipaccess.enable('tipfy.template')`` is needed to make it work.

    See https://github.com/moraes/tipfy/blob/master/tipfy/debugger/__init__.py#L26.
