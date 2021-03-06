import discord
from discord.ext import commands

from datetime import datetime, timedelta
from discord.utils import get
from discord import FFmpegPCMAudio
from discord.voice_client import VoiceClient
from discord import Embed


from youtube_dl import YoutubeDL

numbers = ("1️⃣", "2⃣", "3⃣", "4⃣", "5⃣",
           "6⃣", "7⃣", "8⃣", "9⃣", "🔟")


class musicRate(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.polls = []

        # all the music related stuff
        self.is_playing = False

        # 2d array containing [song, channel]
        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        self.vc = ""

     # searching the item on youtube

    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" %
                                        item, download=False)['entries'][0]
            except Exception:
                return False

        return {'source': info['formats'][0]['url'], 'title': info['title']}

    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            # get the first url
            m_url = self.music_queue[0][0]['source']

            # remove the first element as you are currently playing it
            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(
                m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    # infinite loop checking
    async def play_music(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']

            # try to connect to voice channel if you are not already connected

            if self.vc == "" or not self.vc.is_connected() or self.vc == None:
                self.vc = await self.music_queue[0][1].connect()
            else:
                await self.vc.move_to(self.music_queue[0][1])

            print(self.music_queue)
            # remove the first element as you are currently playing it
            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(
                m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    @commands.command(name="play", help="Plays a selected song from youtube")
    async def play(self, ctx, *args):
        query = " ".join(args)

        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            # you need to be connected so that the bot knows where to go
            await ctx.send("Connect to a voice channel!")
        else:
            song = self.search_yt(query)
            if type(song) == type(True):
                await ctx.send("Could not download the song. Incorrect format try another keyword. This could be due to playlist or a livestream format.")
            else:
                await ctx.send("Song added to the queue! Make sure to use the command '//rate' to give this song a rating!")
                self.music_queue.append([song, voice_channel])

                if self.is_playing == False:
                    await self.play_music()

                # code to vote on the music or function

    @commands.command(name="queue", help="Displays the current songs in queue")
    async def queue(self, ctx):
        retval = ""
        for i in range(0, len(self.music_queue)):
            retval += self.music_queue[i][0]['title'] + "\n"

        print(retval)
        if retval != "":
            await ctx.send(retval)
        else:
            await ctx.send("No music in queue")

    @commands.command(name="skip", help="Skips the current song being played")
    async def skip(self, ctx):
        if self.vc != "" and self.vc:
            self.vc.stop()
            # try to play next in the queue if it exists
            await self.play_music()

    @commands.command(name="pause", help="Pause music")
    async def pause(self, ctx):

        if self.vc != "" and self.vc:
            self.vc.pause()

    @commands.command(name="resume", help="Resume pause music")
    async def resume(self, ctx):

        if self.vc != "" and self.vc:

            self.vc.resume()

    @commands.command(name="disconnect", help="Disconnect from channel")
    async def disconnect(self, ctx):

        if self.vc != "" and self.vc:

            await self.vc.disconnect()

    @commands.command(name="rate", help="Help out by rating the song so we know how good the server thinks it is!")
    async def rate(self, ctx, *options):

        self.ctx = ctx
        # emoji's 1-10
        self.emoji = ['1\u20e3', '2\u20e3', '3\u20e3', '4\u20e3', '5\u20e3',
                      '6\u20e3', '7\u20e3', '8\u20e3', '9\u20e3', '\U0001F51F']

        options = ("This is Music?", "Yeah... no", "If I'm forced to", "Wouldn't play alone", "Meh.. not bad",
                   "Okay", "This is kinda nice", "I like it!", "Dang! Where'd you find this!", "*__GODLIKE__*")


        author_name = ctx.author.mention

        embed = Embed(title=(author_name + " wants to rate this song!"),
                      description="Give it your best score out of 10!",
                      color=ctx.author.color,
                      timestamp=datetime.utcnow())

        fields = [("Options", "\n".join([f"{numbers[idx]} {option}" for idx, option in enumerate(options)]), False),
                  ("Instructions", "React to cast a vote!", False)]

        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

        message = await ctx.send(embed=embed)

        for emoji in numbers[:len(options)]:

            await message.add_reaction(emoji)

        # variable for length of poll
        mins = 5

        self.polls.append((message.channel.id, message.id))

        self.bot.scheduler.add_job(self.complete_poll, "date", run_date=datetime.now()+timedelta(seconds=mins),
                                   args=[message.channel.id, message.id])

    async def complete_poll(self, channel_id, message_id):

        message = await self.bot.get_channel(channel_id).fetch_message(message_id)

        most_voted = max(message.reactions, key=lambda r: r.count)

        await message.channel.send(f"This song has been rated a {most_voted.emoji} by the crowd!")
        self.polls.remove((message.channel.id, message.id))
