class ParameterDefinitions(object):
    def __init__(self,
                 positional_defines=(),
                 option_defines = None):
        self.positional_defines = positional_defines
        self.option_defines = option_defines

    def set_parameters(self, parameters, positionals, options):
        raise NotImplementedError

    def make_cmdline(self, cmd, parameters):
        raise NotImplementedError


class AppWrapper(object):
    cmd = None
    parameter_definitions = None
    result_maker = None
    
    def __init__(self, positionals=(), options=None):
        self.set_parameters(positionals, options)

    def set_parameters(self, positionals=(), options=None):
        self.parameter_definitions.set_parameters(
            self._parameters,
            positionals,
            options)
                  
    def run(self):
        cmdstr = self.parameter_definitions.make_cmdline(
            self.cmd,
            self._parameters)
        return self.result_maker(self._execute(cmdstr))
    
    def _execute(self, cmdstr):
        raise NotImplementedError




