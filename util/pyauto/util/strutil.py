import re
import os
import sys
import six
import shutil
import string
import random

if six.PY2:
    lowercase = string.lowercase
    uppercase = string.uppercase
else:
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase

rand_chars = ''.join([lowercase, uppercase, string.digits])
root_prefix = os.path.splitdrive(sys.executable)[0] or '/'


def abspath_neighbor(filename, *path):
    if len(path) == 1 and path[0].startswith(root_prefix):
        return path[0]
    return os.path.join(os.path.dirname(filename), *path)


def rand_str(n):
    return ''.join(random.sample(rand_chars, n))


def sanitize_name(name):
    return re.sub('[^a-zA-Z0-9-_.]+', '', name)


def camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def get_dir_size(dirname):
    size = 0
    count = 0
    for dirpath, dirnames, filenames in os.walk(dirname):
        for fn in filenames:
            fn = os.path.join(dirpath, fn)
            size += os.path.getsize(fn)
            count += 1
    count += 1
    size += os.path.getsize(dirname)
    return size, count


def get_file_size(filename):
    if not isinstance(filename, six.string_types):
        raise Exception('filename "{0}" is not a string'.format(filename))
    if os.path.isdir(filename):
        size, count = get_dir_size(filename)
    elif os.path.isfile(filename):
        count = 1
        size = os.path.getsize(filename)
    else:
        return None
    return {
        'count': count,
        'size': size,
        'name': filename
    }


def copytree(src, dst, symlinks=False, ignore=None):
    """This is a replacement for shutil.copytree that does not crash when the
    destination directory already exists. Other than that, this function is
    identical to shutil.copytree.
    """
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    if not os.path.isdir(dst):  # This one line does the trick
        os.makedirs(dst)
    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks, ignore)
            else:
                # Will raise a SpecialFileError for unsupported file types
                shutil.copy2(srcname, dstname)
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except shutil.Error as err:
            errors.extend(err.args[0])
        except EnvironmentError as why:
            errors.append((srcname, dstname, str(why)))
    try:
        shutil.copystat(src, dst)
    except OSError as why:
        if shutil.WindowsError is not None and \
                isinstance(why, shutil.WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            errors.extend((src, dst, str(why)))
    if errors:
        raise shutil.Error(errors)
