import itertools
import shlex
import six
import json
from . import api
from jinja2 import Template
from pyauto.util import yamlutil
from collections import OrderedDict


valid_task_sequence_types = ['seq', 'task']
dict_types = (dict, OrderedDict)
text_types = (six.text_type, six.binary_type)


def parse_task(cmd):
    cmd = shlex.split(cmd)
    if len(cmd) == 3:
        return cmd[0], cmd[1], yamlutil.load_dict(cmd[2])
    elif len(cmd) == 2:
        return cmd[0], cmd[1], {}
    else:
        raise InvalidTaskSequence('task is invalid: {0}'.format(cmd))


class TaskSequenceArguments(object):
    def __init__(self, name, spec):
        if not isinstance(name, text_types):
            raise InvalidTaskSequence(
                'task sequence arguments name must be a string')
        if not isinstance(spec, dict_types):
            raise InvalidTaskSequence(
                'task sequence arguments must be a dict')
        self.name = name
        self.spec = spec
        self.kinds = list(spec.values())

    def is_compatible(self, kinds):
        for kind in kinds:
            if kind not in self.kinds:
                return False
        return True

    def has_variable(self, name):
        return name in self.spec

    def assert_variable(self, name):
        if not self.has_variable(name):
            raise InvalidTaskSequence(
                'task sequence arguments "{0}" does not support variable "{1}"'
                .format(self.name, name))

    def build_context(self, query_results):
        parts = [query_results.get(kind, []) for kind in self.kinds]
        for obj in itertools.product(*parts):
            obj = {n: v for n, v in zip(list(self.spec.keys()), list(obj))}
            yield obj


class TaskSequenceQuery(object):
    def __init__(self, sequence, query):
        if not isinstance(query, dict_types):
            raise InvalidTaskSequence('task sequence query must be a map')
        self.sequence = sequence
        for key in query:
            self.sequence.arguments.assert_variable(key)
        self.query = query
        self.query_args = OrderedDict([
            (kind, self.get_variable(varname))
            for varname, kind in self.sequence.arguments.spec.items()
        ])

    def get_variable(self, varname):
        value = self.query.get(varname, {'all': True})
        if isinstance(value, dict_types):
            return value
        else:
            raise InvalidTaskSequence('task sequence query must be a dict')


class TaskSequences(object):
    def __init__(self, sequences):
        if 'arguments' not in sequences or \
                not isinstance(sequences['arguments'], dict_types):
            raise InvalidTaskSequence('task sequences "arguments" are invalid')
        if 'sequences' not in sequences or \
                not isinstance(sequences['sequences'], dict_types):
            raise InvalidTaskSequence('task sequences "sequences" are invalid')
        self.arguments = OrderedDict([
            (name, TaskSequenceArguments(name, spec))
            for name, spec in sequences['arguments'].items()
        ])
        self.sequences = OrderedDict([
            (name, TaskSequence(self, seq, name))
            for name, seq in sequences['sequences'].items()
        ])
        self.validate_sequences()

    def validate_sequences(self):
        for name, sequence in self.sequences.items():
            sequence.validate()

    def get_argument(self, name):
        if name not in self.arguments:
            raise InvalidTaskSequence(
                'unknown task argument: {0}'.format(name))
        return self.arguments[name]

    def get_sequence(self, name):
        if name not in self.sequences:
            raise InvalidTaskSequence(
                'unknown task sequence: {0}'.format(name))
        return self.sequences[name]

    def resolve_context(self, repo, query, name):
        sequence = self.get_sequence(name)
        query = TaskSequenceQuery(sequence, query)
        query_results = repo.query(query.query_args, resolve=True)
        return sequence.resolve_context(query_results)

    def resolve(self, repo, query, name):
        sequence = self.get_sequence(name)
        query = TaskSequenceQuery(sequence, query)
        query_results = repo.query(query.query_args, resolve=True)
        results = []
        sequence.resolve(query_results, results)
        return results

    def run_sequence(self, repo, query, name):
        for cmd in self.resolve(repo, query, name):
            yield repo.invoke(*parse_task(cmd))


class TaskSequence(object):
    def __init__(self, sequences, sequence, name):
        if not isinstance(sequence, dict_types) or len(sequence) != 1:
            raise InvalidTaskSequence(
                'task sequence must have only one argument')
        argument_name = next(iter(sequence.keys()))
        self.name = name
        self.arguments = sequences.get_argument(argument_name)
        self.sequences = sequences
        if not isinstance(sequence[argument_name], list):
            raise InvalidTaskSequence('task sequence must be a list')
        self.sequence = [
            SubTaskSequence(self, subtask)
            for subtask in sequence[argument_name]
        ]

    def validate(self):
        for subtask in self.sequence:
            if 'seq' == subtask.type:
                sequence = self.sequences.get_sequence(subtask.template)
                if not self.arguments.is_compatible(sequence.arguments.kinds):
                    raise InvalidTaskSequence(
                        'subtask arguments are incompatible with parent task '
                        'sequence arguments')

    def resolve_context(self, query_results):
        return self.arguments.build_context(query_results)

    def resolve(self, query_results, commands):
        for subtask in self.sequence:
            if 'seq' == subtask.type:
                sequence = self.sequences.get_sequence(subtask.template)
                sequence.resolve(query_results, commands)
            else:
                for obj in self.resolve_context(query_results):
                    command = subtask.render(**obj)
                    parts = shlex.split(command)
                    commands.append(command)


class SubTaskSequence(object):
    def __init__(self, sequence, subtask):
        if not isinstance(subtask, dict_types) or \
                len(subtask) != 1:
            raise InvalidTaskSequence('subtask must be a dict and set a type')
        self.type = next(iter(subtask.keys()))
        if self.type not in valid_task_sequence_types:
            raise InvalidTaskSequence('subtask type must one of {0}'
                                      .format(valid_task_sequence_types))
        self.sequence = sequence
        self.template = subtask[self.type]
        if not isinstance(self.template, text_types):
            raise InvalidTaskSequence('subtask template must set a string')

    def render(self, **context):
        return Template(self.template).render(**context)


class InvalidTaskSequence(api.PyautoException):
    pass
