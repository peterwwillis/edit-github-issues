#!/usr/bin/env python3
import sys
if sys.version_info < (3, 5):
    raise Exception("Error: must use python 3.5 or greater")

import re
import argparse
import subprocess

class Log(object):
    logging = True
    def __init__(self, string, i=0, logging=True):
        if self.logging == False or logging == False: return
        print( (" " * (i*4)) + string )
class Debug(Log):
    """ Debug class. To enable, set logging = True """
    logging = True

class Util(object):
    @staticmethod
    def exec(cmd):
        return subprocess.check_output(cmd)

class GHIssues(Util):
    @staticmethod
    def load_ghi():
        opencmd = [ "ghi", "list", "--state", "open" ]
        closecmd = [ "ghi", "list", "--state", "closed" ]
        result = Util.exec( cmd ).decode('utf-8')
        rows = [ "issue", "state", "tags", "title" ]
        data = []
        for row in result.split("\n"):
            cols = row.split(",", maxsplit=len(rows)-1)
            # Remove empty list item due to trailing newline
            if len(cols[0]) < 1: continue
            # Remove quotes around the tags
            cols[2] = cols[2][1:-1]
            if len(cols[2]) < 1:
                cols[2] = None
            else:
                cols[2] = cols[2].split(",")
            foo = {}
            for i in range(len(rows)):
                foo[ rows[i].lower() ] = cols[i]
            data.append(foo)
        Debug("load_ghi(): \"%s\"" % data)
        return data

class EditGhi(GHIssues):
    data = {}

    def load_file(self, name, path):
        content = path.read()
        for line in content.splitlines():
            if line == "---":
                Debug("Found new document")
                
        print("content: \"%s\"" % content)

    def parse_file(self, doc):
        print("Doc \"%s\"" % doc)
        for row in doc:
            print("Row \"%s\"" % row)
            cols = row.split()
            print("Cols: \"%s\"" % cols)

    def edit_ghi(self):
        for doc in self.data["data"]:
            self.parse_file(doc)

def options():
    parser = argparse.ArgumentParser(description='Edit GitHub issues in bulk')
    parser.add_argument('file', nargs=1, type=argparse.FileType('r'), help='The YAML file of issues to edit')
    return parser


def main():
    p = options()
    a = p.parse_args()

    v = EditGhi()
    v.load_ghi()

    if a.file != None:
        v.load_file('data', a.file[0])
        v.edit_ghi()

if __name__ == "__main__":
    main()
