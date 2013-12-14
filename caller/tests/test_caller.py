''' Tests for high level interface for caller '''

import sys
from os.path import join as pjoin, dirname

from ..parameters import Positional, Option
from ..defines import ParameterDefinitions, CallerError
from ..wrappers import ShellWrapper

from nose.tools import assert_raises, assert_equal, assert_true


class App1Wrapper(ShellWrapper):
    cmd = (sys.executable,
           pjoin(dirname(__file__), 'scripts', 'app1.py'))
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
    assert_raises(CallerError, app1_wrapped.run)
    app1_wrapped.set_parameters(('arg1','arg2'))
    assert_equal(app1_wrapped.positionals, ('arg1', 'arg2'))
    res = app1_wrapped.run()
    assert_equal(res.stdout.getvalue(), b'arg1 arg2 None\n')
    app1_wrapped.set_parameters(('arg1', 'arg2'), {'option1': 'opt1'})
    res = app1_wrapped.run()
    assert_equal(res.stdout.getvalue(), b'arg1 arg2 opt1\n')
    app1_wrapped.set_parameters(('arg1', 'arg2'), {'-1': 'opt1'})
    res = app1_wrapped.run()
    assert_equal(res.stdout.getvalue(), b'arg1 arg2 opt1\n')
    # To few positional arguments
    app1_wrapped.set_parameters(('arg1',))
    assert_raises(CallerError, app1_wrapped.run)
    # Wrong name for named argument
    assert_raises(CallerError,
                  app1_wrapped.set_parameters,
                  ('arg1', 'arg2'),
                  {'-2': 'opt1'})
