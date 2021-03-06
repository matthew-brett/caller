""" Classes for positional and named parameters
"""

import sys

string_types = (str,) if sys.version_info[0] > 2 else (basestring,)

class CallerError(RuntimeError):
    pass


class PositionalContainer(object):
    """ Class to contain positional parameter defines

    The ``ParameterDefinitions`` class uses this class internally to do
    housekeeping on the collection of positional defines.

    The class houses a sequence of positional parameter objects.  The only
    interface the objects need to obey is that they have method ``keys()``, and
    that there should be no overlap between the results of ``keys()`` across the
    elements.

    Examples
    --------
    >>> from caller import Positional
    >>> p1 = Positional('param1',['p1'])
    >>> p2 = Positional('param2',['p2'])
    >>> pc = PositionalContainer((p1, p2))
    >>> pc.keys()
    ['param1', 'p1', 'param2', 'p2']
    >>> pc.index('p2')
    1
    """
    def __init__(self, positional_defines, last_repeat=False):
        ''' Setup positional container

        Parameters
        ----------
        positional_defines : parameter define objects
           Parameter instance objects.  They must have method ``keys()``
        last_repeat : {False, True}, optional
           If True, the last parameter in the list is repeated as required to
           soak up unspecified numbers of parameters
        '''
        self._positional_defines = positional_defines
        self.last_repeat = last_repeat
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

        If ``self.last_repeat`` is True, return the last positional define forever
        to soak up extra positional arguments
        '''
        for pdef in self._positional_defines:
            yield pdef
        if self.last_repeat:
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
        ''' Returns index of positional parameter with given `key` id

        Parameters
        ----------
        key : object
           dictionary key lookup for positional value

        Returns
        -------
        i : int
           Index position of positional in container

        Notes
        -----
        Raises ValueError if key not found

        Examples
        --------
        >>>
        '''
        for i, pdef in enumerate(self._positional_defines):
            if key in pdef.keys():
                return i
        raise ValueError('"%s" not in container' % key)


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
    def __init__(self,
                 positional_defines,
                 option_defines = (),
                 pos_last_repeat=False):
        """ Initialize definitions

        Parameters
        ----------
        positional_defines : sequence
           sequence of objects matching Positional API, and defining
           positional parameters
        option_defines : sequence, optional
           sequence of objects matching Option API, defining option
           parameters.
        pos_last_repeat : {False, True}, optional
           If True, assume extra positional arguments are of same type as last
           listed.

        Examples
        --------
        >>> from caller import Positional, Option
        >>> poses = (Positional('param1'), Positional('param2'))
        >>> opts = (Option('option1'), Option('option2'))
        >>> pd = ParameterDefinitions(poses, opts)
        """
        self._positional_defines = positional_defines
        self._pos_container = PositionalContainer(positional_defines,
                                                  pos_last_repeat)
        self._option_defines = option_defines
        self._last_pos_repeat = pos_last_repeat
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
        positionals : sequence, optional
           values for positional parameters
        named : None or mapping, optional
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
        options = {}
        named_poses = []
        # check named, and remove positionals
        for key, value in named.items():
            try:
                pos_ind = posdefs.index(key)
            except ValueError:
                pass
            else:
                named_poses.append((pos_ind, value))
                continue
            if not key in self._named_dict:
                raise CallerError('Strange key "%s" in named parameters'
                                 % key)
            ndef = self._named_dict[key]
            # make name canonical for option
            options[ndef.name] = ndef.checker(value)
        # put any named positionals into positionals list
        named_poses.sort(key = lambda x: x[0])
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
                pdef = next(pdef_iter)
            except StopIteration:
                raise CallerError('Too many positional parameters')
            poses.append(pdef.checker(value))
        return tuple(poses), options

    def make_cmdline(self, cmd, positionals=(), named=None, checked=False):
        ''' Make command line sequence from input `cmd` and parameters

        Parameters
        ----------
        cmd : sequence
           command sequence
        positionals : sequence, optional
           sequence of positional argument values
        named : None or mapping, optional
           key, value pairs of named arguememts, either options, or
           named positional. If None, empty mapping.
        checked: {False, True}, optional
           True if `positionals` and `named` have already been checked
           and sorted into positional and option args.

        Returns
        -------
        cmdline : tuple
           command line tuple
        '''
        if isinstance(cmd, string_types):
            cmd = [cmd]
        else:
            cmd = list(cmd)
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
            pdef = next(pdef_iter)
            pos_strs.append(pdef.to_string(value))
        named_strs =  []
        for key, value in named.items():
            ndef = self._named_dict[key]
            named_strs.append(ndef.to_string(value))
        return self._compile(cmd, pos_strs, named_strs)

    def _compile(self, cmd, pos_strs, named_strs):
        return tuple(cmd + named_strs + pos_strs)
