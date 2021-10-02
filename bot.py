from twitchio.ext import commands
from datetime import datetime, date
from constants import *
import os, codecs


class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=oauth_token, prefix='?',
                         initial_channels=['insize', "honeymad", "gandreich", "sgtgrafoyni"])
        self.lst = []

    async def event_raw_data(self, raw):
        raw_set = raw.split(";")
        timestamp = ""
        if "@ban-duration" in raw_set[0]:
            channel = raw_set[-1].split()[3]
            username = raw_set[-1].split(channel)[1][2:]
            duration = raw_set[0].split("=")[1]
            for param in raw_set:
                if "tmi-sent-ts" in param:
                    ms = int(param.split("=")[1][:14])
                    timestamp = datetime.fromtimestamp(ms / 1000).strftime('[%H:%M:%S]')
            log_to_doc(channel[1:], f"{timestamp} {username[:-2]} has been timed out for {duration} seconds.\n")
        elif "@ban-duration" not in raw_set[0] and "CLEARCHAT" in raw_set[-1]:
            channel = raw_set[-1].split()[3]
            username = raw_set[-1].split(channel)[1][2:]
            for param in raw_set:
                if "tmi-sent-ts" in param:
                    ms = int(param.split("=")[1][:14])
                    timestamp = datetime.fromtimestamp(ms / 1000).strftime('[%H:%M:%S]')
            log_to_doc(channel[1:], f"{timestamp} {username[:-2]} has been permanently banned.\n")

    async def event_message(self, message):
        timestamp = str((message.timestamp + timedelta_from_UTC).replace(microsecond=0)).split()
        log_to_doc(message.channel.name, f"[{timestamp[1]}]  {message.author.name}: {message.content}\n")


def log_to_doc(channel, log):
    if not os.path.exists(f"{path_to_logs}{channel}"):
        os.mkdir(f"{path_to_logs}{channel}")
    path = f"{path_to_logs}{channel}\\{channel}-{date.today()}.log"
    with codecs.open(path, 'a+', encoding="utf-8", errors="replace") as file:
        file.write(log)


if irc_bot:
    bot = Bot()
    bot.run()
