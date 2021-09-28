from twitchio.ext import commands
import logging

logging.basicConfig(handlers=[logging.FileHandler(filename="irclog.txt",
                                                 encoding='utf-8')],
                    level=logging.DEBUG)

bot = commands.Bot(token="oauth:11f2ako2oy8ol4u7cgb6swrvg9owgw", nickname="kal_zer", prefix="3",
                   initial_channels=["kaisarg213"])


@bot.event
async def event_ready():
    print("Bot ready, beginning logging")


bot.run()
