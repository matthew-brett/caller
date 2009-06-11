class CallerError(RuntimeError):
    pass


class PositionalsContainer(object):
    """ Class to contain positional parameter defines

    """
    def __init__(self, positional_defines, globbing=False):
        self._positional_defines = positional_defines
        self.globbing = globbing
        # check for duplicate names
        keys = self.keys()
        if len(set(keys)) < len(keys):
            raise ValueError('Duplicate names or aliases in parameters')
        
    @property
    def positional_defines(self):
        # read only to guarantee names check
        return self._positional_defines

    def defines_generator(self):
        ''' generate all positional defines
        '''
        for pdef in self._positional_defines:
            yield pdef
        if self.globbing:
            while True:
                yield pdef

    def keys(self):
        """ All names, aliases for positionals in container
        """
        keys = []
        for pdef in self._positional_defines:
            keys += pdef.keys()
        return keys

    def matching_index(self, key):
        for i, pdef in enumerate(self._positional_defines):
            if key in pdef.keys():
                return i
    
    def check_argno(self, argno):
        ''' Raise error unless valid number of positional arguments passed
        '''
        pdefs = self._positional_defines
        if not self.globbing:
            if argno > len(pdefs):
                raise CallerError('Too many positional arguments')
        min_positionals = sum([pdef.is_required for pdef in pdefs])
        if argno < min_positionals:
            raise CallerError('Need at least %d positional arguments'
                              % min_positionals)
        

class ParameterDefinitions(object):
    """ Class encapsulating parameter definitions

    Parameter definitions define positional arguments and options that
    can be passed to a system command.

    Parameter definitions work on values passed to it.  Values can be as
    part of an arbitrary length ordered sequence ('positionals') or a
    mapping-like ('named').  Typically the positionals are positional
    arguments and the named are options, but the named can include named
    positional arguments.

    The API consists of:

    * a, b = obj.checked_values(positionals, named)
    * cmd_str = obj.as_command(cmd, positionals, named)

    
    """
    options_first = True
    def __init__(self,
                 positional_defines=(),
                 named_defines = None):
        self._positional_defines = positional_defines
        self._pos_container = PositionalsContainer(positional_defines)
        self._named_defines = named_defines
        # check for duplicate names in named defines
        named_dict = {}
        for pdef in self._positional_defines:
            for key in pdef.keys():
                named_dict[key] = pdef
        for odef in self.named_defines:
            for key in odef.keys():
                if key in named_dict:
                    raise ValueError('Duplicate name "%s" for parameter %s'
                                     % (key, odef.name))
                named_dict[key] = odef
        self._named_dict = named_dict

    @property
    def positional_defines(self):
        return self._positional_defines

    @property
    def named_defines(self):
        return self._named_defines
        
    def checked_values(self, positionals, named):
        ''' Check each value using checkers

        Note that the named argumets can also be positional.  They will
        appear in the positionals on return.

        Parameters
        ----------
        positionals : sequence
           values for positional parameters
        named : mapping
           keys, values for options (which must be named) and of any
           named positional parameters

        Returns
        -------
        positionals : sequence
           values for positional parameters, now including any named
           positional parameters from `named` above.
        options : mapping
           keys, values for options, with any positional parameters
           removed

        Examples
        --------
        
           
        '''
        # first process named, pulling out any positional
        posdefs = self._pos_container
        pkeys = posdefs.keys()
        options = {}
        named_poses = []
        for key, value in named.items():
            pos_ind = posdefs.matching_index(key)
            if pos_ind:
                named_poses.append((pos_ind, value))
            if not key in self._named_dict:
                raise CallerError('Strange key "%s" in named parameters'
                                 % key)
            options = self._named_dict[key].checker(value)
        named_poses.sort(lambda x,y: cmp(x[0],y[0]))
        poses = list(positionals)
        for i, val in named_poses:
            if i < len(poses):
                poses[i] = val
                continue
            if i == len(poses):
                poses.append(val)
            else:
                raise CallerError('Named positional too far from end '
                                  ' of positional list')
        pdef_iter = posdefs.defines_generator()
        for value in poses:
            pdef = pdef_iter.next()
            poses.append(pdef.checker(value))
        return tuple(poses), options

    def make_cmdline(self, cmd, positionals, named, checked=False):
        if not checked:
            positionals, named = self.checked_values(positionals, named)
        posdefs = self._pos_container
        posdefs.check_argno(len(positionals))
        pdef_iter = iter(posdefs)
        pos_strs = []
        for value in positionals:
            pdef = pdef_iter.next()
            pos_strs.append(pdef.to_string(value))
        named_strs =  []
        for key, value in named.items():
            ndef = self._named_dict[key]
            named_strs.append(ndef.to_string(value))
        return self._compile(cmd, pos_strs, named_strs)
    
    def _compile(self, cmd, pos_strs, named_strs):
        if self.options_first:
            return ' '.join([cmd]+named_strs+pos_strs)
        else:
            return ' '.join([cmd]+pos_strs+named_strs)


class AppWrapper(object):
    cmd = None
    parameter_definitions = None
    result_maker = None
    
    def __init__(self, positionals=(), named=None):
        self._positionals = ()
        self._options = {}
        self.set_parameters(positionals, named)

    @property
    def positionals(self):
        return self._positionals

    @property
    def options(self):
        return self._options

    def set_parameters(self, positionals=(), named=None):
        if named is None:
            named = {}
        pchecker = self.parameter_definitions
        self._positionals, named = pchecker.checked_values(
            positionals,
            named)
        self._options.update(named)
                  
    def run(self):
        cmdstr = self.parameter_definitions.make_cmdline(
            self.cmd,
            self._positionals,
            self._options,
            checked=True)
        return self.result_maker(self._execute(cmdstr))
    
    def _execute(self, cmdstr):
        raise NotImplementedError




