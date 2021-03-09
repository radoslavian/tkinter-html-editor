import os

def getattr_wrapper():
    '''Redirects calls for non-existent attributes to
    another object-referenced by self.wrapped.'''
    def wrapper(self, attr):
        return lambda *pargs, **kwargs: getattr(
            self.wrapped, attr)(*pargs, **kwargs)
    return wrapper

def base_file_name(path : 'str, bytes, os.PathLike'):
    try:
        file_name = os.path.basename(path)
    except TypeError:
        file_name = None
    return file_name
