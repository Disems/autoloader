import es, cfglib, cmdlib, gamethread, langlib, msglib, os, playerlib, popuplib, random, usermsg

info = es.AddonInfo()
info.name = 'LooneyMapVote'
info.basename = 'looneymapvote'
info.version = '1.0'
info.url = 'http://addons.eventscripts.com/addons/view/LooneyMapVote'
info.author = 'Satoon101'
es.ServerVar('%s_version'%info.basename,info.version,'%s Version'%info.name).makepublic()

gamename = str(es.ServerVar('eventscripts_gamedir')).rsplit(os.sep, 1)[~0]
addonpath = es.getAddonPath('looneymapvote')

def getCfgText(text):
    return '%s\n// ** %s **\n// %s'%('*'*(len(text) + 6),text,'*'*(len(text) + 6))

config = cfglib.AddonCFG(addonpath + '/lmv_config.cfg')
config.text(getCfgText('LooneyMapVote Options'))
lmv_vote_style = config.cvar('lmv_vote_style',1,'0 = No Vote (random map is just selected)\n// 1 = Vote on ALL maps\n// 2 = Random type of GamePlay is chosen and then Vote on those maps\n// 3 = Vote on GamePlay and Random map chosen\n// 4 = Vote on GamePlay then Vote on map')
lmv_maps_to_not_use = config.cvar('lmv_maps_to_not_use','','Add maps (separated by a comma) that you do not want to use')
lmv_command = config.cvar('lmv_command','!vote','Command for players to get Vote popup\n// To set to no command, set to ""\n// If you choose to have no command, players will be sent the vote popup when the voting starts')
lmv_last_x_maps = config.cvar('lmv_last_x_maps',6,'Set to number of last X maps to store and not use in Votes')
lmv_time_to_vote = config.cvar('lmv_time_to_vote',60,'Set to number of seconds for Vote to last')
lmv_maps_in_vote = config.cvar('lmv_maps_in_vote',7,'Set to number of maps to randomly choose for Vote')
lmv_randomize_votes = config.cvar('lmv_randomize_votes',1,'Enable/Disable randomizing options in vote per player')
config.text('\n')
config.text(getCfgText('Start Vote Options'))
lmv_minutes_to_vote = config.cvar('lmv_minutes_to_vote',45,'Minutes to wait after start of map to start map vote')
lmv_gg_vote_level = config.cvar('lmv_gg_vote_level',15,'Start vote when first player reaches this level')
lmv_no_time_vote_for_gg = config.cvar('lmv_no_time_vote_for_gg',1,'1 = Only use GG Level Up for Vote, 0 = Use time if time happens before any player reaches the GG Level')
config.text('\n')
config.text(getCfgText('Message Options'))
lmv_start_vote_message_types = config.cvar('lmv_start_vote_message_types','chat,center,hudhint,toptext','Set to message types to use when Vote is Started\n// Available options are chat, center, hudhint, toptext\n// Separate each with ONLY a comma (no spaces)')
lmv_end_vote_message_types = config.cvar('lmv_end_vote_message_types','chat,center,hudhint,toptext','Set to message types to use to announce Vote Winner\n// Available options are chat, center, hudhint, toptext\n// Separate each with ONLY a comma (no spaces)')
lmv_announce_each_vote = config.cvar('lmv_announce_each_vote',1,'Enable/Disable announcing each players vote to all other players')
lmv_time_left_message_types = config.cvar('lmv_time_left_message_types','center,hudhint','Set to message types to use to announce Time Left to Vote\n// Available options are chat, center, hudhint, toptext\n// Separate each with ONLY a comma (no spaces)')
lmv_time_left_seconds = config.cvar('lmv_time_left_seconds','30,10,5','Place all number of seconds left to remind players to vote\n// Separate each with only a comma.  Set to "" to disable')
lmv_top_red = config.cvar('lmv_top_red',255,'Set to Red value for TopText.  Must be integer from 0 - 255')
lmv_top_green = config.cvar('lmv_top_green',0,'Set to Green value for TopText.  Must be integer from 0 - 255')
lmv_top_blue = config.cvar('lmv_top_blue',0,'Set to Blue value for TopText.  Must be integer from 0 - 255')
lmv_announce_time = config.cvar('lmv_announce_time',5,'Set to number of seconds for Vote Announcements to last for CenterText and TopText')
config.text('\n')
config.text(getCfgText('Sound Options'))
config.text('')
config.text('For all of the following, set to the sounds path relative to the <gamename>/sound/ folder\n// So, if you want to use <gamename>/sound/ui/buttonclick.wav, set to "ui/buttonclick.wav"')
lmv_sound_gameplay_start = config.cvar('lmv_sound_gameplay_start','','Sound to play when GamePlay Vote starts')
lmv_sound_gameplay_end = config.cvar('lmv_sound_gameplay_end','','Sound to play when GamePlay Vote ends')
lmv_sound_mapvote_start = config.cvar('lmv_sound_mapvote_start','','Sound to play when MapVote Vote starts')
lmv_sound_mapvote_end = config.cvar('lmv_sound_mapvote_end','','Sound to play when MapVote Vote ends')
lmv_sound_random_map = config.cvar('lmv_sound_random_map','','Sound to play when set to just pick random map')
config.text('\n')
config.text(getCfgText('Script Manager Options'))
config.text('')
config.text('With Script Manager, you can have scripts loaded based on the GamePlay that wins the vote.\n// You can also have cfg files executed based on the winning GamePlay\n// For each script to be loaded for "any" gameplay, make sure to es_unload the script in your server.cfg')
lmv_scripts_for_gameplay = config.cvar('lmv_scripts_for_gameplay',0,'Enable/Disable use of Script Manager for GamePlay')
lmv_default_gameplay = config.cvar('lmv_default_gameplay','',"Set this to one of your GamePlay types.  This is only used when es_load'ing looneymapvote to start out with a specific GamePlay")
config.write()

