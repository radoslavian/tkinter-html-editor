#!/usr/bin/env python3
import os
import io
import sys
import pathlib
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
from tkSimpleDialog import Dialog
from urllib.request import urlopen
from PIL import Image, ImageTk


file_types = (
            ('Pliki html', ('.htm', '.html')),
            ('Pliki tekstowe', '.txt'),
            ('Wszystkie pliki', '*')
)

class TextFieldModified(Exception): pass

class EditField(ScrolledText):
    def __init__(self, parent):
        ScrolledText.__init__(self, parent)

    def load_doc(self, path):
        if not path: return
        try:
            html_file = open(path)
        except IOError:
            print("Add file_not_found msg")
            raise
        else:
            self.insert_if_empty(html_file.read())
        finally:
            html_file.close()

    def is_empty(self) -> bool:
        return True if self.compare("end-1c", "==", "1.0") else False

    def insert_if_empty(self, content):
        '''Inserts text only if the text edit field is empty
        and unmodified.'''

        if self.edit_modified() or not self.is_empty():
            raise TextFieldModified(
                'Text field {0} is non-empty or '.format(self)
                + 'modified.')
        else:
            self.insert('1.0', content)
            self.edit_modified(False)


class HtmlPreview(tk.Frame):
    """Allows previewing html within a frame that can be embedded in a
    separate tab. Requires tkhtml to work."""

    # To do: doesn't support hyperlinks.

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)

        self.images = {}

        try:
            from tkinterhtml import TkinterHtml

        except ImportError as e:

            error_message = ('The preview html tab is not working due to ' +
            'the following  error:\n\n{0}.\n\nCheck the documentation ' +
            'or try to install the required tkhtml module using the ' +
            'pip3 command-line tool:\n\npip3 install tkinterhtml')
            print(e)

            self.preview_frame = tk.Text(self)
            self.preview_frame.insert('1.0', error_message.format(e))

            self.preview_frame.no_html = True

        else:
            self.preview_frame = TkinterHtml(self,
                                             imagecmd=self.__load_image)
        self.__setup_preview()


    def __setup_preview(self):
        scrollbar = tk.Scrollbar(self)
        self.preview_frame.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.preview_frame.yview)

        tk.Grid.columnconfigure(self, 0, weight=1)
        tk.Grid.rowconfigure(self, 0, weight=1)
        self.preview_frame.grid(row=0, column=0, sticky='wsne')
        scrollbar.grid(row=0, column=1, sticky='wsne')


    def __load_image(self, url):
        try:
            fp = urlopen(url)
        except Exception as e:
            print(e, file=sys.stderr)
            photo = None
        else:
            data = fp.read()
            image = Image.open(io.BytesIO(data))
            photo = ImageTk.PhotoImage(image)
            self.images[url] = photo
            fp.close()

        return photo


    def preview(self, html_code : str):
        if hasattr(self.preview_frame, 'no_html'): return

        self.preview_frame.reset()
        self.preview_frame.parse(html_code)


