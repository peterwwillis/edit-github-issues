#!/usr/bin/env python3
import sys
if sys.version_info < (3, 5):
    raise Exception("Error: must use python 3.5 or greater")

import re
import argparse
import subprocess
import json

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
    issues = None
    def load_ghi(self):
        """
        Get the list of GitHub Issues as a JSON dump.
        Data we get back that's useful:
            - number
            - title
            - labels
              - name
            - state
        """
        issues = Util.exec( [ "ghi", "list", "--state", "all", "--json-out", "--quiet" ] ).decode('utf-8')
        data = json.loads(issues)
        #Debug("load_ghi(): \"%s\"" % data)
        self.issues = data

class EditGhi(GHIssues):
    data = {}

    def load_file(self, name, path):
        """ Load a markdown file and separate its sections by '---' separator """
        content = path.read()
        c=0
        self.data = []
        for line in content.splitlines():
            if line == "---":
                c = c+1
                continue
            if len(self.data) == c:
                self.data.append([])
            self.data[c].append(line)

    def parse_file(self, doc):
        """ Go through each separated section from loaded markdown file.
            Find list items with a checkbox or no checkbox, add them as
            issues to track.
        """
        issues = []
        for row in doc:
            cols = row.split()
            if len(cols) < 1 or len(cols[0]) < 1: continue
            if cols[0] == "-": # list item
                if cols[1] == "[" and cols[2] == "]": # empty checkbox
                    state, rest = "open", cols[3:]
                elif cols[1] == "[x]": # checked box
                    state, rest = "closed", cols[2:]
                else: # should probably look for a '#number' section too
                    continue
                issues.append({'state': state, 'title': " ".join(rest)})
        return issues

    def edit_ghi(self):
        for doc in self.data:
            md_issues = self.parse_file(doc)
            for md_i in md_issues:
                for gh_i in self.issues:
                    if 'title' in gh_i and 'title' in md_i and gh_i['title'] == md_i['title']:
                        print("Found markdown issue '%s' matching github issue '%s'" % (md_i['title'], gh_i['title']))
                        if 'state' in gh_i and 'state' in md_i and gh_i['state'] != md_i['state']:
                            print("  Error: state of markdown issue doesn't match github issue")
                    #else:
                    #    print("Did not match markdown issue '%s' with github issue '%s'" % (md_i['title'], gh_i['title']))


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
