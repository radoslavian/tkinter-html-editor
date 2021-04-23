import io
import sys
import tkinter as tk
import urllib
from widgets import *
from utils import *
from icons import icon
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
            'pip command-line tool:\n\npip install tkinterhtml')
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
            data   = fp.read()
            image  = Image.open(io.BytesIO(data))
            photo  = ImageTk.PhotoImage(image)

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
        self.entity_switch_rb = tk.Checkbutton(
            self, text='html entity', variable=self.entity_switch_var)

        tk.Label(self, text=self.header).grid(row=0, column=0)
        self.bt_frame.grid(row=1, column=0)
        self.entity_switch_rb.grid(row=2, column=0)

    def def_chars(self, fn_obj):
        "Special characters."

        for c, e in (
                ('←', '&#8592;'  ), ('↑', '&#8593;'),
                ('→', '&#8594;'  ), ('↓', '&#8595;'),
                ('⁕', '&#8277;'  ), ('æ', '&#230;'),
                ('®', '&#174;'   ), ('©', '&copy;'),
                ('½', '&#189;'   ), ('∅', '&empty;'),
                ('£', '&#163;'   ), ('¢', '&cent;'),
                ('¥', '&yen;'    ), ('€', '&euro;'),
                ('«', '&#171;'   ), ('»', '&#187;'),
                ('…', '&hellip;' ), ('–', '&ndash;'),
                ('—', '&mdash;'  ), ('―', '&#8213;'),
                ('†', '&dagger;' ), ('‡', '&Dagger;'),
                ('␣', '&nbsp;'   ), ('<', '&lt;'),
                ('>', '&gt;'     ), ('&', '&amp;'),
                ('"', '&quot;'   ), ("'", '&apos;'),
                ('§', '&#167;')
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


class EditHtml(tk.Frame):
    """Main editing tools and edit display-widget."""
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)

        s = ttk.Style()
        s.configure('bottomtab.TNotebook', tabposition='se')

        self.tool_tabs   = ttk.Notebook(self)
        self.edit_field  = HtmlText(self)
        self.wrapped     = self.edit_field

        main_tools       = StandardTools(self)
        page_struct_bar  = PageStructureBar(self)
        font_bar         = FontTools(self)
        table_bar        = TableBar(self)
        list_bar         = ListTab(self)
        semantic_tags    = SemanticTags(self)
        html5_tags       = HTML5Tags(self)
        form_bar         = FormTab(self)

        for bar, txt in (
                (main_tools,       'Main tools'),
                (page_struct_bar,  'Page structure'),
                (font_bar,         'Text formatting'),
                (table_bar,        'Table'),
                (list_bar,         'Lists'),
                (semantic_tags,    'Semantic tags'),
                (html5_tags,       'HTML5 tags'),
                (form_bar,         'Form')):
            self.tool_tabs.add(bar, text=txt)

        self.tool_tabs.grid(row=0, column=0, sticky='w')
        self.edit_field.grid(row=1, column=0, sticky='nwse')
        tk.Grid.columnconfigure(self, 0, weight=1)
        tk.Grid.rowconfigure(self, 1, weight=1)

        self.bind('Control-Key-a', )

    __getattr__ = getattr_redirect

    def focus_set(self):
        self.edit_field.focus_set()

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
            opening_tag += ' ' + opts.rstrip()
        opening_tag = '<' + opening_tag + '>' + start_txt
        self.edit_field.insert(start_idx, opening_tag)

    def insert_doctype(self):
        dtype_dialog = InsertDoctypeDialog(self, title='doctype')

        if dtype_dialog.result:
            self.insert('1.0', dtype_dialog.result)

    def table_creator(self):
        fields = ('rows', 'columns')

        table = CollectValues(
            self, 'Insert table:', inputs=[
                (lambda parent:
                 tk.Spinbox(parent, from_=1, to=300), fields)])

        if table.result:
            self.insert_table(*(int(table.result[v]) for v in fields))

    def insert_table(self, rows, cols):
        init_idx = self.index('insert')

        self.insert(init_idx, '</table>')

        for _ in range(0, rows):
            self.insert(init_idx, '</tr>\n')
            self.insert(init_idx, '<td></td>\n'*cols)
            self.insert(init_idx, '<tr>\n')

        self.insert(init_idx, '<table id="">\n')
 
    def dialog_insert_tag(self, dialog_obj, opening_tag,
                          closing_tag : bool=False, title='Insert html tag:',
                          opts=None, **kwargs):
        options = dialog_obj(self, title).result
        if not options: return
        html_opts = str()

        if opts:
            html_opts += opts

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

    def sel_menu_target(self, parent):
        '''Returns predefined SelectMenu (tk.OptionMenu)
        to be used for dynamic created dialogs.'''

        return SelectMenu(parent, '', '_self', '_blank', '_parent', '_top')

    def formmethod(self, parent):
        "Predefined SelectMenu to be used for eg. in form dialog."
        return SelectMenu(parent, '', 'get', 'post')

    def tag_f(self, tag_name, cnt='\n', **kwargs):
        self.parent.insert_tag(
            *self.parent.get_selection_indices(), tag_name,
            closing_tag=True, start_txt=cnt, end_txt=cnt, **kwargs)

    def ctag_f(self, tag_name, closing_tag=True, **kwargs):
        self.parent.insert_tag(
            *self.parent.get_selection_indices(), tag_name,
            closing_tag=closing_tag, **kwargs)

    def tag(self, tag_name, **kwargs):
        "returns callback for opening/closing tags with two newlines between"

        return lambda: self.tag_f(tag_name, cnt='\n', **kwargs)

    def ctag(self, tag_name, **kwargs):
        "returns callback for inline opening and _c_losing tags"

        return lambda: self.ctag_f(tag_name, **kwargs)

    def stag(self, tag_name, **kwargs):
        "returns callback for inline _s_ingle closed <tag />"

        return lambda: self.parent.insert_formatting_tag(
            opening_tag=tag_name, **kwargs)

    def collect_values_dialog(
            self, inputs, booleans, tag, **kwargs):

        self.parent.dialog_insert_tag(
            dialog_obj=lambda parent, title=None: CollectValues(
                parent=parent, title=title,
                inputs=inputs, booleans=booleans),

            opening_tag=tag, **kwargs)

    def dialog_generator(
            self, inputs, booleans, tag, *args, title=None,
            start_txt='\n', end_txt='\n', icon=None, **kwargs):
        '''Returns tuple to be used as an input for add_tool_buttons.'''

        # The dialog is called in the following way:
        # CollectValues(
        # self, parent, booleans=[], inputs=[], title = None)

        return (icon, tag, lambda:
                self.collect_values_dialog(
                    inputs, booleans, tag, title=title,
                    start_txt='\n', end_txt='\n', **kwargs))

    def add_widget(self, widget, *pargs, padx=1, **kwargs):
        self.widgets.append(widget(self, *pargs, **kwargs))
        self.widgets[-1].grid(
            row=0, column=self.cur_widgets_col, sticky='nwse', padx=padx)
        self.cur_widgets_col += 1

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
        media_types = ('', 'all', 'print', 'screen', 'speech')

        referrer_policy_list = (
            '', 'no-referrer', 'no-referrer-when-downgrade',
            'origin', 'origin-when-cross-origin', 'unsafe-url')

        referrer_policy = (lambda parent: SelectMenu(
            parent, *referrer_policy_list), ('referrerpolicy',))

        crossorigin = (lambda parent: SelectMenu(
            parent, '', 'anonymous', 'use-credentials'), ('crossorigin',))

        link_rel = ('alternate', 'author', 'dns-prefetch', 'help',
                    'icon', 'license', 'next', 'pingback', 'preconnect',
                    'prefetch', 'preload', 'prerender', 'prev', 'search',
                    'stylesheet')

        script_inputs = (
            crossorigin, referrer_policy,
            (lambda parent: SelectMenu(
                parent, '', 'True', 'False'), ('nomodule',)),

            (lambda parent: FileChooser(
                parent, filetypes=[
                    ('Javascript files', '*js'),
                    (('All files', '*'))]), ('src',)),

            (tk.Entry, ('type',)))

        script_bools = ('async', 'defer')

        link_inputs = [
            crossorigin,
            (lambda parent: SelectMenu(
                parent, *media_types), ('media',)),
            referrer_policy,

            (lambda parent: SelectMenu(
                parent, *link_rel), ('rel',)),

            (tk.Entry, ('sizes', 'title', 'type', 'hreflang')),

            (lambda parent: FileChooser(
                parent, filetypes=[
                    ('Css stylesheets', '*css'),
                    ('All files', '*')]), ('href',))]

        self.add_tool_buttons(
            (icon('doctype.png' ), '!doc', self.parent.insert_doctype),
            (icon('html.png'    ), 'html', self.tag('html')),
            (icon('head.png'    ), 'head', self.tag('head')),

            (icon('external_link.png'), 'link',
             lambda: self.collect_values_dialog(
                 inputs=link_inputs, booleans=[], tag='link',
                 title='Insert external link')),

            (icon('css.png'), 'style', self.tag(
                'style', opts='type="text/css"')),

            (icon('script.png'), 'script', lambda: self.collect_values_dialog(
                inputs=script_inputs, booleans=script_bools, tag='script',
                title='Insert script', closing_tag=True)),

            (icon('title.png'), 'title', self.ctag('title')),
            (icon('body.png'), 'body', self.tag('body')))

        self.separator()

        self.add_widget(lambda parent: tk.Label(parent, text='Meta:'))
        self.add_meta_menu()

    def add_meta_menu(self):
        self.meta_types = ('charset', 'http-equiv', 'name')
        input_option = tk.StringVar()
        input_option.set(self.meta_types[0])

        self.add_widget(
            tk.OptionMenu, input_option, *self.meta_types,
            command=self.meta_http_equiv_cb)

        self.meta_names = ['application-name', 'author', 'description',
             'generator', 'keywords', 'viewport']

    def meta_http_equiv_cb(self, val):
        if val == 'name':
            inputs = [
                (lambda parent: SelectMenu(parent, *self.meta_names),
                 ('name',)), (tk.Entry, ('content',))]

            self.collect_values_dialog(
                inputs=inputs, booleans=[], tag='meta')

        elif val == 'http-equiv':
            self.parent.dialog_insert_tag(
                opening_tag='meta', dialog_obj=HttpEquivDialog,
                title='Insert meta tag:')

        elif val == 'charset':
            self.parent.insert_formatting_tag('meta', opts='charset="utf-8"')


