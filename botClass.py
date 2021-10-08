from twitchio.ext import commands
from datetime import datetime, date
import codecs
import asyncio
import threading
from constants import *


class Bot(commands.Bot):
    def __init__(self, gui):
        super().__init__(token=oauth_token, prefix='###666@@@',
                         initial_channels=streamersLogging)
        self.process = threading.Thread(target=self.ircbot_process)
        self.process.name = 'ircBot'
        self.process.daemon = True
        self.GUI = gui

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
            self.log_to_doc(channel[1:], f"{timestamp} {username[:-2]} has been timed out for {duration} seconds.\n")
        elif "@ban-duration" not in raw_set[0] and "CLEARCHAT" in raw_set[-1]:
            channel = raw_set[-1].split()[3]
            username = raw_set[-1].split(channel)[1][2:]
            for param in raw_set:
                if "tmi-sent-ts" in param:
                    ms = int(param.split("=")[1][:14])
                    timestamp = datetime.fromtimestamp(ms / 1000).strftime('[%H:%M:%S]')
            self.log_to_doc(channel[1:], f"{timestamp} {username[:-2]} has been permanently banned.\n")

    async def event_message(self, message):
        timestamp = str((message.timestamp + timedelta_from_UTC).replace(microsecond=0)).split()
        self.log_to_doc(message.channel.name, f"[{timestamp[1]}]  {message.author.name}: {message.content}\n")

    def log_to_doc(self, channel, log):

        self.GUI.logged_messages[channel] += 1
        if not os.path.exists(f"{path_to_logs}{channel}"):
            os.mkdir(f"{path_to_logs}{channel}")
        path_channel = f"{path_to_logs}{channel}\\{channel}-{date.today()}.log"
        with codecs.open(path_channel, 'a+', encoding="utf-8", errors="replace") as file:
            file.write(log)

    def ircbot_process(self):
        loop_bot = asyncio.new_event_loop()
        asyncio.set_event_loop(loop_bot)
        self.run()

    def start(self):
        self.process.start()
