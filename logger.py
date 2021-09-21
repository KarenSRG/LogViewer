import os, codecs, requests
import subprocess, threading

from pystray import MenuItem, Menu, Icon

from time import sleep
from datetime import datetime, timedelta

import psutil, json
from pymongo import MongoClient

from tkinter import WORD, ttk, HORIZONTAL, VERTICAL, Label, scrolledtext, END
from ttkthemes import ThemedTk
from PIL import Image
from bson.json_util import dumps


class LogViewer(ThemedTk):
    def __init__(self):
        # Setting up Player window.
        super().__init__(theme="equilux")
        self.geometry("743x440")
        self['background'] = "#464646"
        self.title("LogViewer")
        self.resizable(False, False)
        self.iconbitmap('icon.ico')
        self.setup_ui()

    def setup_ui(self):
        self.from_label = Label(self, text="Logger's logs")
        self.from_label['background'] = "#464646"
        self.from_label['foreground'] = "#BEBEBE"

        self.to_label = Label(self, text="Checker's logs")
        self.to_label['background'] = "#464646"
        self.to_label['foreground'] = "#BEBEBE"

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

        self.hseparatorMID.place(x=2, y=220, relwidth=0.995, relheight=0.03)
        self.hseparatorBOT.place(x=2, y=437, relwidth=.995, relheight=0.03)
        self.vseparatorLEFT.place(x=0, y=2, relwidth=0.003, relheight=0.994)
        self.vseparatorMID.place(x=740, y=2, relwidth=0.003, relheight=0.994)
        self.vseparatorRIGHT.place(x=857, y=2, relwidth=0.003, relheight=0.994)
        self.hseparatorTOP.place(x=2, y=0, relwidth=0.995, relheight=0.025)
        self.from_label.place(x=10, y=5)
        self.to_label.place(x=10, y=228)
        self.logger_console.place(x=11, y=30, height=180, width=715)
        self.checker_console.place(x=11, y=253, height=175, width=715)

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

    def print_logger(self, mess):
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

    def print_checker(self, mess):
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


class LogRequest:
    def __init__(self, syncid):
        self.syncID = syncid

        self.streamer = ""
        self.date_from = ""
        self.date_to = ""
        self.body = ""
        self.user = ""
        self.mentions = []
        self.moderationMSG = False
        self.andMode = True

    def __str__(self):
        return f"{self.streamer} {self.date_from} {self.date_to} {self.user} {self.body} {self.mentions}"

    def set_body(self, body):
        self.body = body

    def set_streamer(self, _streamer):
        self.streamer = _streamer

    def set_date(self, date_from, date_to):
        self.date_from, self.date_to = date_from, date_to

    def set_user(self, user):
        self.user = user

    def set_mentions(self, mention_list):
        if mention_list == "":
            mention_list = []
        self.mentions = mention_list

    def moderation(self, boolean):
        self.moderationMSG = boolean


# noinspection PyUnusedLocal,PyShadowingNames
def quit_window(icon, MenuItem):
    global loop, checker_thread, logger_thread, chatterino_thread, gui
    icon.stop()
    loop = False
    gui.destroy()


# noinspection PyUnusedLocal,PyShadowingNames
def show_window(icon, MenuItem):
    icon.stop()
    gui.after(0, gui.deiconify)


def withdraw_window():
    gui.withdraw()
    image = Image.open("icon.ico")
    menu = Menu(MenuItem('Выход', quit_window), MenuItem('Открыть', show_window))
    icon = Icon("LogViwer", image, "LogViwer", menu)
    icon.run()


