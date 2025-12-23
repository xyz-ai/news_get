from ui.theme import Theme

theme = Theme(mode="dark")


def set_theme(mode):
    global theme
    theme = Theme(mode)


def title(text):
    print(theme.c("title") + text + Theme.RESET)


def ok(text):
    print(theme.c("ok") + text + Theme.RESET)


def warn(text):
    print(theme.c("warn") + text + Theme.RESET)


def err(text):
    print(theme.c("err") + text + Theme.RESET)


def plain(text):
    print(theme.c("text") + text + Theme.RESET)
