import sys
from StringIO import StringIO
import subprocess

class CallerError(RuntimeError):
    pass


class PositionalsContainer(object):
    """ Class to contain positional parameter defines

    The ``ParameterDefinitions`` class uses this class internally to do
    housekeeping on the collection of positional defines

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

    def gen_defines(self):
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

    def index(self, key):
        for i, pdef in enumerate(self._positional_defines):
            if key in pdef.keys():
                return i
    

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
    * cmd_str = obj.make_command(cmd, positionals, named)

    """
    options_first = True
    
    def __init__(self,
                 positional_defines,
                 option_defines = (),
                 positional_globbing=False):
        """ Initialize definitions

        Parameters
        ----------
        positional_defines : sequence
           sequence of objects matching Positional API, and defining
           positional parameters
        option_defines : sequence
           sequence of objects matching Option API, defining option
           parameters.
        positional_globbing : bool
           If True, positional arguments can extend to infinite number
           
        Examples
        --------
        >>> from caller import Positional, Option
        >>> poses = (Positional('param1'), Positional('param2'))
        >>> opts = (Option('option1'), Option('option2'))
        >>> pd = ParameterDefinitions(poses, opts)
        """
        self._positional_defines = positional_defines
        self._pos_container = PositionalsContainer(positional_defines,
                                                   positional_globbing)
        self._option_defines = option_defines
        self._positional_globbing = positional_globbing
        # check for duplicate names in named defines
        named_dict = {}
        for pdef in self._positional_defines:
            for key in pdef.keys():
                named_dict[key] = pdef
        for odef in self.option_defines:
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
    def option_defines(self):
        return self._option_defines
        
    def checked_values(self, positionals=(), named=None):
        ''' Check each value using checkers

        Note that the named argumets can also be positional.  They will
        appear in the positionals on return.

        Parameters
        ----------
        positionals : sequence
           values for positional parameters
        named : mapping or None
           keys, values for options (which must be named) and of any
           named positional parameters. If None (the default) then
           assume empty mapping

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
        >>> from caller import Positional, Option
        >>> poses = (Positional('param1'), Positional('param2'))
        >>> opts = (Option('option1'), Option('option2'))
        >>> pd = ParameterDefinitions(poses, opts)
        >>> pvals, ovals = pd.checked_values(('1','2'),{'option1':'Yo'})
        >>> pvals
        ('1', '2')
        >>> ovals
        {'option1': 'Yo'}
        '''
        if named is None:
            named = {}
        # first process named, pulling out any positional
        posdefs = self._pos_container
        pkeys = posdefs.keys()
        options = {}
        named_poses = []
        # check named, and remove positionals
        for key, value in named.items():
            pos_ind = posdefs.index(key)
            if not pos_ind is None:
                named_poses.append((pos_ind, value))
                continue
            if not key in self._named_dict:
                raise CallerError('Strange key "%s" in named parameters'
                                 % key)
            ndef = self._named_dict[key]
            # make name canonical for option
            options[ndef.name] = ndef.checker(value)
        # put any named positionals into positionals list
        named_poses.sort(lambda x,y: cmp(x[0],y[0]))
        positionals = list(positionals)
        for i, val in named_poses:
            if i < len(positionals):
                positionals[i] = val
                continue
            if i == len(positionals):
                positionals.append(val)
            else:
                raise CallerError('Named positional too far from end '
                                  'of positional list')
        # check positionals
        pdef_iter = posdefs.gen_defines()
        poses = []
        for value in positionals:
            try:
                pdef = pdef_iter.next()
            except StopIteration:
                raise CallerError('Too many positional parameters')
            poses.append(pdef.checker(value))
        return tuple(poses), options

    def make_cmdline(self, cmd, positionals=(), named=None, checked=False):
        ''' Make command line string from input `cmd` and parameters

        Parameters
        ----------
        cmd : string
           command
        positionals : sequence
           sequence of positional argument values
        named : mapping
           key, value pairs of named arguememts, either options, or
           named positional
        checked: bool
           True if `positionals` and `named` have already been checked
           and sorted into positional and option args.

        Returns
        -------
        cmdline : string
           command line string
        '''
        if named is None:
            named = {}
        if not checked:
            positionals, named = self.checked_values(positionals, named)
        # check that required arguments are present
        for i, pdef in enumerate(self._positional_defines):
            if pdef.is_required and i >= len(positionals):
                raise CallerError('Not enough positional arguments')
        for odef in self._option_defines:
            if odef.is_required and odef.name not in named:
                raise CallerError('Expecting required option "%s"'
                                  % odef.name)
        pdef_iter = self._pos_container.gen_defines()
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
        return self.result_maker(*self._execute(cmdstr))
    
    def _execute(self, cmdstr):
        raise NotImplementedError


class ShellResult(object):
    def __init__(self, 
                 result_code,
                 stdout,
                 stdin):
        self.result_code = result_code
        self.stdout = stdout
        self.stdin = stdin
        self.fields = {}
        
        
class ShellWrapper(AppWrapper):
    result_maker = ShellResult
    
    def _execute(self, cmdstr):
        child = subprocess.Popen(cmdstr,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=(sys.platform!="win32"))
        (out, err) = child.communicate()
        error_code = child.returncode
        return error_code, StringIO(out), StringIO(err)
    
