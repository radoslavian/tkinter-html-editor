from utils import *
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from html.parser import HTMLParser
import re
#import time

def index_to_numbers(idx : 'line.col') -> '(line, col)':
    return tuple(map(lambda x: int(x), idx.split('.')))

def scr_update(fn):
    def wrapper(self, *args, **kwargs):
        fn(self,  *args, **kwargs)
        self.update_current_screen()
    return wrapper

def whole_scr_upd(fn):
    def wrapper(self, *args, **kwargs):
        fn(self,  *args, **kwargs)
        self.update_whole_doc()
    return wrapper

class TextFieldModified(Exception): pass

class HtmlParser(HTMLParser):
    def __init__(self, text_ref : 'tk.Text', *pargs, **kwargs):
        # definicja tagów etc.
        self.html_fld_ref = text_ref
        HTMLParser.__init__(self, *pargs, **kwargs)
        self.convert_charrefs = False

    def apply_t(self, t_len, t_name):
        '''Shorthand for the HtmlText.apply_tag method call.'''
        self.html_fld_ref.apply_tag(*self.getpos(), t_len, t_name)

    def handle_comment(self, data):
        data_len = len(data) + len('<!---->')
        self.apply_t(data_len, 'comment')

    def handle_pi(self, data):
        '''Handle processing instruction.'''
        self.apply_t(len(data)+len('<?>'), 'proc_i')

    def handle_decl(self, decl):
        self.apply_t(len(decl)+3, 'doctype')

    def handle_endtag(self, tag):
        self.apply_t(len(tag)+3, 'html_tag')

    def handle_entityref(self, name):
        self.apply_t(len(name)+2, 'entity')

    def handle_charref(self, name):
        self.apply_t(len(name)+3, 'charref')

    def handle_starttag(self, tag, attrs):
        tag_text = self.get_starttag_text()

        self.apply_t(len(tag_text), 'html_tag')
        self.highlight_attr_names(tag_text, attrs, self.getpos())

    def highlight_attr_names(self, html_tag, attrs, pos):
        '''Highlights html attribute names.
        html_tag - whole tag (eg. <name attr="value">)
        pos - value returned by p.getpos()'''

        attr_names = set(attr[0] for attr in attrs)

        # attribute name and initial indices of its each occurrence
        # within an html tag:

        for attr in attr_names:
            indices = tuple(
                idx.start() for idx in re.finditer(attr, html_tag))

            for index in indices:
                self.html_fld_ref.apply_tag(
                    pos[0], pos[1]+index, len(attr), 'attr_name')

class HtmlText(ScrolledText):
    def __init__(self, parent, *pargs, **kwargs):
        ScrolledText.__init__(self, parent, undo=True, maxundo=-1,
                              autoseparators=True, *pargs, **kwargs)

        self.parser = HtmlParser(self)
        self.wrapped = self.parser

        self.last_event_time = int()
        self.last_fed_indices = ('1.0', 'end')

        self.configure_tags()
        self.bind_events()

    def bind_events(self):
        events = (
            ('<Key>', self.update_current_screen),
            ('<<Paste>>', lambda e: self.after(300, self.update_whole_doc)),
            ('<Control-Key-a>', self.select_all))

        for ev in events:
            self.bind(*ev)

    __getattr__ = getattr_wrapper()

    insert = scr_update(ScrolledText.insert)
    edit_undo = whole_scr_upd(ScrolledText.edit_undo)
    edit_redo = whole_scr_upd(ScrolledText.edit_redo)

    def select_all(self, event=None):
        self.tag_add(tk.SEL, '1.0', tk.END)
        return 'break'

    @whole_scr_upd
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
            self.edit_reset()
            html_file.close()

    def is_empty(self):
        return True if self.compare("end-1c", "==", "1.0") else False

    def insert_if_empty(self, content):
        '''Inserts text only if the text edit field is empty
        AND unmodified.'''

        if self.edit_modified() or not self.is_empty():
            raise TextFieldModified(
                'Text field {0} is non-empty or modified'.format(self))
        else:
            self.insert('1.0', content)
            self.edit_modified(False)

    def configure_tags(self):
        self.tags = (
            ('html_tag', {'foreground': 'brown'}),
            ('comment', {'foreground': 'blue'}),
            ('attr_name', {'foreground': 'khaki4'}),
            ('entity', {'foreground': 'SlateBlue2'}),
            ('charref', {'foreground': 'CadetBlue4'}),
            ('doctype', {'foreground': 'thistle4'}),
            ('proc_i', {'foreground': 'sienna2'}))

        for t_name, t_formatting in self.tags:
            self.tag_configure(t_name, t_formatting)

    def update_whole_doc(self, event=None):
        '''Updates tags in a whole document.'''

        self.last_fed_indices = ('1.0', 'end')
        self.feed_parser()

    def update_current_screen(self, event=None):
        self.clear_screen()
        self.feed_parser()

        # self.last_event_time = self.last_fed_time = now

    def feed_parser(self):
        '''Feeds visible text contents of the component into the parser.'''
        self.reset()
        self.feed(self.get(*self.last_fed_indices))

    def get_visible_area(self) -> 'topleft_idx, bottom_right_idx':
        width = self.winfo_width()
        height = self.winfo_height()

        top_left_idx = self.index('@0,0' + ' linestart')
        bottom_right_idx = self.index(
            '@{0},{1} lineend'.format(width, height))

        return top_left_idx, bottom_right_idx

    def clear_tags(self, tag_name):
        '''Removes tags in a last visited screen area.'''
        self.tag_remove(tag_name, *self.last_fed_indices)

    def clear_screen(self):
        '''Refreshes tags on a current screen.'''
        self.last_fed_indices = self.get_visible_area()
        for tag in self.tags:
            self.clear_tags(tag[0])

    def apply_tag(self, p_line : int, p_col : int, tag_len, tk_tag):
        '''Apply tkinter.Text tag

        p_line, p_col - parser lines/columns: values returned by 
        the html parser (lines/cols relative to
        the start of what's been fed into it).'''

        text_line, text_col = index_to_numbers(self.last_fed_indices[0])
        new_init_idx = '{0}.{1}+{2}c'.format(
            text_line+p_line-1, text_col, p_col)

        self.tag_add(
            tk_tag, new_init_idx, '{0}+{1}c'.format(new_init_idx, tag_len))

if __name__ == '__main__':

    import tkinter as tk
    root = tk.Tk()
    text = HtmlText(root)
    text.grid()
    text.insert('1.0', '''<meta property="og:url" 
property="prop2" content="https://stackoverflow.com/"/>''')
    root.mainloop()
