#!/usr/bin/env python2

from __future__ import print_function
import os, os.path
import Tkinter as tk

import utils as U


def job_split(jfull):
    d, j = os.path.split(jfull)
    ds = []
    while d:
        d, d1 = os.path.split(d)
        ds.append(d1)
    ds.reverse()
    return (ds, j)

def file_img(f):
    return tk.PhotoImage(file=os.path.join(U.cgenie_root, 'tools',
                                           'images', f + '.gif'))

def walk_jobs(p, basedir=None):
    if not basedir: basedir = p
    model_dir = os.path.join(basedir, 'MODELS')
    es = os.listdir(p)
    for e in os.listdir(p):
        f = os.path.join(p, e)
        if f.startswith(model_dir): continue
        if os.path.exists(os.path.join(f, 'config', 'config')):
            yield (f, 'JOB')
        elif os.path.isdir(f):
            if not os.listdir(f):
                yield (f, 'FOLDER')
            else:
                for sube in walk_jobs(f, basedir):
                    yield sube


def is_folder(tree, id):
    if id == U.cgenie_jobs: return True
    return str(tree.item(id, 'image')[0]) == str(status_img('FOLDER'))

status_images = { }
def status_img(s):
    if not s in status_images:
        p = os.path.join(U.cgenie_root, 'tools', 'images',
                         'status-' + s + '.gif')
        status_images[s] = tk.PhotoImage(file=p)
    return status_images[s]

def job_status(jd):
    if not os.path.exists(os.path.join(jd, 'data_genie')):
        return 'UNCONFIGURED'
    if not os.path.exists(os.path.join(jd, 'status')):
        return 'RUNNABLE'
    with open(os.path.join(jd, 'status')) as fp:
        return fp.readline().strip().split()[0]

def job_pct(jd):
    if not os.path.exists(os.path.join(jd, 'status')):
        return None
    with open(os.path.join(jd, 'status')) as fp:
        ss = fp.readline().strip().split()
        if ss[0] != 'RUNNING' and ss[0] != 'PAUSED': return None
        return 100 * float(ss[1]) / float(ss[2])


'''Michael Lange <klappnase (at) freakmail (dot) de>

The ToolTip class provides a flexible tooltip widget for Tkinter; it is based on
IDLE's ToolTip module which unfortunately seems to be broken (at least the
version I saw).

INITIALIZATION OPTIONS:
anchor :        where the text should be positioned inside the widget, must be
                one of "n", "s", "e", "w", "nw" and so on; default is "center"
bd :            borderwidth of the widget; default is 1 (NOTE: don't use
                "borderwidth" here)
bg :            background color to use for the widget; default is
                "lightyellow" (NOTE: don't use "background")
delay :         time in ms that it takes for the widget to appear on the screen
                when the mouse pointer has entered the parent widget; default is
                1500
fg :            foreground (i.e. text) color to use; default is "black" (NOTE:
                don't use "foreground")
follow_mouse :  if set to 1 the tooltip will follow the mouse pointer instead of
                being displayed outside of the parent widget; this may be useful
                if you want to use tooltips for large widgets like listboxes or
                canvases; default is 0
font :          font to use for the widget; default is system specific
justify :       how multiple lines of text will be aligned, must be "left",
                "right" or "center"; default is "left"
padx :          extra space added to the left and right within the widget;
                default is 4
pady :          extra space above and below the text; default is 2
relief :        one of "flat", "ridge", "groove", "raised", "sunken" or "solid";
                default is "solid"
state :         must be "normal" or "disabled"; if set to "disabled" the tooltip
                will not appear; default is "normal"
text :          the text that is displayed inside the widget
textvariable :  if set to an instance of Tkinter.StringVar() the variable's
                value will be used as text for the widget
width :         width of the widget; the default is 0, which means that
                "wraplength" will be used to limit the widgets width
wraplength :    limits the number of characters in each line; default is 150

WIDGET METHODS:
configure(**opts) : change one or more of the widget's options as described
                    above; the changes will take effect the next time the
                    tooltip shows up; NOTE: follow_mouse cannot be changed
                    after widget initialization

Other widget methods that might be useful if you want to subclass ToolTip:
enter() :           callback when the mouse pointer enters the parent widget
leave() :           called when the mouse pointer leaves the parent widget
motion() :          is called when the mouse pointer moves inside the parent
                    widget if follow_mouse is set to 1 and the tooltip has
                    shown up to continually update the coordinates of the
                    tooltip window
coords() :          calculates the screen coordinates of the tooltip window
create_contents() : creates the contents of the tooltip window (by default a
                    Tkinter.Label)
'''
# Ideas gleaned from PySol

