from commandline import ShellCommandline, _Option,_Argument,checkfloat,\
    check_is_str

class BetCommandline(ShellCommandline):
    def __init__(self, cmd='bet'):
        super(BetCommandline, self).__init__(cmd)
        self.parameters = [
            _Argument(['infile', 'input file'],
                       ['input'],
                       check_is_str,
                       True,
                       'input file'),
            _Argument(['outfile', 'output file'],
                      ['input', 'output','file'],
                      check_is_str,
                      True,
                      'input file'),
            _Option(['-f', 'frac', 'fractional intensity threshold'],
                    ['input'],
                    checkfloat,
                    False,
                    'fractional intensity threshold')]


if __name__ == '__main__':
    import sys
    try:
        infile = sys.argv[1]
    except IndexError:
        raise OSError('Need input file')
    better = BetCommandline()
    better.set_parameter('infile', infile)
    better.set_parameter('outfile', 'test_bet.nii')
    better.set_parameter('frac', 0.5)
    res, out, err = better.run()
    print res.get_result('output file')
    
    
