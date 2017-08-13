import re
import collections

import classes as c
import helpers as h
import interface as iface


class ClassMap:
    def __init__(self, s):
        # Takes in a string of the form Class [(Subclass)] Level,...
        # TODO: _classes should be a list of Class objects
        self._classes = []
        self._subclasses = []
        self.levels = []
        self.classes = collections.OrderedDict()

        L = s.split(',')
        for substr in L:
            pattern = r'\s*([a-zA-Z\']+)\s*(\(([a-zA-Z\'\s]+)\))?\s*([0-9]+)'
            desc_ = re.match(pattern, substr).groups()
            desc = [str(item) for item in desc_ if item is not None]
            if (len(desc) == 2):
                self._classes.append(desc[0])
                self._subclasses.append('')
                self.levels.append(int(desc[1]))
            else:
                self._classes.append(desc[0])
                self._subclasses.append(desc[2])
                self.levels.append(int(desc[3]))

        self.hook()

    def __len__(self):
        return len(self._classes)

    def __str__(self):
        out = []
        for (C, S, L) in zip(self._classes, self._subclasses, self.levels):
            out.extend((C, (''.join((' (', S, ') ')) if S else ' '), str(L),
                        ', '))
        return ''.join(out[:-1])

    def __iter__(self):
        return (tup for tup in zip(self.classes.keys(), self.classes.values(),
                                   self.levels))

    def __getitem__(self, key):
        if (isinstance(key, str)):
            return self.classes[key]
        elif (isinstance(key, int)):
            for i, v in enumerate(self.classes.values()):
                if (i == key):
                    return v
            raise IndexError
        raise TypeError

    def sum(self):
        return sum(self.levels)

    def names(self):
        return self._classes

    def hook(self):
        main = 'class/{}.class'
        sub = 'class/{}.{}.sub.class'
        super_ = 'class/{}.super.class'
        for (C, S, L) in zip(self._classes, self._subclasses, self.levels):
            C = h.clean(C)
            S = h.clean(S)
            file_ = main.format(C)
            subfile_ = sub.format(C, S)
            mainclass = iface.JSONInterface(file_)
            try:
                subclass = iface.JSONInterface(subfile_)
                subclassfound = True
            except FileNotFoundError:
                subclassfound = False
            superclasses = [iface.JSONInterface(super_.format(name))
                            for name in mainclass.get('/superclass')]
            if (subclassfound):
                jf = iface.LinkedInterface(*superclasses, mainclass,
                                           subclass)
                # self.classes.update(
                #     {str(mainclass): iface.LinkedInterface(*superclasses,
                #                                            mainclass,
                #                                            subclass)})
            else:
                jf = iface.LinkedInterface(*superclasses, mainclass)
                # self.classes.update(
                #     {str(mainclass): iface.LinkedInterface(*superclasses,
                #                                            mainclass)})
            self.classes.update({str(mainclass): c.Class(jf, L)})


class RaceMap:
    def __init__(self, s):
        pattern = '\s*(\w+)\s*\(?(\w+)?\)?\s*'
        res = re.match(pattern, s).groups()
        self.race = res[0]
        self.subrace = res[1] or ''

    def __getattr__(self, key):
        return self.core.__getattribute__(key)

    def __str__(self):
        return self.race + (' ({})'.format(self.subrace)
                            if self.subrace else '')

    def hook(self):
        main = 'race/{}.race'.format(self.race)
        sub = 'race/{}.{}.sub.race'.format(self.race, self.subrace)
        mainjf = iface.JSONInterface(main)
        if (self.subrace):
            subjf = iface.JSONInterface(sub)
            self.core = c.Race(iface.LinkedInterface(mainjf, subjf), str(self))
        else:
            # For the sake of having a consistent API it needs to be a LinkedInterface
            self.core = c.Race(iface.LinkedInterface(mainjf), str(self))