class MainToolBar(ToolBar):
    '''Top bar with buttons for the following commands:
    open, save, save as, copy/cut/paste, undo, redo, view in browser'''

    def tools(self):
        self.add_tool_buttons(
            (icon('folder_open.png'), 'Open', self.parent.open_document),
            (icon('save_file.png'), 'Save', self.parent.save_document),
            (icon('save_as.png'), 'Save as', self.parent.save_document_as))

        self.separator()

        self.add_tool_buttons(
            (icon('copy.png'), 'Copy', get_ev_cb(self.parent, '<<Copy>>')),
            (icon('cut.png'), 'Cut', get_ev_cb(self.parent, '<<Cut>>')),
            (icon('paste.png'), 'Paste', get_ev_cb(self.parent,'<<Paste>>')))

        self.separator()

        self.add_tool_buttons(
            (icon('undo_icon.png'), 'Undo',
             self.parent.main_tabs.edit_html.edit_undo),
            (icon('redo_icon.png'), 'Redo',
             self.parent.main_tabs.edit_html.edit_redo))

        self.separator()

        self.add_tool_buttons(
            (icon('search.png'), 'Search', self.parent.find_text),
            (icon('globe_icon.png'), 'Browser', self.parent.view_in_browser))


class StandardTools(ToolBar):
    def tools(self):
        "par, br, img, anchor, comment"

        # ('path_to_icon', 'text', 'command')
        # better way to supply arguments: items[:4] ...

        self.add_tool_buttons(
            (icon('paragraph.png'), 'P', self.ctag('p')),
            (icon('newline.png'), 'newline', self.stag('br /')),
            (icon('div.png'), 'div', self.ctag('div', opts='class=""')),
            (icon('span.png'), 'span', self.ctag('span', opts='class=""')),
            (icon('hr.png'), 'hr', self.stag('hr /')),

            (icon('insert_image.png'), 'img',
             lambda: self.parent.dialog_insert_tag(
                 opening_tag='img', title ='Insert image',
                 dialog_obj=InsertImgDialog)),

            (icon('insert_hyperlink.png'), 'anchor',
             lambda: self.collect_values_dialog(
                 inputs=[(tk.Entry, ('href', 'rel')),
                         (self.sel_menu_target, ('target',))],
                 booleans=[], tag='a', closing_tag=True)))

        self.separator()

        self.add_tool_buttons(
            (icon('comment.png'), '<!-',
             lambda: self.parent.insert_startendtag(
                 '<!-- ', ' -->', *self.parent.get_selection_indices())))


