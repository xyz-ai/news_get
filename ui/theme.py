class Theme:
    LIGHT = {
        "title": "\033[95m",
        "ok": "\033[92m",
        "warn": "\033[93m",
        "err": "\033[91m",
        "text": "\033[0m",
    }

    DARK = {
        "title": "\033[96m",
        "ok": "\033[92m",
        "warn": "\033[93m",
        "err": "\033[91m",
        "text": "\033[97m",
    }

    RESET = "\033[0m"

    def __init__(self, mode="dark"):
        self.colors = self.DARK if mode == "dark" else self.LIGHT

    def c(self, key):
        return self.colors.get(key, self.RESET)
