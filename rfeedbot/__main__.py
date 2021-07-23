import asyncio

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

from configparser import ConfigParser

import asyncpraw
from telethon import TelegramClient
from telethon.network.connection.tcpabridged import ConnectionTcpAbridged

config = ConfigParser()
config.read("settings.ini")

api_id = int(config.get("DEFAULT", "api_id"))
api_hash = config.get("DEFAULT", "api_hash")
bot_token = config.get("DEFAULT", "bot_token")
feed_channel_id = int(config.get("DEFAULT", "feed_channel_id"))

client = TelegramClient("session", api_id, api_hash, connection=ConnectionTcpAbridged).start(bot_token=bot_token)
praw = asyncpraw.Reddit(client_id='-fmzwojFG6JkGg', client_secret=None, user_agent='rfeedbot')

subreddits = config.get("DEFAULT", "subreddits").split("|")

async def update_feed():
    while client.is_connected():
        for subreddit in subreddits:
            curr_latest = config.get("DEFAULT", f"{subreddit}_latest", fallback=None)
            new_latest = None

            async for submission in (await praw.subreddit(subreddit)).new():
                if submission and submission.id:
                    new_latest = new_latest or submission.id

                    if curr_latest != submission.id and curr_latest is not None:
                        await client.send_message(feed_channel_id, f"https://reddit.com{submission.permalink}")
                    else:
                        break
                else:
                    break

            if curr_latest != new_latest:
                config.set("DEFAULT", f"{subreddit}_latest", new_latest)

                with open('settings.ini', 'w') as config_file:
                    config.write(config_file)
                    config_file.close()

        await asyncio.sleep(45)

client.loop.run_until_complete(update_feed())