class InsertImgDialog(Dialog):

    def body(self, parent):

        def adjust_preview():
            if preview_lbl.img != '':
                img_width = preview_lbl.img.width()
                img_height = preview_lbl.img.height()

                if img_width > 256:
                    img_width = 256

                if img_height > 256:
                    img_height = 256

                preview_lbl.configure(width=img_width, height=img_height,
                                      image=preview_lbl.img)
            else:
                preview_lbl.configure(preview_def_size)


        def img_browse_callback():
            path_to_image = fd.askopenfilename(filetypes=(
                ('Images', ('.jpg','.jpeg', '.png', '.gif')),
                ('All files', '*')
            ))

            if not path_to_image: return

            self.path_to_image = path_to_image
            image_file_name = os.path.basename(self.path_to_image)
            self.img_path.set(image_file_name)

            try:
                preview_lbl.img = tk.PhotoImage(file=self.path_to_image)

            except tk.TclError:
                try:
                    from PIL import Image, ImageTk

                    preview_lbl.img = ImageTk.PhotoImage(
                        Image.open(self.path_to_image))

                except (tk.TclError, OSError) as e:
                    messagebox.showerror("Can't preview image file:", e)

                    if preview_lbl.img is not self.no_img_available:
                        preview_lbl.img = self.no_img_available
                        preview_lbl.configure(image=preview_lbl.img)

            adjust_preview()

        try:
            self.no_img_available = tk.PhotoImage(
                file='icons/no_image_available.png')
        except tk.TclError as e:
            print(e)
            self.no_img_available = ''

        preview_def_size = dict(width=20, height=5)

        self.img_path = tk.StringVar()
        self.path_to_image = ''

        tk.Label(parent, text='Path:').grid(row=1)
        self.img_path_ent = tk.Entry(parent,
                                     textvariable = self.img_path,
                                     state='readonly')
        self.img_path_ent.grid(row=1, column=1)

        tk.Label(parent, text='Alt:').grid(row=2)
        self.alt_ent = tk.Entry(parent)
        self.alt_ent.grid(row=2, column=1)

        tk.Label(parent, text='Height:').grid(row=3)
        self.height_ent = tk.Entry(parent)
        self.height_ent.grid(row=3, column=1)

        tk.Label(parent, text='Width:').grid(row=4)
        self.width_ent = tk.Entry(parent)
        self.width_ent.grid(row=4, column=1)

        tk.Label(parent, text='Style:').grid(row=5)
        self.style_ent = tk.Entry(parent)
        self.style_ent.grid(row=5, column=1)

        img_browse_bt = tk.Button(parent, text='Browse',
                                  command=img_browse_callback)
        img_browse_bt.grid(row=6, column=1, sticky='we')

        tk.Label(parent, text='Preview:').grid(row=0, column=2)
        preview_lbl = tk.Label(parent, bg='white', **preview_def_size)
        preview_lbl.grid(row=1, column=2, rowspan=5, padx=5, sticky='snwe')
        preview_lbl.img = ''

        tk.Grid.columnconfigure(self, 2, weight=1)
        tk.Grid.rowconfigure(self, 1, weight=1)


    def apply(self):
        path_to_image = ''
        if self.path_to_image:
            path_to_image = pathlib.Path(self.path_to_image).as_uri()

        self.result = {
            'src'      : path_to_image,
            'alt'      : str(self.alt_ent.get()),
            'height'   : str(self.height_ent.get()),
            'width'    : str(self.width_ent.get()),
            'style'    : str(self.style_ent.get())
        }


class InsertHyperlinkDialog(Dialog):

    def body(self, parent):

        tk.Label(parent, text='Target:').grid(row=0, column=0)
        self.target_ent = tk.Entry(parent)
        self.target_ent.grid(row=0, column=1)

        tk.Label(parent, text='Style:').grid(row=1, column=0)
        self.style_ent = tk.Entry(parent)
        self.style_ent.grid(row=1, column=1)

    def apply(self):
        self.result = {
            'target' : str(self.target_ent.get()),
            'style'  : str(self.style_ent.get())
        }


