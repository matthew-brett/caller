from io import BytesIO
import subprocess


class AppWrapper(object):
    """ Base class to wrap an application

    Instance accepts positional argument *values* and named argument *values* as
    key / value pairs.

    Class attributes are:

    * cmd : sequence - sequence of strings beginning command
    * parameter_definitions : an instance of class:`ParameterDefinitions`
      defining valid positional and named arguments
    * result_maker : callable accepting results of running command, returning
      packaged result output
    """
    cmd = None
    parameter_definitions = None
    result_maker = None

    def __init__(self, positionals=(), named=None):
        """ Create AppWrapper instance

        Parameters
        ----------
        positionals : sequence, optional
            positional argument values
        named : None or mapping
            named argument values
        """
        self._positionals = ()
        self._options = {}
        self.set_parameters(positionals, named)

    @property
    def positionals(self):
        """ Return read-only positionals attribute """
        return self._positionals

    @property
    def options(self):
        """ Return read-only options attribute """
        return self._options

    def set_parameters(self, positionals=(), named=None):
        """ Set positional parameters and options for command

        Parameters
        ----------
        positionals : sequence, optional
            sequence of positional argument values
        named : None or mapping, optional
            mapping with key, value pairs being named argument values
        """
        if named is None:
            named = {}
        pchecker = self.parameter_definitions
        self._positionals, named = pchecker.checked_values(
            positionals,
            named)
        self._options.update(named)

    def run(self):
        """ Execute implied command, return results object

        Parameters
        ----------
        None

        Returns
        -------
        res_obj : object
            results object instance, as returned from output of command after
            processing with ``self.result_maker``
        """
        cmdstr = self.parameter_definitions.make_cmdline(
            self.cmd,
            self._positionals,
            self._options,
            checked=True)
        return self.result_maker(*self._execute(cmdstr))

    def _execute(self, cmd):
        """ Raw execute of command `cmd`

        Parameters
        ----------
        cmd : str
        """
        raise NotImplementedError


class ShellResult(object):
    """ Package results of running a system command line """
    def __init__(self,
                 result_code,
                 stdout,
                 stdin):
        self.result_code = result_code
        self.stdout = stdout
        self.stdin = stdin
        self.fields = {}


class ShellWrapper(AppWrapper):
    """ Wrap system command line application """
    result_maker = ShellResult
    shell=True

    def _execute(self, cmd):
        child = subprocess.Popen(cmd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=self.shell)
        (out, err) = child.communicate()
        error_code = child.returncode
        return error_code, BytesIO(out), BytesIO(err)
