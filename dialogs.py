import pathlib
import tkinter as tk
from tkinter import filedialog as fd
from utils import *
from tkinter import messagebox as msgbox
from tkSimpleDialog import Dialog


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
                    msgbox.showerror("Can't preview image file:", e)

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

        try:
            for v in rows, cols:
                if not v.isdigit():
                    msg = 'Not a valid, positive number: {}'.format(v)
                    raise ValueError
                if int(v) not in range(1, 1000):
                    msg = 'Value not in 1-999 range: {}'.format(v)
                    raise ValueError

        except ValueError:
            msgbox.showerror(
                parent=self, title='Input error', message=msg)
            return False

        else:
            return True

    def apply(self):
        self.result = tuple(int(v) for v in self.collect_vals())


class InsertDoctypeDialog(Dialog):
    def body(self, master):
        self.doctype_var = tk.IntVar(0)

        tk.Radiobutton(
            master, text='HTML5 Doctype', variable=self.doctype_var,
            command=self.on_dtype_sel, value=0
        ).grid(row=0, column=0, sticky='w')

        tk.Radiobutton(
            master, text='Other:', variable=self.doctype_var,
            command=self.on_dtype_sel, value=1
        ).grid(row=1, column=0, sticky='w')

        self.doc_type = {
            'HTML 4.01 Strict': '<!DOCTYPE HTML PUBLIC '
            + '"-//W3C//DTD HTML 4.01//EN" '
            + '"http://www.w3.org/TR/html4/strict.dtd">',

            'HTML 4.01 Transitional': '<!DOCTYPE HTML PUBLIC '
            + '"-//W3C//DTD HTML 4.01 Transitional//EN" '
            + '"http://www.w3.org/TR/html4/loose.dtd">',

            'HTML 4.01 Frameset': '<!DOCTYPE HTML PUBLIC '
            + '"-//W3C//DTD HTML 4.01 Frameset//EN" '
            + '"http://www.w3.org/TR/html4/frameset.dtd">',

            'XHTML 1.0 Strict': '<!DOCTYPE html PUBLIC '
            + '"-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.o'
            +'rg/TR/xhtml1/DTD/xhtml1-strict.dtd">',

            'XHTML 1.0 Transitional': '<!DOCTYPE html PUBLIC '
            + '"-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3'
            + '.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">',

            'XHTML 1.0 Frameset': '<!DOCTYPE html PUBLIC "-//W3C//'
            + 'DTD XHTML 1.0 Frameset//EN" "http://www.w3.org/TR/'
            + 'xhtml1/DTD/xhtml1-frameset.dtd">',

            'XHTML 1.1': '<!DOCTYPE html PUBLIC "-'
            + '//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR'
            + '/xhtml11/DTD/xhtml11.dtd">'}

        self.dtype_option = tk.StringVar()
        self.dtype_option.set('HTML 4.01 Strict')

        self.dtype_version = tk.OptionMenu(
            master, self.dtype_option, *self.doc_type)
        self.dtype_version.configure(state="disabled")
        self.dtype_version.grid(row=1, column=1)

    def on_dtype_sel(self):
        "on doctype select"
        {'0': lambda: self.dtype_version.configure(state='disabled'),
         '1': lambda: self.dtype_version.configure(state='normal')
        }[str(self.doctype_var.get())]()

    def apply(self):
        val = self.doctype_var.get()

        if val == 0:
            self.result = '<!DOCTYPE html>'
        elif val == 1:
            self.result = self.doc_type[self.dtype_option.get()]
        else:
            raise ValueError(
                'Unexpected value returned by self.doctype_var.get():', val)
        self.result += '\n'


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


