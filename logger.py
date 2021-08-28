import os, codecs, requests, sys
import subprocess, threading

from time import sleep
from datetime import datetime, timedelta

import psutil, json
from pymongo import MongoClient


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
        self.andSwitcher = False

    def set_body(self, body):
        self.body = body

    def set_streamer(self, _streamer):
        self.streamer = _streamer

    def set_date(self, date_from, date_to):
        self.date_from, self.date_to = date_from, date_to

    def set_user(self, user):
        self.user = user

    def set_mentions(self, mention_list):
        self.mentions = mention_list

    def moderation(self, boolean):
        self.moderationMSG = boolean


def check_of_chatterino():
    for process_ifc in psutil.process_iter():
        if "chatterino.exe" == process_ifc.name():
            return "Info: Chatterino обнаружен.", 1
    return "Info: Chatterino не обнаружен.", 0


def run_chatterino():
    def sub_func():
        subprocess.call(f"{path_to_chatterino}chatterino.exe")

    chatterino_thread = threading.Thread(target=sub_func)
    chatterino_thread.start()


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
                          headers={'Accept': constants["Accept"], 'Client-ID': constants["Client-ID"]}).json()
    if 'error' in id_req:
        return f"{streamer} не найден, пропускаю.", 0

    if id_req['_total'] == 0:
        return f"{streamer} не найден, пропускаю.", 0

    channel_id = id_req['users'][0]['_id']

    if datatype == "id+status":
        status_req = requests.get(f"https://api.twitch.tv/kraken/channels/{channel_id}",
                                  headers={'Accept': constants["Accept"], 'Client-ID': constants["Client-ID"]}).json()

        return channel_id, status_req["status"], 1

    elif datatype == "streams":
        stream_req = requests.get(f"https://api.twitch.tv/kraken/streams/?channel={channel_id}",
                                  headers={'Accept': constants["Accept"], 'Client-ID': constants["Client-ID"]}).json()
        if not stream_req["streams"]:
            going_offline(channel_name)
            return f"{channel_name} в офлайне."

        stream_now = stream_req["streams"][0]
        return stream_now["channel"]["status"], stream_now["_id"], stream_now["created_at"]


def addtodb_streamer(channel_name, _id, status):
    db.create_collection(channel_name)
    db["streamers"].insert_one({
        "name": channel_name,
        "id": _id,
        "status": status,
        "last_log": "",
        "last_line": 0})


def checkdb_streamer(channel_name, _id, status):
    streamer_inf = db["streamers"].find_one({"name": channel_name})
    last_log_now = streamerlist[channel_name]["last_log"]
    last_line_now = streamerlist[channel_name]["last_line"]

    if streamer_inf is None:
        addtodb_streamer(channel_name, _id, status)
        return f"{channel_name} не в базе данных, добавляем."

    if streamer_inf["status"] != status:
        db["streamers"].update_one({"name": channel_name}, {"$set": {"status": status}})
        return f"Обновляем статус у {channel_name} в базе данных."

    if streamer_inf["last_log"] != last_log_now:
        db["streamers"].update_one({"name": channel_name}, {"$set": {"last_log": last_log_now}})

    if streamer_inf["last_line"] != last_line_now:
        db["streamers"].update_one({"name": channel_name}, {"$set": {"last_line": last_line_now}})

    return 1


def getinfo_lastlog(_streamer_logs, _streamer):
    list_of_logs = [os.path.join(_streamer_logs, i) for i in os.listdir(_streamer_logs)]
    readed_log = streamerlist[_streamer]["last_log"]
    streamerlist[_streamer]["last_log"] = sorted(list_of_logs, key=os.path.getmtime)[-1]
    if streamerlist[_streamer]["last_log"] != readed_log:
        streamerlist[_streamer]["last_line"] = 0
        return f"Найден новый лог-файл.", 1
    return "пока нечего читать.", 0


def addtodb_messages(_streamer_logs, _streamer):
    log_path = streamerlist[_streamer]["last_log"]
    if log_path == '':
        getinfo_lastlog(_streamer_logs, _streamer)
        log_path = streamerlist[_streamer]["last_log"]
    log_date = log_path.split(_streamer)[-1][1:11]
    last_log_line = streamerlist[_streamer]["last_line"]
    log_file = codecs.open(log_path, "r", "utf_8_sig")
    new_logs = log_file.readlines()[last_log_line:]
    rows_added = 0
    if len(new_logs) != 0:
        for log_line in new_logs:
            streamerlist[_streamer]["last_line"] += 1
            if log_line[0] != "#" and len(log_line.split()) > 2:
                rows_added += 1
                if ":" not in log_line[12:]:
                    is_moderation = True
                    user = log_line.split()[1]
                    body = log_line.split(user)[1]
                else:
                    is_moderation = False
                    user = log_line[12:].split(":")[0]
                    body = log_line[12:].split(":")[1][1:]
            else:
                continue

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

        else:
            log_file.close()
            if rows_added != 0:
                return f"{rows_added} строк(а) добавлено в базу данных."
            return "пока нечего читать."

    log_file.close()
    loginginfo = getinfo_lastlog(_streamer_logs, _streamer)
    if loginginfo[1] != 1:
        return loginginfo[0]


