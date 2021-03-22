import io
import sys
import pathlib
import tkinter as tk
import urllib
from utils import *
from urllib.request import urlopen
from tkinter import ttk
from tkinter import filedialog as fd
from HtmlText import *
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
from tkSimpleDialog import Dialog
from PIL import Image, ImageTk

file_types = (
    ('Html files', ('.htm', '.html')),
    ('Text files', '.txt'),
    ('All files', '*'))

def get_ev_cb(obj, event : str):
    '''Get event callback
    Returns callback for tkinter events such as cut, copy, paste.
    obj - tkinter class instance with focus_get() method'''
    return lambda: obj.focus_get().event_generate(event)

class UnsavedDocument(Exception): pass
class DocumentSaveCancelled(UnsavedDocument): pass
class BreakLoop(Exception): pass

class HtmlPreview(tk.Frame):
    """Allows previewing html within a frame that can be embedded in a
    separate tab. Requires tkhtml to work."""

    # To do: hyperlinks don't work (and I probably won't  be able
    # to fix that).

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
            self.preview_frame = TkinterHtml(
                self, imagecmd=self._load_image)
        self._setup_preview()

    def _setup_preview(self):
        scrollbar = tk.Scrollbar(self)
        self.preview_frame.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.preview_frame.yview)

        self.preview_frame.grid(row=0, column=0, sticky='wsne')
        scrollbar.grid(row=0, column=1, sticky='wsne')
        tk.Grid.columnconfigure(self, 0, weight=1)
        tk.Grid.rowconfigure(self, 0, weight=1)

    def _load_image(self, url):
        try:
            fp = urlopen(url)
        except (ValueError, FileNotFoundError, urllib.error.URLError) as e:
            print("Internal exception:", e, file=sys.stderr)
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

                preview_lbl.configure(
                    width=img_width, height=img_height, image=preview_lbl.img)
            else:
                preview_lbl.configure(preview_def_size)

        def img_browse_callback():
            path_to_image = fd.askopenfilename(filetypes=(
                ('Images', ('.jpg','.jpeg', '.png', '.gif')),
                ('All files', '*')
            ))

            if not path_to_image: return

            self.path_to_image = path_to_image
            image_file_name = base_file_name(self.path_to_image)
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

        # TODO: use loops to put widgets in a form:

        tk.Label(parent, text='Path:').grid(row=1)
        self.img_path_ent = tk.Entry(
            parent, textvariable = self.img_path, state='readonly')
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


class InsertTableDialog(Dialog):
    def body(self, master):
        tk.Label(master, text='Rows:').grid(row=0, column=0)
        tk.Label(master, text='Columns:').grid(row=1, column=0)

        self.rows_counter = tk.Spinbox(master, from_ = 1, to=100, increment=1)
        self.rows_counter.grid(row=0, column=1)

        self.cols_counter = tk.Spinbox(master, from_ = 1, to=100, increment=1)
        self.cols_counter.grid(row=1, column=1)

    def collect_vals(self):
        return self.rows_counter.get(), self.cols_counter.get()

    def validate(self):
        rows, cols = self.collect_vals()

        for v in rows, cols:
            if not v.isdigit():
                print('not a digit:', v)
                return False

        return True

    def apply(self):
        self.result = tuple(int(v) for v in self.collect_vals())

class InsertHyperlinkDialog(Dialog):
    def body(self, master):
        tk.Label(master, text='Target:').grid(row=0, column=0)
        self.target_ent = tk.Entry(master)
        self.target_ent.grid(row=0, column=1)

        tk.Label(master, text='Style:').grid(row=1, column=0)
        self.style_ent = tk.Entry(master)
        self.style_ent.grid(row=1, column=1)

    def apply(self):
        self.result = {
            'target' : str(self.target_ent.get()),
            'style'  : str(self.style_ent.get())
        }