class SearchTextDialog(Dialog):
    def __init__(self, master, txt_fld : tk.Text):
        for attr in 'direction', 'mode', 'case':
            setattr(self, attr, tk.IntVar())

        self.last_idx = txt_fld.index(tk.INSERT)

        self.txt_field_ref = txt_fld
        txt_fld.tag_configure(
            'highlight', background='blue', foreground='white')

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
        # merge this meth into search_text()

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
        found_text_idxs = self._search_text(
            entry_text, direction, mode, case, start_idx, stop_idx)

        if not found_text_idxs and direction == 0:
            self.ask_to_restart_search(direction)
        elif not found_text_idxs:
            print(found_text_idxs, direction)
            msgbox.showinfo(
                parent=self, title='End of backward search',
                message='You reached the beginning of the document.')

    def bring_index_up(self, idx):
        '''Moves the view into the position of a given index.'''
        self.txt_field_ref.see(idx)

    def cancel(self, event=None):
        self.clear_tags()
        Dialog.cancel(self, event)

    def ask_to_restart_search(self, direction):
        decision = msgbox.askyesno(
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
        replace_ent = tk.Entry(
            master, width=30, textvariable=self.replace_entry)
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
            decision = msgbox.askyesnocancel(
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

        msgbox.showinfo(
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


class InsertMetaDialog(Dialog):
    def body(self, master):
        # Może lepiej checkbuttony odblokowujące jedną z grup opcji?
        row = 0
        for txt in 'Meta-value:', 'Value:':
            tk.Label(master, text=txt).grid(column=0, row=row)
            row += 1

        attr_names = ('name', 'http-equiv')
        self.meta_attr_sel = tk.StringVar()
        self.meta_attr_sel.set('name')

        self.attr_name = tk.OptionMenu(
            master, self.meta_attr_sel, *attr_names, command=lambda : True)
        self.attr_name.grid(column=1, row=0)

    def cancel(self, ev=None):
        # !!!
        # Remember to remove before running in an application !!!
        # !!!
        self.parent.destroy()

class InsertForm(Dialog):
    def body(self, master):
        row = 0
        for txt in 'Action:', 'Method:':
            tk.Label(master, text=txt).grid(column=0, row=row)
            row += 1

        self.action_var = tk.StringVar()
        action_ent = tk.Entry(master, textvariable = self.action_var)
        action_ent.grid(column=1, row=0)

        methods = ('get', 'post')
        self.method_var = tk.StringVar()
        self.method_var.set('get')

        method_ent = tk.OptionMenu(
            master, self.method_var, *methods)
        method_ent.grid(column=1, row=1, sticky='w')

    def apply(self):
        self.result = dict(
            action=self.action_var.get(), method=self.method_var.get())


class CollectValues(Dialog):
    "Generic dialog to collect value/boolean input."

    def __init__(
            self, parent, booleans=[], inputs=[], title = None, maxlength=100):
        self.fields = []
        self.inputs = inputs
        self.booleans = booleans

        Dialog.__init__(self, parent, title)

    def body(self, master):
        inputs_fr = tk.Frame(master)
        booleans_fr = tk.Frame(master)

        for fr in inputs_fr, booleans_fr:
            fr.pack()

        row = 0
        for items in self.inputs:
            print(items[1])
            for name in items[1]:
                tk.Label(inputs_fr, text=name+':').grid(column=0, row=row)
                setattr(self, name+'__', items[0](inputs_fr))
                getattr(self, name+'__').grid(
                    column=1, row=row, columnspan=2, sticky='w')
                row += 1

            self.fields.extend(items[1])

        row = 0
        col = 0
        for name in self.booleans:
            if row > 1:
                row = 0
                col += 1

            setattr(self, name+'__', tk.IntVar())
            setattr(self, name+'_cbutton', tk.Checkbutton(
                booleans_fr, text=name, variable=getattr(self, name+'__')))

            getattr(self, name+'_cbutton').grid(
                column=col, row=row, sticky='w')
            row += 1

    def validate(self):
        try:
            for field in self.fields:
                fld = getattr(self, field+'__')
                if type(fld) is tk.Entry:
                    if (len(fld.get())) > self.maxlength:
                        msg = 'The text in the field "{0}" is too long.'.format(
                            field)
                        raise ValueError

                elif type(fld) is tk.Spinbox:
                    if not fld.get().isdigit():
                        msg = ('The value in the field "{0}"'.format(field)
                        +' should be numerical.')
                        raise ValueError
        except ValueError:
            msgbox.showerror(parent=self, title='Input error', message=msg)
            return False
        else:
            return True

    def apply(self):

        self.result = {
            **{bl: bl for bl in self.booleans if getattr(self, bl+'__').get()},
            **{attr: getattr(self, attr+'__').get() for attr in self.fields}}


if __name__ == '__main__':
    root = tk.Tk()
    insertst = InsertSelectTag(root)
    root.mainloop()
