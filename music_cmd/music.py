import discord
from discord.ext import commands
from youtube_dl import YoutubeDL as yt
import json, asyncio, random, datetime

MFILE = open('./music_cmd/music_config.json','r')
MDATA = json.load(MFILE)

class Music(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

        self.is_looped = False
        self.is_paused = False
        self.is_playing = False

        self.music_queue = []
        self.now_playing = None

        self.vc = None
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    @commands.command(name='join',aliases=["j"], help=MDATA["c_help"]["j"])
    async def _join(self,ctx,*args):
        if self.vc != None:
            await ctx.send("Already joined the voice channel")
            return

        self.vc = await ctx.message.author.voice.channel.connect()
        self.is_looped = False
        self.is_paused = False
        self.is_playing = False

        self.music_queue = []
        self.now_playing = None

        if self.vc == None:
            await ctx.send("Can not join voice channel!")
            return

        await ctx.send(f"Bot connects to the voice channel {ctx.message.author.voice.channel.name}!")

    
    @commands.command(name="leave", aliases=["l", "disconnect", "d"], help=MDATA["c_help"]["l"])
    async def _leave(self, ctx, *args):
        if self.vc == None:
            await ctx.send("Already left the voice channel")
            return

        self.is_playing = False
        self.is_looped = False
        self.is_paused = False
        self.index = 0 #don't use pop, so I can implement loop feature

        await self.vc.disconnect()
        self.music_queue = []
        self.vc = None
        self.now_playing = None

        await ctx.send(f"Bot disconnects from the voice channel {ctx.message.author.voice.channel.name}!")


    def __search(self, item):
        try:
            if item.startswith("https:"):
                downloader = yt(self.YDL_OPTIONS)
                r = downloader.extract_info(item, download = False)
            else:
                downloader = yt(self.YDL_OPTIONS)
                r = downloader.extract_info(f"ytsearch:{item}", download=False)['entries'][0]
        except:
            return False

        return {'url': r.get('url'), 
        'uploader': r.get('uploader'), 
        'title': r.get('title'), 
        'duration': r.get('duration'), 
        'webpage_url': r.get('webpage_url'), 
        'thumbnail': r.get('thumbnails')[0]['url']}

    @commands.command(name="insert", aliases=["i",], help=MDATA["c_help"]["i"])
    async def _insert(self, ctx, *args):
        query = " ".join(args)

        if ctx.author.voice == None or self.vc == None:
            await ctx.send("Can not insert the song you request!")
            return
        elif self.is_paused:
            return
        else:
            song = self.__search(query)
            if type(song) == type(True):
                await ctx.send("Can not fetch the song information")
            else:
                await ctx.send(f"Song {song['title']} inserts into the queue") #should use a embbed messasge
                self.music_queue.insert(0, ([song, ctx.author.voice.channel, ctx.author.voice]))
        
    @commands.command(name='play', aliases=["p"], help=MDATA["c_help"]["p"])
    async def _play(self, ctx, *args):
        query = " ".join(args)

        if ctx.author.voice == None:
            await ctx.send("Please join the voice channel!")
            return
        elif self.is_paused:
            return
        else:
            song = self.__search(query)
            if type(song) == type(True):
                await ctx.send("Can not fetch the song information")
            else:
                await ctx.send(f"Song {song['title']} added the queue") #should use a embbed messasge
                self.music_queue.append([song, ctx.author.voice.channel, ctx.author.voice])

                if self.is_playing == False:
                    await self.__play_music(ctx)

    async def __play_music(self, ctx):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['url']

            if self.vc == None or not self.vc.is_connected():
                self.vc = await self.music_queue[0][1].connect()

                if self.vc == None:
                    ctx.send(f'Can not move to the voice channel!')
                    return 

            elif self.vc.channel.id != self.music_queue[0][1].id:
                await self.vc.move_to(self.music_queue[0][1])

            self.now_playing = self.music_queue.pop(0)
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e:self.__play_next())
        else:
            self.is_playing = False
    
    def __play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True
            m_url = self.music_queue[0][0]['url']

            self.now_playing = self.music_queue.pop(0)
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e:self.__play_next())
        else:
            self.is_playing = False

    @commands.command(name='skip', aliases=["s"], help=MDATA["c_help"]["s"])
    async def _skip(self, ctx):
        if self.vc != None and self.vc:
            self.vc.stop()
            await ctx.send(f"Skip the music {self.now_playing[0]['title']}!")
            await self.__play_music(ctx)

    @commands.command(name="clear", aliases=["c", "bin"], help=MDATA["c_help"]["c"])
    async def _clear(self, ctx):
        if self.vc != None and self.is_playing:
            self.vc.stop()

        self.music_queue = []
        self.now_playing = None
        await ctx.send("Music queue cleared!")

    @commands.command(name="queue", aliases=["q"], help=MDATA["c_help"]["q"])
    async def _queue(self, ctx):
        if len(self.music_queue) > 0:
            songlist = discord.Embed(title="Song Queue", color = 0xff3838)

            for idx in range(0, len(self.music_queue)):
                if (idx > 6):
                    break
                
                songlist.add_field(name = f'{idx+1}.', value = self.music_queue[idx][0]['title'])
            
            songlist.set_footer(text="All artworks credit to the artist @Zzul0714 // 哈哈屁眼")
            ran_num = random.randint(1,4)
            picfile = discord.File(MDATA['q_img'][str(ran_num)], filename = MDATA['q_img'][str(ran_num)].split('/')[3])
            songlist.set_thumbnail(url= "attachment://{}".format(MDATA['q_img'][str(ran_num)].split('/')[3]))
            await ctx.send( file = picfile, embed = songlist)
        else:
            await ctx.send("No song in the queue!")
    
    @commands.command(name="pause", help=MDATA["c_help"]["pause"])
    async def _pause(self, ctx):
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()
            await ctx.send(f"Pauses the song {self.now_playing[0]['title']}!")
        elif self.is_paused:
            self.is_paused = False
            self.is_playing = True
            self.vc.resume()
            await ctx.send(f"Resumes the song {self.now_playing[0]['title']}!")

    @commands.command(name="resume", aliases=["r"], help=MDATA["c_help"]["r"])
    async def _resume(self, ctx):
        if self.is_paused:
            self.is_paused = False
            self.is_playing = True
            self.vc.resume()
            await ctx.send(f"Resumes the song {self.now_playing[0]['title']}!")
        else:
            await ctx.semd("The song is currently playing!")
    
    @commands.command(name="nowplaying", aliases=["n", "np"], help=MDATA["c_help"]["n"])
    async def _now_playing(self,ctx):
        if self.now_playing:
            song = discord.Embed(title = "Current Song Playing", url = self.now_playing[0]["webpage_url"], color = 0xff3838)
            song.add_field(name = self.now_playing[0]['title'], value = f"Author: {self.now_playing[0]['uploader']}\nDuration: {str(datetime.timedelta(seconds=self.now_playing[0]['duration']))}")
            song.set_thumbnail(url = self.now_playing[0]["thumbnail"])
            await ctx.send(embed = song)
        else:
            await ctx.send("No current song is playing!")

async def setup(bot):
    await bot.add_cog(Music(bot))      




    