import requests
from pymongo import MongoClient
from datetime import datetime
from bson.json_util import dumps
import json

connect_string = "localhost:27017"
mongodb = MongoClient(connect_string)
db = mongodb["main"]


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


response = requests.get("https://cyberinquisitor414.glitch.me/LOGWIEWIERdb").json()

logreqs = []
for req in response["whatweneed"]:
    rawlogreq = LogRequest(req["SyncID"])
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
            dateFrom = datetime.strptime(f'{logreq.date_from}', "%Y-%m-%dT%H:%M:%S.%fZ").replace(microsecond=0)
            dateTo = datetime.strptime(f'{logreq.date_to}', "%Y-%m-%dT%H:%M:%S.%fZ").replace(microsecond=0)
            for mess in list_of_mess:
                mess.pop('_id')
                messDate = mess["date"]
                mess["date"] = str(mess["date"].isoformat())
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
    print(post_data)
    post_req = requests.post("https://cyberinquisitor414.glitch.me/logsresponce",
                             json=json.loads(dumps(post_data)),
                             headers=headers)
