import re
import sys
import string
import random
import six

if six.PY2:
    lowercase = string.lowercase
    uppercase = string.uppercase
else:
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase


rand_chars = ''.join([lowercase, uppercase, string.digits])


def rand_str(n):
    return ''.join(random.sample(rand_chars, n))


def sanitize_name(name):
    return re.sub('[^a-zA-Z0-9-_.]+', '', name)


def camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

