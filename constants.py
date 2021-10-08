import json, os
from datetime import timedelta

headersAC = {'Accept': 'application/vnd.twitchtv.v5+json',
             'Client-ID': 'gp762nuuoqcoxypju8c569th9wz7q5'}
headersCT = {'Content-type': 'application/json'}

connect_string = "localhost:27017"

config_dict = json.load(open("config.json"))

streamersLogging = config_dict["streamers"]
proxy = config_dict["proxy"]
path_to_logs = config_dict["path_to_logs"] + "\\Twitch\\Channels\\"
oauth_token = config_dict["oauth"]
bot_nick = config_dict["bot_nick"]
timedelta_from_UTC = timedelta(hours=config_dict["timedelta_from_UTC"])

preStartInfo = []
preStartExceptions = []
following_streamers = []

