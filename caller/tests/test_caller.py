''' Tests for high level interface for caller '''

import os
from os.path import join as pjoin

from caller import Positional, Option, ShellWrapper, ParameterDefinitions, \
    CallerError

import nose
from nose.tools import assert_raises, assert_equal, assert_true


class App1Wrapper(ShellWrapper):
    cmd = 'python ' + pjoin(
        os.path.split(__file__)[0],
        'scripts',
        'app1.py')
    parameter_definitions = ParameterDefinitions(
        positional_defines = (
            Positional(name='param1',
                       is_required=True),
            Positional(name='param2',
                       is_required=True),
            ),
        option_defines = (
            Option(name='option1',
                   aliases=['-1'],
                   checker = str),
            ))


def test_app1():
    app1_wrapped = App1Wrapper()
    yield assert_raises, CallerError, app1_wrapped.run
    app1_wrapped.set_parameters(('arg1','arg2'))
    yield assert_equal, app1_wrapped.positionals, ('arg1', 'arg2')
    res = app1_wrapped.run()
    yield assert_equal, res.stdout.getvalue(), 'arg1 arg2 None\n'
    app1_wrapped.set_parameters(('arg1','arg2'),{'option1':'opt1'})
    res = app1_wrapped.run()
    yield assert_equal, res.stdout.getvalue(), 'arg1 arg2 opt1\n'
