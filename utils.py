import os


def list_files(directory : str, f_ext : str) -> [] or None:
    '''Lists files with a given extension in a directory.

    f_ext-file extension
    eg.: list_files('icons/', '.png')'''

    _, _, filenames = next(os.walk(directory))

    return list(filter(
        lambda f: True if os.path.splitext(f)[-1] == f_ext else False,
        filenames))


def getattr_redirect(self, attr_name, *pargs, **kwargs):
    '''Redirects calls for attributes not present in an instance to
    an embedded object-referenced by self.wrapped.

    Function has to be assigned to the __getattr__ method of an 
    instance. Only method calls are redirected.'''

    def wrapper(*pargs, **kwargs):
        attribute = getattr(self.wrapped, attr_name)

        if callable(attribute):
            attribute(*pargs, **kwargs)
        else:
            raise AttributeError(
                "{} is not a callable.".format(attr)) from ValueError

    return wrapper


def base_file_name(path : 'str, bytes, os.PathLike'):
    try:
        file_name = os.path.basename(path)
    except TypeError:
        file_name = None
    return file_name
