from utils import *
import re
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from html.parser import HTMLParser


def scr_update_scheduler(fn):
    '''Decorator associated with the HtmlText class to be used with
    text colorization update methods.'''

    def wrapper(self, event=None):
        def run_fn(): fn(self)

        if event:
            self.after_cancel(self.update_after_id)
            self.update_after_id = self.after(
                self.scr_update_time, run_fn)
        else:
             run_fn()
    return wrapper


def index_to_numbers(idx : 'line.col') -> '(line, col)':
    return tuple(map(lambda x: int(x), idx.split('.')))


def scr_update(fn):
    def wrapper(self, *args, **kwargs):
        fn(self, *args, **kwargs)
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
        self.highlight_attributes(tag_text, attrs, self.getpos())

    def highlight_attributes(self, html_tag, attrs, pos):
        '''Highlights html attribute names.
        htmltag - whole tag (eg. <name attr="value">)
        pos - value returned by p.getpos()'''

        attr_names = set(attr[0] for attr in attrs)

        # tag name with left <
        tag_name_match = re.match('^<\w*\s', html_tag)
        if tag_name_match:
            start_idx = tag_name_match.end()
        else:
            start_idx = 0

        # attribute name and initial indices of its each occurrence
        # within an html tag:

        for attr in attr_names:
            indices = tuple(
                idx.start()+start_idx for idx in re.finditer(
                    attr, html_tag[start_idx:]))

            for index in indices:
                self.html_fld_ref.apply_tag(
                    pos[0], pos[1]+index, len(attr), 'attr_name')

        # attr values

        attr_reg = r'["\'](.*?)["\']'
        attr_values_indices = tuple(
            (idx.start(), idx.end()) for idx in re.finditer(
            attr_reg, html_tag))

        for idx in attr_values_indices:
            self.html_fld_ref.apply_tag(
                pos[0], pos[1]+idx[0], idx[1]-idx[0], 'attr_value')


