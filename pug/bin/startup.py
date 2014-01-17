#~/src/pug/bin/exit.py

# Save the ipython command history to a runnable file, not including the last save command!
#
from IPython.core.magic import (Magics, magics_class, line_magic, cell_magic, line_cell_magic)


@magics_class
class AutoMagics(Magics):

    #@line_magic
    def line_exit2(self, line):
        "my cell magic to save before exiting %d" % 5
        "my line magic"
        print "Full access to the main IPython object:", self.shell
        print "Variables in the user namespace:", self.shell.user_ns.keys()
        ip = self.shell
        this_line = list(ip.history_manager.get_tail())[-1][1]
        ip.magic(u'save -r test.py 0-%d' % (int(this_line) - 1))
        ip.confirm_exit = False
        ip.exit()

    #@cell_magic
    def cell_exit2(self, line, cell):
        "'Cell' Magic function to save history before exiting %d" % 5
        #ip = get_ipython()
        return line, cell

    @line_cell_magic
    def exit2(self, line, cell=None):
        "Magic that works both as %lcmagic and as %%lcmagic"
        if cell is None:
            print "Called as line magic"
            return self.line_exit2(line)
        else:
            print "Called as cell magic"
            return self.cell_exit2(line, cell)


ip = get_ipython()
# Register the Magics class. IPython will call its constructor.
ip.register_magics(AutoMagics)


# # see http://ipython.org/ipython-doc/rel-1.1.0/interactive/reference.html to finish this up
# from IPython.core.magic import register_cell_magic

# @register_cell_magic

# del exit

