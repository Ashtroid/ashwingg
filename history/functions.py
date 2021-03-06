import requests
try:
    import ujson as json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        import json
import os
import timeago, datetime
from league.settings import BASE_DIR, API_KEY, lol_patch, lol_version
from . import config
from .models import MatchInfo
from roleidentification import pull_data, get_roles
import multiprocessing as mp
from functools import partial

def requestSummonerId(id, region):
	response = callAPI(id, region, "/lol/summoner/v4/summoners/by-name/")
	return response

def requestSummonerInfoById(id, region):
	response = callAPI(id, region, "/lol/league/v4/entries/by-summoner/")
	return response

def getSummonersInActiveGame(summonerId, region):
	response = callAPI(summonerId, region, "/lol/spectator/v4/active-games/by-summoner/")
	return response

def requestMatchesById(id, region, startGame):
	startGame = int(startGame)
	numGames = 5
	beginTime = 1605312000000
	URL = "https://%s.api.riotgames.com/lol/match/v4/matchlists/by-account/%s?queue=420&beginIndex=%d&endIndex=%d&beginTime=%d&api_key=%s" % (region, id, startGame, startGame + numGames, beginTime, API_KEY)
	response = requests.get(URL)
	return response.json()

def getAccountStats(id, region):
	summonerDataList = requestSummonerInfoById(id, region).json()
	for summonerData in summonerDataList:
		if summonerData["queueType"] == "RANKED_SOLO_5x5":
			return summonerData
	return 404

def getMatchData(id, region):
	matchData = callAPI(id, region, "/lol/match/v4/matches/")
	return matchData.json()

def getSummonersInActiveGame(summonerId, region):
	response = callAPI(summonerId, region, "/lol/spectator/v4/active-games/by-summoner/")
	return response

def callAPI(id, region, APIUrl):
	URL = "https://" + region + ".api.riotgames.com" + APIUrl + str(id) + "?api_key=" + API_KEY
	return requests.get(URL)

