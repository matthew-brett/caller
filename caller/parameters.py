class Parameter(object):
    def __init__(self,
                 name,
                 aliases=None,
                 checker=None,
                 is_required=False):
        self.name = name
        if not aliases:
            aliases = ()
        self.aliases = ()
        self.checker = checker
        self.is_required = is_required

    def to_string(self, value):
        return str(value)


class Positional(Parameter):
    pass


class Option(Parameter):
    def to_string(self, value):
        if self.value:
            return '--%s=%s' % (self.name, value)

    
    
