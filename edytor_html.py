import io
import sys
import tkinter as tk
import urllib
from utils import *
from dialogs import *
from urllib.request import urlopen
from tkinter import ttk
from HtmlText import *
from tkinter.scrolledtext import ScrolledText
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
    """Html file (very basic) preview frame that can be embedded in a
    separate tab. Requires tkhtml to work."""

    # To do: hyperlinks don't work (and I probably won't be able
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
            print("{0}: internal exception:".format(self.__class__.__name__),
                  e, file=sys.stderr)
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
            #print("Error while creating button '{0}': {1}".format(text, err))
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

        s = ttk.Style()
        s.configure('bottomtab.TNotebook', tabposition='se')

        self.tool_tabs = ttk.Notebook(self)
        self.edit_field = HtmlText(self)
        self.wrapped = self.edit_field

        main_tools = StandardTools(self)
        page_struct_bar = PageStructureBar(self)
        font_bar = FontTools(self)
        table_bar = TableBar(self)
        list_bar = ListTab(self)
        semantic_tags = SemanticTags(self)
        html5_tags = HTML5Tags(self)
        form_bar = FormTab(self)

        for bar, txt in (
                (main_tools, 'Main tools'),
                (page_struct_bar, 'Page structure'),
                (font_bar, 'Text formatting'),
                (table_bar, 'Table'),
                (list_bar, 'Lists'),
                (semantic_tags, 'Semantic tags'),
                (html5_tags, 'HTML5 tags'),
                (form_bar, 'Form')):
            self.tool_tabs.add(bar, text=txt)

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

    def insert_tag(self, start_idx, end_idx, opening_tag,
                   start_txt='', end_txt='', closing_tag : bool = False,
                   opts : str = None):
        """
        start_idx-where opening tag should start
        end_idx-where closing tag should start
        content-optional text put between tags only if end-tag
        is present
        start_txt, end_txt - text after initial/before end tag

        Should be called this way:

        self.insert_tag(*self.get_selection_indices(),
                        opening_tag=opening_tag,
                        [closing_tag=True,
                        opts=tag_opts])
        """

        if closing_tag:
            end_tag = end_txt + '</' + opening_tag + '>'
            self.edit_field.insert(end_idx, end_tag)
        if opts:
            opening_tag += ' ' + opts
        opening_tag = '<' + opening_tag + '>' + start_txt
        self.edit_field.insert(start_idx, opening_tag)

    def insert_doctype(self):
        dtype_dialog = InsertDoctypeDialog(self, title='Insert doctype')

        if dtype_dialog.result:
            self.insert('1.0', dtype_dialog.result)

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
                          closing_tag : bool=False, title='Tk Dialog', **kwargs):
        options = dialog_obj(self, title).result
        if not options: return
        html_opts = str()

        for option in options.items():
            opt, val = option
            if val:
                html_opts += '{0}="{1}" '.format(opt, val)

        start_idx, end_idx = self.get_selection_indices()
        self.insert_tag(
            start_idx=start_idx, end_idx=end_idx, opening_tag=opening_tag,
            closing_tag=closing_tag, opts=html_opts, **kwargs)

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
    Details in the resources module.
    """

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)

        self.parent = parent
        self.cur_widgets_col = 0
        self.widgets = list()
        self.user_widgets = list()

        self.tools()

    def tag(self, tag_name, cnt='\n', **kwargs):
        "opening/closing tags with two spaces between"

        return lambda: self.parent.insert_tag(
            *self.parent.get_selection_indices(), tag_name,
            closing_tag=True, start_txt=cnt, end_txt=cnt, **kwargs)

    def ctag(self, tag_name, **kwargs):
        "inline opening and _c_losing tags"

        return lambda: self.parent.insert_tag(
            *self.parent.get_selection_indices(), tag_name,
            closing_tag=True, **kwargs)

    def stag(self, tag_name, **kwargs):
        "inline _s_ingle closed <tag />"

        return lambda: self.parent.insert_formatting_tag(
            opening_tag=tag_name, **kwargs)

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
        "implemented in derived classes"
        pass

class PageStructureBar(ToolBar):
    def tools(self):
        self.add_tool_buttons(
            (None, '!doc', self.parent.insert_doctype),
            (None, 'html', self.tag('html')),
            (None, 'head', self.tag('head')),
            (None, 'style', self.tag('style', opts='type="text/css"')),
            (None, 'title', self.ctag('title')),
            (None, 'body', self.tag('body')))


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
            ('icons/undo_icon.png', 'Undo',
             self.parent.main_tabs.edit_html.edit_undo),
            ('icons/redo_icon.png', 'Redo',
             self.parent.main_tabs.edit_html.edit_redo))

        self.separator()

        self.add_tool_buttons(
            ('icons/search.png', 'Search', self.parent.find_text),
            ('icons/globe_icon.png', 'Browser', self.parent.view_in_browser))


class StandardTools(ToolBar):
    def tools(self):
        "par, br, img, anchor, comment"

        # ('path_to_icon', 'text', 'command')
        # better way to supply arguments: items[:4] ...

        self.add_tool_buttons(
            ('icons/paragraph.png', 'P', self.ctag('p')),
            ('icons/newline.png', 'newline', self.stag('br /')),
            ('icons/div_icon.png', 'div', self.ctag('div', opts='class=""')),
            ('icons/span.png', 'span', self.ctag('span', opts='class=""')),
            ('icons/hr.png', 'hr', self.stag('hr /')),

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
            (None, 'table', self.tag('table')),
            (None, 'row',self.ctag('tr')),
            (None, 'th', self.ctag('th')),
            (None, 'td', self.ctag('td')))


class FontTools(ToolBar):
    def tools(self):
        self.add_tool_buttons(
            ('icons/bold_type.png',     'B',self.ctag('b')),
            ('icons/italic_type.png',   'I',self.ctag('i')),
            ('icons/strikethrough.png', 'S',self.ctag('strike')),
            ('icons/underline.png',     'U',self.ctag('u')))

        self.separator()

        self.add_tool_buttons(
            ('icons/superscript.png', 'sup',self.ctag('sup')),
            ('icons/subscript.png', 'sub',self.ctag('sub')))

        # Headers (h1-h6) drop-down:
        #
        option = tk.StringVar()
        headers = {'Header '+str(h): 'h'+str(h) for h in range(1, 7)}
        option.set('Header 1')

        self.add_widget(
            tk.OptionMenu, option, *headers,
            command=lambda header: self.parent.insert_formatting_tag(
                opening_tag=headers[header], closing_tag=True))


class ListTab(ToolBar):
    def tools(self):
        self.add_tool_buttons(
            (None, 'ul', self.tag('ul')),
            (None, 'ol', self.tag('ol')),
            (None, 'li', self.ctag('li')))

        self.separator()

        self.add_tool_buttons(
            (None, 'dl', self.tag('dl')),
            (None, 'dd', self.ctag('dd')),
            (None, 'dt', self.ctag('dt')))

class SemanticTags(ToolBar):
    def tools(self):
        self.add_tool_buttons(
            (None, 'strong', self.ctag('strong')),
            ('icons/exclamation.png', 'em',self.ctag('em')),

            (None, 'blockquote', lambda:
             self.parent.insert_tag(
                 *self.parent.get_selection_indices(), 'blockquote',
                 closing_tag=True, start_txt='\n<p>', end_txt='</p>\n')),

            (None, 'q', self.ctag('q', opts='cite=""')),
            (None, 'cite', self.ctag('cite')),
            (None, 'abbr', self.ctag('abbr', opts='title=""')),
            (None, 'dfn', self.ctag('dfn')),
            (None, 'addr', self.ctag('address')),
            (None, 'del', self.ctag('del')),
            (None, 'ins', self.ctag('ins')),
            (None, 's', self.ctag('s')))


class FormTab(ToolBar):
    def tools(self):

        def dialog_generator(inputs, booleans, tag, title=None):
            # The dialog is called in the following way:
            # CollectValues(
            # self, parent, booleans=[], inputs=[], title = None)

            return (
                None, tag,
                lambda: self.parent.dialog_insert_tag(
                    dialog_obj=lambda parent, title: CollectValues(
                        parent=parent, title=title,
                        inputs=inputs, booleans=booleans),

                    title=title, opening_tag=tag,
                    closing_tag=True, start_txt='\n', end_txt='\n'))

        sel_inputs = [
            (tk.Entry, ('form', 'name')),
            (lambda parent: tk.Spinbox(
                parent, from_=1, to=100, increment=1, width=6), ('size',))]

        sel_booleans = ('autofocus', 'disabled', 'multiple', 'required')

        self.add_tool_buttons(
            (None, 'form',
             lambda: self.parent.dialog_insert_tag(
                 dialog_obj=InsertForm, opening_tag='form',
                 closing_tag=True, title='Insert form',
                 start_txt='\n', end_txt='\n')),

            dialog_generator(
                sel_inputs, sel_booleans, 'select', title='Insert select tag:'),

            (None, 'textarea',
             lambda: self.parent.dialog_insert_tag(
                 dialog_obj=InsertTextarea, opening_tag='textarea',
                 closing_tag=True, title='Insert textarea',
                 start_txt='\n', end_txt='\n')),

            dialog_generator(
                [(tk.Entry, ('form', 'name'))], ['disabled'], 'fieldset',
                title='Insert fieldset:'),

            (None, 'legend', self.ctag('legend')),
            (None, 'button', self.ctag('button', opts='type="button"')),
            (None, 'option', self.ctag('option', opts='value=""')),
            (None, 'opt_gr', self.tag('optgroup', opts='label=""')),
            (None, 'label', self.ctag('label', opts='for=""')))

class HTML5Tags(ToolBar):
    def tools(self):
        self.add_tool_buttons(
            (None, 'aside', self.ctag('aside')),
            (None, 'nav', self.ctag('nav')),
            (None, 'article', self.ctag('article')),
            (None, 'section', self.ctag('section')))


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