def timeStatus(epochTime):
	date = datetime.datetime.fromtimestamp(epochTime//1000)
	now = datetime.datetime.now()
	return timeago.format(date, now)

def gameDuration(seconds):
	hours = seconds//3600
	seconds = seconds%3600
	minutes = seconds//60
	seconds = seconds%60
	if hours > 0:
		return "%dh %dm %ds" % (hours, minutes, seconds)
	return " %dm %ds" % (minutes, seconds)

def getRunes(stats):
	map = json.load(open(os.path.join(BASE_DIR, "history/static/runes.json")))
	runes = []
	for i in range(0, 6):
		perkStr = 'perk' + str(i)
		if perkStr in stats:
			runes.append(map.get(str(stats[perkStr])))
	if 'perkSubStyle' in stats:
		subRune = map.get(str(stats['perkSubStyle']))
	else:
		subRune = ''
	return {'all': runes, 'subRune': subRune}

#update on champion release
def getParticipantData(champion_roles, participantDataMap, unsortedChampListBlue, unsortedChampListRed):
	participantData = []
	roles = ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY']
	#champion_roles[360] = {'JUNGLE': 0.0, 'TOP': 0.0, 'MIDDLE': 0.0, 'BOTTOM': 1.0, 'UTILITY': 0.0}
	blueRoles = get_roles(champion_roles, unsortedChampListBlue)
	redRoles = get_roles(champion_roles, unsortedChampListRed)
	teams = [blueRoles, redRoles]
	for team in teams:
		participantDataList = []
		for role in roles:
			participantDataMap[team[role]]['role'] = role
			participantDataList.append(participantDataMap[team[role]])
		participantData.append(participantDataList)
	return participantData

def getCurrentMatchResult(summonerId, region):
	response = getSummonersInActiveGame(summonerId, region)
	match = response.json()
	if response.status_code != 200 or "gameQueueConfigId" not in match or match["gameQueueConfigId"] != 420:
		return {"status": 0}
	result = getLiveMatchData(match, summonerId, region)
	return {"status": 1, "matchData": result}

def getCurrentMatchResultBoolean(summonerId, region):
	response = getSummonersInActiveGame(summonerId, region)
	match = response.json()
	return response.status_code == 200 and "gameQueueConfigId" in match and match["gameQueueConfigId"] == 420

def getLiveMatchData(match, summonerId, region):
	championDict = json.load(open(os.path.join(BASE_DIR, "history/static/champions.json")))
	summonerSpell = json.load(open(os.path.join(BASE_DIR, "history/static/summonerSpell.json")))
	summoner = requests.get("%s/%s/data/en_US/summoner.json"%(lol_version, lol_patch)).json()["data"]
	map = json.load(open(os.path.join(BASE_DIR, "history/static/runes.json")))
	matchInfo = dict()
	gameStartTime = match["gameStartTime"]
	if gameStartTime == 0:
		matchInfo["gameDelta"] = 0
	else:
		matchInfo["gameDelta"] = int(datetime.datetime.now().timestamp() - gameStartTime//1000)
	participantDataMap = dict()
	champion_roles = pull_data()
	unsortedChampListBlue = []
	unsortedChampListRed = []
	for participant in match["participants"]:
		data = dict()
		data["summonerName"] = participant["summonerName"]
		data["summonerId"] = participant["summonerId"]
		championId = participant["championId"]
		champion = championDict[str(championId)]
		data["champion"] = champion
		data["spell1Id"] = summonerSpell[str(participant["spell1Id"])]
		data["spell2Id"] = summonerSpell[str(participant["spell2Id"])]
		data["spell1Name"] = summoner[data["spell1Id"]]["name"]
		data["spell1Tooltip"] = summoner[data["spell1Id"]]["description"]
		data["spell2Name"] = summoner[data["spell2Id"]]["name"]
		data["spell2Tooltip"] = summoner[data["spell2Id"]]["description"]
		runes = []
		perks = participant["perks"]["perkIds"]
		for rune in perks:
			rune_url = map.get(str(rune))
			if rune_url:
				runes.append(rune_url)
		data["runes"] = runes
		participantDataMap[championId] = data
		if participant["teamId"] == 100:
			unsortedChampListBlue.append(championId)
		else:
			unsortedChampListRed.append(championId)
	matchInfo["participantData"] = getParticipantData(champion_roles, participantDataMap, unsortedChampListBlue, unsortedChampListRed)
	return matchInfo

def processMatch(region, championDict, summonerSpell, summoner, itemJson, champion_roles, database, match):
	gameId = match["gameId"]
	if gameId in database:
		return database[gameId]
	else:
		unsortedChampListBlue = []
		unsortedChampListRed = []
		matchInfo = dict()
		matchInfo["gameId"] = gameId
		matchData = getMatchData(gameId, region)
		matchInfo["gameDuration"] = gameDuration(matchData["gameDuration"])
		matchInfo["gameCreation"] = matchData["gameCreation"] + matchData["gameDuration"]*1000
		participantDataMap = dict()
		accountIdToInfo = dict()
		for participant in matchData["participantIdentities"]:
			data = dict()
			info = dict()
			data["summonerName"] = participant["player"]["summonerName"]
			participantId = participant["participantId"]
			participantInfo = matchData["participants"][participantId-1]
			info["spell1Id"] = summonerSpell[str(participantInfo["spell1Id"])]
			info["spell1Name"] = summoner[info["spell1Id"]]["name"]
			info["spell1Tooltip"] = summoner[info["spell1Id"]]["description"]
			info["spell2Id"] = summonerSpell[str(participantInfo["spell2Id"])]
			info["spell2Name"] = summoner[info["spell2Id"]]["name"]
			info["spell2Tooltip"] = summoner[info["spell2Id"]]["description"]
			stats = participantInfo["stats"]
			info["runes"] = getRunes(stats)
			if matchData["gameDuration"] < 300:
				matchStatus = "remake"
			elif stats["win"]:
				matchStatus = "win"
			else:
				matchStatus = "loss"
			info["matchStatus"] = matchStatus
			info["KDA"] = str(stats["kills"]) + " / " + str(stats["deaths"]) + " / " + str(stats["assists"])
			itemList = []
			for i in range(0, 6):
				itemIntKey = stats["item" + str(i)]
				if itemIntKey == 0:
					itemList.append(0)
				else:
					itemKey = str(itemIntKey)
					itemDict = dict()
					if itemKey not in itemJson:
						print(itemKey)
					else:
						itemDict["image"] = itemKey + ".png"
						itemDict["name"] = itemJson[itemKey]["name"]
						itemDict["gold"] = itemJson[itemKey]["gold"]
						itemDict["description"] = itemJson[itemKey]["description"]
					itemList.append(itemDict)
			info["items"] = itemList
			trinket = str(stats["item6"])
			info["trinket"] = trinket
			if trinket != '0':
				info["trinketName"] = itemJson[trinket]["name"]
				info["trinketDescription"] = itemJson[trinket]["description"]
			championId = matchData["participants"][participantId-1]["championId"]
			champion = championDict[str(championId)]
			data["champion"] = champion
			info["champion"] = champion
			accountIdToInfo[participant["player"]["accountId"]] = info
			data["accountId"] = participant["player"]["accountId"]
			participantDataMap[championId] = data
			if participantId < 6:
				unsortedChampListBlue.append(championId)
			else:
				unsortedChampListRed.append(championId)
		matchInfo["participantData"] = getParticipantData(champion_roles, participantDataMap, unsortedChampListBlue, unsortedChampListRed)
		matchInfo["infoByAccountId"] = accountIdToInfo
	return matchInfo

def getMatchResults(matches, accountId, region):
	championDict = json.load(open(os.path.join(BASE_DIR, "history/static/champions.json")))
	summonerSpell = json.load(open(os.path.join(BASE_DIR, "history/static/summonerSpell.json")))
	summoner = requests.get("%s/%s/data/en_US/summoner.json"%(lol_version, lol_patch)).json()["data"]
	itemJson = requests.get("%s/%s/data/en_US/item.json"%(lol_version, lol_patch)).json()["data"]
	champion_roles = pull_data()
	database = dict()
	for match in matches:
		gameId = match["gameId"]
		game = MatchInfo.objects.filter(gameId = region + str(gameId))
		if game.exists():
			gameFromDB = game.first()
			gameData = gameFromDB.getData()
			matchInfo = json.loads(gameData)
			database[gameId] = matchInfo
	matchList = []
	for match in matches:
		matchResult = processMatch(region, championDict, summonerSpell, summoner, itemJson, champion_roles, database, match)
		matchList.append(matchResult)
	for match in matchList:
		gameId = match["gameId"]
		if gameId not in database:
			jsonStr = json.dumps(match)
			MatchInfo.objects.create(gameId = region + str(gameId), gameData = jsonStr)
		match["timeStatus"] = timeStatus(match["gameCreation"])
		infoByAccountId = match.pop("infoByAccountId")
		match["info"] = infoByAccountId[accountId]
	return matchList

def getThreadedMatchResults(matches, accountId, region):
	championDict = json.load(open(os.path.join(BASE_DIR, "history/static/championKey.json")))
	summonerSpell = json.load(open(os.path.join(BASE_DIR, "history/static/summonerSpell.json")))
	champToChampName = requests.get("%s/%s/data/en_US/champion.json"%(lol_version, lol_patch)).json()["data"]
	champion_roles = pull_data()
	database = dict()
	for match in matches:
		gameId = match["gameId"]
		game = MatchInfo.objects.filter(gameId = region + str(gameId))
		if game.exists():
			gameFromDB = game.first()
			gameData = gameFromDB.getData()
			matchInfo = json.loads(gameData)
			database[gameId] = matchInfo
	pool = mp.Pool()
	function = partial(processMatch, region, championDict, summonerSpell, champToChampName, champion_roles, database)
	matchList = pool.map(function, matches)
	pool.close()
	pool.join()
	for match in matchList:
		gameId = match["gameId"]
		if gameId not in database:
			jsonStr = json.dumps(match)
			MatchInfo.objects.create(gameId = region + str(gameId), gameData = jsonStr)
		match["timeStatus"] = timeStatus(match["gameCreation"])
		infoByAccountId = match.pop("infoByAccountId")
		match["info"] = infoByAccountId[accountId]
	return matchList

class Container():

	def getRegionList():
		return ['NA1', 'EUW1', 'KR', 'BR1', 'EUN1', 'JP1', 'LA1', 'LA2', 'OC1', 'TR1', 'RU']

	def getExtendedData(gameId, region):
		game = MatchInfo.objects.filter(gameId = region + str(gameId)).first()
		gameData = game.getData()
		match = json.loads(gameData)
		participantData = match['participantData']
		info = match["infoByAccountId"]
		for team in participantData:
			for key in team:
				key["accountInfo"] = info[key['accountId']]
		return participantData

	def getMatchInfo(accountId, region, startGame):
		matches = requestMatchesById(accountId, region, startGame)
		if 'status' in matches:
			return {'status_code': matches['status']['status_code']}
		matchResults = getMatchResults(matches["matches"], accountId, region)
		#matchResults = getThreadedMatchResults(matches["matches"], accountId, region)
		return {"matchResults": matchResults, "numGames": len(matchResults), "status_code": '200'}

	def isInGame(summonerId, region):
		return getCurrentMatchResultBoolean(summonerId, region)

	def getUserInfo(summonerName, region):
		summonerIdResponse = requestSummonerId(summonerName, region)
		if summonerIdResponse.status_code == 404 or summonerIdResponse.status_code == 404:
			return {'was_found': False}
		summonerId = summonerIdResponse.json()
		data = dict()
		identity = summonerId['id']
		accountStats = getAccountStats(identity, region)
		if accountStats == 404:
			data['rank'] = "Unranked"
		else:
			tier = accountStats["tier"].lower().capitalize()
			data['rank'] =  tier + " " + accountStats["rank"]
			data["LP"] = str(accountStats["leaguePoints"]) + " LP"
			data["rankUrl"] = "https://ashwingg-static.s3.amazonaws.com/ranked-emblems/Emblem_%s.png" % tier
			data["games"] = str(accountStats["wins"] + accountStats["losses"])
			data["winPercent"] = str(accountStats["wins"] * 100 // (accountStats["wins"] + accountStats["losses"])) + "%"
		data["summonerName"] = summonerId["name"]
		data["summonerId"] = identity
		return {'was_found': True, 'data': data}

	def getLiveInfoWithSummonerId(summonerId, region):
		game = getCurrentMatchResult(summonerId, region)
		if game["status"] == 0:
			return {'status': 0, 'message': "This summoner is not currently in an active ranked game"}
		for team in game['matchData']['participantData']:
			for summoner in team:
				identity = summoner['summonerId']
				accountStats = getAccountStats(identity, region)
				if accountStats == 404:
					summoner['rank'] = "Unranked"
				else:
					tier = accountStats["tier"].lower().capitalize()
					summoner['rank'] =  tier + " " + accountStats["rank"]
					summoner["LP"] = str(accountStats["leaguePoints"]) + " LP"
					summoner["rankUrl"] = "https://ashwingg-static.s3.amazonaws.com/ranked-emblems/Emblem_%s.png" % tier
					summoner["games"] = str(accountStats["wins"] + accountStats["losses"])
					summoner["winPercent"] = str(accountStats["wins"] * 100 // (accountStats["wins"] + accountStats["losses"])) + "%"
		return {'status': 1, 'data': game["matchData"], 'summonerId': summonerId}

	def getLiveInfoWithSummonerName(summonerName, region):
		summonerIdResponse = requestSummonerId(summonerName, region)
		if summonerIdResponse.status_code == 404 or summonerIdResponse.status_code == 500:
			return {'status': 0, 'message': summonerName + ' is not a valid account in ' + region}
		summonerIdJSON = summonerIdResponse.json()
		summonerId = summonerIdJSON["id"]
		return Container.getLiveInfoWithSummonerId(summonerId, region)

	def getPageInfo(summonerName, region):
		summonerIdResponse = requestSummonerId(summonerName, region)
		if summonerIdResponse.status_code == 404:
			return config.NO_SUMMONER_FOUND
		elif summonerIdResponse.status_code == 500:
			return config.REQUEST_500
		summonerId = summonerIdResponse.json()

		jsonDict = dict()
		id = summonerId["id"]
		currentMatchResult = getCurrentMatchResult(id, region)
		jsonDict["isInGame"] = False
		if currentMatchResult["status"] == 1:
			jsonDict["isInGame"] = True
			jsonDict["matchData"] = currentMatchResult["matchData"]
		jsonDict["summonerId"] = id
		jsonDict["accountId"] = summonerId["accountId"]
		jsonDict["summonerName"] = summonerId["name"]
		jsonDict["profileIconId"] = summonerId["profileIconId"]
		jsonDict["summonerLevel"] = summonerId["summonerLevel"]
		accountStats = getAccountStats(id, region)
		if accountStats == 404:
			return config.NO_RANK_FOUND
		tier = accountStats["tier"].lower().capitalize()
		jsonDict["ELO"] =  tier + " " + accountStats["rank"]
		jsonDict["rankUrl"] = "https://ashwingg-static.s3.amazonaws.com/ranked-emblems/Emblem_%s.png" % tier
		jsonDict["LP"] = str(accountStats["leaguePoints"]) + " LP"
		jsonDict["winloss"] = str(accountStats["wins"]) + "W " + str(accountStats["losses"]) + "L"
		jsonDict["winPercent"] = str(accountStats["wins"] * 100 // (accountStats["wins"] + accountStats["losses"])) + "%"
		return jsonDict