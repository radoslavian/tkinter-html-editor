"Customized tkinter widgets for the basic tkinter HTML Editor App"

import os
import sys
import tkinter as tk
import pathlib
from tkinter import messagebox as msgbox
from tkinter import filedialog as fd
from modules.utilities import *
from PIL import ImageTk, Image

class IconButton(tk.Button):
    def __init__(
            self, parent, icon_path, text=None, command=None, *args, **kwargs):

        self.parent = parent
        try:
            if not icon_path: raise tk.TclError

            img = Image.open(icon_path)
            img = self.resize_image(img, 28, 0.55)
            self.icon_obj = ImageTk.PhotoImage(img)

        except (FileNotFoundError, tk.TclError) as err:
            print("Error while creating button '{0}' - {1}".format(
                text, err), file=sys.stderr)
            self.icon_obj = None

        tk.Button.__init__(
            self, parent, command=command, relief='raised', text=text,
            image=self.icon_obj, *args, **kwargs)

    def resize_image(self, img, thld, ratio):
        '''Returns resized image if either width or height
        is beyond threshold.'''

        height, width = img.size
        if height > thld or width > thld:
            img = img.resize(
                (round(height*ratio), round(width*ratio)), Image.ANTIALIAS)
        return img


class SelectMenu(tk.OptionMenu):
    def __init__(self, master, *values, **kwargs):
        self.variable = tk.StringVar()
        self.variable.set(values[0])

        tk.OptionMenu.__init__(self, master, self.variable, *values, **kwargs)

    def get(self):
        return self.variable.get()


class FileChooser(tk.Frame):
    def __init__(
            self, parent, filetypes=[('All files', '*')], *pargs, **kwargs):
        tk.Frame.__init__(self, parent, *pargs, **kwargs)

        self._state = 'normal'
        self._unlocked = dict(state='readonly', background='white')
        self._locked = dict(state='disabled', background='grey')

        self.file_name = tk.StringVar()
        self.clear()
        self.filetypes = filetypes

        self.entry = tk.Entry(
            self, textvariable=self.file_name, **self._unlocked)
        self.entry.grid(column=0, row=0, columnspan=2, sticky='we')
        tk.Grid.columnconfigure(self, 0, weight=1)

        self.browse_bt = tk.Button(self, text='Browse', command=self.browse_cb)
        self.browse_bt.grid(column=0, row=1, sticky='we')

        self.clear_bt = tk.Button(self, text='\u232B', command=self.clear)
        self.clear_bt.grid(column=1, row=1, sticky='we')

        self.rel_path = tk.IntVar()
        self.rel_path.set(0)
        self.rel_path_cbt = tk.Checkbutton(
            self, text='relative path', variable=self.rel_path)
        self.rel_path_cbt.grid(column=0, row=2, sticky='w')

        self.cget = self.entry.cget

    def browse_cb(self):
        path_to_file = fd.askopenfilename(parent=self, filetypes=self.filetypes)

        if not path_to_file: return

        self.path_to_file = path_to_file
        file_name = base_file_name(self.path_to_file)
        self.file_name.set(file_name)

    def clear(self):
        self.path_to_file = ''
        self.file_name.set('')

    def get(self):
        "Returns absolute url or a relative path to a file."

        if self.disabled(): return

        if self.path_to_file:
            return {
                '0': lambda: pathlib.Path(self.path_to_file).as_uri(),
                '1': lambda: pathlib.Path(
                    os.path.relpath(self.path_to_file)).as_posix()
            }[str(self.rel_path.get())]()

    def disabled(self):
        "Returns state in a True (disabled)/False(normal) format."

        return {'disabled': True, 'normal': False}[self._state]

    def disable(self, state=True):
        if state == self.disabled():
            # no state change
            return

        if state == True:
            self._state = 'disabled'
            self.entry.configure(**self._locked)

        elif state == False:
            self._state = 'normal'
            self.entry.configure(**self._unlocked)

        else:
            raise ValueError('state must be True or False')

        for wdg in self.browse_bt, self.rel_path_cbt, self.clear_bt:
            wdg.configure(state=self._state)


if __name__ == '__main__':
    root = tk.Tk()
    # fc = FileChooser(root)
    # fc.disabled(True)
    # print(fc.disabled())
    # fc.grid(column=0, sticky='we')
    # tk.Grid.columnconfigure(root, 0, weight=1)

    from icons import icon
    IconButton(root, icon('button.png')).grid()
    
    tk.mainloop()
