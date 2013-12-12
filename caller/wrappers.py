import sys
from io import BytesIO
import subprocess


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
        return error_code, BytesIO(out), BytesIO(err)
