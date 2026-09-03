# 🤖Multifunctional Discord-bot

## 📋Description
>This is a multifunctional Discord bot written in Python.  
It includes features for moderation, music playback, ticket system, and a simple economy system.
The project is designed for learning purposes and uses JSON as a database, so it is not optimized for large-scale servers.

## 🧑‍💻Technologies

* [disnake](https://disnake.dev/)
* loguru
* [FFMPEG](https://ffmpeg.org/), yt_dlp, spotipy (music)

## 🛠 Setup and Configuration

Make sure you have Python installed. Then install the required dependencies::

1. Open the console and create a virtual environment if desired
2. Run the following commands:

    ```git clone ...```

    ```pip install -r requirements.txt```

    ```python3 bot.py```

The configuration file looks like this (```config.py```):
```
TOKEN_BOT = "your_token" # Your Discord bot token

GUILD_ID = 123123123 # Guild ID
TICKET_CHANNEL_ID = 123123123 # The channel ID where the ticket message will be sent
DEVELOPER_ID = 123123123 # Your Discord ID
LOG_CHANNEL_ID = 12312312312 # The channel where logging will be displayed

SPOTIFY_CLIENT_ID = "your_spotify_id" # https://support.heateor.com/get-spotify-client-id-client-secret/
SPOTIFY_CLIENT_SECRET = "your_spotify_secret" # https://support.heateor.com/get-spotify-client-id-client-secret/

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin',
    'options': '-vn -b:a 128k -threads 1'
}

NAME_CURRENCY = "name" # Name currency
BOT_NAME = "Bot-Name" # Your bot name
BOT_VERSION = f"{BOT_NAME}-1.4.1stable" # Bot version
MUSIC_VERSION = f"{BOT_NAME}-Music v1.3stable" # Music version
```

### 🧑‍💻 Debugging

Debugging is designed to simplify interaction with the bot's internal settings.

 The !debug command has several types:
1. ```!debug stats``` - view the bot's statistics

2. ```!debug guild_info``` - view the guild's statistics

3. ```!debug modules``` - view the enabled modules (```cogs/```)

You can also disable modules using the !modules command
Examples of the command: ```!modules music off```, ```!modules tickets on```
By default, all modules are enabled.

To add a user to the database manually, !indata *user mention*
To change the amount of virtual currency a user has manually, ```!setcoins *user mention* *amount*```

### 💸 Economy

Economy-related commands:

* ```!bal``` - view balance
* ```!bonus``` - receive a daily bonus (1-20 coins)
* ```/dice``` *opponent* *bet* - play dice with another user
* ```/top``` - top 10 by balance

The bot's economy is implemented using JSON and is located in ```cogs/user.py```, and the user database itself is located in ```data/user_data.json``` and the file looks like this:
```
{
    "123456789101112131415": {
        "123123123": {
            "balance": 123,
            "last_bonus": null
        }
    }
}
```
* "123456789101112131415" - in place of this line you will have the guild ID

* "123123123" - in place of this line you will have the Discord user ID

* "balance": 123 - User balance

* "last_bonus": null - the last bonus when using the /bonus command (the default value is null, but if the user has received a bonus, there will be a date with precision to the seconds)
### 🛡 Moderation

The moderation system is used to manage server activity and enforce rules. It is implemented in ```cogs/moderation.py```

Commands:
* ```/mute id duration reason(optional) voice_mute(optional)```
* ```/unmute id```
* ```/ban id duration reason(optional)```
* ```/unban id```
* ```/kick id reason(optional)```

Notes: 
* id implies the ability to enter the user's ID, or it can be mentioned
* duration - time in the format m/h/d (in the case of a ban, only days are used - d)
* voice_mute - the ability to issue a voice mute in voice chats when the value is True. This option is optional, as it is False by default - mute in the chat

Additionally, the **tickets** system ```cogs/tickets.py``` is also related to moderation. By default, when the bot starts, it sends an embed to the channel that must be specified in ```config.py```:
```
TICKET_CHANNEL_ID = *tickets_channel_id*
```
### 🎵 Music

The bot includes a music system with playlist support.  

Note: Music features may not work in some regions due to restrictions on **Spotify** or **YouTube**.

Commands:
* ```!play *link to a song/playlist in YouTube or Spotify*``` - play music
* ```!queue``` - shows the queue
* ```!skip``` - skip the current track and go to the next one
* ```!stop``` - stop playing music completely
* ```!toggle``` - temporarily stop music/continue playing

### 📄Logging

Logs are displayed in the console and also saved in ```log/logging.log```