class ToolTip:
    def __init__(self, master, text='Your text here', delay=750, **opts):
        self.master = master
        self._opts = {'anchor':'center', 'bd':1, 'bg':'lightyellow',
                      'delay':delay, 'fg':'black', 'follow_mouse':0,
                      'font':None, 'justify':'left', 'padx':4, 'pady':2,
                      'relief':'solid', 'state':'normal', 'text':text,
                      'textvariable':None, 'width':0, 'wraplength':150}
        self.configure(**opts)
        self._tipwindow = None
        self._id = None
        self._id1 = self.master.bind("<Enter>", self.enter, '+')
        self._id2 = self.master.bind("<Leave>", self.leave, '+')
        self._id3 = self.master.bind("<ButtonPress>", self.leave, '+')
        self._follow_mouse = 0
        if self._opts['follow_mouse']:
            self._id4 = self.master.bind("<Motion>", self.motion, '+')
            self._follow_mouse = 1

    def configure(self, **opts):
        for key in opts:
            if self._opts.has_key(key):
                self._opts[key] = opts[key]
            else:
                KeyError = 'KeyError: Unknown option: "%s"' %key
                raise KeyError

    ## These methods handle the callbacks on "<Enter>", "<Leave>" and
    ## "<Motion>" events on the parent widget; override them if you
    ## want to change the widget's behavior

    def enter(self, event=None):
        self._schedule()

    def leave(self, event=None):
        self._unschedule()
        self._hide()

    def motion(self, event=None):
        if self._tipwindow and self._follow_mouse:
            x, y = self.coords()
            self._tipwindow.wm_geometry("+%d+%d" % (x, y))

    ## The methods that do the work:

    def _schedule(self):
        self._unschedule()
        if self._opts['state'] == 'disabled':
            return
        self._id = self.master.after(self._opts['delay'], self._show)

    def _unschedule(self):
        id = self._id
        self._id = None
        if id:
            self.master.after_cancel(id)

    def _show(self):
        if self._opts['state'] == 'disabled':
            self._unschedule()
            return
        if not self._tipwindow:
            self._tipwindow = tw = tk.Toplevel(self.master)
            # hide the window until we know the geometry
            tw.withdraw()
            tw.wm_overrideredirect(1)

            if tw.tk.call("tk", "windowingsystem") == 'aqua':
                tw.tk.call("::tk::unsupported::MacWindowStyle", "style",
                           tw._w, "help", "none")

            self.create_contents()
            tw.update_idletasks()
            x, y = self.coords()
            tw.wm_geometry("+%d+%d" % (x, y))
            tw.deiconify()

    def _hide(self):
        tw = self._tipwindow
        self._tipwindow = None
        if tw:
            tw.destroy()

    ## These methods might be overridden in derived classes:

    def coords(self):
        # The tip window must be completely outside the master widget;
        # otherwise when the mouse enters the tip window we get a
        # leave event and it disappears, and then we get an enter
        # event and it reappears, and so on forever :-( or we take
        # care that the mouse pointer is always outside the tipwindow
        # :-)
        tw = self._tipwindow
        twx, twy = tw.winfo_reqwidth(), tw.winfo_reqheight()
        w, h = tw.winfo_screenwidth(), tw.winfo_screenheight()
        # calculate the y coordinate:
        if self._follow_mouse:
            y = tw.winfo_pointery() + 20
            # make sure the tipwindow is never outside the screen:
            if y + twy > h:
                y = y - twy - 30
        else:
            y = self.master.winfo_rooty() + self.master.winfo_height() + 3
            if y + twy > h:
                y = self.master.winfo_rooty() - twy - 3
        # we can use the same x coord in both cases:
        x = tw.winfo_pointerx() - twx / 2
        if x < 0:
            x = 0
        elif x + twx > w:
            x = w - twx
        return x, y

    def create_contents(self):
        opts = self._opts.copy()
        for opt in ('delay', 'follow_mouse', 'state'):
            del opts[opt]
        label = tk.Label(self._tipwindow, **opts)
        label.pack()

## DEMO CODE

# def demo():
#     root = tk.Tk(className='ToolTip-demo')
#     l = tk.Listbox(root)
#     l.insert('end', "I'm a listbox")
#     l.pack(side='top')
#     t1 = ToolTip(l, follow_mouse=1,
#                  text="I'm a tooltip with follow_mouse set to 1, " +
#                  "so I won't be placed outside my parent")
#     b = tk.Button(root, text='Quit', command=root.quit)
#     b.pack(side='bottom')
#     t2 = ToolTip(b, text='Enough of this')
#     root.mainloop()

# if __name__ == '__main__':
#     demo()


class Tailer:
    def __init__(self, app, fname):
        self.app = app
        self.fname = fname
        self.pos = 0
        self.fp = None
        self.after_id = None
        self.cb = None

    def start(self, cb):
        self.cb = cb
        if not self.after_id: self.after_id = self.app.after(500, self.read)

    def stop(self):
        if self.after_id: self.app.after_cancel(self.after_id)
        self.after_id = None

    def read(self):
        if not self.fp and os.path.exists(self.fname):
            self.fp = open(self.fname)
            self.pos = 0
        if self.fp:
            self.fp.seek(0, os.SEEK_END)
            self.size = self.fp.tell()
            if self.size > self.pos:
                self.fp.seek(self.pos, os.SEEK_SET)
                new = self.fp.read(self.size - self.pos)
                self.pos = self.size
                self.cb(new)
        self.after_id = self.app.after(500, self.read)