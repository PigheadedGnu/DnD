import json
import collections
import re
import dpath
from os.path import abspath


class JSONInterface:
    OBJECTSPATH = './tools/objects/'
    EXTANT = {}
    # OBJECTSPATH = abspath('.') + '/tools/objects/'

    def __new__(cls, filename, **kwargs):
        # If there is already an interface to the file open, return that
        #   instead of opening a new one
        if (JSONInterface.OBJECTSPATH + filename in JSONInterface.EXTANT):
            return JSONInterface.EXTANT[JSONInterface.OBJECTSPATH + filename]
        else:
            obj = super().__new__(cls)
            return obj

    def __init__(self, filename, isabsolute=False):
        # broken = filename.split('/')[-1].split('.')
        # self.shortfilename = ' '.join(reversed(broken[:len(broken) // 2]))
        self.shortfilename = filename.split('/')[-1]
        # self.shortfilename = filename
        # TODO: Unclean filename?
        if (isabsolute):
            self.filename = filename
        else:
            self.filename = self.OBJECTSPATH + filename
        with open(self.filename) as f:
            data = json.load(f, object_pairs_hook=collections.OrderedDict)
            self.info = data
        JSONInterface.EXTANT.update({self.filename: self})

    def __str__(self):
        return self.shortfilename

    def __repr__(self):
        return "<JSONInterface to {}>".format(self.filename)

    def __add__(self, other):
        if (isinstance(other, JSONInterface)):
            return LinkedInterface(self, other)
        if (isinstance(other, LinkedInterface)):
            # Use LinkedInterface's add method
            return other + self
        else:
            raise TypeError('You can only add a JSONInterface or a '
                            'LinkedInterface to a JSONInterface')

    def __iter__(self):
        yield self

    def get(self, path):
        if (path == '/'):
            return self.info
        try:
            return dpath.get(self.info, path)
        except KeyError:
            return None

    def delete(self, path):
        if (path == '/'):
            del self.info
            return True
        try:
            return dpath.delete(self.info, path)
        except dpath.exceptions.PathNotFound:
            return False

    def set(self, path, value):
        if (path == '/'):
            return False
        return dpath.new(self.info, path, value)

    def write(self):
        with open(self.filename, 'w') as f:
            json.dump(obj=self.info, fp=f, indent=2)


class LinkedInterface:
    def __init__(self, *ifaces):
        self.searchpath = collections.OrderedDict(
            ((str(iface), iface) for iface in ifaces))

    def __add__(self, other):
        if (isinstance(other, LinkedInterface)):
            self.searchpath.update(other.searchpath)
            return self
        elif (isinstance(other, JSONInterface)):
            self.searchpath.update({str(other): other})
            return self
        else:
            raise TypeError('You can only add a JSONInterface or a '
                            'LinkedInterface to a LinkedInterface')

    def __str__(self):
        return ', '.join(reversed(self.searchpath.keys()))

    def __repr__(self):
        return '<LinkedInterface to {}>'.format(str(self))

    def __iter__(self):
        return (iface for iface in self.searchpath.values())

    def get(self, path):
        s = path.split('/')
        filename, remaining = (s[0], s[1:]) if s[0] else (s[1], s[2:])
        remaining = '/'.join(remaining)
        if (filename in self.searchpath):
            # find the result in the specified file
            return self.searchpath[filename]._get(remaining)
        elif (filename == '*'):
            # Find all results in all files
            # Search in more general files then override with more specific
            first = True
            for name, iface in self.searchpath.items():
                found = iface.get(remaining)
                if (found is not None):
                    if (first):
                        rv = found
                        first = False
                        if (isinstance(rv, list)):
                            add = list.extend
                        elif (isinstance(rv, dict)):
                            add = dict.update
                    else:
                        add(rv, found)
            return rv
        else:
            # Find one result in the most specific file you can find it in
            for name, iface in reversed(self.searchpath.items()):
                rv = iface.get(path)
                if (rv is not None):
                    return rv
            return None

    def set(self, path, value):
        s = path.split('/')
        filename, remaining = (s[0], s[1:]) if s[0] else (s[1], s[2:])
        remaining = '/'.join(remaining)
        if (filename in self.searchpath):
            return self.searchpath[filename]._set(remaining, value)
        else:
            for name, iface in reversed(self.searchpath.items()):
                rv = iface._set(path, value)
                if (rv):
                    return rv
            return False