class TableBar(ToolBar):
    def tools(self):
        "Table creator (dialog), table, tr, th, td."

        self.add_tool_buttons(
            (icon('insert_table.png'), 'table_creator',
             self.parent.table_creator))

        self.separator()

        self.add_tool_buttons(
            (icon('table.png'), 'table', self.tag('table')),
            (icon('insert_row.png'), 'row',self.ctag('tr')),
            (icon('table_header.png'), 'th', self.ctag('th')),
            (icon('table_cell.png'), 'td', self.ctag('td')))


class FontTools(ToolBar):
    def tools(self):
        self.add_tool_buttons(
            (icon('bold_type.png'),     'B',self.ctag('b')),
            (icon('font_italic.png'),   'I',self.ctag('i')),
            (icon('strikethrough.png'), 'S',self.ctag('strike')),
            (icon('underline.png'),     'U',self.ctag('u')))

        self.separator()

        self.add_tool_buttons(
            (icon('superscript.png'), 'sup',self.ctag('sup')),
            (icon('subscript.png'), 'sub',self.ctag('sub')))

        self.separator()

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
            (icon('unordered_list.png'), 'ul', self.tag('ul')),
            (icon('ordered_list.png'), 'ol', self.tag('ol')),
            (icon('list_item.png'), 'li', self.ctag('li')))

        self.separator()

        self.add_tool_buttons(
            (icon('definition_list.png'), 'dl', self.tag('dl')),
            (icon('defined_term.png'), 'dt', self.ctag('dt')),
            (icon('definition.png'), 'dd', self.ctag('dd')))

