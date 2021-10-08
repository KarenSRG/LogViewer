from datetime import date
import codecs

from constants import *
from guiClass import LogViewer
from botClass import Bot
from loggerClass import Logger
from checkerClass import Checker

loop = True

if not os.path.exists(path_to_logs):
    preStartExceptions.append("Exception: Не найдена папка логов.")

GUI = LogViewer()
BOT = Bot(GUI)
Logger = Logger(GUI)
Checker = Checker(GUI)

if preStartExceptions:
    GUI.print_logger("Fatal: Запуcк невозможен.")
    loop = False

else:
    GUI.print_logger("Starting: Запуcкаем логгер.")
    GUI.print_logger(f"Info: Собираем логи от: {', '.join(following_streamers)}.")
    for streamer_ in streamersLogging:
        path = f"{path_to_logs}{streamer_}\\{streamer_}-{date.today()}.log"
        if not os.path.exists(path):
            if not os.path.exists(f"{path_to_logs}{streamer_}"):
                os.mkdir(f"{path_to_logs}{streamer_}")
                GUI.print_logger(f"Info: Создаем папку логов {streamer_}.")
            codecs.open(path, 'a+').write(f"# Starting {date.today()}\n")

    GUI.print_checker("$TYPE$Starting$TYPE$$MESS$Запускаем чеккер.$MESS$")
    GUI.print_checker("$TYPE$Info$TYPE$$MESS$Слушаем: cyberinquisitor414.glitch.me $MESS$")
    GUI.print_ircbot("$TYPE$Starting$TYPE$$MESS$Запускаем бота.$MESS$")
    GUI.print_ircbot(f"$TYPE$Info$TYPE$$MESS$Заходим в чаты как: {bot_nick}")

if loop:
    GUI.after(100, func=GUI.logs_to_console)
    Logger.start()
    Checker.start()
    BOT.start()

GUI.protocol('WM_DELETE_WINDOW', GUI.withdraw_window)
GUI.mainloop()
