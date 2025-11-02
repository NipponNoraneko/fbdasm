#!/usr/bin/env python3

import sys

allowedChars = ('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
                + '0123456789_')
isBadChar = lambda c: c not in allowedChars

def die(s):
    print(s, file=sys.stderr)
    sys.exit(1)

def processKeyword(addr, code, kw, name):
    print(f'CertainlyData ${addr:04X} {name}')
    print(f'Comment ${addr:04X} "\'{kw}\'"')
    return addr + len(kw) + 1

def main():
    startAddr = 0x4CAB

    f = open("keywords.txt", "r")
    addr = startAddr
    while line := f.readline():
        line = line.rstrip()
        tokens = line.split()
        [code, kw] = tokens[0:2]

        if len(tokens) > 2:
            name = tokens[2]
        else:
            name = kw
            if name.endswith('$'):
                name = name.removesuffix('$') + '_STR'
        name = "tok_" + name

        badCharsMap = map(isBadChar, name)
        if any(badCharsMap):
            die(f'Bad chars in label name; line: "{line}"')
        addr = processKeyword(addr, code, kw, name)

main()