class SpecialCharactersFrame(tk.Frame):
    """Frame for special character buttons."""

    def __init__(self, parent,  header, cols = 1, *args, **kwargs):

        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.header = header

        self.no_of_cols = cols if cols > 0 else 1
        self.cur_row = 0
        self.cur_col = 0
        self.entity_switch_var = tk.IntVar()

        self.__setup_widgets()

    def __setup_widgets(self):

        self.bt_frame = tk.Frame(self)
        self.entity_switch_rb = tk.Checkbutton(self,
                                        text='html entity',
                                        variable=self.entity_switch_var)

        tk.Label(self, text=self.header).grid(row=0, column=0)
        self.bt_frame.grid(row=1, column=0)
        self.entity_switch_rb.grid(row=2, column=0)

    def def_chars(self, fn_obj):

        for c, e in (
            ('←', '&#8592;'), ('↑', '&#8593;'),
            ('→', '&#8594;'), ('↓', '&#8595;'),
            ('⁕', '&#8277;'), ('æ', '&#230;'),
            ('®', '&#174;'), ('½', '&#189;'),
            ('£', '&#163;'), ('§', '&#167;'),
            ('«', '&#171;'), ('»', '&#187;'),
            ('…', '&hellip;'), ('–', '&ndash;'),
            ('—', '&mdash;'), ('―', '&#8213;'),
            ('†', '&dagger;'), ('‡', '&Dagger;'),
            ('␣', '&nbsp;'), ('∅', '&empty;')
        ):
            self.add_char_bt(char=c,
                callback=self.get_char(fn_obj, char=c, htm_entity=e))
        
    def add_char_bt(self, char : str, callback=None):
        """Adds new button in a free row, column slot."""

        tk.Button(self.bt_frame,
                  text=char,
                  command=callback,
                  relief='flat').grid(row=self.cur_row, column=self.cur_col)

        if self.cur_col == self.no_of_cols - 1:
            self.cur_row += 1
            self.cur_col = 0
        else:
            self.cur_col += 1

    def get_char(self, fn_obj, char : str = 'c', htm_entity : str = None):
        """Takes a function-object as an argument and returns
        a callback function to be attached to a button.

        fn_obj - a callable that accepts string as an input."""

        def char_callback():
            if self.entity_switch_var.get() == 0:
                fn_obj(char)
            else:
                fn_obj(htm_entity)

        return char_callback


class IconButton(tk.Button):
    """Simplifies creating icon buttons."""

    def __init__(self, parent, icon_path, text=None,
                 command=None, *args, **kwargs):

        self.parent = parent

        try:
            self.icon_obj = tk.PhotoImage(file=icon_path)
        except tk.TclError as err:
            print("Error while creating button '{0}': {1}".format(text, err))
            self.icon_obj = None
        else:
            self.icon_path = icon_path

        tk.Button.__init__(self, parent, command=command,
                           relief='solid', text=text,
                           image=self.icon_obj, *args, **kwargs)


class EditHtml(tk.Frame):
    """Main editing tools and edit display-widget."""

    def __init__(self, parent, *args, **kwargs):

        tk.Frame.__init__(self, parent, *args, **kwargs)

        self.tool_tabs = ttk.Notebook(self)
        self.edit_field = EditField(self)

        main_tools = ToolBar(self)
        main_tools.standard_tools(self)
        self.tool_tabs.add(main_tools, text="Main tools")

        font_bar = ToolBar(self)
        font_bar.font(self)
        self.tool_tabs.add(font_bar, text="Edit font")    

        self.tool_tabs.pack(anchor='nw', side='top')
        self.edit_field.pack(anchor='sw', side='bottom',
                             expand=True, fill='both')


    def get_selection_indices(self):
        try:
            start_idx = self.edit_field.index('sel.first')
            end_idx = self.edit_field.index('sel.last')
        except tk.TclError:
            start_idx = end_idx = self.edit_field.index('insert')
        except Exception as e:
            print("Unexpected exception: ", e)

        return start_idx, end_idx


    def insert_tag(self, start_idx, end_idx,
                   opening_tag='tag',
                   closing_tag : bool = False,
                   opts : str = None):
        """Should be called for ex. that way:

        self.insert_tag(*self.get_selection_indices(),
                        opening_tag=opening_tag,
                        [closing_tag=True,
                        opts=tag_opts])
        """

        if closing_tag:
            end_tag = '</' + opening_tag + '>'
            self.edit_field.insert(end_idx, end_tag)

        if opts:
            opening_tag += ' ' + opts

        opening_tag = '<' + opening_tag + '>'
        self.edit_field.insert(start_idx, opening_tag)


    def dialog_insert_tag(self, dialog_obj, opening_tag,
                          closing_tag : bool = False, title='Tk Dialog'):

        options = dialog_obj(self, title).result

        if not options: return

        html_opts = str()

        for option in options.items():
            opt, val = option

            if val:
                html_opts += "{0}='{1}' ".format(opt, val)

        start_idx, end_idx = self.get_selection_indices()
        self.insert_tag(start_idx=start_idx, end_idx=end_idx,
                        opening_tag=opening_tag,
                        closing_tag=closing_tag,
                        opts=html_opts)


    def insert_comment(self):
        opening_tag = '<!-- '
        closing_tag = ' -->'

        start_idx, end_idx = self.get_selection_indices()

        self.edit_field.insert(end_idx, closing_tag)
        self.edit_field.insert(start_idx, opening_tag)


    def insert_formatting_tag(self, opening_tag, closing_tag : bool = False,
                   opts : str = None):
        """Customized insert_tag() to be attached as a callback.
        
        Should only be used when only simple tag insertions in
        editing viewport are needed (no additional dialog-boxes etc.)"""

        self.insert_tag(*self.get_selection_indices(),
                        opening_tag=opening_tag,
                        closing_tag=closing_tag, opts=opts)


    def insert_text(self, text : str):
        idx = self.edit_field.index('insert')
        self.edit_field.insert(idx, text)

    def get_contents(self) -> str:
        return self.edit_field.get('1.0', 'end-1c')