class SpecialCharactersFrame(tk.Frame):
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
        """Adds a new button in a free row/column slot."""
        tk.Button(
            self.bt_frame, text=char, command=callback, relief='flat').grid(
                row=self.cur_row, column=self.cur_col)

        if self.cur_col == self.no_of_cols - 1:
            self.cur_row += 1
            self.cur_col = 0
        else:
            self.cur_col += 1

    def get_char(self, fn_obj, char : str = 'c', htm_entity : str = None):
        """Returns callbacks for buttons.
        fn_obj - callable that accepts string as an input."""
        def char_callback():
            if self.entity_switch_var.get() == 0:
                fn_obj(char)
            else:
                fn_obj(htm_entity)
        return char_callback

class IconButton(tk.Button):
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
        self.edit_field = HtmlText(self)
        self.wrapped = self.edit_field

        main_tools = StandardTools(self)
        font_bar = FontTools(self)
        table_bar = TableBar(self)

        self.tool_tabs.add(main_tools, text="Main tools")
        self.tool_tabs.add(font_bar, text="Text formatting")
        self.tool_tabs.add(table_bar, text="Table")

        self.tool_tabs.grid(row=0, column=0, sticky='w')
        self.edit_field.grid(row=1, column=0, sticky='nwse')
        tk.Grid.columnconfigure(self, 0, weight=1)
        tk.Grid.rowconfigure(self, 1, weight=1)

        self.bind('Control-Key-a', )

    __getattr__ = getattr_wrapper()

    def get_selection_indices(self):
        try:
            start_idx = self.edit_field.index('sel.first')
            end_idx = self.edit_field.index('sel.last')
        except tk.TclError:
            start_idx = end_idx = self.edit_field.index('insert')

        return start_idx, end_idx

    def insert_tag(self, start_idx, end_idx, opening_tag, content='',
                   closing_tag : bool = False, opts : str = None):
        """
        start_idx-where opening tag should start
        end_idx-where closing tag should start
        content-optional text put between tags only if end-tag
        is present

        Should be called this way:

        self.insert_tag(*self.get_selection_indices(),
                        opening_tag=opening_tag,
                        [closing_tag=True,
                        content='text',
                        opts=tag_opts])
        """

        if closing_tag:
            end_tag = '</' + opening_tag + '>'
            self.edit_field.insert(end_idx, end_tag)
            if content:
                self.edit_field.insert(end_idx, content)
        if opts:
            opening_tag += ' ' + opts
        opening_tag = '<' + opening_tag + '>'
        self.edit_field.insert(start_idx, opening_tag)

    def table_creator(self):
        table_dialog = InsertTableDialog(self)
        if table_dialog.result:
            self.insert_table(*table_dialog.result)

    def insert_table(self, rows, cols):
        init_idx = self.index('insert')

        self.insert(init_idx, '</table>')

        for _ in range(0, rows):
            self.insert(init_idx, '</tr>\n')
            self.insert(init_idx, '<td></td>\n'*cols)
            self.insert(init_idx, '<tr>\n')

        self.insert(init_idx, '<table id="">\n')
 
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
        self.insert_tag(
            start_idx=start_idx, end_idx=end_idx, opening_tag=opening_tag,
            closing_tag=closing_tag, opts=html_opts)

    def insert_startendtag(self, opening_tag, closing_tag, start_idx, end_idx):
        for item in ((end_idx, closing_tag), (start_idx, opening_tag)):
            self.edit_field.insert(*item)

    def insert_formatting_tag(self, opening_tag, closing_tag : bool = False,
                   opts : str = None):
        """Customized insert_tag() to be attached as a callback.
        
        Should only be used when only simple tag insertions in
        editing viewport are needed (no additional dialog-boxes etc.)"""

        self.insert_tag(*self.get_selection_indices(),
                        opening_tag=opening_tag,
                        closing_tag=closing_tag, opts=opts)

    def insert_text(self, text):
        idx = self.edit_field.index('insert')
        self.edit_field.insert(idx, text)

    def get_contents(self) -> str:
        # Move into HtmlText
        return self.edit_field.get('1.0', 'end-1c')

