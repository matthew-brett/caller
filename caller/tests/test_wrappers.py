''' Test for wrapping interface '''

import os
from os.path import join as pjoin

from caller import Positional, Option, CallerError
from caller.wrappers import PositionalsContainer

import nose
from nose.tools import assert_raises, assert_equal, assert_true

p1 = Positional('param1', ['p1', 'prm1'], is_required=True)
p2 = Positional('param2', ['p2', 'prm2'])

def test_pos_container():
    pc = PositionalsContainer((p1, p2))
    yield assert_equal, pc.positional_defines, (p1, p2)
    yield assert_equal, pc.globbing, False
    # the defines are read only
    yield assert_raises, AttributeError, pc.__setattr__, 'positional_defines', None
    # the globbing, not
    pc.globbing = False
    # with globbing False, the generator just returns the input defines
    generated = tuple(pc.defines_generator())
    yield assert_equal, generated, (p1, p2)
    # with globbing True, it carries on for ever
    pc.globbing = True
    def_list = []
    gen = pc.defines_generator()
    for i in range(4):
        def_list.append(gen.next())
    yield assert_equal, def_list, [p1, p2, p2, p2]
    # keys are all names and aliases
    yield assert_equal, pc.keys(), p1.keys() + p2.keys()
    # matching index finds which of the sequence corresponds to the key
    yield assert_equal, pc.matching_index('param1'), 0
    yield assert_equal, pc.matching_index('prm1'), 0
    yield assert_equal, pc.matching_index('param2'), 1
    yield assert_equal, pc.matching_index('p2'), 1
    yield assert_equal, pc.matching_index('implausible'), None
    # arg number check raises error for bad number of args
    # Here min is 1 max is 2
    pc.globbing = False
    pc.check_argno(1)
    pc.check_argno(2)
    yield assert_raises, CallerError, pc.check_argno, 0
    yield assert_raises, CallerError, pc.check_argno, 3
    # but, infinite args possible if globbing is True
    pc.globbing = True
    yield assert_raises, CallerError, pc.check_argno, 0
    pc.check_argno(1000)
    