class SemanticTags(ToolBar):
    def tools(self):
        self.add_tool_buttons(
            (icon('strong.png'), 'strong', self.ctag('strong')),
            (icon('emph.png'), 'em',self.ctag('em')),

            (icon('blockquote.png'), 'blockquote', lambda:
             self.parent.insert_tag(
                 *self.parent.get_selection_indices(), 'blockquote',
                 closing_tag=True, start_txt='\n<p>', end_txt='</p>\n')),

            (icon('quote.png'), 'q', self.ctag('q', opts='cite=""')),
            (icon('cite_art.png'), 'cite', self.ctag('cite')),
            (icon('abbr.png'), 'abbr', self.ctag('abbr', opts='title=""')),
            (icon('dfn.png'), 'dfn', self.ctag('dfn')),
            (icon('address_book.png'), 'addr', self.ctag('address')),
            (icon('erase.png'), 'del', self.ctag('del')),
            (icon('insert.png'), 'ins', self.ctag('ins')),
            (icon('s_incorrect.png'), 's', self.ctag('s')))


class FormTab(ToolBar):
    def tools(self):
        sel_inputs = [
            (tk.Entry, ('form', 'name')),
            (lambda parent: tk.Spinbox(
                parent, from_=1, to=100, increment=1, width=6), ('size',))]

        sel_booleans = ('autofocus', 'disabled', 'multiple', 'required')

        def insert_textarea(parent, title):
            txarea_inputs = [
                (lambda parent: tk.Spinbox(
                    parent, from_=0, to=100, increment=1, width=6),
                 ('cols', 'maxlength', 'rows')),

                (tk.Entry, ('name', 'placeholder', 'dirname', 'form')),

                (lambda parent: SelectMenu(
                    parent, '', 'hard', 'soft'), ('wrap',))]

            txarea_booleans = ('autofocus', 'disabled', 'readonly', 'required')

            return CollectValues(
                parent, title, inputs=txarea_inputs, booleans=txarea_booleans)


        self.add_tool_buttons(
            (icon('webform.png'), 'form',
             lambda: self.parent.dialog_insert_tag(
                 dialog_obj=lambda parent, title:
                 CollectValues(parent, title=title, inputs=[
                     (tk.Entry, ['action']),
                     (lambda parent:
                      SelectMenu(parent, '', 'get', 'post'), ['method'])]),

                 opening_tag='form',
                 closing_tag=True, title='Insert form',
                 start_txt='\n', end_txt='\n')),

            self.dialog_generator(
                sel_inputs, sel_booleans, 'select',
                icon=icon('select_form.png'), title='Insert select tag:',
                closing_tag=True),

            (icon('textarea.png'), 'textarea',
             lambda: self.parent.dialog_insert_tag(
                 dialog_obj=insert_textarea, opening_tag='textarea',
                 closing_tag=True, title='Insert textarea',
                 start_txt='\n', end_txt='\n')),

            self.dialog_generator(
                [(tk.Entry, ('form', 'name'))], ['disabled'], 'fieldset',
                icon=icon('fieldset.png'), title='Insert fieldset:',
                closing_tag=True),

            (icon('legend.png'), 'legend', self.ctag('legend')),
            (icon('button.png'), 'button',
             self.ctag('button', opts='type="submit"')),
            (icon('option.png'), 'option',
             self.ctag('option', opts='value=""')),
            (icon('opt_group.png'), 'opt_gr',
             self.tag('optgroup', opts='label=""')),
            (icon('label.png'), 'label', self.ctag('label', opts='for=""')))

        self.add_html_inputs()

    def add_html_inputs(self):
        self.input_std_opts_vals = [(tk.Entry, ('name', 'id', 'value'))]
        self.input_std_opts_vals_bools = ('disabled', 'readonly')

        def spellcheck(parent):
            # enumeratory type:
            # explicit true/false/no value

            return SelectMenu(parent, 'true', 'false', '')


        self.input_list_dialog = {
            'file': {'booleans': ('accept', 'multiple')},

            'image': {'inputs': [
                (tk.Entry, ('formaction',)),
                (lambda parent:
                 FileChooser(parent, filetypes=(
                     ('Images', ('.jpg','.jpeg', '.png', '.gif')),
                     ('All files', '*')
                 )), ('src',)),

                (self.sel_menu_target, ('formtarget',)),
                (self.formmethod, ('formmethod',))]},

            'submit': {'booleans': ('formnovalidate',),
                       'inputs': [
                           (tk.Entry, ('formaction',)),
                           (self.sel_menu_target, ('formtarget',)),
                           (self.formmethod, ('formmethod',))]},

            'tel': {'inputs': [(tk.Entry, ('list', 'pattern', 'placeholder')),
                               (lambda parent: tk.Spinbox(
                                   parent, from_=0, to=30),
                                ('maxlength', 'minlength'))]},

            'url': {'inputs': [(tk.Entry, ('list', 'pattern', 'placeholder')),
                               (spellcheck, ('spellcheck',)),
                               (lambda parent: tk.Spinbox(
                                   parent, from_=0, to=100),
                                ('maxlength', 'minlength', 'size'))]},
            'text': {'inputs': [(tk.Entry, ('placeholder',)),
                                (spellcheck, ('spellcheck',)),
            ]}
        }
        
        inputs = ['Insert input', 'button', 'checkbox', 'color', 'date',
                  'datetime-local', 'email', 'hidden','month', 'number', 'week',
                  'password', 'radio', 'range', 'reset', 'search', 'time']
        inputs.extend(self.input_list_dialog.keys())

        self.input_list = tuple(sorted(inputs))

        self.input_option = tk.StringVar()
        self.input_option.set('Insert input')

        self.add_widget(
            tk.OptionMenu, self.input_option, *self.input_list,
            command=self.html_input)

    def html_input(self, type_):
        if type_ == 'Insert input':
            return

        elif type_ in self.input_list_dialog:
            values = []
            for std_vals, vals_name in (
                    (self.input_std_opts_vals, 'inputs'),
                    (self.input_std_opts_vals_bools, 'booleans')):

                if vals_name in self.input_list_dialog[type_]:
                    val = std_vals + self.input_list_dialog[type_][vals_name]
                else:
                    val = std_vals
                values.append(val)

            inputs, booleans = values

            self.collect_values_dialog(
                inputs, booleans, 'input', opts='type="{}" '.format(type_),
                title='Insert input "{0}":'.format(type_))

        elif type_ in self.input_list:
            self.ctag_f(
                'input', opts='type="{0}" name="" id="" value=""'.format(type_),
                closing_tag=False)

        self.input_option.set('Insert input')


