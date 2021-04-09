import os


def list_files(directory : str, f_ext : str) -> [] or None:
    '''Lists files with a given extension in a directory.

    f_ext-file extension
    eg.: list_files('icons/', '.png')'''

    _, _, filenames = next(os.walk(directory))

    return list(filter(
        lambda f: True if os.path.splitext(f)[-1] == f_ext else False,
        filenames))


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
