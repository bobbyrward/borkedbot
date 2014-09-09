import pkgutil 

__path__ = pkgutil.extend_path(__path__, __name__)
_m_imports = []
_n_imports = []

_reload_module = {}

for _importer, _modname, _ispkg in pkgutil.walk_packages(path=__path__, prefix=__name__+'.'):
    try:
        __import__(_modname)

        _m_imports.append(eval(_modname.split('.')[1]))
        _n_imports.append(_modname)
        _reload_module[_modname] = True

    except Exception as e:
        print
        print "Error importing %s: %s" % (_modname, e.message)
        print e
        print