"""
tkinter HTML text widgets
"""
import sys
import tkinter as tk

import ttkbootstrap
from tkhtmlview import html_parser

VERSION = "0.1.0.post1"


class _ScrolledText(tk.Text):
    # ----------------------------------------------------------------------------------------------
    def __init__(self, master=None, **kw):
        self.frame = tk.Frame(master)

        self.vbar = ttkbootstrap.Scrollbar(self.frame, bootstyle='round')
        kw.update({'yscrollcommand': self.vbar.set})
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.vbar['command'] = self.yview

        tk.Text.__init__(self, self.frame, **kw)
        self.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        text_meths = vars(tk.Text).keys()
        methods = vars(tk.Pack).keys() | vars(tk.Grid).keys() | vars(tk.Place).keys()
        methods = methods.difference(text_meths)

        for m in methods:
            if m[0] != '_' and m != 'config' and m != 'configure':
                setattr(self, m, getattr(self.frame, m))

    def __str__(self):
        return str(self.frame)


class HTMLScrolledText(_ScrolledText):
    # ----------------------------------------------------------------------------------------------
    """
    HTML scrolled text widget
    """

    def __init__(self, *args, html=None, **kwargs):
        # ------------------------------------------------------------------------------------------
        super().__init__(*args, **kwargs)
        self._w_init(kwargs)
        self.html_parser = html_parser.HTMLTextParser()
        if isinstance(html, str):
            self.set_html(html)

    def _w_init(self, kwargs):
        # ------------------------------------------------------------------------------------------
        if not 'wrap' in kwargs.keys():
            self.config(wrap='word')
        if not 'background' in kwargs.keys():
            if sys.platform.startswith('win'):
                self.config(background='SystemWindow')
            else:
                self.config(background='white')

    def fit_height(self):
        # ------------------------------------------------------------------------------------------
        """
        Fit widget height to wrapped lines
        """
        for h in range(1, 4):
            self.config(height=h)
            self.master.update()
            if self.yview()[1] >= 1:
                break
        else:
            self.config(height=0.5 + 3 / self.yview()[1])

    def set_html(self, html, strip=True):
        # ------------------------------------------------------------------------------------------
        """
        Set HTML widget text. If strip is enabled (default) it ignores spaces and new lines.

        """
        prev_state = self.cget('state')
        self.config(state=tk.NORMAL)
        self.delete('1.0', tk.END)
        self.tag_delete(self.tag_names)
        self.html_parser.w_set_html(self, html, strip=strip)
        self.config(state=prev_state)


class HTMLText(HTMLScrolledText):
    # ----------------------------------------------------------------------------------------------
    """
    HTML text widget
    """

    def _w_init(self, kwargs):
        # ------------------------------------------------------------------------------------------
        super()._w_init(kwargs)
        self.vbar.pack_forget()

    def fit_height(self):
        # ------------------------------------------------------------------------------------------
        super().fit_height()
        # self.master.update()
        self.vbar.pack_forget()


class TkHtmlView_noscrollbar(HTMLText):
    # ----------------------------------------------------------------------------------------------
    """
    HTML label widget
    """

    def _w_init(self, kwargs):
        # ------------------------------------------------------------------------------------------
        super()._w_init(kwargs)
        if not 'background' in kwargs.keys():
            if sys.platform.startswith('win'):
                self.config(background='SystemButtonFace')
            else:
                self.config(background='#d9d9d9')

        if not 'borderwidth' in kwargs.keys():
            self.config(borderwidth=0)

        if not 'padx' in kwargs.keys():
            self.config(padx=3)

    def set_html(self, *args, **kwargs):
        # ------------------------------------------------------------------------------------------
        super().set_html(*args, **kwargs)
        self.config(state=tk.DISABLED)


class TkHtmlView(HTMLScrolledText):
    # ----------------------------------------------------------------------------------------------
    """
    HTML label widget
    """

    def _w_init(self, kwargs):
        # ------------------------------------------------------------------------------------------
        super()._w_init(kwargs)
        if not 'background' in kwargs.keys():
            if sys.platform.startswith('win'):
                self.config(background='SystemButtonFace')
            else:
                self.config(background='#d9d9d9')

        if not 'borderwidth' in kwargs.keys():
            self.config(borderwidth=0)

        if not 'padx' in kwargs.keys():
            self.config(padx=3)

    def set_html(self, *args, **kwargs):
        # ------------------------------------------------------------------------------------------
        super().set_html(*args, **kwargs)
        self.config(state=tk.DISABLED)
