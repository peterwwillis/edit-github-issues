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

class EGDoc(object):
    issues = []

class EGDocs(EGDoc):
    filename = None


class EditGhi(GHIssues):
    data = {}

    def load_file(self, name, path):
        """ Load a markdown file and separate its sections by '---' separator """
        content = path.read()
        c=0
        self.data[name] = []
        for line in content.splitlines():
            if line == "---":
                c = c+1
                continue
            if len(self.data[name]) == c:
                self.data[name].append([])
            self.data[name][c].append(line)

    def parse_file(self, docs):
        """ Go through each separated section from loaded markdown file.
            Find list items with a checkbox or no checkbox, add them as
            issues to track.
        """
        _docs = []
        for doci, doc in enumerate(docs):
            _docs.append([])

            for rowi, row in enumerate(doc): 
                cols = row.split()
                if len(cols) < 1 or len(cols[0]) < 1: continue
                if cols[0] == "-": # list item
                    state, title, issues, tags = None, None, [], []

                    # record "[", "]" as an empty checkbox (open issue)
                    if cols[1] == "[" and cols[2] == "]":
                        state, rest = "open", cols[3:]
                    # record "[x]" as a checked box (closed issue)
                    elif cols[1] == "[x]":
                        state, rest = "closed", cols[2:]
                    else:
                        continue

                    for rcol in rest:
                        # Find issue numbers
                        if rcol[0] == '#':
                            if rcol[1:].isdigit():
                                issues.append( rcol[1:] )
                        # Find '[tag,tag2]' tags
                        elif rcol[0] == '[':
                            if rcol[-1] == ']':
                                tags.append( rcol[1:-1].split(",") )
                        # Find "username/repo#number" issue references
                        else:
                            m = re.search(r'^[\w.]+/[\w.]+#([0-9]+)$', rcol, re.I)
                            if m != None and m.group(1):
                                issues.append( m.group(1) )

                    _docs[doci].append({'state': state, 'title': " ".join(rest), 'issue': issues, 'tag': tags})
        return _docs

    def handle_issues(self, docs):
        for doc in docs:
            print("Issues: '%s'" % doc)
        return

    def edit_ghi(self):
        for name, doc in self.data.items():
            print("Processing file '%s'" % name)
            doc_issues = self.parse_file(doc)
            self.handle_issues(doc_issues)


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
        v.load_file(a.file[0].name, a.file[0])
        v.edit_ghi()

if __name__ == "__main__":
    main()
