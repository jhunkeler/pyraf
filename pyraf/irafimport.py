"""module irafimport.py -- modify import mechanism

Modify module import mechanism so that
(1) 'from iraf import pkg' automatically loads the IRAF package 'pkg'
(2) 'import iraf' returns a wrapped module instance that allows minimum-match
        access to task names (e.g. iraf.imhead, not just iraf.imheader)

Assumes that all IRAF tasks and packages are accessible as iraf
module attributes.  Only affects imports of iraf module.

$Id$

R. White, 1999 August 17
"""

from __future__ import division  # confidence high

import imp
import inspect
import sys

from stsci.tools import minmatch

import pyraf


def _find_module_in_package(fullname, path=None):
    parts = fullname.split('.')
    modname = fullmodname = parts.pop(0)
    while parts:
        if fullmodname in sys.modules:
            mod = sys.modules[fullmodname]
        else:
            fileobj, path, description = imp.find_module(modname, path)
            mod = imp.load_module(modname, fileobj, path, description)
        # If there are still parts remaining, mod should be a package:
        path = mod.__path__
        modname = parts.pop(0)
        fullmodname += '.' + modname
    return imp.find_module(modname, path)


class IrafImporter(object):
    def find_module(self, fullname, path=None):
        modname = None
        if fullname == 'pyraf.iraf':
            modname = 'pyraf.iraf'
        elif fullname == 'iraf':
            modname = 'pyraf.iraf'
        elif fullname == 'pytools':
            modname = 'stsci.tools'
        elif fullname.startswith('pytools.'):
            _, rest = fullname.split('.', 1)
            modname = 'stsci.tools.' + rest
        elif fullname.startswith('pyraf.'):
            # !!! TEMPORARY KLUDGE !!! keep this code until cache files are
            # updated
            mod = fullname.split('.')[1]
            if mod in ['minmatch', 'irafutils', 'dialog', 'listdlg',
                       'filedlg', 'alert', 'irafglobals']:
                modname = 'stsci.tools.' + mod

        if modname is not None:
            return IrafLoader(modname, *_find_module_in_package(modname, path))


class IrafLoader(object):
    def __init__(self, fullname, fileobj, pathname, description):
        self.fullname = fullname
        self.fileobj = fileobj
        self.pathname = pathname
        self.description = description

    def load_module(self, modname):
        # The passed in module name is ignored--we use the module name we were
        # told to use...
        if self.fullname in sys.modules:
            return sys.modules[self.fullname]

        if self.fullname != 'pyraf.iraf':
            mod = imp.load_module(self.fullname, self.fileobj, self.pathname,
                                  self.description)
            mod.__loader__ = self
        else:
            mod = _IrafModuleProxy(self)

        if self.fullname == 'pyraf.iraf':
            sys.modules['pyraf.iraf'] = mod
        elif self.fullname == 'stsci.tools':
            sys.modules['pytools'] = mod
        elif self.fullname.startswith('stsci.tools.'):
            _, _, rest = self.fullname.split('.', 2)
            sys.modules['pytools.' + rest] = mod

        return mod


class _IrafModuleProxy(object):
    """Proxy for iraf module that makes tasks appear as attributes"""

    __instance = None
    module = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is not None:
            return cls.__instance

        cls.__instance = super(_IrafModuleProxy, cls).__new__(cls, *args,
                                                              **kwargs)
        return cls.__instance

    def __init__(self, loader):
        self.loader = loader
        self.__name__ = self.loader.fullname
        self.mmdict = None

    def __repr__(self):
        if self.module is not None:
            return repr(self.module)
        return super(_IrafModuleProxy, self).__repr__()

    def __getattr__(self, attr):
        if self.module is None:
            module = imp.load_module(self.loader.fullname, self.loader.fileobj,
                                     self.loader.pathname,
                                     self.loader.description)
            module.__loader__ = self.loader
            self.mmdict = minmatch.MinMatchDict(vars(module))
            self.module = module
            # Fix up sys.modules again so importing tasks from pyraf.iraf still
            # works
            sys.modules[module.__name__] = self

        # first try getting this attribute directly from the usual module
        try:
            val = getattr(self.module, attr)
        except AttributeError:
            # if that fails, try getting a task with this name
            try:
                val = self.module.getTask(attr)
            except minmatch.AmbiguousKeyError, e:
                raise AttributeError(str(e))
            except KeyError, e:
                # last try is minimum match dictionary of rest of module
                # contents
                try:
                    val = self.mmdict[attr]
                except KeyError:
                    raise AttributeError("Undefined IRAF task `%s'" % (attr,))

        from .iraftask import IrafPkg
        if not self.__cl and isinstance(val, IrafPkg) and not val.isLoaded():
            val.run(_doprint=0, _hush=1)

        return val

    def __setattr__(self, attr, value):
        # add an attribute to the module itself
        if self.module is not None:
            setattr(self.module, attr, value)
            self.mmdict.add(attr, value)
        else:
            super(_IrafModuleProxy, self).__setattr__(attr, value)

    @property
    def __cl(self):
        return (hasattr(pyraf, '_pyrafMain') and pyraf._pyrafMain and
                pyraf.doCmdline)

    def getAllMatches(self, taskname):
        """Get list of names of all tasks that may match taskname

        Useful for command completion.
        """
        if self.module is None: self._moduleInit()
        if taskname == "":
            matches = self.mmdict.keys()
        else:
            matches = self.mmdict.getallkeys(taskname, [])
        matches.extend(self.module.getAllTasks(taskname))
        return matches


sys.meta_path.insert(0, IrafImporter())