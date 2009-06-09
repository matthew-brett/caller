''' Tests for high level interface for caller '''

import os
from os.path import join as pjoin

import caller

import nose

script_path = pjoin(os.path.split(__file__)[0], 'scripts')

class App1Wrapper(caller.AppWrapper):
    cmd = 'python ' + pjoin(script_path, 'app1')
    positional_defines = (
        caller.Positional(name='param1'
                          is_required=True),
        caller.Positional(name='param2',
                          is_required=True),
        )
    option_defines =  (
        caller.Option(name='option1',
                      aliases=['-1'],
                      checker = str),
        )

        
def test_app1():
    app1_wrapper = App1Wrapper()
    res = app1_wrapper.run()
    
