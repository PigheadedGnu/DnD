import tkinter as tk

import helpers as h
import GUIbasics as gui
import interface as iface
import tkUtility as util
import classes as c


class NumberDisplay(gui.Section):
    def __init__(self, container, character):
        gui.Section.__init__(self, container)
        self.character = character
        self.values = []
        self.entries = []
        self.labels = []
        self.incs = []
        self.decs = []
        for i in range(1, len(character.spell_slots)):
            self.values.append(tk.StringVar())
            self.entries.append(tk.Entry(self.f, textvariable=self.values[i-1], width=2))
            self.labels.append(tk.Label(self.f, text=i))
            self.incs.append(tk.Button(self.f, text='+', command=lambda x=i: self.change(x, 1)))
            self.decs.append(tk.Button(self.f, text='-', command=lambda x=i: self.change(x, -1)))
        self.rest = tk.Button(self.f, text='Long Rest', command=self.long_rest)
        ############
        self.draw_static()
        self.draw_dynamic()

    def draw_static(self):
        for i in range(len(self.character.spell_slots) - 1):
            self.labels[i].grid(row=i, column=0)
            self.entries[i].grid(row=i, column=1)
            self.incs[i].grid(row=i, column=2)
            self.decs[i].grid(row=i, column=3)
        self.rest.grid(row=len(self.character.spell_slots), column=4)

    def draw_dynamic(self):
        slots = self.character.spell_slots_get('*')[1:]
        for i, num in enumerate(slots):
            self.values[i].set(str(num))

    def long_rest(self):
        self.character.rest('long')
        self.draw_dynamic()

    def change(self, level, num):
        curr = self.character.spell_slots_get(level)
        self.character.spell_slots_set(level, curr + num)
        self.draw_dynamic()


class SpellDisplay(gui.Section):
    def __init__(self, container, handler, output, numbers):
        gui.Section.__init__(self, container, bd=2, relief='sunken')
        self.handler = handler
        self.output = output
        self.numbers = numbers
        #####
        levelnamemap = ['cantrip', '1st-level', '2nd-level', '3rd-level', '4th-level', '5th-level', '6th-level', '7th-level', '8th-level', '9th-level']
        self.namelevel = tk.Frame(self.f)
        self.nameL = tk.Label(self.namelevel, text=self.handler.name)
        args = (levelnamemap[self.handler.level], self.handler.school)
        lev = '{} {}'.format(*(reversed(args) if self.handler.level == 0 else args))
        self.leveltype = tk.Label(self.namelevel, text=lev)
        self.castingtime = tk.Label(self.f, text=self.handler.casting_time)
        self.range = tk.Label(self.f, text=self.handler.range)
        self.CAST = tk.Button(self.f, text='Cast', command=self.cast)
        ######
        self.draw_static()

    def draw_static(self):
        self.namelevel.grid(row=0, column=0)
        self.nameL.grid(row=0, column=0)
        self.leveltype.grid(row=0, column=1)
        #######
        self.castingtime.grid(row=1, column=0)
        self.range.grid(row=2, column=0)
        self.CAST.grid(row=3, column=0)

    def cast(self):
        try:
            effect = self.handler.cast()
        except c.OutOfSpells as e:
            effect = str(e)
        self.output.update(h.shorten(effect), effect)
        self.numbers.draw_dynamic()


class SpellSection(gui.Section):
    def __init__(self, container, jf, character):
        gui.Section.__init__(self, container)
        self.thisf = tk.Frame(self.f)
        self.character = character
        self.displays = {}
        self.numbers = NumberDisplay(self.f, self.character)
        self.effectvalue = tk.StringVar()
        self.effects = gui.EffectPane(self.thisf, '', '')
        self.handler = c.SpellsPrepared(jf, character)
        for obj in self.handler.objects():
            self.displays[obj.name] = SpellDisplay(self.thisf, obj, self.effects, self.numbers)
        self.draw_static()
        self.draw_dynamic()

    def draw_static(self):
        self.thisf.grid(row=0, column=0)
        self.numbers.grid(row=0, column=1)

    def draw_dynamic(self):
        s = 5
        for (i, d) in enumerate(self.displays.values()):
            d.grid(row=i%s, column=i//s)
        i = len(self.displays)
        self.effects.grid(row=i%s, column=i//s)


class main(gui.Section):
    def __init__(self, window):
        gui.Section.__init__(self, window)
        self.charactername = {}
        self.QUIT = tk.Button(self.f, text='QUIT', command=self.writequit)
        self.begin_start()

    def draw_static(self):
        self.handler.grid(row=0, column=0)
        self.QUIT.grid(row=1, column=2)

    def begin_start(self):
        gui.Query(self.charactername, self.begin_end, 'Character name?')
        self.container.withdraw()

    def begin_end(self):
        name = self.charactername['Character name?']
        filename = 'character/{}.character'.format(h.clean(name))
        self.record = iface.JSONInterface(filename)
        self.character = c.Character(self.record)
        self.handler = SpellSection(self.f, self.record, self.character)
        self.container.deiconify()
        self.draw_static()

    def writequit(self):
        self.character.write()
        self.container.destroy()


if (__name__ == '__main__'):
    win = tk.Tk()
    iface.JSONInterface.OBJECTSPATH = '../objects/'
    app = main(win)
    app.pack()
    win.mainloop()