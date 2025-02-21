import scripts.Updater
import scripts.Database
from colorama import init, Fore, Style
init(autoreset=True)


def start():
    scripts.Updater.update()
    scripts.Database.startup()
