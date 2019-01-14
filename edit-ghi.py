#!/usr/bin/env python3
import sys
if sys.version_info < (3, 5):
    raise Exception("Error: must use python 3.5 or greater")

import re
import argparse
import subprocess
import json
import os

class Log(object):
    logging = True
    def __init__(self, string, i=0, logging=True):
        if self.logging == False or logging == False: return
        print( (" " * (i*4)) + string )
class Debug(Log):
    """ Debug class. To enable, set logging = True """
    logging = False
    if "DEBUG" in os.environ: logging = os.environ["DEBUG"]

class Util(object):
    @staticmethod
    def exec(cmd):
        return subprocess.check_output(cmd)

class GHIssues(Util):
    """ A class to manage GitHub issues """

    def __init__(self):
        self.cache = {}

    def get_issues(self):
        """
        Get the list of GitHub Issues as a JSON dump.
        Data we get back that's useful:
            - number
            - title
            - labels
              - name
            - state
        """
        issues = Util.exec( 
                [ "ghi", "list", "--state", "all", "--json-out", "--quiet" ] 
        ).decode('utf-8')
        data = json.loads(issues)
        Debug("load_ghi(): \"%s\"" % data)
        return data

    def issues(self):
        if not self.cache:
            self.cache = self.get_issues()
        return self.cache

    def issue(self, issue):
        """ Look at the internal cache of GH issues and see if an issue matching
            the dict 'issue' exists; if so, return True.

            A GH issue is a Python datastructure of the JSON returned from the
            GitHub Issues API. Common values include:
             - url
             - id
             - node_id
             - number
             - title
             - labels
             - state
        """
        Debug("Checking if issue exists: '%s'" % issue)
        for i in self.issues():
            if 'title' in issue and 'title' in i and issue['title'] in i['title']:
                Log("Found matching issue: issue[title] matches i[title]: '%s'" % i['title'])
                return i
        return None

    def update_issue(self, issue, gh_issue):
        Log("Updating GH issue '%s' with '%s'" % (gh_issue['number'], issue) )


class EGFile(object):
    """
    Loads a markdown file and separates its sections by '---' separator 
    into separate document streams (kinda like YAML). Detects potential GitHub
    issues in each document if a line starts with ' - [ ]' or ' - [x]'.
    """
    def __init__(self, path):
        self.docs = []
        filename = path.name
        self.content = path.read()
        self._load_content()

    def _load_content(self):
        doci=0
        for line in self.content.splitlines():
            if line == "---":
                doci = doci+1
                continue
            if self.doc(doci) == None:
                self.add_doc()
            self.doc(doci).add_line(line)

    def __repr__(self):
        return '<%s, docs: [%s]>' % (self.__class__.__name__, self.docs)

    def add_doc(self):
        self.docs.append( EGDoc() )

    def doc(self, num):
        if len(self.docs) >= (num+1):
            if self.docs[num] != None:
                return self.docs[num]
        return None

class EGDoc(object):
    """ A class to manage a list of issues """

    def __init__(self):
        self.heading = None
        self.issues = []

    def __repr__(self):
        return '<%s, issues: [%s]>' % (self.__class__.__name__, self.issues)

    def add_issue(self, args):
        if not 'title' in args:
            raise Exception("Error: all issues need a title (got: '%s')" % args)
        if not 'state' in args:
            raise Exception("Error: all issues need a state (got: '%s')" % args)
        self.issues.append( EGIssue(args) )

    def add_line(self, line):
        cols = line.split()

        if len(cols) < 1 or len(cols[0]) < 1: # skip empty lines
            return

        if cols[0][0] == '#': # headings
            self.heading = " ".join(cols)

        if cols[0] == "-": # list item
            args = { }
            args['issues'], args['tags'] = [], []
            #state, title, issues, tags = None, None, [], []

            # record "[", "]" as an empty checkbox (open issue)
            if cols[1] == "[" and cols[2] == "]":
                args['state'], rest = "open", cols[3:]
            # record "[x]" as a checked box (closed issue)
            elif cols[1] == "[x]":
                args['state'], rest = "closed", cols[2:]
            else:
                return

            for rcol in rest:
                if rcol[0] == '#': # Find issue numbers
                    if rcol[1:].isdigit():
                        args['issues'].append( rcol[1:] )
                elif rcol[0] == '[': # Find '[tag,tag2]' tags
                    if rcol[-1] == ']':
                        args['tags'].append( rcol[1:-1].split(",") )
                else: # Find "username/repo#number" issue references
                    m = re.search(r'^[\w.]+/[\w.]+#([0-9]+)$', rcol, re.I)
                    if m != None and m.group(1):
                        args['issues'].append( m.group(1) )

            args['title'] = " ".join(rest)
            if self.heading != None:
                args['heading'] = self.heading

            self.add_issue( args )
        return

class EGIssue(dict):
    """ A dict object for an individual issue.
    
        An EG Issue is the internal representation of issues that have been
        read from a file. Common values include:
         - heading (the '# some heading' part of a file)
         - title (the title of the issue)
         - state ('open' or 'closed')
         - issues (a list of issue number references)
         - tags (a list of tags)
    """
    def __init__(self, *arg, **kw):
        super(EGIssue, self).__init__(*arg, **kw)


class EditGhi(object):
    """ Class to manage editing of GitHub issues """

    def __init__(self, args):
        self.files = []
        self.gh = GHIssues()
        self.args = args

        if self.args.file != None:
            for f in self.args.file:
                self.load_file(f)

    def load_file(self, path):
        self.files.append( EGFile(path) )

    def issues(self):
        for egf in self.files:
            for doc in egf.docs:
                for issue in doc.issues:
                    Debug("Issue: '%s'" % issue)
                    yield issue
        return

    def fix_gh(self):
        for issue in self.issues():
            ghi = self.gh.issue(issue)
            if ghi != None:
                self.gh.update_issue(issue, ghi)

    def handle_issues(self):
        for egf in self.files:
            for doc in egf.docs:
                for issue in doc.issues:
                    Debug("Issue: '%s'" % issue)
        return

    def edit_ghi(self):
        if self.args.fix_to_gh != None:
            self.fix_gh()


def options():
    parser = argparse.ArgumentParser(description='Edit GitHub issues in bulk')
    parser.add_argument('file', nargs=1, type=argparse.FileType('r'), help='The YAML file of issues to edit')
    parser.add_argument('--add-to-gh', action='store_true', help='Add any issues found in the file to GitHub')
    parser.add_argument('--add-to-file', action='store_true', help='Add any isses found in GitHub to the file')
    parser.add_argument('--fix-to-gh', action='store_true', help='If there is inconsistency between the file and GitHub, apply the file issues to GitHub')
    parser.add_argument('--fix-to-file', action='store_true', help='If there is inconsistency between the file and GitHub, apply GitHub issues to the file')
    return parser


def main():
    p = options()
    a = p.parse_args()

    v = EditGhi( a )
    v.edit_ghi()

if __name__ == "__main__":
    main()