class ToolBar(tk.Frame):
    """Class for making tool-bars with html-tag buttons.

    Icons are either labelled as free to reuse
    or += require a link to the site they come from:
    - https://www.visualpharm.com/
    - https://www.iconarchive.com/
    - https://www.kindpng.com/
    - https://commons.wikimedia.org/
    - https://www.iconfinder.com/
    """

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)

        self.cur_widgets_col = 0
        self.widgets = list()
        self.user_widgets = list()


    def add_widget(self, widget, *pargs, **kwargs):
        self.widgets.append(widget(self, *pargs, **kwargs))
        self.widgets[-1].grid(row=0, column=self.cur_widgets_col,
                              sticky='nwse', padx=1)

        self.cur_widgets_col += 1


    def add_tool_buttons(self, *tools):
        for tool in tools:
            self.add_widget(IconButton, *tool)


    def separator(self):
        self.add_widget(ttk.Separator, orient=tk.VERTICAL)

    def standard_tools(self, edit_fld): # edit_fld-method/function only, instead of whole obj ref
        """copy, cut, paste, par, br, img, anchor, comment"""

        # ('path_to_icon', 'text', 'command')
        # better way to supply arguments: items[:4] ...

        self.add_tool_buttons(('icons/copy.png', 'Copy'),
                              ('icons/cut.png', 'Cut'),
                              ('icons/paste.png', 'Paste'))

        self.separator()

        self.add_tool_buttons(('icons/paragraph.png', 'P',
                                lambda: edit_fld.insert_formatting_tag(
                                    opening_tag='p', closing_tag=True)),

                               ('icons/newline.png', 'newline',
                                lambda: edit_fld.insert_formatting_tag(
                                    opening_tag='br /')),

                               ('icons/insert_img.png', 'img',
                                lambda: edit_fld.dialog_insert_tag(
                                    opening_tag = 'img',
                                    title = 'Insert image',
                                    dialog_obj = InsertImgDialog)
                               ),

                               ('icons/insert_hyperlink.png', 'anchor',
                                lambda: edit_fld.dialog_insert_tag(
                                    opening_tag = 'a',
                                    closing_tag = True,
                                    title = 'Insert hyperlink',
                                    dialog_obj = InsertHyperlinkDialog)
                               ))

        self.separator()

        self.add_tool_buttons(('icons/comment.png', '<!--',
                                edit_fld.insert_comment))


    def font(self, edit_fld):
        """b, u, i, s, font size up/down, font size, 

        To do: headers (as a drop-down menu)."""

        self.add_tool_buttons(('icons/bold_type.png', 'B',
                                lambda: edit_fld.insert_formatting_tag(
                                    opening_tag='b', closing_tag=True)),

                               ('icons/italic_type.png', 'I',
                                lambda: edit_fld.insert_formatting_tag(
                                    opening_tag='i', closing_tag=True)),

                               ('icons/strikethrough.png', 'S',
                                lambda: edit_fld.insert_formatting_tag(
                                    opening_tag='strike', closing_tag=True)),

                               ('icons/underline.png', 'U',
                                lambda: edit_fld.insert_formatting_tag(
                                    opening_tag='u', closing_tag=True)))

        self.separator()

        self.add_tool_buttons(('icons/font_size_increase.png', 'A^'),
                               ('icons/decrease_font.png', 'A_'),
                               ('icons/font_size.png', 'Aa'))


    def html_list(self):
        pass


    def table(self):
        pass


