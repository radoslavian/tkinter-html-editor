"Customized tkinter widgets for tkinter (basic) HTML Editor App"

import tkinter as tk

class IconButton(tk.Button):
    def __init__(self, parent, icon_path, text=None,
                 command=None, *args, **kwargs):
        self.parent = parent
        try:
            self.icon_obj = tk.PhotoImage(file=icon_path)
        except tk.TclError as err:
            #print("Error while creating button '{0}': {1}".format(text, err))
            self.icon_obj = None
        else:
            self.icon_path = icon_path
        tk.Button.__init__(
            self, parent, command=command, relief='solid', text=text,
            image=self.icon_obj, *args, **kwargs)


class SelectMenu(tk.OptionMenu):
    def __init__(self, master, *values, **kwargs):
        self.variable = tk.StringVar()
        self.variable.set(values[0])

        tk.OptionMenu.__init__(self, master, self.variable, *values, **kwargs)

    def get(self):
        return self.variable.get()


class FileChooser(tk.Frame):
    def __init__(self, parent, *pargs, **kwargs):
        tk.Frame.__init__(self, parent, *pargs, **kwargs)

        self.file_entry = tk.Entry(self, state='readonly')
        self.file_entry.grid(column=0, row=0, sticky='we')

        self.browse_bt = tk.Button(self, text='Browse', command=self.browse)
        self.browse_bt.grid(column=1, row=0)

    def browse(self):
        pass

    def get(self):
        pass

if __name__ == '__main__':
    root = tk.Tk()
    fc = FileChooser(root)
    fc.grid()
    tk.mainloop()