gameplay_ini = {}
allmaps = set()
allseconds = set()
lmv = {}

class Vote:
    options = set()
    vote_status = 0
    last_x_maps = set()
    votes = {}
    current_user_votes = {}
    gameplay = ''
    
    def mapStart(self,gameplay=''):
        self.gameplay = gameplay if gameplay else self.gameplay
        if not self.gameplay or not self.gameplay in gameplay_ini or not lmv_scripts_for_gameplay: return
        for script in gameplay_ini[self.gameplay]['Scripts']:
            es.load(gameplay_ini[self.gameplay]['Scripts'][script])
        for cfg in gameplay_ini[self.gameplay]['Configs']:
            es.server.queuecmd('es_mexec ../%s/%s.cfg'%(gamename,gameplay_ini[self.gameplay]['Configs'][cfg]))
    
    def resetMapVote(self,currentmap):
        self.gameplay = 0
        self.options.clear()
        self.vote_status = 0
        self.last_x_maps.add(currentmap)
        while len(self.last_x_maps) > lmv_last_x_maps:
            self.last_x_maps.remove(self.last_x_maps[0])
        self.cancelDelays()
    
    def startVote(self):
        if self.vote_status: return
        if lmv_vote_style == 0:
            self.playSound(lmv_sound_random_map)
            self.setNextMap(random.choice(list(allmaps.difference(self.last_x_maps))))
        if lmv_vote_style == 1:
            self.startMapVote(list(allmaps.difference(self.last_x_maps)))
        if lmv_vote_style == 2:
            self.gameplay = random.choice(list(lmv['maps']))
            self.startMapVote(list(set(lmv['maps'][self.gameplay].values()).difference(self.last_x_maps)))
        if lmv_vote_style == 3:
            self.startGamePlayVote(False)
        if lmv_vote_style == 4:
            self.startGamePlayVote()
    
    def startGamePlayVote(self,do_map_vote=True):
        self.vote_status = 1
        self.votes.clear()
        self.options = set(lmv['maps'])
        if lmv['command']:
            self.sendAllPlayersMessages('Start GamePlay Vote',{'command':lmv['command']},str(lmv_start_vote_message_types).split(','))
        else:
            self.sendAllPlayersVote()
        self.playSound(lmv_sound_gameplay_start)
        gamethread.delayedname(lmv_time_to_vote,'lmv_GamePlayVote',self.endGamePlayVote,do_map_vote)
        self.sendReminders()
    
    def endGamePlayVote(self,do_map_vote):
        self.unsendVotes('Vote on GamePlay')
        self.vote_status = 2
        self.current_user_votes.clear()
        self.gameplay = str(self.getWinner())
        self.sendAllPlayersMessages('End GamePlay Vote',{'gameplay':self.gameplay},str(lmv_end_vote_message_types).split(','))
        mapsToVote = list(set(lmv['maps'][self.gameplay].values()).difference(self.last_x_maps))
        self.playSound(lmv_sound_gameplay_end)
        self.options.clear()
        if do_map_vote:
            gamethread.delayedname(lmv_announce_time,'lmv_BetweenVotes',self.startMapVote,mapsToVote)
        else:
            self.vote_status = 3
            gamethread.delayedname(lmv_announce_time,'lmv_NoMapVote',self.setNextMap,random.choice(mapsToVote))
    
    def startMapVote(self,mapsToVote):
        if not self.vote_status in (0,2): return
        self.votes.clear()
        self.vote_status = 4
        self.options = set(random.sample(mapsToVote,min(len(mapsToVote),int(lmv_maps_in_vote))))
        if lmv['command']:
            self.sendAllPlayersMessages('Start Map Vote',{'command':lmv['command']},str(lmv_start_vote_message_types).split(','))
        else:
            self.sendAllPlayersVote()
        self.playSound(lmv_sound_mapvote_start)
        gamethread.delayedname(lmv_time_to_vote,'lmv_MapVote',self.endMapVote)
        self.sendReminders()
    
    def endMapVote(self):
        self.unsendVotes('Vote on Map')
        self.setNextMap(str(self.getWinner()))
        self.playSound(lmv_sound_mapvote_end)
        self.current_user_votes.clear()
        self.votes.clear()
        self.options.clear()
    
    def setNextMap(self,nextmap):
        self.vote_status = 5
        self.nextmap = nextmap
        self.sendAllPlayersMessages('End Map Vote',{'nextmap':self.nextmap},str(lmv_end_vote_message_types).split(','))
        es.set('eventscripts_nextmapoverride',self.nextmap)
    
    def sendReminders(self):
        for second in str(lmv_time_left_seconds).split(','):
            if second.isdigit() and 0 < int(second) < int(lmv_time_to_vote):
                second = int(second)
                seconds_to_wait = int(lmv_time_to_vote) - second
                allseconds.add(second)
                gamethread.delayedname(seconds_to_wait,'lmv_reminder_%s'%second,self.sendAllPlayersMessages,('One Second Remains' if second == 1 else 'Time Remaining',{'seconds':second},str(lmv_time_left_message_types).split(','),True))
    
    def getWinner(self):
        if not len(self.votes): return random.choice(list(self.options))
        return random.choice(filter(lambda nextmap: self.votes[nextmap] == self.votes[sorted(self.votes, key=lambda nextmap: self.votes[nextmap], reverse=True)[0]], self.votes))
    
    def sendAllPlayersVote(self):
        for userid in playerlib.getUseridList('#human'):
            self.sendPlayerVoteMenu(userid)
    
    def sendPlayerVoteMenu(self,userid):
        if not es.getuserid(userid): return
        player = playerlib.getPlayer(userid)
        message, tokens = self.checkSendVote(player.uniqueid(True))
        if message:
            es.tell(userid,'#multi',lmv['lang'](message,tokens,player.lang))
        elif popuplib.isqueued('Vote on GamePlay_%s'%userid,userid) or popuplib.isqueued('Vote on Map_%s'%userid,userid): return
        else:
            if lmv_randomize_votes:
                options = list(self.options)
                random.shuffle(options)
                self.options = set(options)
            popupname = 'Vote on GamePlay' if self.vote_status == 1 else 'Vote on Map'
            uservotemenu = popuplib.easymenu('%s_%s'%(popupname,userid),'choice',self.getPlayerVote)
            uservotemenu.settitle(lmv['lang'](popupname,lang=player.lang))
            for option in self.options:
                uservotemenu.addoption(option,lmv['lang'](option,lang=player.lang) if self.vote_status == 1 else option)
            uservotemenu.send(userid)
    
    def checkSendVote(self,uniqueid):
        if not self.vote_status: return ('Vote Not Started',{})
        elif self.vote_status == 2: return ('Between Votes',{})
        elif self.vote_status == 3: return ('Vote Over',{})
        elif self.vote_status == 5: return ('NextMap Decided',{'nextmap':self.nextmap})
        elif uniqueid in self.current_user_votes: return ('Already Voted',{'playervote':self.current_user_votes[uniqueid]})
        return (False,{})
    
    def getPlayerVote(self,userid,choice,popupid):
        player = playerlib.getPlayer(userid)
        self.current_user_votes[player.uniqueid(True)] = choice
        if not choice in self.votes:
            self.votes[choice] = 0
        self.votes[choice] += 1
        if lmv_announce_each_vote:
            self.sendAllPlayersMessages('Player Vote',{'player':player.name,'choice':choice},'chat')
    
    @staticmethod
    def unsendVotes(popupname):
        for userid in playerlib.getUseridList('#human'):
            if popuplib.isqueued('%s_%s'%(popupname,userid),userid):
                popuplib.unsendname('%s_%s'%(popupname,userid),userid)
    
    @staticmethod
    def playSound(sound):
        if not str(sound): return
        for userid in playerlib.getUseridList('#human'):
            es.playsound(userid,sound,1.0)
    
    @staticmethod
    def sendAllPlayersMessages(message,tokens,message_types,reminder=False):
        for player in playerlib.getPlayerList('#human'):
            pmessage = lmv['lang'](message,tokens,player.lang)
            if 'chat' in message_types:
                es.tell(player.userid,'#multi',pmessage)
            for color in ('#default','#green','#lightgreen','[LooneyMapVote]'):
                pmessage = pmessage.replace(color,'')
            ptime = 1 if reminder else lmv_announce_time
            if 'hudhint' in message_types:
                usermsg.hudhint(player.userid,pmessage)
            if 'center' in message_types:
                for second in range(ptime):
                    gamethread.delayed(second,usermsg.centermsg,(player.userid,pmessage))
            if 'toptext' in message_types:
                msglib.VguiDialog(pmessage,pmessage,5,'%s %s %s 255'%(lmv_top_red,lmv_top_green,lmv_top_blue),ptime).send(player.userid)
    
    @staticmethod
    def cancelDelays():
        for delayname in ('lmv_GamePlayVote','lmv_BetweenVotes','lmv_MapVote','lmv_NoMapVote','lmv_TimeVote'):
            gamethread.cancelDelayed(delayname)
        for second in allseconds:
            gamethread.cancelDelayed('lmv_reminder_%s'%second)