def checkdb_messages(_streamer_logs, _streamer):
    if not os.path.exists(_streamer_logs) or os.listdir(_streamer_logs) == []:
        return f"Не найдены логи стримера {_streamer}, пропускаю.", 0
    addtodb_inf = addtodb_messages(_streamer_logs, _streamer)
    if addtodb_inf:
        return f"Читаем логи {_streamer}, {addtodb_inf}", 1
    else:
        return f"Читаем логи {_streamer}.", 1


constants = {'Accept': 'application/vnd.twitchtv.v5+json',
             'Client-ID': 'gp762nuuoqcoxypju8c569th9wz7q5'}

#

loop = True

connect_string = "localhost:27017"
mongodb = MongoClient(connect_string)
db = mongodb["main"]

timedelta_from_UTC = timedelta(hours=4)

config_dict = json.load(open("config.json"))

preStartInfo = []
preStartExceptions = []
following_streamers = []

path_to_chatterino = config_dict["chatterino_folder"]
path_to_logs = os.getenv('APPDATA') + "\\Chatterino2\\Logs\\Twitch\\Channels\\"
path_to_settings = os.getenv('APPDATA') + "\\Chatterino2\\Settings\\window-layout.json"

#

result_check_of_chatterino = check_of_chatterino()

if check_of_chatterino()[1] == 1:
    preStartInfo.append(result_check_of_chatterino[0])
else:
    if os.path.exists(path_to_chatterino):
        preStartInfo.append("Info: Chatterino не обнаружен, запускаем.")
        run_chatterino()

    else:
        preStartExceptions.append("Exception: Неправильный путь к папке Chatterino.")

if not os.path.exists(path_to_logs):
    preStartExceptions.append("Exception: Не найдена папка логов.")

streamerlist = {}
with open(path_to_settings, "r") as file:
    for streamer_ifc in json.load(file)['windows'][0]["tabs"]:
        stremaer = streamer_ifc["splits2"]["data"]["name"]
        following_streamers.append(stremaer)
        if db["streamers"].find_one({"name": stremaer}) is None:
            addtodb_streamer(stremaer, *(getstreamerinfo(stremaer))[:-1])

for fromdb in list(db["streamers"].find({})):
    streamerlist[fromdb["name"]] = {"last_log": fromdb["last_log"], "last_line": fromdb["last_line"]}

if preStartExceptions:
    for Exception_ifc in preStartExceptions:
        print(Exception_ifc)
    print("fatal: Запуcк невозможен.")
    loop = False
elif not preStartExceptions and preStartInfo:
    for Info_ifc in preStartInfo:
        print(Info_ifc)
    print(f"info: Собираем логи от: {', '.join(following_streamers)}.")
    print("starting: Запуcкем...")
    sleep(10)
while loop:

    # Чекируем стримеров, стримы и сообщения.
    print("(|======================================================================================================|)")
    for streamer in streamerlist:
        sleep(1)
        # Streamers
        stream_state, log_state, streamer_state = "", "", ""
        streamer_info = getstreamerinfo(streamer)
        if len(streamer_info) == 2:
            print(streamer_info[0])
            continue

        streamer_id = streamer_info[0]
        streamer_status = streamer_info[1]
        streamer_db_action = checkdb_streamer(streamer, streamer_id, streamer_status)
        if type(streamer_db_action) != int:
            streamer_state = streamer_db_action

        # Streams
        stream_info = checkdb_streams(streamer)
        if type(stream_info) != int:
            stream_state = stream_info

        # Logs
        streamer_logs = path_to_logs + streamer + "\\"
        logs_status = checkdb_messages(streamer_logs, streamer)
        log_state = logs_status[0]
        if logs_status[1] == 0:
            continue
        time_now = datetime.now().replace(microsecond=0).isoformat()
        print(f"{time_now} : {log_state} {streamer_state} {stream_state}")

    # Чекируем флаг на сервере.
