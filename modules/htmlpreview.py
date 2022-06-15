"""Classes for generating webpage previews."""

import tkinter as tk
import urllib.request
import types
import pathlib
import sys
import os
import io
from PIL import Image, ImageTk


class HtmlPreview(tk.Frame):
    """Html file (very basic) preview frame that can be embedded in a
    separate tab. Requires tkhtml to work."""

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.images = {}

        try:
            from tkinterhtml import TkinterHtml

        except ImportError as e:
            error_message = (
                'The preview html tab is not working due to ' +
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

        self._setup_scrollbar()
        self._setup_preview()

    def _setup_scrollbar(self):
        scrollbar = tk.Scrollbar(self)
        self.preview_frame.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.preview_frame.yview)
        scrollbar.grid(row=0, column=1, sticky='wsne')

    def _setup_preview(self):
        self.preview_frame.grid(row=0, column=0, sticky='wsne')
        tk.Grid.columnconfigure(self, 0, weight=1)
        tk.Grid.rowconfigure(self, 0, weight=1)

    def _load_image(self, url):
        try:
            fp = urllib.request.urlopen(url)

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

    def preview(self, html_code: str):
        if hasattr(self.preview_frame, 'no_html'):
            return
        self.preview_frame.reset()
        self.preview_frame.parse(html_code)


class WebPreview(HtmlPreview, tk.Frame):
    '''Implements more resourceful tkinterweb website rendering
    mechanism but retains tkhtml-based HtmlPreview as a fallback.'''

    def __init__(self, parent, *args, **kwargs):
        try:
            from tkinterweb import HtmlFrame

        except ImportError as err:
            print(f'{self.__class__.__name__}:', err,
                  '- using tkinterhtml', file=sys.stderr)
            HtmlPreview.__init__(self, parent, *args, **kwargs)

        else:
            tk.Frame.__init__(self, parent, *args, **kwargs)
            self.preview_frame = HtmlFrame(self)
            HtmlPreview._setup_preview(self)

            self.preview = types.MethodType(WebPreview.__preview, self)

    def __preview(self, html_code):
        # apparently bogus filename has to be added
        # to the base url - doesn't work otherwise

        self.preview_frame.load_html(
            html_code, base_url=pathlib.Path(
                os.getcwd() + '/index.html').as_uri())


if __name__ == '__main__':
    root = tk.Tk()
    web = WebPreview(root)
    web.grid()
    tk.mainloop()
