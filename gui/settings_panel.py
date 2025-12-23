import tkinter as tk
from gui.i18n import set_language
from gui.theme import set_theme


class SettingsPanel(tk.Toplevel):
    def __init__(self, master, refresh_ui):
        super().__init__(master)
        self.refresh_ui = refresh_ui

        tk.Button(self, text="中文", command=lambda: self.change_lang("zh")).pack()
        tk.Button(self, text="English", command=lambda: self.change_lang("en")).pack()

        tk.Button(self, text="Dark", command=lambda: self.change_theme("dark")).pack()
        tk.Button(self, text="Light", command=lambda: self.change_theme("light")).pack()

    def change_lang(self, lang):
        set_language(lang)
        self.refresh_ui()

    def change_theme(self, theme):
        set_theme(theme)
        self.refresh_ui()