class ToolBar(tk.Frame):
    """Class for making tool-bars with html-tag buttons.

    Icons are either labelled as free to reuse or reused
    with attribution (as noted in a licence).
    Details in a resources module.
    """

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)

        self.parent = parent
        self.cur_widgets_col = 0
        self.widgets = list()
        self.user_widgets = list()

        self.tools()

    def add_widget(self, widget, *pargs, padx=1, **kwargs):
        self.widgets.append(widget(self, *pargs, **kwargs))
        self.widgets[-1].grid(
            row=0, column=self.cur_widgets_col, sticky='nwse', padx=padx)
        self.cur_widgets_col += 1

    def print_widgets_info(self):
        for wdg in self.widgets:
            #print('Wdg name:', wdg.__name__)
            print('Wdg height:', wdg.winfo_height())
            print('-'*30)

    def add_tool_buttons(self, *tools):
        for tool in tools:
            self.add_widget(IconButton, *tool)

    def separator(self):
        self.add_widget(ttk.Separator, orient=tk.VERTICAL, padx=3)

    def tools(self):
        "To be implemented in derived classes."
        pass


class MainToolBar(ToolBar):
    '''Top bar with buttons for the following commands:
    open, save, save as, copy/cut/paste, undo, redo, view in browser'''

    def tools(self):
        self.add_tool_buttons(
            ('icons/folder_open.png', 'Open', self.parent.open_document),
            ('icons/save_file.png', 'Save', self.parent.save_document),
            ('icons/save_as.png', 'Save as', self.parent.save_document_as))

        self.separator()

        self.add_tool_buttons(
            ('icons/copy.png', 'Copy', get_ev_cb(self.parent, '<<Copy>>')),
            ('icons/cut.png', 'Cut', get_ev_cb(self.parent, '<<Cut>>')),
            ('icons/paste.png', 'Paste', get_ev_cb(self.parent,'<<Paste>>')))

        self.separator()

        self.add_tool_buttons(
            ('icons/undo_icon.png', 'Undo', self.parent.main_tabs.edit_html.edit_undo),
            ('icons/redo_icon.png', 'Redo', self.parent.main_tabs.edit_html.edit_redo))

        self.separator()

        self.add_tool_buttons(
            ('icons/search.png', 'Search', self.parent.find_text),
            ('icons/globe_icon.png', 'Browser', self.parent.view_in_browser))


class StandardTools(ToolBar):
    def tools(self):
        '''par, br, img, anchor, comment'''

        # ('path_to_icon', 'text', 'command')
        # better way to supply arguments: items[:4] ...

        self.add_tool_buttons(
            ('icons/paragraph.png', 'P',
             lambda: self.parent.insert_formatting_tag(
                 opening_tag='p', closing_tag=True)),

            ('icons/newline.png', 'newline',
             lambda: self.parent.insert_formatting_tag(
                 opening_tag='br /')),

            ('icons/div_icon.png', 'div',
             lambda: self.parent.insert_formatting_tag(
                 opening_tag='div', closing_tag=True, opts='class=""')),

            ('icons/span.png', 'span',
             lambda: self.parent.insert_formatting_tag(
                 opening_tag='span', closing_tag=True, opts='class=""')),

            ('icons/hr.png', 'hr',
             lambda: self.parent.insert_formatting_tag(
                 opening_tag='hr /')),

            ('icons/insert_img.png', 'img',
             lambda: self.parent.dialog_insert_tag(
                 opening_tag = 'img', title = 'Insert image',
                 dialog_obj = InsertImgDialog)),

            ('icons/insert_hyperlink.png', 'anchor',
             lambda: self.parent.dialog_insert_tag(
                 opening_tag = 'a', closing_tag = True,
                 title = 'Insert hyperlink',
                 dialog_obj = InsertHyperlinkDialog)))

        self.separator()

        self.add_tool_buttons(
            ('icons/comment.png', '<!-',
             lambda: self.parent.insert_startendtag(
                 '<!-- ', ' -->', *self.parent.get_selection_indices())))


class TableBar(ToolBar):
    def tools(self):
        "Table creator (dialog), table, tr, th, td."

        self.add_tool_buttons(
            (None, 'table_creator', self.parent.table_creator))

        self.separator()

        self.add_tool_buttons(
            (None, 'table',
             lambda: self.parent.insert_tag(
                 *self.parent.get_selection_indices(),
                 content='\n', opening_tag='table', closing_tag=True)),

            (None, 'row',
             lambda: self.parent.insert_formatting_tag(
                 opening_tag='tr', closing_tag=True)),

            (None, 'th',
             lambda: self.parent.insert_formatting_tag(
                 opening_tag='th', closing_tag=True)),

            (None, 'td',
             lambda: self.parent.insert_formatting_tag(
                 opening_tag='td', closing_tag=True)))


