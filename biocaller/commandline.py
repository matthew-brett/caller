"""General mechanisms to access applications in biopython.

http://www.biopython.org/DIST/LICENSE

Original code from biopython / Bio / Application / __init__.py

See: http://github.com/biopython

These changes (by Matthew Brett) under the biopython license also
"""
import sys
import subprocess
from StringIO import StringIO


class ApplicationResult(object):
    """Make results of a program available through a standard interface.
    
    This tries to pick up output information available from the program
    and make it available programmatically.

    Specifically, the init parses the input commandline object looking
    for parameters labeled as 'output' and 'file', and puts them into a
    dictionary for retrieval by the class methods below.

    The class implements methods:

    * get_result(name)
    * available_results()
    

    """
    def __init__(self, application_cl, return_code):
        """Intialize with the commandline from the program.

        Parameters
        ----------
        application_cl : ``AbstractCommandLine``-like
           object should have ``parameters`` attribute, from which
           results are compiled.  Parameters is iterable with items
           having attributes ``param_types``, ``is_set``, ``names`` and
           ``value``
        return_code : int
           usually the program return code from the system
        """
        self._cl = application_cl

        # provide the return code of the application
        self.return_code = return_code

        # get the application dependent results we can provide
        # right now the only results we handle are output files
        self._results = {}

        try:
            parameters = application_cl.parameters
        except AttributeError:
            return
        for parameter in parameters:
            if "file" in parameter.param_types and \
               "output" in parameter.param_types:
                if parameter.is_set:
                    self._results[parameter.names[-1]] = parameter.value

    def get_result(self, output_name):
        """Retrieve result information for the given output.
        """
        return self._results[output_name]

    def available_results(self):
        """Retrieve a list of all available results.
        """
        result_names = self._results.keys()
        result_names.sort()
        return result_names


class AbstractCommandline(object):
    """Generic interface for running applications from biopython.

    This class shouldn't be called directly; it should be subclassed to
    provide an implementation for a specific application.

    In particular, you will want to build an attribute
    ``parameters``, usually made up of ``_Argument`` and ``_Option``
    class instances.
    """
    
    result_maker = ApplicationResult
    
    def __init__(self):
        self.program_name = ""
        self.parameters = []
    
    def __str__(self):
        """Make the commandline with the currently set options.
        """
        commandline = "%s " % self.program_name
        for parameter in self.parameters:
            if parameter.is_required and not(parameter.is_set):
                raise ValueError("Parameter %s is not set." % parameter.names)
            if parameter.is_set:
                commandline += str(parameter)
        return commandline

    def set_parameter(self, name, value = None):
        """Set a commandline option for a program.
        """
        set_option = 0
        for parameter in self.parameters:
            if name in parameter.names:
                if value is not None:
                    self._check_value(value, name, parameter.checker_function)
                    parameter.value = value
                parameter.is_set = 1
                set_option = 1
        if set_option == 0:
            raise ValueError("Option name %s was not found." % name)

    def _check_value(self, value, name, check_function):
        """Check whether the given value is valid.

        This uses the passed function 'check_function', which can either
        return a [0, 1] (bad, good) value or raise an error. Either way
        this function will raise an error if the value is not valid, or
        finish silently otherwise.
        """
        if check_function is not None:
            is_good = check_function(value)
            if is_good in [0, 1]: # if we are dealing with a good/bad check
                if not(is_good):
                    raise ValueError(
                            "Invalid parameter value %r for parameter %s" %
                            (value, name))


def run_command(commandline):
    """Run an system command with givem commandline.

    The interface we need from `commandline` is:

    * str(commandline) returns a system callable commmand line
    
    WARNING - This will read in the full program output into memory!
    This may be in issue when the program writes a large amount of
    data to standard output.
    """
    child = subprocess.Popen(str(commandline),
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             shell=(sys.platform!="win32"))
    (out, err) = child.communicate()
    error_code = child.returncode
    return error_code, StringIO(out), StringIO(err)


class ShellCommandline(AbstractCommandline):
    ''' Implements generic command line running '''
    def __init__(self, cmd=""):
        self.program_name = cmd
        self.parameters = []
        
    def run(self):
        return_code, out, err = run_command(self)
        if return_code != 0:
            raise OSError('Command %s failed with code %s'
                          ' and message %s' % (self,
                                               return_code,
                                               err.getvalue()))
        return self.result_maker(self, return_code), out, err


class _AbstractParameter(object):
    """A class to hold information about a parameter for a commandline.

    A parameter in the sense of _AbtractParameter can be either a
    positional command line argument or an option (both implemented by
    subclasses of _AbstractParameter).
    
    Do not use this directly, instead use one of the subclasses.

    Attributes:

    o names -- a list of string names by which the parameter can be
    referenced (ie. ["-a", "--append", "append"]). The first name in
    the list is considered to be the one that goes on the commandline,
    for those parameters that print the option. The last name in the list
    is assumed to be a "human readable" name describing the option in one
    word.

    o param_type -- a list of string describing the type of parameter, 
    which can help let programs know how to use it. Example descriptions
    include 'input', 'output', 'file'

    o checker_function -- a reference to a function that will determine
    if a given value is valid for this parameter. This function can either
    raise an error when given a bad value, or return a [0, 1] decision on
    whether the value is correct.

    o description -- a description of the option.

    o is_required -- a flag to indicate if the parameter must be set for
    the program to be run.

    o is_set -- if the parameter has been set

    o value -- the value of a parameter
    """
    def __init__(self, names = [], types = [], checker_function = None, 
                 is_required = 0, description = ""):
        self.names = names
        self.param_types = types
        self.checker_function = checker_function
        self.description = description
        self.is_required = is_required

        self.is_set = 0
        self.value = None


class _Option(_AbstractParameter):
    """Represent an option that can be set for a program.

    This holds UNIXish options like --append=yes and -a yes
    """
    def __str__(self):
        """Return the value of this option for the commandline.
        """
        # first deal with long options
        if self.names[0].find("--") >= 0:
            output = "%s" % self.names[0]
            if self.value is not None:
                output += "=%s " % self.value
            else:
                output += " "
        # now short options
        elif self.names[0].find("-") >= 0:
            output = "%s " % self.names[0]
            if self.value is not None:
                output += "%s " % self.value
        else:
            raise ValueError("Unrecognized option type: %s" % self.names[0])
        return output


class _Argument(_AbstractParameter):
    """Represent an argument on a commandline.
    """
    def __str__(self):
        if self.value is not None:
            return "%s " % self.value
        else:
            return " "


def checkint(var, mn=None, mx=None):
    ''' Check for an int'''
    ret = int(var)
    if mn and ret < mn:
        raise ValueError('Value should be >= %s' % mn)
    if mx and ret > mx:
        raise ValueError('Value should be <= %s' % mx)
    return ret


def checkfloat(var, mn=None, mx=None):
    ''' Check for an float'''
    ret = float(var)
    if mn and ret < mn:
        raise ValueError('Value should be >= %s' % mn)
    if mx and ret > mx:
        raise ValueError('Value should be <= %s' % mx)
    return ret


def check_is_str(var):
    ''' Check for an str'''
    if not isinstance(var, basestring):
        raise ValueError('Value should be a string')
    return var