mapVote = Vote()

def load():
    config.execute()
    lmv['command'] = str(lmv_command)
    if lmv['command']:
        cmdlib.registerSayCommand(lmv['command'],sendVote,'Send Player Vote popup')
        cmdlib.registerClientCommand(lmv['command'],sendVote,'Send Player Vote popup')
    ini = cfglib.AddonINI(addonpath + '/strings.ini')
    ini.addValueToGroup('Vote on GamePlay','en','Vote for next GamePlay:')
    ini.addValueToGroup('Vote on Map','en','Vote on a Map:')
    ini.addValueToGroup('Start GamePlay Vote','en','#green[LooneyMapVote]#default Use the command "#lightgreen$command#default" to vote for the next GamePlay')
    ini.addValueToGroup('End GamePlay Vote','en','#green[LooneyMapVote]#default Next GamePlay will be#lightgreen $gameplay#default!')
    ini.addValueToGroup('Start Map Vote','en','#green[LooneyMapVote]#default Use the command "#lightgreen$command#default" to Vote for the next Map')
    ini.addValueToGroup('End Map Vote','en','#green[LooneyMapVote]#default Next Map is#lightgreen $nextmap#default!')
    ini.addValueToGroup('Vote Not Started','en','#green[LooneyMapVote]#default Vote has not started yet')
    ini.addValueToGroup('Between Votes','en','#green[LooneyMapVote]#default Please wait to use this command, we are between votes')
    ini.addValueToGroup('Vote Over','en','#green[LooneyMapVote]#default Sorry, voting is over')
    ini.addValueToGroup('NextMap Decided','en','#green[LooneyMapVote]#default NextMap has already been decided.#lightgreen  NextMap#default:#green $nextmap')
    ini.addValueToGroup('Already Voted','en','#green[LooneyMapVote]#default You already voted for#lightgreen $playervote')
    ini.addValueToGroup('Player Vote','en','#green[LooneyMapVote]#default $player voted for#lightgreen $choice')
    ini.addValueToGroup('Time Remaining','en','#green[LooneyMapVote]#default Vote ends in $seconds seconds')
    ini.addValueToGroup('One Second Remains','en','#green[LooneyMapVote]#default Vote ends in 1 second')
    lmv['maps'] = cfglib.AddonINI(addonpath + '/maptypes.ini')
    for mapbsp in os.listdir(str(es.ServerVar('eventscripts_gamedir')) + '/maps/'):
        if not mapbsp.endswith('.bsp'): continue
        mapname = mapbsp[0:~3]
        if mapname in str(lmv_maps_to_not_use).split(','): continue
        allmaps.add(mapname)
        if notInHeader(mapname):
            prefix = mapname.split('_')[0] + '_'
            lmv['maps'].addValueToGroup(prefix,getNumber(prefix),mapname)
    lmv['maps'].write()
    serverlang = langlib.getDefaultLang()
    for gameplay in lmv['maps']:
        ini.addValueToGroup(gameplay,serverlang,gameplay)
    first = True
    for group in ini:
        if first:
            first = False
        else:
            ini.setGroupComments(group,'')
    ini.write()
    lmv['lang'] = langlib.Strings(ini)
    if lmv_scripts_for_gameplay:
        scriptpath = addonpath + '/scriptmanager'
        if not os.path.isdir(scriptpath):
            os.makedirs(scriptpath)
        for gameplay in lmv['maps']:
            gameplay_ini[gameplay] = cfglib.AddonINI(scriptpath + '/%s.ini'%gameplay)
            gameplay_ini[gameplay].addValueToGroup('Scripts','1','')
            gameplay_ini[gameplay].setGroupComments('Scripts',['Set scripts to be loaded for maptype below','Use a different number for each and follow the same syntax'])
            gameplay_ini[gameplay].addValueToGroup('Configs','1','')
            gameplay_ini[gameplay].setGroupComments('Configs',['Set .cfg files to be executed for maptype below','Use a different number for each and follow the same syntax','Please use the path relative to <gamename>','For instance, if your cfg is in <gamename>/cfg/myconfigs/configone.cfg, you would use "cfg/myconfigs/configone"'])
            gameplay_ini[gameplay].write()
    mapVote.mapStart(str(lmv_default_gameplay))
    mapVote.resetMapVote(str(es.ServerVar('eventscripts_currentmap')))
    startTimeVote()