class FontTools(ToolBar):
    def tools(self):
        """
        b, u, i, s, font size up/down, set font size, 
        To do: headers (as a drop-down menu).
        """

        self.add_tool_buttons(
            ('icons/bold_type.png', 'B',
             lambda: self.parent.insert_formatting_tag(
                 opening_tag='b', closing_tag=True)),

            ('icons/italic_type.png', 'I',
             lambda: self.parent.insert_formatting_tag(
                 opening_tag='i', closing_tag=True)),

            ('icons/strikethrough.png', 'S',
             lambda: self.parent.insert_formatting_tag(
                 opening_tag='strike', closing_tag=True)),

            ('icons/underline.png', 'U',
             lambda: self.parent.insert_formatting_tag(
                 opening_tag='u', closing_tag=True)))

        self.separator()

        self.add_tool_buttons(
            ('icons/exclamation.png', 'em',
             lambda: self.parent.insert_formatting_tag(
                 opening_tag='em', closing_tag=True)),

            ('icons/superscript.png', 'sup',
             lambda: self.parent.insert_formatting_tag(
                 opening_tag='sup', closing_tag=True)),

            ('icons/subscript.png', 'sub',
             lambda: self.parent.insert_formatting_tag(
                 opening_tag='sub', closing_tag=True)))

        # Headers (h1-h6) drop-down:
        #
        option = tk.StringVar()
        headers = {'Header '+str(h): 'h'+str(h) for h in range(1, 7)}
        option.set('Header 1')

        self.add_widget(
            tk.OptionMenu, option, *headers,
            command=lambda header: self.parent.insert_formatting_tag(
                opening_tag=headers[header], closing_tag=True))

class MainTabs(ttk.Notebook):
    def __init__(self, parent, *args, **kwargs):
        ttk.Notebook.__init__(self, parent, *args, **kwargs)

        self.edit_tab_name = 'Edit Html'
        self.preview_tab_name = 'Preview'

        self.edit_html = EditHtml(self)
        self.html_view = HtmlPreview(self)

        self.add(self.edit_html, text=self.edit_tab_name)
        self.add(self.html_view, text=self.preview_tab_name)

        self.bind("<<NotebookTabChanged>>", self.on_tab_change)

    def on_tab_change(self, event_data):
        if self.tab(self.select())['text'] == self.preview_tab_name:
            self.html_view.preview(self.edit_html.get_contents())

class MenuBar(tk.Menu):
    def __init__(self, parent, app):
        tk.Menu.__init__(self, parent)
        self.parent = parent
        self.app = app

        # Space for defining menus:
        for menu in 'file_menu', 'edit_menu', 'document_menu', 'help_menu':
            setattr(self, menu, tk.Menu(self))

        menus = (
            (self.file_menu,                        # parent-menu
             ('Open', 'Save', 'Save as', 'Exit'),   # label
             ('Ctrl+O', 'Ctrl+S', None, 'Ctrl+Q'),  # accelerator
             (app.open_document, app.save_document, # command
              app.save_document_as, app._quit)),

            (self.edit_menu,
             ('Undo', 'Redo', 'Select all', 'Copy', 'Cut', 'Paste'),
             ('Ctrl+Z', 'Shift+Ctrl+Z', 'Ctrl+A', 'Ctrl+C', 'Ctrl+X', 'Ctrl+V'),
             (app.main_tabs.edit_html.edit_undo,
              app.main_tabs.edit_html.edit_redo,
              app.main_tabs.edit_html.select_all,
              get_ev_cb(self.app, "<<Copy>>"), get_ev_cb(self.app, "<<Cut>>"),
              get_ev_cb(self.app, "<<Paste>>"))),

             (self.document_menu,
              ('Find text', 'Replace text', 'View in browser'),
              ('Ctrl+F', 'Ctrl+R', None),
              (app.find_text, app.replace_text, app.view_in_browser)))

        for menu in menus:
            for (label, acc, cmd) in zip(*menu[1:]):
                menu[0].add_command(label=label, accelerator=acc, command=cmd)

        self.help_menu.add_command(label='About')

        # Adding menus to the menubar:
        for lbl, menu in zip(
                ('File', 'Edit', 'Document', 'Help'),
                (self.file_menu, self.edit_menu,
                 self.document_menu, self.help_menu)):
            self.add_cascade(label=lbl, menu=menu)


