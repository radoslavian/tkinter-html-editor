#!/usr/bin/env python3
from tkinter import messagebox
from html_editor import *
import webbrowser


class MainApp(tk.Toplevel):
    class InnerDecorators:
        @classmethod
        def save_as(cls, fn):
            def wrapper(self):
                file_path = fd.asksaveasfilename(
                    title='Save as a new file:',
                    initialdir='./test',
                    filetypes=file_types)

                if file_path:
                    self.root.opened_files.remove(self.html_file_path)
                    fn(self, file_path)

                    if self.html_file_path != file_path:
                        self.update_work_state(file_path)

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

    def __init__(self, root, path_to_doc = None):
        tk.Toplevel.__init__(self, root)

        self.root = root
        self.html_file_path = None
        self.app_name = 'Basic tkinter HTML Editor'

        self._arrange_subframes()

        self.menu = MenuBar(self)
        self.config(menu=self.menu)

        if path_to_doc:
            self.open_document(path=path_to_doc)

        # Event handlers:
        self.protocol("WM_DELETE_WINDOW", self.quit)
        self.bind_events()

        self.set_mw_title()
        self.main_tabs.edit_html.edit_field.focus_set()

    def _new_instance(self, path_to_doc=None):
        app = MainApp(self.root, path_to_doc)
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
            ('<Control-n>', lambda ev: self._new_instance()),
            ('<Control-o>', lambda ev: self.open_document(event=ev)),
            ('<Control-s>', self.save_document),
            ('<Control-q>', self.quit),
            ('<Control-f>', self.find_text),
            ('<Control-r>', self.replace_text))

        for ev, fn in events:
            self.bind(ev, fn)

    def find_text(self, event=None):
        SearchTextDialog(self.main_tabs.edit_html, self.main_tabs.edit_html)

    def replace_text(self, event=None):
        ReplaceTextDialog(
            self.main_tabs.edit_html, self.main_tabs.edit_html)

    def open_document(self, path=None, event=None):
        if path:
            filename = path
        else:
            filename = fd.askopenfilename(
                parent=self, initialdir='./test', title='Select file',
                filetypes=file_types)

            if not filename:
                return

            elif filename in self.root.opened_files:
                messagebox.showerror(
                    parent=self, title='File already opened.',
                    message='The file is already opened in another window.')
                return

        try:
            self.main_tabs.edit_html.load_doc(filename)

        except TextFieldModified:
            self._new_instance(filename)

        except IOError as e:
            messagebox.showerror(
                parent=self, title='I/O Error',
                message='Error while attempting to load file: {}'.format(e))

        else:
            self.update_work_state(filename)

    def _save(self, file_path, txt_fld : tk.Text):
        with open(file_path, 'w') as file:
            file.write(txt_fld.get("1.0", "end-1c"))

    def save_doc(self, file_path):
        try:
            self._save(file_path, self.main_tabs.edit_html)

        except IOError as e:
            messagebox.showerror(
                parent=self, title='I/O Error',
                message='Error while attempting to save file: {}'.format(e))
        else:
            self.main_tabs.edit_html.edit_modified(False)

    save_document_as = InnerDecorators.save_as(save_doc)
    save_document = InnerDecorators.save(save_doc)

    def update_work_state(self, file_path):
        '''Sets current: window title, working directory and appends opened/saved
        file(name) to the list of the currently opened files (root.opened_files).'''

        self.html_file_path = file_path
        os.chdir(os.path.dirname(file_path))
        self.root.opened_files.append(file_path)
        self.set_mw_title()

    def set_mw_title(self):
        if self.html_file_path:
            title_addon = ' - ' + base_file_name(self.html_file_path)
        else:
            title_addon = ' - new document'
        self.title(self.app_name + title_addon)

    def ask_to_save_file(self):
        result = messagebox.askyesnocancel(parent=self,
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

    def quit(self, event=None):
        if self.main_tabs.edit_html.edit_modified():
            try:
                self.ask_to_save_file()
            except DocumentSaveCancelled:
                print('document save cancelled')
                return

        if self.html_file_path:
            self.root.opened_files.remove(self.html_file_path)

        self.destroy()

        # Following is the call to RootWin's quit()
        # method, which in turn counts
        # the number of remaining instances of the MainApp
        # class and terminates the application only if
        # the counter drops to 0.

        self.root.quit()


class RootWin(tk.Tk):
    '''Every MainApp instance should be a child window of the RootWin and
    there should only be a single instance of RootWin.

    Thus we can have multiple MainApp windows within
    a single Python process.'''

    instance_count = 0

    def __init__(self, *pargs, **kwargs):
        if RootWin.instance_count > 0:
            raise RuntimeError(
                'Only one instance of this class is allowed to be created'
                + ' at the same time.')

        RootWin.instance_count += 1
        self.opened_files = []

        tk.Tk.__init__(self, *pargs, **kwargs)
        self.withdraw()

    def __del__(self):
        '''Tkinter application runs only as long as the Tk root window exists,
        so this is only for the reason of cohesiveness.'''

        RootWin.instance_count -= 1

    def quit(self):
        if len(self.winfo_children()) < 1:
            super().quit()


if __name__ == '__main__':
    root = RootWin()
    mapp = MainApp(root)
    root.mainloop()