class MainTabs(ttk.Notebook):
    def __init__(self, parent, *args, **kwargs):

        ttk.Notebook.__init__(self, parent, *args, **kwargs)

        edit_tab_name = 'Edit Html'
        preview_tab_name = 'Preview'

        self.edit_html = EditHtml(self)
        self.html_view = HtmlPreview(self)

        self.add(self.edit_html, text=edit_tab_name)
        self.add(self.html_view, text=preview_tab_name)

        def on_tab_change(event_data):
            if self.tab(self.select())['text'] == preview_tab_name:
                self.html_view.preview(self.edit_html.get_contents())
                  

        self.bind("<<NotebookTabChanged>>", on_tab_change)


class MenuBar(tk.Menu):
    def __init__(self, parent, app):
        tk.Menu.__init__(self, parent)
        self.parent = parent

        # Space for defining menus:
        # File menu:
        self.file_menu = tk.Menu(self, tearoff=0)
        self.file_menu.add_command(label='Open',
                                   command=app.open_document)
        self.file_menu.add_command(label='Save',
                                   command=app.save_document)
        self.file_menu.add_command(label='Save as',
                                   command=app.save_document_as)
        self.file_menu.add_command(label='Exit',
                                   command=app._quit)

        # Space for adding menus to the menubar:
        self.add_cascade(label='File', menu=self.file_menu)


class MainApp(tk.Frame):
    def __init__(self, parent, path_to_doc = None):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.html_file_path = None
        self.app_name = 'Basic HTML Editor'

        parent.menu = MenuBar(parent, self)
        parent.config(menu=parent.menu)
        self._arrange_subframes()

        if path_to_doc:
            self.open_document(path_to_doc)
        self.set_mw_title()

    def _arrange_subframes(self):
        self.spc_frame = SpecialCharactersFrame(self,
                                                'Special characters:',
                                                cols=3)
        self.main_tabs = MainTabs(self)
        self.spc_frame.def_chars(self.main_tabs.edit_html.insert_text)

        self.spc_frame.grid(row=0, column=0, sticky='nw')
        self.main_tabs.grid(row=0, column=1, sticky='nwse')
        tk.Grid.columnconfigure(self.parent, 1, weight=1)
        tk.Grid.rowconfigure(self.parent, 0, weight=1)
        self.grid()

    def open_document(self, path=None):
        if path:
            filename = path
        else:
            filename = fd.askopenfilename(
                initialdir='~/Dokumenty/Programy/kurs_html_css/',
                title='Select file')
        try:
            self.main_tabs.edit_html.edit_field.load_doc(filename)
        except TextFieldModified:
            MainApp(tk.Toplevel(), filename)
        except IOError:
            messagebox.showerror(title='I/O Error',
                                 message='Error while attempting '+ 
                                 'to load file.')
        else:
            self.html_file_path = filename

    def _save_doc(self, path=None):
        '''Helper for save_document and save_document_as.'''
        pass

    def save_document(self):
        if not self.main_tabs.edit_html.edit_field.edit_modified(): return

    def save_as_decorator(self, fn):
        pass

    def save_document_as(self, fn):
        file_path = fd.asksaveasfilename()
        if file_path:
            try:
                self._save_doc(file_path)
            except IOError:
                messagebox.showerror(title='Error',
                    message='Error while attempting to save file.')
            else:
                self.html_file_path = file_path
                self.main_tabs.edit_html.edit_field.edit_modified(False)

    def set_mw_title(self):
        if self.html_file_path:
            title_addon = ' - ' + os.path.basename(self.html_file_path)
        else:
            title_addon = ' - new document'

        self.parent.title(self.app_name + title_addon)

    def _quit(self):
        self.master.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    app = MainApp(root)
    tk.mainloop()

