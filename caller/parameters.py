class Parameter(object):
    """ Class implementing positional and named parameters
    >>> param = Parameter('p',['param'],float,True)
    >>> param.to_string(1)
    '1.0'
    >>> param.default_formatter = 'param=%(value)s'
    >>> param.to_string(1)
    'param=1.0'
    """
    default_formatter = '%(value)s'
    
    def __init__(self,
                 name,
                 aliases=None,
                 checker=None,
                 is_required=False,
                 stringer=None):
        self.name = name
        if not aliases:
            aliases = ()
        self.aliases = aliases
        if checker is None:
            checker = lambda x : x
        self.checker = checker
        self.is_required = is_required
        if stringer is None:
            stringer = self.default_stringer
        elif isinstance(stringer, basestring):
            # assume stringer is a format string
            fmtstr = stringer
            def stringer(value): return fmtstr % value
        self.stringer = stringer

    def default_stringer(self, value):
        mapper = self.__dict__.copy()
        mapper.update({'value':value})
        return self.default_formatter % mapper

    def to_string(self, value):
        return self.stringer(self.checker(value))

    def keys(self):
        ''' Return name and any aliases for this parameter

        >>> param = Parameter('param')
        >>> param.keys()
        ['param']
        >>> param = Parameter('param', ['p', 'p1'])
        >>> param.keys()
        ['param', 'p', 'p1']
        '''
        return [self.name] + list(self.aliases)
    

class Positional(Parameter):
    pass


class Option(Parameter):
    """ Class to instantiate options

    Options differ from parameters in that they have a different default
    formatter, and they can be 'flags'.  Flags are Options with
    attribute is_flag set to True.  These return the empty string from
    ``to_string(value)`` when ``not value`` is True.
    
    >>> opt = Option('o',['opt'],float,True)
    >>> opt.to_string(1)
    '--o=1.0'
    >>> opt.default_formatter='--opt %(value)s'
    >>> opt.to_string(1)
    '--opt 1.0'
    >>> opt = Option('p',['opt'],float,True,stringer='--opt %s')
    >>> opt.to_string(1)
    '--opt 1.0'
    >>> opt = Option('opt', is_flag=False) # the default
    >>> opt.to_string(1)
    '--opt=1'
    >>> opt.to_string(0)
    '--opt=0'
    >>> opt = Option('opt', is_flag=True)
    >>> opt.to_string(1)
    '--opt=1'
    >>> opt.to_string(0)
    ''
    """
    default_formatter = '--%(name)s=%(value)s'

    def __init__(self,
                 name,
                 aliases=None,
                 checker=None,
                 is_required=False,
                 stringer=None,
                 is_flag=False):
        super(Option, self).__init__(name, aliases,checker,is_required,stringer)
        self.is_flag = is_flag
    
    def to_string(self, value):
        if value or not self.is_flag:
            return super(Option, self).to_string(value)
        return ''

    
    