class HTML5Tags(ToolBar):
    def tools(self):
        self.add_tool_buttons(
            (icon('aside.png'), 'aside', self.ctag('aside')),
            (icon('navigation.png'), 'nav', self.ctag('nav')),
            (icon('article.png'), 'article', self.ctag('article')),
            (icon('section.png'), 'section', self.ctag('section')),
            (icon('footer.png'), 'footer', self.ctag('footer')))


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
    def __init__(self, app):
        tk.Menu.__init__(self, app)
        self.app = app

        # Space for defining menus:
        for menu in 'file_menu', 'edit_menu', 'document_menu', 'help_menu':
            setattr(self, menu, tk.Menu(self))

        menus = (
            (self.file_menu,                                    # parent-menu
             ('New window', 'Open', 'Save', 'Save as', 'Exit'), # label
             ('Ctrl+N', 'Ctrl+O', 'Ctrl+S', None, 'Ctrl+Q'),    # accelerator
             (app._new_instance, app.open_document,             # command
              app.save_document, app.save_document_as, app.quit)),

            (self.edit_menu,
             ('Undo', 'Redo', 'Select all', 'Copy', 'Cut', 'Paste'),
             ('Ctrl+Z', 'Shift+Ctrl+Z', 'Ctrl+A', 'Ctrl+C', 'Ctrl+X',
              'Ctrl+V'),
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
