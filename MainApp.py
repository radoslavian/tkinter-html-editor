#!/usr/bin/env python3
from tkinter import messagebox
from edytor_html import *
import webbrowser

class MainApp(tk.Frame):
    class InnerDecorators:
        @classmethod
        def save_as(cls, fn):
            def wrapper(self):
                file_path = fd.asksaveasfilename(
                    title='Save as a new file:',
                    initialdir='./test',
                    filetypes=file_types)
                if file_path:
                    fn(self, file_path)
                else:
                    raise DocumentSaveCancelled('The document is unsaved - '
                            'cancelled while selecting a file.')
            return wrapper

        @classmethod
        def save(cls, fn):
            def wrapper(self, event=None):
                if not self.main_tabs.edit_html.edit_modified():
                    return
                if self.html_file_path:
                    fn(self, file_path=self.html_file_path)
                else:
                    self.save_document_as()
            return wrapper

    def __init__(self, parent, path_to_doc = None):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.html_file_path = None
        self.app_name = 'Basic HTML Editor'

        self._arrange_subframes()

        parent.menu = MenuBar(parent, self)
        parent.config(menu=parent.menu)

        if path_to_doc:
            self.open_document(path=path_to_doc)
        self.set_mw_title()

        # Event handlers:
        parent.protocol("WM_DELETE_WINDOW", self._quit)
        self.bind_events()

    @classmethod
    def new_instance(cls, parent, path_to_doc=None):
        app = MainApp(parent, path_to_doc)
        app.grid(column=0, row=0, sticky='nwse')
        tk.Grid.columnconfigure(parent, 0, weight=1)
        tk.Grid.rowconfigure(parent, 0, weight=1)
        return app

    def _arrange_subframes(self):
        self.spc_frame = SpecialCharactersFrame(
            self, 'Special characters:', cols=3)
        self.spc_frame.grid(row=1, column=0, sticky='n')

        self.main_tabs = MainTabs(self)
        self.spc_frame.def_chars(self.main_tabs.edit_html.insert_text)
        self.main_tabs.grid(row=1, column=1, sticky='nwse')

        self.main_toolbar = MainToolBar(self)
        self.main_toolbar.grid(row=0, column=0, columnspan=2, sticky='wn')

        tk.Grid.columnconfigure(self, 1, weight=1)
        tk.Grid.rowconfigure(self, 1, weight=1)

    def bind_events(self):
        events = (
            ('<Control-o>', lambda ev: self.open_document(event=ev)),
            ('<Control-s>', self.save_document),
            ('<Control-q>', self._quit),
            ('<Control-f>', self.find_text),
            ('<Control-r>', self.replace_text))

        for ev, fn in events:
            self.bind_all(ev, fn)

    def find_text(self, event=None):
        SearchTextDialog(self, self.main_tabs.edit_html)

    def replace_text(self, event=None):
        ReplaceTextDialog(self, self.main_tabs.edit_html)

    def open_document(self, path=None, event=None):
        if path:
            filename = path
        else:
            filename = fd.askopenfilename(
                initialdir='./test',
                title='Select file',
                filetypes=file_types)
        try:
            self.main_tabs.edit_html.load_doc(filename)
        except TextFieldModified:
            MainApp.new_instance(tk.Toplevel(), filename)
        except IOError as e:
            messagebox.showerror(
                parent=self.parent, title='I/O Error',
                message='Error while attempting to load file: {}'.format(e))
        else:
            self.html_file_path = filename
            os.chdir(os.path.dirname(filename))

    def _save(self, file_path, txt_fld : tk.Text):
        with open(file_path, 'w') as file:
            file.write(txt_fld.get("1.0", "end-1c"))

    def save_doc(self, file_path):
        try:
            self._save(file_path, self.main_tabs.edit_html)
        except IOError as e:
            messagebox.showerror(
                parent=self.parent, title='I/O Error',
                message='Error while attempting to save file: {}'.format(e))
        else:
            if self.html_file_path != file_path:
                self.html_file_path = file_path
                self.set_mw_title()
            self.main_tabs.edit_html.edit_modified(False)

    save_document_as = InnerDecorators.save_as(save_doc)
    save_document = InnerDecorators.save(save_doc)

    def set_mw_title(self):
        if self.html_file_path:
            title_addon = ' - ' + base_file_name(self.html_file_path)
        else:
            title_addon = ' - new document'
        self.parent.title(self.app_name + title_addon)

    def ask_to_save_file(self):
        result = messagebox.askyesnocancel(parent=self.parent,
            title='unsaved document',
            message="The document '{}' was modified but wasn't saved. ".format(
                base_file_name(self.html_file_path)) +
            "Do you want to save it now?")
        if result:
            self.save_document()
        elif result == False:
            return
        else:
            raise DocumentSaveCancelled

    def view_in_browser(self):
        if self.main_tabs.edit_html.edit_modified():
            try:
                self.save_document()
            except DocumentSaveCancelled:
                messagebox.showinfo(
                    parent=self, title='Unsaved file',
                    message='You have to save the file first in order'
                    ' to view it in an external browser.')
                return

        if not self.html_file_path:
            return

        try:
            webbrowser.open(pathlib.Path(self.html_file_path).as_uri())
        except webbrowser.Error as err:
            messagebox.showerror(
                parent=self, title='Browser control error',
                message='During the operation browser control error'
                ' has occured: {}.'.format(err))

    def _quit(self, event=None):
        if self.main_tabs.edit_html.edit_modified():
            try:
                self.ask_to_save_file()
            except DocumentSaveCancelled:
                print('document save cancelled')
                return
        self.master.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    MainApp.new_instance(root)
    tk.mainloop()