class HtmlText(ScrolledText):
    def __init__(self, parent, *pargs, **kwargs):
        ScrolledText.__init__(self, parent, undo=True, maxundo=-1,
                              autoseparators=True, *pargs, **kwargs)

        self.parser = HtmlParser(self)
        self.wrapped = self.parser

        # indentation:
        self.indent = True
        self.indent_depth = 2
        self.indent_mark = ' ' # indenting with spaces
        
        self.last_fed_indices = ('1.0', 'end')
        self.scr_update_time = 400
        self.update_after_id = self.after_idle(self.update_current_screen)

        self.configure_tags()
        self.bind_events()

        self.line_parser = HtmlText.ParseLine()


    class ParseLine(HTMLParser):
        '''
        This class instance when called like a function and given
        html-formatted text as an argument returns opening/closing etc.
        tags in the form of the list:
        [('starttag', init_offset), ('endtag', init_offset)]
        '''

        def __init__(self):
            HTMLParser.__init__(self)
            self.data = []

        def handle_starttag(self, tag, attrs):
            self.data.append(['starttag',tag, self.getpos()])

        def handle_startendtag(self, tag, attrs):
            self.data.append(['startendtag', tag, self.getpos()])

        def handle_endtag(self, tag):
            self.data.append(['endtag', tag, self.getpos()])

        def __call__(self, data):
            self.data = []
            self.feed(data)

            return self.data


    def bind_events(self):
        events = (
            ('<Key>', self.update_current_screen),
            ('<<Paste>>', lambda e: self.after(300, self.update_whole_doc)),
            ('<Control-Key-a>', self.select_all),
            ('<KeyRelease-Return>', self.return_press_cb),
            ('<KeyRelease-F2>', self.return_press_cb))

        for ev in events:
            self.bind(*ev)

    def return_press_cb(self, ev):
        if not self.indent:
            return

        def check_if_opened_on_the_same_line(tags):
            if not tags: return

            closing_tag = tags[-1][1]

            # extremely rudimentary, to be amended:
            # can return True even if closing tag wasn't
            # really opened on the same line (eg. there were
            # several other opening tags:

            for tag in tags[0:-1]:
                if tag[1] == closing_tag:
                    return True                    
            return False

        cur_line_idx = self.index('insert linestart')
        cur_line = self.get(cur_line_idx, cur_line_idx+' lineend')
                
        cur_tag = self.line_parser(cur_line)

        cur_l_white_chars = re.match('^\s+', cur_line)

        cur_line_indent = 0
        prev_line_indent = 0

        if cur_l_white_chars:
            cur_line_indent = (cur_l_white_chars.end()
                               - cur_l_white_chars.start())

        # endtag in current (insert) line:
        # update diagram with that

        if (cur_tag and cur_tag[-1][0] == 'endtag' and cur_line_indent
            and not check_if_opened_on_the_same_line(cur_tag)):

            new_indent = cur_line_indent - self.indent_depth

            if new_indent < 0:
                new_indent = 0

            self.delete(
                'insert linestart', 'insert linestart+{0}c'.format(
                    cur_line_indent))

            self.insert(
                'insert linestart', self.indent_mark*new_indent)

            return

        prev_line_idx = self.index('insert linestart-1c')
        prev_line = self.get(
            prev_line_idx+' linestart', prev_line_idx+' lineend')
        prev_tag = self.line_parser(prev_line)

        # prev. line white characters:
        white_chars = re.match('^\s+', prev_line)

        if white_chars:
            prev_line_indent = white_chars.end() - white_chars.start()

        if prev_tag and not check_if_opened_on_the_same_line(prev_tag):
            if prev_tag[-1][0] == 'starttag':
                if cur_line_indent:
                    if cur_line_indent == prev_line_indent + self.indent_depth:
                        return
                    else:
                        # del cur line indent
                        print('deleting:', cur_line_idx)
                        self.delete(
                            cur_line_idx, '{0}+{1}c'.format(
                                cur_line_idx, len(cur_l_white_chars.group(0))))

                print('indenting:{}'.format(self.indent_depth+prev_line_indent))
                self.insert(
                    'insert linestart',
                    self.indent_mark*(self.indent_depth+prev_line_indent))

            elif prev_tag[-1][0] == 'endtag':

                if cur_line_indent:
                    if prev_line_indent == cur_line_indent: return

                    cur_indent = prev_line_indent

                    print('prevline, indent:', prev_line_indent, self.indent_depth)
                    print('cur_line_indent, cur_indent:', cur_line_indent, cur_indent)

                    print('cur_indent:', cur_indent)
                    self.delete(
                        'insert linestart', 'insert linestart+{0}c'.format(
                            cur_line_indent))
                    self.insert(
                        'insert linestart', self.indent_mark*cur_indent)

                else:
                    if (prev_line_indent - self.indent_depth) > 0:
                        self.insert(
                            'insert linestart',
                            self.indent_mark*(
                                prev_line_indent-self.indent_depth))

        # line with white characters only
        elif re.match('^\s+$', prev_line):
            print('white chars')

        elif re.match('^$', prev_line):
            print('newline only')

        else: # data - letters etc.
            if cur_line_indent == prev_line_indent:
                return

            if prev_line_indent:
                self.insert(
                    'insert linestart', self.indent_mark*prev_line_indent)

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
            ('attr_name', {'foreground': 'medium violet red'}),
            ('attr_value', {'foreground': 'aquamarine4'}),
            ('entity', {'foreground': 'SlateBlue2'}),
            ('charref', {'foreground': 'cyan2'}),
            ('doctype', {'foreground': 'thistle4'}),
            ('proc_i', {'foreground': 'sienna2'}))

        for t_name, t_formatting in self.tags:
            self.tag_configure(t_name, t_formatting)

    @scr_update_scheduler
    def update_whole_doc(self, event=None):
        "Updates text colorization in a whole document."

        #print('update_whole_doc') # debug
        self.last_fed_indices = ('1.0', 'end')
        self.feed_parser()

    @scr_update_scheduler
    def update_current_screen(self, event=None):
        "Updates text colorization in a current screen."

        #print('update_current_screen') # debug
        self.clear_screen()
        self.feed_parser()

    def feed_parser(self):
        '''Feeds text contents (portion of or whole document)
        of the component into the parser.'''

        self.reset()
        indices = self.last_fed_indices
        self.feed(self.get(*self.last_fed_indices))

    def get_visible_area(self) -> 'topleft_idx, bottom_right_idx':
        width = self.winfo_width()
        height = self.winfo_height()

        top_left_idx = self.index('@0,0' + ' linestart')
        bottom_right_idx = self.index(
            '@{0},{1} lineend'.format(width, height))

        return top_left_idx, bottom_right_idx

    def clear_tags(self, tag_name):
        "Removes tags in a last visited screen area."

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
    root = tk.Tk()
    text = HtmlText(root)
    text.grid()
    text.insert('1.0', '''<meta property="og:url" 
property="prcontentop2" content="httpsproperty://stackoverflow.com/"/>
<![CDATA[
      <message> Welcome to TutorialsPoint </message>
   ]] >
  </a>
<html>
<body>
<head></head>''')
    text.update_whole_doc()
    text.focus_set()
    root.mainloop()
