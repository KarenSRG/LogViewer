from tkinter import WORD, ttk, HORIZONTAL, VERTICAL, Label, scrolledtext, END
from ttkthemes import ThemedTk
from PIL import Image
from pystray import MenuItem, Menu, Icon

from constants import *

from datetime import datetime


class LogViewer(ThemedTk):
    def __init__(self):
        # Setting up Player window.
        super().__init__(theme="equilux")
        self.geometry("743x440")
        self['background'] = "#464646"
        self.title("LogViewer")
        self.resizable(False, False)
        self.logger_logs, self.checker_logs, self.ircbot_logs = [], [], []

        menu = Menu(MenuItem('Выход', self.quit_window), MenuItem('Открыть', self.show_window))
        self.icon = Icon("LogViwer", Image.open("adds/icon.ico"), "LogViwer", menu)

        self.logged_messages = {}
        self.logged_messagesOLD = {}

        for streamer in streamersLogging:
            self.logged_messages[streamer] = 0
            self.logged_messagesOLD[streamer] = 0

        self.last_logLoggerOLD, self.last_logLogger, self.last_logCheckerOLD, self.last_logChecker = "", "", "", ""

        self.iconbitmap('adds/icon.ico')
        self.on_console = False
        self.setup_ui()


    def setup_ui(self):
        self.logger_lbl = Label(self, text="Logger's logs")
        self.logger_lbl['background'] = "#464646"
        self.logger_lbl['foreground'] = "#BEBEBE"

        self.checker_lbl = Label(self, text="Checker's logs")
        self.checker_lbl['background'] = "#464646"
        self.checker_lbl['foreground'] = "#BEBEBE"

        self.ircbot_lbl = Label(self, text="Bot's logs")
        self.ircbot_lbl['background'] = "#464646"
        self.ircbot_lbl['foreground'] = "#BEBEBE"

        self.stoplog = Label(self, text="Логгер приостановлен", font=("roobert", 15))
        self.stoplog['background'] = "#464646"
        self.stoplog['foreground'] = "#BEBEBE"

        self.stopcheck = Label(self, text="Чеккер приостановлен", font=("roobert", 15))
        self.stopcheck['background'] = "#464646"
        self.stopcheck['foreground'] = "#BEBEBE"

        self.stopbot = Label(self, text="Бот приостановлен", font=("roobert", 15))
        self.stopbot['background'] = "#464646"
        self.stopbot['foreground'] = "#BEBEBE"

        self.hseparatorTOP = ttk.Separator(self, orient=HORIZONTAL)
        self.hseparatorMID = ttk.Separator(self, orient=HORIZONTAL)
        self.hseparatorBOT = ttk.Separator(self, orient=HORIZONTAL)
        self.vseparatorLEFT = ttk.Separator(self, orient=VERTICAL)
        self.vseparatorMID = ttk.Separator(self, orient=VERTICAL)
        self.vseparatorRIGHT = ttk.Separator(self, orient=VERTICAL)

        self.logger_console = scrolledtext.ScrolledText(self, wrap=WORD, width=50, height=50, font=("roobert", 9))
        self.logger_console['background'] = "#18181b"
        self.checker_console = scrolledtext.ScrolledText(self, wrap=WORD, width=50, height=50, font=("roobert", 9))
        self.checker_console['background'] = "#18181b"
        self.ircbot_console = scrolledtext.ScrolledText(self, wrap=WORD, width=50, height=50, font=("roobert", 9))
        self.ircbot_console['background'] = "#18181b"

        self.logger_lbl.place(x=10, y=5)
        self.checker_lbl.place(x=10, y=228)
        self.ircbot_lbl.place(x=378, y=228)

        self.logger_console.place(x=11, y=30, height=180, width=719)
        self.checker_console.place(x=11, y=253, height=175, width=345)
        self.ircbot_console.place(x=379, y=253, height=175, width=351)

        self.vseparatorMID.place(x=368, y=222, relwidth=0.004, relheight=0.4875)
        self.hseparatorMID.place(x=2, y=220, relwidth=0.995, relheight=0.01)
        self.hseparatorBOT.place(x=2, y=437, relwidth=.995, relheight=0.03)
        self.vseparatorLEFT.place(x=0, y=2, relwidth=0.003, relheight=0.994)
        self.vseparatorRIGHT.place(x=740, y=2, relwidth=0.003, relheight=0.994)
        self.hseparatorTOP.place(x=2, y=0, relwidth=0.995, relheight=0.01)

        self.logger_console.tag_config("timestamp", foreground="#4dd64f")
        self.logger_console.tag_config("draw", foreground="#269e28")
        self.logger_console.tag_config("log", foreground="#c8c8c8")
        self.logger_console.tag_config("info", foreground="#0027a6")
        self.logger_console.tag_config("starting", foreground="#0ae002")
        self.logger_console.tag_config("fatal", foreground="#c20000")
        self.logger_console.tag_config("exception", foreground="#d6d60d")

        self.checker_console.tag_config("timestamp", foreground="#4dd64f")
        self.checker_console.tag_config("draw", foreground="#269e28")
        self.checker_console.tag_config("log", foreground="#c8c8c8")
        self.checker_console.tag_config("info", foreground="#0027a6")
        self.checker_console.tag_config("starting", foreground="#0ae002")
        self.checker_console.tag_config("request", foreground="#33cccc")
        self.checker_console.tag_config("answer", foreground="#3399cc")
        self.checker_console.tag_config("exception", foreground="#d6d60d")

        self.ircbot_console.tag_config("timestamp", foreground="#4dd64f")
        self.ircbot_console.tag_config("draw", foreground="#269e28")
        self.ircbot_console.tag_config("log", foreground="#c8c8c8")
        self.ircbot_console.tag_config("info", foreground="#0027a6")
        self.ircbot_console.tag_config("request", foreground="#33cccc")
        self.ircbot_console.tag_config("starting", foreground="#0ae002")
        self.ircbot_console.tag_config("channel", foreground="#3399cc")
        self.ircbot_console.tag_config("exception", foreground="#d6d60d")

    def adding_log_to_console(self, mess):
        self.logger_console.configure(state='normal')
        spltd = mess.split()
        log = mess.split(spltd[0])[1]
        if spltd[0] == "Info:":
            self.logger_console.insert(END, " " + spltd[0], "info")
            self.logger_console.insert(END, " " + log + "\n", "log")
        elif spltd[0] == "Fatal:":
            self.logger_console.insert(END, " " + spltd[0], "fatal")
            self.logger_console.insert(END, " " + log + "\n", "log")
        elif spltd[0] == "Starting:":
            self.logger_console.insert(END, " " + spltd[0], "starting")
            self.logger_console.insert(END, " " + log + "\n", "log")
        elif spltd[0] in ["Exception:", "Decoding:", "Connection:"]:
            self.logger_console.insert(END, " " + spltd[0], "exception")
            self.logger_console.insert(END, " " + log + "\n", "log")
        else:
            self.logger_console.insert(END, " " + "[" + " ", "draw")
            self.logger_console.insert(END, spltd[0][:-1], "timestamp")
            self.logger_console.insert(END, " " + "]" + " ", "draw")
            self.logger_console.insert(END, log + "\n", "log")
        self.logger_console.yview(END)
        self.logger_console.configure(state='disabled')

    def adding_check_to_console(self, mess):
        self.checker_console.configure(state='normal')

        messtype = mess.split("$TYPE$")[1]
        messbody = mess.split("$MESS$")[1]
        if messtype == "Info":
            self.checker_console.insert(END, " " + messtype + ":", "info")
            self.checker_console.insert(END, " " + messbody + "\n", "log")
        elif messtype == "Starting":
            self.checker_console.insert(END, " " + messtype + ":", "starting")
            self.checker_console.insert(END, " " + messbody + "\n", "log")
        elif messtype == "Exception":
            self.checker_console.insert(END, " " + messtype + ":", "exception")
            self.checker_console.insert(END, " " + messbody + "\n", "log")
        if "$TIME$" in mess:
            messtime = mess.split("$TIME$")[1]
            if messtype == "[Answer]":
                self.checker_console.insert(END, " " + messtype, "answer")
                self.checker_console.insert(END, " " + "[" + " ", "draw")
                self.checker_console.insert(END, messtime, "timestamp")
                self.checker_console.insert(END, " " + "]" + " ", "draw")
                self.checker_console.insert(END, " : " + messbody + "\n", "log")
            elif messtype == "[Request]":
                self.checker_console.insert(END, " " + messtype, "request")
                self.checker_console.insert(END, " " + "[" + " ", "draw")
                self.checker_console.insert(END, messtime, "timestamp")
                self.checker_console.insert(END, " " + "]" + " ", "draw")
                self.checker_console.insert(END, " : " + messbody + "\n", "log")

        self.checker_console.yview(END)
        self.checker_console.configure(state='disabled')

    def adding_ircbot_to_console(self, mess):
        self.ircbot_console.configure(state='normal')

        messtype = mess.split("$TYPE$")[1]

        messbody = mess.split("$MESS$")[1]
        if messtype == "Info":
            self.ircbot_console.insert(END, " " + messtype + ":", "info")
            self.ircbot_console.insert(END, " " + messbody + "\n", "log")
        elif messtype == "Starting":
            self.ircbot_console.insert(END, " " + messtype + ":", "starting")
            self.ircbot_console.insert(END, " " + messbody + "\n", "log")
        elif messtype == "Exception":
            self.ircbot_console.insert(END, " " + messtype + ":", "exception")
            self.ircbot_console.insert(END, " " + messbody + "\n", "log")
        if "$TIME$" in mess:
            messtime = mess.split("$TIME$")[1]
            channel = mess.split("$CHANNEL$")[1]
            if messtype == "[ W ]":
                self.ircbot_console.insert(END, " " + messtype, "request")
                self.ircbot_console.insert(END, " " + "[" + " ", "draw")
                self.ircbot_console.insert(END, messtime, "timestamp")
                self.ircbot_console.insert(END, " " + "]" + " ", "draw")
                self.ircbot_console.insert(END, " " + channel, "channel")
                self.ircbot_console.insert(END, ": " + messbody + "\n", "log")

        self.ircbot_console.yview(END)
        self.ircbot_console.configure(state='disabled')

    def print_logger(self, mess):
        if mess != "update":
            if self.on_console != "logger":
                if self.logger_logs:
                    for past_mess in self.logger_logs:
                        self.adding_log_to_console(past_mess)
                    self.logger_logs = []
                else:
                    self.adding_log_to_console(mess)
            else:
                self.logger_logs.append(mess)
        else:
            if self.logger_logs:
                for past_mess in self.logger_logs:
                    self.adding_log_to_console(past_mess)
                self.logger_logs = []

    def print_checker(self, mess):
        if mess != "update":
            if self.on_console != "checker":
                if self.checker_logs:
                    for past_mess in self.checker_logs:
                        self.adding_check_to_console(past_mess)
                    self.checker_logs = []
                else:
                    self.adding_check_to_console(mess)
            else:
                self.checker_logs.append(mess)
        else:
            if self.checker_logs:
                for past_mess in self.checker_logs:
                    self.adding_check_to_console(past_mess)
                self.checker_logs = []

    def print_ircbot(self, mess):
        if mess != "update":
            if self.on_console != "irc_bot":
                if self.ircbot_logs:
                    for past_mess in self.ircbot_logs:
                        self.adding_ircbot_to_console(past_mess)
                    self.ircbot_logs = []
                else:
                    self.adding_ircbot_to_console(mess)
            else:
                self.ircbot_logs.append(mess)
        else:
            if self.ircbot_logs:
                for past_mess in self.ircbot_logs:
                    self.adding_ircbot_to_console(past_mess)
                self.ircbot_logs = []

    def is_mouse_on_console(self):
        abs_coord_x = self.winfo_pointerx() - self.winfo_rootx()
        abs_coord_y = self.winfo_pointery() - self.winfo_rooty()
        if 10 < abs_coord_x < 725 and 30 < abs_coord_y < 207:
            self.on_console = "logger"
        elif 10 < abs_coord_x < 335 and 255 < abs_coord_y < 425:
            self.on_console = "checker"
        elif 373 < abs_coord_x < 725 and 255 < abs_coord_y < 425:
            self.on_console = "irc_bot"
        else:
            self.on_console = False

    def logs_to_console(self):

        if self.last_logLoggerOLD != self.last_logLogger:
            self.print_logger(self.last_logLogger)
            self.last_logLoggerOLD = self.last_logLogger

        if self.last_logCheckerOLD != self.last_logChecker:
            self.print_checker(self.last_logChecker)
            self.last_logCheckerOLD = self.last_logChecker

        if self.logged_messagesOLD != self.logged_messages:
            for stremaer__ in self.logged_messages.keys():
                if self.logged_messages[stremaer__] != self.logged_messagesOLD[stremaer__]:
                    delta = self.logged_messages[stremaer__] - self.logged_messagesOLD[stremaer__]
                    time_now = datetime.now().replace(microsecond=0).isoformat()
                    printing = f"$TYPE$[ W ]$TYPE$" \
                               f"$TIME${time_now}$TIME$" \
                               f"$CHANNEL${stremaer__}$CHANNEL$:" \
                               f"$MESS$Написано: {delta}$MESS$"

                    self.print_ircbot(printing)
                    self.logged_messagesOLD[stremaer__] = self.logged_messages[stremaer__]

        self.is_mouse_on_console()
        if self.on_console == "logger":
            self.stoplog.place(x=250, y=0)
        else:
            self.print_logger("update")
            self.stoplog.place_forget()
        if self.on_console == "checker":
            self.stopcheck.place(x=10, y=223)
        else:
            self.print_checker("update")
            self.stopcheck.place_forget()
        if self.on_console == "irc_bot":
            self.stopbot.place(x=375, y=223)
        else:
            self.print_ircbot("update")
            self.stopbot.place_forget()

        self.after(100, func=self.logs_to_console)

    def quit_window(self):
        self.icon.stop()
        self.destroy()

    def show_window(self):
        self.icon.stop()
        self.after(0, self.deiconify)

    def withdraw_window(self):
        self.withdraw()
        self.icon.run()
