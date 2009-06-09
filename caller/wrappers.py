

class AppWrapper(object):
    positional_defines = ()
    option_defines = ()
    def __init__(self, positionals=(), options=None):
        self.positionals = positionals
        self.options = options

    def set_parameters(self, positionals=(), options=None):
        for i, param in enumerate(positionals):
            self.positionals[i] = param
        if options:
            self._set_options(options)

    def _set_positionals(self, positionals):
        for param in positionals:
            

    def run(self):
        self.check_parameters()
        cmdline = 
        return self.execute()

    def execute(self):
        raise NotImplementedError

    
