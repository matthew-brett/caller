''' Tests for high level interface for caller '''

import os
from os.path import join as pjoin

from caller import Positional, Option, AppWrapper, ParameterDefinitions

import nose
from nose.tools import assert_raises


class App1Wrapper(AppWrapper):
    cmd = pjoin(os.path.split(__file__)[0], 'scripts')
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
    appwrapped = App1Wrapper()
    yield assert_raises, CallerError, app1_wrapper.run
    
