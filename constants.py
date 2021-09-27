import json, os
from datetime import timedelta

headersAC = {'Accept': 'application/vnd.twitchtv.v5+json',
             'Client-ID': 'gp762nuuoqcoxypju8c569th9wz7q5'}
headersCT = {'Content-type': 'application/json'}

connect_string = "localhost:27017"

config_dict = json.load(open("config.json"))

proxy = config_dict["proxy"]
path_to_chatterino = config_dict["chatterino_folder"]
path_to_logs = config_dict["path_to_logs"] + "\\Twitch\\Channels\\"
timedelta_from_UTC = timedelta(hours=config_dict["timedelta_from_UTC"])

path_to_settings = os.getenv('APPDATA') + "\\Chatterino2\\Settings\\window-layout.json"

preStartInfo = []
preStartExceptions = []
following_streamers = []

last_logLogger = ""
last_logChecker = ""
last_logLoggerOLD = ""
last_logCheckerOLD = ""




