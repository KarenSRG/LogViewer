import requests
import threading
from datetime import datetime
from time import sleep
import codecs
from constants import *
from pymongo import MongoClient


class Logger:
    def __init__(self,  gui):
        self.GUI = gui

        self.db = MongoClient(connect_string)["main"]

        self.process = threading.Thread(target=self.logger_process)
        self.process.name = 'Logger'
        self.process.daemon = True

        self.streamerInfo = {}
        for stremaer_ in streamersLogging:
            dbinf = self.db["streamers"].find_one({"name": stremaer_})
            following_streamers.append(stremaer_)
            if dbinf is None:
                self.streamerInfo[stremaer_] = {"logfiles": {}}
                self.addtodb_streamer(stremaer_, *(self.getstreamerinfo(stremaer_))[:-1])
            else:
                self.streamerInfo[stremaer_] = {"logfiles": dbinf["logfiles"]}

    def logger_process(self):
        sleep(5)
        while True:
            for streamer in self.streamerInfo:
                try:
                    sleep(2)
                    stream_state, log_state, streamer_state = "", "", ""
                    # Streams
                    stream_info = self.checkdb_streams(streamer)
                    if type(stream_info) != int:
                        stream_state = stream_info
                        # Streamers
                    streamer_info = self.getstreamerinfo(streamer)
                    if len(streamer_info) == 2:
                        self.GUI.last_logLogger = f"{streamer_info[0]}\n"
                        continue
                    streamer_id = streamer_info[0]
                    streamer_status = streamer_info[1]
                    streamer_db_action = self.checkdb_streamer(streamer, streamer_id, streamer_status)
                    if type(streamer_db_action) != int:
                        streamer_state = streamer_db_action
                    # Logs
                    streamer_logs = path_to_logs + streamer + "\\"
                    logs_status = self.checkdb_messages(streamer_logs, streamer)
                    log_state = logs_status[0]
                    if logs_status[1] == 0:
                        continue
                    time_now = datetime.now().replace(microsecond=0).isoformat()
                    self.GUI.last_logLogger = f"{time_now}: {log_state} {streamer_state} {stream_state}"

                except UnicodeDecodeError or ValueError:
                    self.GUI.last_logLogger = f"Decoding: Возникла ошибка при декодировании, когда читали логи {streamer}"

    def checkdb_streams(self, channel_name):
        stream_status = self.getstreamerinfo(channel_name, "streams")
        if type(stream_status) == str:
            return stream_status
        if not self.db["streams"].find_one({"name": stream_status[0]}):
            self.db["streams"].insert_one({
                "streamer": channel_name,
                "name": stream_status[0],
                "id": stream_status[1],
                "created_at": stream_status[2],
                "finished_at": ""})
            return f'Стрим "{stream_status[0]}" от "{channel_name}" добавлен в базу данных.'
        return 1

    def going_offline(self, channel_name):
        timenow_utc = datetime.now().replace(microsecond=0).isoformat()
        self.db["streams"].update_one({"streamer": channel_name},
                                      {"$set": {"finished_at": timenow_utc}})

    def getstreamerinfo(self, channel_name, datatype="id+status"):
        id_req = requests.get(f'https://api.twitch.tv/kraken/users?login={channel_name}',
                              headers=headersAC, proxies=proxy).json()
        if 'error' in id_req:
            return f"{channel_name} не найден, пропускаю.", 0

        if id_req['_total'] == 0:
            return f"{channel_name} не найден, пропускаю.", 0

        channel_id = id_req['users'][0]['_id']

        if datatype == "id+status":
            status_req = requests.get(f"https://api.twitch.tv/kraken/channels/{channel_id}",
                                      headers=headersAC, proxies=proxy).json()

            return channel_id, status_req["status"], 1

        elif datatype == "streams":
            stream_req = requests.get(f"https://api.twitch.tv/kraken/streams/?channel={channel_id}",
                                      headers=headersAC, proxies=proxy).json()
            if not stream_req["streams"]:
                self.going_offline(channel_name)
                return f"{channel_name} в офлайне."

            stream_now = stream_req["streams"][0]
            return stream_now["channel"]["status"], stream_now["_id"], stream_now["created_at"]

    def addtodb_streamer(self, channel_name, _id, status):
        streamer_logs_ = path_to_logs + channel_name + "\\"
        list_of_logs = [os.path.join(streamer_logs_, i) for i in os.listdir(streamer_logs_)]
        for logfile in sorted(list_of_logs, key=os.path.getmtime):
            self.streamerInfo[channel_name]["logfiles"][logfile] = 0
        self.db.create_collection(channel_name)
        self.db["streamers"].insert_one({
            "name": channel_name,
            "id": _id,
            "status": status,
            "logfiles": self.streamerInfo[channel_name]["logfiles"]})

    def checkdb_streamer(self, channel_name, _id, status):
        streamer_inf = self.db["streamers"].find_one({"name": channel_name})
        last_logfiles = self.streamerInfo[channel_name]["logfiles"]

        if streamer_inf is None:
            self.addtodb_streamer(channel_name, _id, status)
            return f"{channel_name} не в базе данных, добавляем."

        if streamer_inf["status"] != status:
            self.db["streamers"].update_one({"name": channel_name}, {"$set": {"status": status}})
            return f"Обновляем статус у {channel_name} в базе данных."

        if streamer_inf["logfiles"] != last_logfiles:
            self.db["streamers"].update_one({"name": channel_name}, {"$set": {"logfiles": last_logfiles}})

        return 1

    def addtodb_message(self, log_line, _streamer, log_date):
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
        last_stream = self.db["streams"].find_one({"streamer": _streamer})
        if last_stream:
            if last_stream["finished_at"] == "":
                stream_id = last_stream["id"]

        mentions = [word for word in body.split() if "@" in word]

        if body.endswith('\n'):
            body = body[:-1]
        self.db[_streamer].insert_one({
            "date": date,
            "user": user,
            "mentions": mentions,
            "body": body,
            "stream_id": stream_id,
            "moderationMSG": is_moderation})

    def getinfo_lastlog(self, _streamer_logs, _streamer):
        rows_added = 0
        rows_skipped = 0
        logging = []
        for logfile in self.streamerInfo[_streamer]["logfiles"].keys():
            logline = self.streamerInfo[_streamer]["logfiles"][logfile]
            log_file = codecs.open(logfile, "r", "utf-8-sig", errors='ignore')
            loglines = log_file.readlines()
            if len(loglines) > logline:
                log_date = logfile.split(_streamer)[-1][1:11]
                for log_line in loglines[logline:]:
                    try:
                        if self.addtodb_message(log_line, _streamer, log_date) != "Exception":
                            rows_added += 1
                    except ValueError:
                        rows_skipped += 1
            self.streamerInfo[_streamer]["logfiles"][logfile] = len(loglines)

        list_of_logs = [os.path.join(_streamer_logs, i) for i in os.listdir(_streamer_logs)]
        lastests = sorted(list_of_logs, key=os.path.getmtime)
        log_files_inDB = self.streamerInfo[_streamer]["logfiles"].keys()

        if rows_skipped != 0:
            logging.append(f"пропущено строк {rows_skipped}")
        if lastests != log_files_inDB:
            cnt = 0
            for new_logfile in lastests:
                if new_logfile not in log_files_inDB:
                    self.streamerInfo[_streamer]["logfiles"][new_logfile] = 0
                    cnt += 1
            if cnt:
                logging.append(f"найдено новых лог-файлoв {cnt}")
        if rows_added != 0:
            if logging:
                return f"добавлено {rows_added} cтрок в базу данных, {', '.join(logging)}."
            return f"добавлено {rows_added} cтрок в базу данных."
        if logging:
            return f"пока нечего читать, {', '.join(logging)}."
        return f"пока нечего читать."

    def checkdb_messages(self, _streamer_logs, _streamer):
        if not os.path.exists(_streamer_logs) or os.listdir(_streamer_logs) == []:
            return f"Не найдены логи стримера {_streamer}, пропускаю.", 0
        addtodb_inf = self.getinfo_lastlog(_streamer_logs, _streamer)

        if addtodb_inf:
            return f"Читаем логи {_streamer}, {addtodb_inf}", 1
        else:
            return f"Читаем логи {_streamer}.", 1

    def start(self):
        self.process.start()
