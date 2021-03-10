from utils import *
from tkinter.scrolledtext import ScrolledText
from html.parser import HTMLParser
#import time

def numbers_to_index(line, col, offset=None) -> 'line.column':
    if offset:
        return '{0}.{1}+{2}c'.format(line, col, offset)
    else:
        return '{0}.{1}'.format(line, col)

def index_to_numbers(idx : 'line.col') -> '(line, col)':
    return tuple(map(lambda x: int(x), idx.split('.')))

def scr_update(fn):
    '''Decorator factory-returns decorators for HtmlText screen/document
    view update tag highliting methods.'''
    def decorator(meth):
        def wrapper(self, *args, **kwargs):
            fn(self,  *args, **kwargs)
            return getattr(self, meth)()
        return wrapper
    return method

class TextFieldModified(Exception): pass

class HtmlParser(HTMLParser):
    def __init__(self, text_ref : 'tk.Text', *pargs, **kwargs):
        # definicja tagów etc.
        self.html_fld_ref = text_ref
        HTMLParser.__init__(self, *pargs, **kwargs)

    def handle_starttag(self, tag, attrs):
        index = self.getpos()
        tag_text = self.get_starttag_text()

        self.html_fld_ref.apply_tag(*index, len(tag_text), 'html_tag')

    def handle_endtag(self, tag):
        index = self.getpos()
        self.html_fld_ref.apply_tag(*index, len(tag)+3, 'html_tag')

    def handle_comment(self, data):
        data_len = len(data) + len('<!---->')
        self.html_fld_ref.apply_tag(*self.getpos(), data_len, 'comment')

class HtmlText(ScrolledText):
    def __init__(self, parent, *pargs, **kwargs):
        ScrolledText.__init__(self, parent, undo=True, maxundo=-1,
                              autoseparators=True, *pargs, **kwargs)

        self.parser = HtmlParser(self)
        self.wrapped = self.parser

        self.last_event_time = int()
        self.last_fed_time = int()
        self.last_fed_indices = ('1.0', self.index('end'))

        self.configure_tags()
        self.bind_events()

    def bind_events(self):
        self.bind('<Key>', self.update_current_screen)
        self.bind(
            '<<Paste>>', lambda e: self.after(3000, self.update_whole_doc))

    __getattr__ = getattr_wrapper()
    insert = scr_update(ScrolledText.insert)('update_current_screen')

    @scr_update('update_whole_doc')
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
            ('comment', {'foreground': 'blue'}))

        for t_name, t_formatting in self.tags:
            self.tag_configure(t_name, t_formatting)

    def update_whole_doc(self, event=None):
        '''Updates tags in a whole document.'''
        print('update_whole_doc') # debug

        self.last_fed_indices = ('1.0', 'end')
        self.feed_parser()

    def update_current_screen(self, event=None):
        print('update_current_screen') # debug
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

        # debug
        print(top_left_idx, bottom_right_idx)

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
        '''p_line, p_col - parser lines/columns,
        values returned by the html parser (lines/cols relative to
        the start of what's been fed into it).'''
        text_line, text_col = index_to_numbers(self.last_fed_indices[0])
        new_init_idx_numbers = (text_line+p_line-1, text_col+p_col)

        self.tag_add(
            tk_tag, numbers_to_index(*new_init_idx_numbers),
            numbers_to_index(*new_init_idx_numbers, tag_len))


if __name__ == '__main__':

    import tkinter as tk
    root = tk.Tk()
    text = HtmlText(root)
    text.grid()
    root.mainloop()