def checker():
    global last_logChecker
    while loop:
        sleep(10)
        try:
            logreqs = []
            response = requests.get("https://cyberinquisitor414.glitch.me/LOGWIEWIERdb", proxies=proxy).json()
        except json.decoder.JSONDecodeError:
            last_logChecker = f"$TYPE$Exception$TYPE$$MESS$Не удалось прочесть: " \
                              f" https://cyberinquisitor414.glitch.me/LOGWIEWIERdb$MESS$"
            continue
        if response["whatweneed"]:
            for req in response["whatweneed"]:
                formated_req = f"\n\n Стример: {req['streamer']} \n От: {req['dateFrom']} \n" \
                               f" До: {req['dateTo']} \n Ник: {req['user']} \n SyncID: {req['SyncID']} \n"
                time_now = datetime.now().replace(microsecond=0).isoformat()
                last_logChecker = f"$TYPE$[Request]$TYPE$$TIME${time_now}$TIME$$MESS${formated_req}$MESS$"
                sleep(1)

                rawlogreq = LogRequest(str(req["SyncID"]))
                rawlogreq.set_streamer(req["streamer"])
                rawlogreq.set_user(req["user"].lower())
                rawlogreq.set_date(req["dateFrom"], req["dateTo"])

                if "moderationMsg" in req:
                    rawlogreq.moderation(True)

                if "mention" in req:
                    rawlogreq.set_mentions(req["mention"])

                if "msgBody" in req:
                    rawlogreq.set_body(req["msgBody"])

                logreqs.append(rawlogreq)

            for logreq in logreqs:
                post_data = {"SyncID": logreq.syncID, "Exceptions": [], "data": {}}
                if logreq.streamer in db.list_collection_names():
                    list_of_mess = list(db[logreq.streamer].find({"user": logreq.user}))
                    if list_of_mess:
                        timeline_mess_list = []
                        dateFrom = datetime.strptime(f'{logreq.date_from}', "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                            microsecond=0)
                        dateTo = datetime.strptime(f'{logreq.date_to}', "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                            microsecond=0)
                        for mess in list_of_mess:
                            mess.pop('_id')
                            messDate = mess["date"]
                            mess["date"] = str(mess["date"].isoformat()) + "Z"
                            if dateFrom <= messDate <= dateTo:
                                timeline_mess_list.append(mess)
                        if timeline_mess_list:
                            mentionValid_mess_list = []
                            if logreq.mentions:
                                for mess1 in timeline_mess_list:
                                    if logreq.mentions == mess1["mentions"]:
                                        mentionValid_mess_list.append(mess1)
                                if not mentionValid_mess_list and logreq.andMode:
                                    post_data["Exceptions"].append("No matching mentions in messages.")
                            else:
                                mentionValid_mess_list = timeline_mess_list
                            wordValid_mess_list = []
                            if logreq.andMode and mentionValid_mess_list:
                                if logreq.body != "":
                                    for mess2 in mentionValid_mess_list:
                                        if logreq.body in mess2["body"]:
                                            wordValid_mess_list.append(mess2)
                                else:
                                    wordValid_mess_list = mentionValid_mess_list
                                if wordValid_mess_list:
                                    post_data["data"] = wordValid_mess_list

                                else:
                                    post_data["Exceptions"].append(
                                        "There are no matching words in the messages")
                            elif not logreq.andMode and mentionValid_mess_list:
                                if logreq.body != "":
                                    for mess2 in mentionValid_mess_list:
                                        if logreq.body in mess2["body"]:
                                            wordValid_mess_list.append(mess2)
                                else:
                                    wordValid_mess_list = mentionValid_mess_list
                                if not wordValid_mess_list and mentionValid_mess_list:
                                    post_data["data"] = mentionValid_mess_list
                                    post_data["Exceptions"].append(
                                        "There are no matching words in the messages, but there are matching mentions")
                                elif wordValid_mess_list and not mentionValid_mess_list:
                                    post_data["data"] = wordValid_mess_list
                                    post_data["Exceptions"].append(
                                        "There are no matching mentions in the messages, but there are matching words")
                                elif not wordValid_mess_list and not mentionValid_mess_list:
                                    post_data["Exceptions"].append(
                                        "There are no matching words or mentions in the messages")

                        else:
                            post_data["Exceptions"].append("Not matching messages in this timeline.")
                    else:
                        post_data["Exceptions"].append("No matching messages.")
                else:
                    post_data["Exceptions"].append("Streamer not in DB.")
                headers = {'Content-type': 'application/json'}
                # requests.post("https://cyberinquisitor414.glitch.me/logsresponce",
                #               json=json.loads(dumps(post_data)),
                #               headers=headers, proxies=proxy)
                time_now = datetime.now().replace(microsecond=0).isoformat()
                last_logChecker = f"$TYPE$[Answer]$TYPE$$TIME${time_now}$TIME$" \
                                  f"$MESS$Отправлено сообшений {len(post_data['data'])}$MESS$"


def logger():
    global last_logLogger, loop
    # Чекируем стримеров, стримы и сообщения.
    sleep(5)
    while loop:
        for streamer in streamerlist:
            try:
                sleep(2)
                stream_state, log_state, streamer_state = "", "", ""
                # Streams
                stream_info = checkdb_streams(streamer)
                if type(stream_info) != int:
                    stream_state = stream_info
                    # Streamers
                streamer_info = getstreamerinfo(streamer)
                if len(streamer_info) == 2:
                    last_logLogger = f"{streamer_info[0]}\n"
                    continue
                streamer_id = streamer_info[0]
                streamer_status = streamer_info[1]
                streamer_db_action = checkdb_streamer(streamer, streamer_id, streamer_status)
                if type(streamer_db_action) != int:
                    streamer_state = streamer_db_action
                # Logs
                streamer_logs = path_to_logs + streamer + "\\"
                logs_status = checkdb_messages(streamer_logs, streamer)
                log_state = logs_status[0]
                if logs_status[1] == 0:
                    continue
                time_now = datetime.now().replace(microsecond=0).isoformat()
                last_logLogger = f"{time_now}: {log_state} {streamer_state} {stream_state}"

            except UnicodeDecodeError or ValueError:
                last_logLogger = f"Decoding: Возникла ошибка при декодировании, когда читали логи {streamer}"


def logs_to_console():
    global last_logLoggerOLD, last_logLogger
    if last_logLoggerOLD != last_logLogger:
        gui.print_logger(last_logLogger)
        last_logLoggerOLD = last_logLogger

    global last_logCheckerOLD, last_logChecker
    if last_logCheckerOLD != last_logChecker:
        gui.print_checker(last_logChecker)
        last_logCheckerOLD = last_logChecker
    gui.after(500, logs_to_console)


def check_of_chatterino():
    for process_ifc in psutil.process_iter():
        if "chatterino.exe" == process_ifc.name():
            return "Info: Chatterino обнаружен.", 1
    return "Info: Chatterino не обнаружен.", 0


def chatterino_subprocess():
    process = subprocess.Popen([f"{path_to_chatterino}chatterino.exe"], stdout=subprocess.DEVNULL)
    while True:
        if not loop:
            process.terminate()
            return
        sleep(1)


def checkdb_streams(channel_name):
    stream_status = getstreamerinfo(channel_name, "streams")
    if type(stream_status) == str:
        return stream_status
    if not db["streams"].find_one({"name": stream_status[0]}):
        db["streams"].insert_one({
            "streamer": channel_name,
            "name": stream_status[0],
            "id": stream_status[1],
            "created_at": stream_status[2],
            "finished_at": ""})
        return f'Стрим "{stream_status[0]}" от "{channel_name}" добавлен в базу данных.'
    return 1


def going_offline(channel_name):
    timenow_utc = datetime.now().replace(microsecond=0).isoformat()
    db["streams"].update_one({"streamer": channel_name},
                             {"$set": {"finished_at": timenow_utc}})


def getstreamerinfo(channel_name, datatype="id+status"):
    id_req = requests.get(f'https://api.twitch.tv/kraken/users?login={channel_name}',
                          headers={'Accept': constants["Accept"], 'Client-ID': constants["Client-ID"]},
                          proxies=proxy).json()
    if 'error' in id_req:
        return f"{channel_name} не найден, пропускаю.", 0

    if id_req['_total'] == 0:
        return f"{channel_name} не найден, пропускаю.", 0

    channel_id = id_req['users'][0]['_id']

    if datatype == "id+status":
        status_req = requests.get(f"https://api.twitch.tv/kraken/channels/{channel_id}",
                                  headers={'Accept': constants["Accept"], 'Client-ID': constants["Client-ID"]},
                                  proxies=proxy).json()

        return channel_id, status_req["status"], 1

    elif datatype == "streams":
        stream_req = requests.get(f"https://api.twitch.tv/kraken/streams/?channel={channel_id}",
                                  headers={'Accept': constants["Accept"], 'Client-ID': constants["Client-ID"]},
                                  proxies=proxy).json()
        if not stream_req["streams"]:
            going_offline(channel_name)
            return f"{channel_name} в офлайне."

        stream_now = stream_req["streams"][0]
        return stream_now["channel"]["status"], stream_now["_id"], stream_now["created_at"]


def addtodb_streamer(channel_name, _id, status):
    streamer_logs_ = path_to_logs + channel_name + "\\"
    if not os.path.exists(streamer_logs_):
        return f"Exception: Не найдена папка с логами {channel_name}"
    list_of_logs = [os.path.join(streamer_logs_, i) for i in os.listdir(streamer_logs_)]
    for logfile in sorted(list_of_logs, key=os.path.getmtime):
        streamerlist[channel_name]["logfiles"][logfile] = 0
    db.create_collection(channel_name)
    db["streamers"].insert_one({
        "name": channel_name,
        "id": _id,
        "status": status,
        "logfiles": streamerlist[channel_name]["logfiles"]})


def checkdb_streamer(channel_name, _id, status):
    streamer_inf = db["streamers"].find_one({"name": channel_name})
    last_logfiles = streamerlist[channel_name]["logfiles"]

    if streamer_inf is None:
        adding_status_ = addtodb_streamer(channel_name, _id, status)
        if type(adding_status_) is str:
            return adding_status_
        return f"{channel_name} не в базе данных, добавляем."

    if streamer_inf["status"] != status:
        db["streamers"].update_one({"name": channel_name}, {"$set": {"status": status}})
        return f"Обновляем статус у {channel_name} в базе данных."

    if streamer_inf["logfiles"] != last_logfiles:
        db["streamers"].update_one({"name": channel_name}, {"$set": {"logfiles": last_logfiles}})

    return 1


def addtodb_message(log_line, _streamer, log_date):
    if log_line[0] != "#" and len(log_line.split()) > 2:
        if ":" not in log_line[12:]:
            is_moderation = True
            user = log_line.split()[1]
            body = log_line.split(user)[1]
        else:
            is_moderation = False
            user = log_line[12:].split(":")[0]
            body = log_line[12:].split(":")[1][1:]
    else:
        return "Exception"

    logline_time = log_line.split("]")[0][1:]
    date = (datetime.fromisoformat(f"{log_date}T{logline_time}") - timedelta_from_UTC).replace(microsecond=0)
    stream_id = "offline"
    last_stream = db["streams"].find_one({"streamer": _streamer})
    if last_stream:
        if last_stream["finished_at"] == "":
            stream_id = last_stream["id"]

    mentions = [word for word in body.split() if "@" in word]

    if body.endswith('\n'):
        body = body[:-1]
    db[_streamer].insert_one({
        "date": date,
        "user": user,
        "mentions": mentions,
        "body": body,
        "stream_id": stream_id,
        "moderationMSG": is_moderation})


def getinfo_lastlog(_streamer_logs, _streamer):
    rows_added = 0
    rows_skipped = 0
    logging = []
    for logfile in streamerlist[_streamer]["logfiles"].keys():
        logline = streamerlist[_streamer]["logfiles"][logfile]
        log_file = codecs.open(logfile, "r", "utf-8-sig", errors='ignore')
        loglines = log_file.readlines()
        if len(loglines) > logline:
            log_date = logfile.split(_streamer)[-1][1:11]
            for log_line in loglines[logline:]:
                try:
                    if addtodb_message(log_line, _streamer, log_date) != "Exception":
                        rows_added += 1
                except ValueError:
                    rows_skipped += 1
        streamerlist[_streamer]["logfiles"][logfile] = len(loglines)

    list_of_logs = [os.path.join(_streamer_logs, i) for i in os.listdir(_streamer_logs)]
    lastests = sorted(list_of_logs, key=os.path.getmtime)
    log_files_inDB = streamerlist[_streamer]["logfiles"].keys()

    if rows_skipped != 0:
        logging.append(f"пропущено строк {rows_skipped}")
    if lastests != log_files_inDB:
        for new_logfile in lastests:
            if new_logfile not in log_files_inDB:
                streamerlist[_streamer]["logfiles"][new_logfile] = 0
                logging.append("найден новый лог-файл")
    if rows_added != 0:
        if logging:
            return f"добавлено {rows_added} cтрок в базу данных, {', '.join(logging)}."
        return f"добавлено {rows_added} cтрок в базу данных."
    if logging:
        return f"пока нечего читать, {', '.join(logging)}."
    return f"пока нечего читать."


def checkdb_messages(_streamer_logs, _streamer):
    if not os.path.exists(_streamer_logs) or os.listdir(_streamer_logs) == []:
        return f"Не найдены логи стримера {_streamer}, пропускаю.", 0
    addtodb_inf = getinfo_lastlog(_streamer_logs, _streamer)

    if addtodb_inf:
        return f"Читаем логи {_streamer}, {addtodb_inf}", 1
    else:
        return f"Читаем логи {_streamer}.", 1


gui = LogViewer()

constants = {'Accept': 'application/vnd.twitchtv.v5+json',
             'Client-ID': 'gp762nuuoqcoxypju8c569th9wz7q5'}

loop = True

last_logLogger = ""
last_logChecker = ""
last_logLoggerOLD = ""
last_logCheckerOLD = ""

logger_thread = threading.Thread(target=logger)
chatterino_thread = threading.Thread(target=chatterino_subprocess)
checker_thread = threading.Thread(target=checker)
logger_thread.daemon = True
chatterino_thread.daemon = True
checker_thread.daemon = True

connect_string = "localhost:27017"
mongodb = MongoClient(connect_string)
db = mongodb["main"]

config_dict = json.load(open("config.json"))

proxy = config_dict["proxy"]

preStartInfo = []
preStartExceptions = []
following_streamers = []

timedelta_from_UTC = timedelta(hours=config_dict["timedelta_from_UTC"])

path_to_chatterino = config_dict["chatterino_folder"]
path_to_logs = config_dict["path_to_logs"] + "\\Twitch\\Channels\\"
path_to_settings = os.getenv('APPDATA') + "\\Chatterino2\\Settings\\window-layout.json"

result_check_of_chatterino = check_of_chatterino()

if check_of_chatterino()[1] == 1:
    preStartInfo.append(result_check_of_chatterino[0])
else:
    if os.path.exists(path_to_chatterino):
        preStartInfo.append("Info: Chatterino не обнаружен, запускаем.")
        chatterino_thread.start()

    else:
        preStartExceptions.append("Exception: Неправильный путь к папке Chatterino.")

if not os.path.exists(path_to_logs):
    preStartExceptions.append("Exception: Не найдена папка логов.")

streamerlist = {}
with open(path_to_settings, "r") as file:
    for streamer_ifc in json.load(file)['windows'][0]["tabs"]:
        if "data" in streamer_ifc["splits2"]:
            stremaer = streamer_ifc["splits2"]["data"]["name"]
            dbinf = db["streamers"].find_one({"name": stremaer})
            following_streamers.append(stremaer)
            if dbinf is None:
                streamerlist[stremaer] = {"logfiles": {}}
                adding_status = addtodb_streamer(stremaer, *(getstreamerinfo(stremaer))[:-1])
                if type(adding_status) is str:
                    preStartExceptions.append(adding_status)
            else:
                streamerlist[stremaer] = {"logfiles": dbinf["logfiles"]}
        else:
            preStartExceptions.append("Exception: Пустые вкладки в Chatterino.")
            break
if preStartExceptions:
    fatal = False
    for Exception_ifc in preStartExceptions:
        if "Не найдена папка с логами" not in Exception_ifc:
            fatal = True
        gui.print_logger(Exception_ifc)
    if fatal:
        gui.print_logger("Fatal: Запуcк невозможен.")
        loop = False

elif not preStartExceptions and preStartInfo:
    for Info_ifc in preStartInfo:
        gui.print_logger(Info_ifc)
    gui.print_logger(f"Info: Собираем логи от: {', '.join(following_streamers)}.")
    gui.print_logger("Starting: Запуcкаем логгер.")
    gui.print_checker("$TYPE$Starting$TYPE$$MESS$Запускаем чеккер.$MESS$")
    gui.print_checker("$TYPE$Info$TYPE$$MESS$Слушаем https://cyberinquisitor414.glitch.me/LOGWIEWIERdb.$MESS$")

if loop:
    gui.after(500, logs_to_console)
    logger_thread.start()
    checker_thread.start()
gui.protocol('WM_DELETE_WINDOW', withdraw_window)
gui.mainloop()
