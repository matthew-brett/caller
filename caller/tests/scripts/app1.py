#!/bin/env python
''' Script to print out distances between pairs of words in file '''

from caller import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-1",
                    "--option1",
                    dest="option1")
parser.add_argument('param1')
parser.add_argument('param2')


if __name__ == '__main__':
    args = parser.parse_args()
    print args.param1, args.param2, args.option1