def unload():
    if lmv['command']:
        cmdlib.unregisterSayCommand(lmv['command'])
        cmdlib.unregisterClientCommand(lmv['command'])
    mapVote.cancelDelays()

def es_map_start(ev):
    mapVote.mapStart()
    mapVote.resetMapVote(ev['mapname'])
    startTimeVote()

def startTimeVote():
    gamethread.cancelDelayed('lmv_TimeVote')
    gamethread.delayedname(lmv_minutes_to_vote * 60,'lmv_TimeVote',mapVote.startVote)
    doDownloads()

def notInHeader(mapname):
    for header in lmv['maps']:
        for value in lmv['maps'][header]:
            if mapname == lmv['maps'][header][value]: return False
    return True

def getNumber(header):
    length = len(lmv['maps'][header])
    if not length: return '0'
    for num in range(length):
        if not str(num) in lmv['maps'][header]: return str(num)
    return str(length)

def doDownloads():
    for sound in (lmv_sound_gameplay_start,lmv_sound_gameplay_end,lmv_sound_mapvote_start,lmv_sound_mapvote_end,lmv_sound_random_map):
        if str(sound):
            es.stringtable('downloadables','sound/%s'%sound)

def gg_levelup(ev):
    if lmv_no_time_vote_for_gg:
        gamethread.cancelDelayed('lmv_TimeVote')
    if int(ev['new_level']) == lmv_gg_vote_level:
        mapVote.startVote()

def sendVote(userid,args):
    mapVote.sendPlayerVoteMenu(str(userid))