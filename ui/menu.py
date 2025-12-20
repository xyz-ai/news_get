import os
from ui import printer
import subprocess
import sys

PYTHON = sys.executable


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    input("\nPress Enter to continue...")


def run_script(script, args=None):
    cmd = [PYTHON, script]
    if args:
        cmd.extend(args)
    subprocess.run(cmd)


def main_menu():
    while True:
        clear()
        printer.title("📰 News System - Main Menu")
        printer.plain("1. Fetch news now")
        printer.plain("2. Query news")
        printer.plain("3. Show statistics")
        printer.plain("4. Health check")
        printer.plain("5. Cleanup database")
        printer.plain("6. Toggle theme (dark/light)")
        printer.plain("0. Exit")

        choice = input("\nSelect: ").strip()

        if choice == "1":
            run_script("news_fetch_and_store.py")
            pause()

        elif choice == "2":
            region = input("Region (US/China/World): ")
            run_script("news_query.py", ["--region", region])
            pause()

        elif choice == "3":
            run_script("news_stats.py")
            pause()

        elif choice == "4":
            run_script("health_check.py")
            pause()

        elif choice == "5":
            run_script("db_cleanup.py")
            pause()

        elif choice == "6":
            toggle_theme()
            pause()

        elif choice == "0":
            printer.ok("Bye 👋")
            break

        else:
            printer.err("Invalid choice")
            pause()


def toggle_theme():
    from ui import printer
    current = printer.theme
    new_mode = "light" if current.colors == current.DARK else "dark"
    printer.set_theme(new_mode)
    printer.ok(f"Theme switched to {new_mode}")
