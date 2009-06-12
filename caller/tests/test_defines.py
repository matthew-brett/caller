''' Test for wrapping interface '''

from caller import Positional, Option, Flag, CallerError
from caller.defines import PositionalContainer, ParameterDefinitions

from nose.tools import assert_raises, assert_equal, assert_true

p1 = Positional('param1', ['p1', 'prm1'], is_required=True)
p2 = Positional('param2', ['p2', 'prm2'])
o1 = Option('option1', ['o1', '-1'])
o2 = Option('option2', ['o2', '-2'])
f1 = Flag('option3', ['o3','-3'])


def test_pos_container():
    pc = PositionalContainer((p1, p2))
    yield assert_equal, pc.positional_defines, (p1, p2)
    yield assert_equal, pc.globbing, False
    # the defines are read only
    yield assert_raises, AttributeError, pc.__setattr__, 'positional_defines', None
    # the globbing, not
    pc.globbing = False
    # with globbing False, the generator just returns the input defines
    generated = tuple(pc.gen_defines())
    yield assert_equal, generated, (p1, p2)
    # with globbing True, it carries on for ever
    pc.globbing = True
    def_list = []
    gen = pc.gen_defines()
    for i in range(4):
        def_list.append(gen.next())
    yield assert_equal, def_list, [p1, p2, p2, p2]
    # keys are all names and aliases
    yield assert_equal, pc.keys(), p1.keys() + p2.keys()
    # matching index finds which of the sequence corresponds to the key
    yield assert_equal, pc.index('param1'), 0
    yield assert_equal, pc.index('prm1'), 0
    yield assert_equal, pc.index('param2'), 1
    yield assert_equal, pc.index('p2'), 1
    yield assert_raises, ValueError, pc.index, 'implausible'
    

def test_param_defs_init():
    # options can be nothing
    pd = ParameterDefinitions((p1, p2))
    yield assert_equal, pd.positional_defines, (p1, p2)
    # or something
    pd = ParameterDefinitions((p1, p2), (o1, o2))
    yield assert_equal, pd.positional_defines, (p1, p2)
    yield assert_equal, pd.option_defines, (o1, o2)
    # pos and option defines are read-only
    yield assert_raises, AttributeError, pd.__setattr__, 'positional_defines', (p1,)
    yield assert_raises, AttributeError, pd.__setattr__, 'option_defines', (o1,)
    # duplicate names are detected
    yield assert_raises, ValueError, ParameterDefinitions, (p1,
                                                            Positional('param1'))
    yield assert_raises, ValueError, ParameterDefinitions, (p1,
                                                            Positional('param2',
                                                                       ['p1']))
    yield assert_raises, ValueError, ParameterDefinitions, (p1,),(
        Option('param1'),)
    yield assert_raises, ValueError, ParameterDefinitions, (p1,),(
        Option('option1', ['p1']),)


def test_param_defs_chkvals():
    pd = ParameterDefinitions((p1, p2), (o1, o2))
    pvals, ovals = pd.checked_values(('1','2'))
    yield assert_equal, pvals, ('1', '2')
    yield assert_equal, ovals, {}
    pvals, ovals = pd.checked_values(('1','2'),{'option1':'Yo'})
    yield assert_equal, pvals, ('1', '2')
    yield assert_equal, ovals, {'option1':'Yo'}
    # aliases in options recognized, and names made canonical
    pvals, ovals = pd.checked_values((),{'o1':'Yo'})
    yield assert_equal, pvals, ()
    yield assert_equal, ovals, {'option1':'Yo'}
    # we check the keys in the mapping for unexpectedness
    yield assert_raises, CallerError, pd.checked_values, (),{'crazy':'Yo'}
    # named parameters shift into positionals after checking
    pvals, ovals = pd.checked_values(('1',),{'param2':'Yo'})
    yield assert_equal, pvals, ('1', 'Yo')
    yield assert_equal, ovals, {}
    # the named parameter overwrites corresponding positional parameter
    pvals, ovals = pd.checked_values(('1',),{'param1':'Yo'})
    yield assert_equal, pvals, ('Yo',)
    yield assert_equal, ovals, {}
    # if the named positional parameter is more than one off the end of
    # the unnamed positional parameters, there's an error
    yield assert_raises, CallerError, pd.checked_values, (), {'param2':'Yo'}
    yield assert_equal, pvals, ('Yo',)
    yield assert_equal, ovals, {}
    # but we'll append happily to the end of the list
    pvals, ovals = pd.checked_values((),{'param1':'Yo'})
    yield assert_equal, pvals, ('Yo',)
    yield assert_equal, ovals, {}
    # too many positionals will cause trouble
    yield assert_raises, CallerError, pd.checked_values, ('1','2','3')
    # but not if we turn on globbing
    pd = ParameterDefinitions((p1, p2), (o1, o2), positional_globbing=True)
    pvals, ovals = pd.checked_values(('1','2','3'))
    yield assert_equal, pvals, ('1', '2', '3')
    yield assert_equal, ovals, {}


def test_param_defs_cmdline():
    pd = ParameterDefinitions((p1, p2))
    # there's a required parameter, and here we don't pass it
    yield assert_raises, CallerError, pd.make_cmdline, 'cmd'
    # now we do
    yield assert_equal, pd.make_cmdline('cmd', ('a1',)), 'cmd a1'
    yield assert_equal, pd.make_cmdline('cmd', ('a1','a2')), 'cmd a1 a2'
    # with some options
    pd = ParameterDefinitions((p1, p2),(o1, o2, f1))
    yield assert_equal, pd.make_cmdline('cmd', ('a1',)), 'cmd a1'
    yield assert_equal, pd.make_cmdline('cmd', ('a1','a2')), 'cmd a1 a2'
    yield (assert_equal,
           pd.make_cmdline('cmd', ('arg1',), {'o1':'3'}),
           'cmd --option1=3 arg1')
    yield (assert_equal,
           pd.make_cmdline('cmd', ('arg1',), {'o2': True}),
           'cmd --option2=True arg1')
    yield (assert_equal,
           pd.make_cmdline('cmd', ('arg1',), {'o3': True}),
           'cmd --option3 arg1')
    