class SearchTextDialog(Dialog):
    def __init__(self, master, txt_fld : tk.Text):
        for attr in 'direction', 'mode', 'case':
            setattr(self, attr, tk.IntVar())

        self.last_idx = txt_fld.index(tk.INSERT)

        self.txt_field_ref = txt_fld
        txt_fld.tag_configure('highlight', background='blue', foreground='white')

        Dialog.__init__(self, master, title='Search phrase:')

    def body(self, master):
        for col, name in zip(range(0, 3), ('Direction:', 'Mode:', 'Case:')):
            tk.Label(master, text=name).grid(column=col, row=0)

        col = 0
        for names, var in ((('forward', 'backward'), self.direction),
                           (('exact', 'regexp'), self.mode),
                           (('case', 'nocase'), self.case)):
            for row, name in zip(range(1, 3), names):
                val = row - 1
                tk.Radiobutton(master, text=name, variable=var,
                               value=val).grid(column=col, row=row)
            col += 1

        self.entry_text = tk.StringVar()
        tk.Label(master, text='Search for:').grid(column=0, row=3)
        entry = tk.Entry(master, width=30, textvariable=self.entry_text)
        entry.grid(column=1, row=3, columnspan=3)

        return entry

    def buttonbox(self):
        Dialog.buttonbox(self)
        self.ok_bt.configure(text='Search')
        self.cancel_bt.configure(text='Close')

    def ok(self, event=None):
        self.search_text()

    def get_word_end_index(self, init_idx, text_len):
        '''Returns outer bound of a given phrase in the form
        of a tk.Text index: line.column.'''
        return self.txt_field_ref.index('{0}+{1}c'.format(
            init_idx, text_len))

    def clear_tags(self):
        self.txt_field_ref.tag_remove('highlight', '1.0', tk.END)

    def highlight_text(self, start_idx, end_idx):
        self.txt_field_ref.tag_add('highlight', start_idx, end_idx)

    def highlight_make_visible(self, found_text_idx, last_idx):
        self.highlight_text(found_text_idx, last_idx)
        self.bring_index_up(found_text_idx)

    def _search_text(self, search_txt, direction,
                    mode, case, start_idx, stop_idx=None):
        '''Returns indexes marking search phrase bounds if successes.
        None otherwise.'''

        # Put all search code into UML diagrams.
        # merge into search_text()

        found_text_idx = self.txt_field_ref.search(
            search_txt, start_idx, stop_idx, forwards=direction,
            backwards=direction, exact=mode, regexp=mode, nocase=case)

        if found_text_idx:
            self.clear_tags()
            self.last_idx = '{0}+{1}c'.format(found_text_idx, len(search_txt))
            self.txt_field_ref.mark_set('insert', found_text_idx)
            self.highlight_make_visible(found_text_idx, self.last_idx)

            return found_text_idx, self.last_idx

    def get_form_values(self):
        return (self.entry_text.get(),
                self.direction.get(),
                self.mode.get(),
                self.case.get())

    def get_start_stop_idx(self, direction):
        '''Returns indexes needed by search methods
        for seeking through contents of the tk.Text.'''
        if direction == 0: # forward search
            start_idx = self.last_idx
            stop_idx = tk.END
        else:
            start_idx = self.txt_field_ref.index(tk.INSERT)
            stop_idx = '1.0'

        return start_idx, stop_idx
        
    def search_text(self):
        (entry_text, direction, mode, case, *other) = self.get_form_values()
        if not entry_text: return

        start_idx, stop_idx = self.get_start_stop_idx(direction)
        found_text_idxs = self._search_text(entry_text, direction,
                                            mode, case, start_idx, stop_idx)

        if not found_text_idxs and direction == 0:
            self.ask_to_restart_search(direction)
        elif not found_text_idxs:
            print(found_text_idxs, direction)
            messagebox.showinfo(
                parent=self, title='End of backward search',
                message='You reached the beginning of the document.')

    def bring_index_up(self, idx):
        '''Moves the view into the position of a given index.'''
        self.txt_field_ref.see(idx)

    def cancel(self, event=None):
        self.clear_tags()
        Dialog.cancel(self, event)

    def ask_to_restart_search(self, direction):
        decision = messagebox.askyesno(
            parent=self, title='End of search',
            message='Do you want to restart search?')

        if decision == True:
            if direction == 0:
                self.last_idx = '1.0'
            else:
                self.last_idx = tk.END
            self.ok()

class ReplaceTextDialog(SearchTextDialog):
    def __init__(self, *pargs, **kwargs):
        SearchTextDialog.__init__(self, *pargs, **kwargs)

    def body(self, master):
        focus = SearchTextDialog.body(self, master)

        tk.Label(master, text='Replace with:').grid(column=0, row=4)
        self.replace_entry = tk.StringVar()
        replace_ent = tk.Entry(master, width=30, textvariable=self.replace_entry)
        replace_ent.grid(column=1, row=4, columnspan=3)

        self.replace_all_var = tk.IntVar()
        tk.Checkbutton(master, text='Replace all',
                       variable=self.replace_all_var).grid(column=1, row=5)

        return focus

    def get_form_values(self):
        return (SearchTextDialog.get_form_values(self)
                + (self.replace_entry.get(),))

    def phrase_replacer(self, idx_1, idx_2, new_phrase):
        self.txt_field_ref.delete(idx_1, idx_2)
        self.txt_field_ref.insert(idx_1, new_phrase)

    def replace_text(
            self, searched_text, mode, case, replace_txt,
            interactive_mode=False, direction=0,):
        '''Searches and replaces text from the current cursor position
        to the end of the document (noninteractive mode is default).'''

        start_idx, stop_idx = self.get_start_stop_idx(direction)
        found_text_len = tk.IntVar()
        end_text_idx = ''
        replaced_phrases_no = 0

        def _noninteractive_replace():
            nonlocal found_text_init_idx, end_text_idx
            nonlocal replace_txt, replaced_phrases_no

            self.phrase_replacer(
                found_text_init_idx, end_text_idx, replace_txt)
            end_text_idx = self.get_word_end_index(
                found_text_init_idx, len(replace_txt))
            replaced_phrases_no += 1

        def _interactive_replace():
            decision = messagebox.askyesnocancel(
                parent=self, title='Found phrase', message='Replace?')

            if decision == True:
                _noninteractive_replace()
            elif decision is None:
                raise BreakLoop

        while True:
            found_text_init_idx = self.txt_field_ref.search(
                searched_text, start_idx, stop_idx, count=found_text_len,
                backwards=direction, exact=mode, regexp=mode, nocase=case)

            if not found_text_init_idx:
                break

            end_text_idx = self.get_word_end_index(
                    found_text_init_idx, found_text_len.get())
            if interactive_mode:
                self.highlight_make_visible(found_text_init_idx, end_text_idx)
                try:
                    _interactive_replace()
                except BreakLoop:
                    break
                self.clear_tags()
            else:
                _noninteractive_replace()

            if direction == 0:
                start_idx = end_text_idx
            else:
                start_idx = found_text_init_idx

        title = 'Search and replace summary'
        if replaced_phrases_no:
            message = 'Number of changes made: {}.'.format(replaced_phrases_no)
        else:
            message = 'No changes have been made.'

        messagebox.showinfo(
            parent=self, title=title, message=message)

    def ok(self, event=None):
        (search_txt, direction,
         mode, case, replace_txt) = self.get_form_values()

        if not search_txt:
            return

        self.clear_tags()

        if self.replace_all_var.get():
            self.last_idx = '1.0'
            self.replace_text(searched_text=search_txt, mode=mode, case=case,
                              replace_txt=replace_txt)
        else:
            self.replace_text(
                search_txt, mode, case,
                replace_txt, direction=direction, interactive_mode=True)

if __name__ == '__main__':
    root = tk.Tk()
    table_dialog = InsertTableDialog(root)
    print(table_dialog.result)
    root.mainloop()
