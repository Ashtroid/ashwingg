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
from league.settings import BASE_DIR, API_KEY
from . import config
from .models import MatchInfo
from roleidentification import pull_data, get_roles

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
	season = 13
	URL = "https://%s.api.riotgames.com/lol/match/v4/matchlists/by-account/%s?queue=420&beginIndex=%d&endIndex=%d&season=%d&api_key=%s" % (region, id, startGame, startGame + numGames, season, API_KEY)
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
	if epochTime == 0:
		return "Loading Screen"
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

def getRankUrl(tier, rank):
	tierMap = {
		"IRON": "1",
		"BRONZE": "2",
		"SILVER": "3",
		"GOLD": "4",
		"PLATINUM": "5",
		"DIAMOND": "6",
		"MASTER": "7",
		"GRANDMASTER": "8",
		"CHALLENGER": "9"
	}
	rankMap = {
		"I": "1",
		"II": "2",
		"III": "3",
		"IV": "4",
		"V": "5"
	}
	return "https://cdn2.leagueofgraphs.com/img/league-icons-v2/160/" + tierMap[tier] + "-" + rankMap[rank] + ".png"

def getRunes(stats):
	map = json.load(open(os.path.join(BASE_DIR, "history/static/runes.json")))
	rune = map.get(str(stats["perk0"]))
	return rune

def getParticipantData(champion_roles, participantDataMap, unsortedChampListBlue, unsortedChampListRed):
	participantData = []
	blueRoles = get_roles(champion_roles, unsortedChampListBlue)
	redRoles = get_roles(champion_roles, unsortedChampListRed)
	teams = [blueRoles, redRoles]
	roles = ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY']
	for team in teams:
		participantDataList = []
		for role in roles:
			participantDataList.append(participantDataMap[team[role]])
		participantData.append(participantDataList)
	return participantData
	

def getCurrentMatchResult(summonerId, region):
	response = getSummonersInActiveGame(summonerId, region)
	match = response.json()
	if response.status_code != 200 or match["gameQueueConfigId"] != 420:
		return {"status": 0}
	result = getLiveMatchData(match, summonerId, region)
	return {"status": 1, "matchData": [result]}

def getLiveMatchData(match, summonerId, region):
	championDict = json.load(open(os.path.join(BASE_DIR, "history/static/championKey.json")))
	summonerSpell = json.load(open(os.path.join(BASE_DIR, "history/static/summonerSpell.json")))
	champToChampName = requests.get("https://ddragon.leagueoflegends.com/cdn/10.12.1/data/en_US/champion.json").json()["data"]
	matchInfo = dict()
	matchInfo["timeStatus"] = timeStatus(match["gameStartTime"])
	matchInfo["gameDuration"] = "In progress"
	info = {}
	matchInfo["isComplete"] = False
	participantDataMap = dict()
	champion_roles = pull_data()
	unsortedChampListBlue = []
	unsortedChampListRed = []
	for participant in match["participants"]:
		data = dict()
		data["summonerName"] = participant["summonerName"]
		championId = participant["championId"]
		champion = championDict[str(championId)]
		data["champion"] = champion
		if participant["summonerId"] == summonerId:
			info["champion"] = champion
			info["championName"] = champToChampName[champion]["name"]
			info["spell1Id"] = summonerSpell[str(participant["spell1Id"])]
			info["spell2Id"] = summonerSpell[str(participant["spell2Id"])]
			perks = participant["perks"]["perkIds"]
			map = json.load(open(os.path.join(BASE_DIR, "history/static/runes.json")))
			rune = map.get(str(perks[0]))
			info["rune"] = rune
			info["matchStatus"] = "live"
			info["KDA"] = "LIVE"
		participantDataMap[championId] = data
		if participant["teamId"] == 100:
			unsortedChampListBlue.append(championId)
		else:
			unsortedChampListRed.append(championId)
	matchInfo["participantData"] = getParticipantData(champion_roles, participantDataMap, unsortedChampListBlue, unsortedChampListRed)
	matchInfo["info"] = info
	return matchInfo

def getMatchResults(matches, accountId, region):
	championDict = json.load(open(os.path.join(BASE_DIR, "history/static/championKey.json")))
	summonerSpell = json.load(open(os.path.join(BASE_DIR, "history/static/summonerSpell.json")))
	champToChampName = requests.get("https://ddragon.leagueoflegends.com/cdn/10.12.1/data/en_US/champion.json").json()["data"]
	champion_roles = pull_data()
	matchList = []
	for match in matches:
		gameId = match["gameId"]
		game = MatchInfo.objects.filter(gameId = region + str(gameId))
		if game.exists():
			gameFromDB = game.first()
			gameData = gameFromDB.getData()
			matchInfo = json.loads(gameData)
		else:
			unsortedChampListBlue = []
			unsortedChampListRed = []
			matchInfo = dict()
			matchInfo["gameId"] = gameId
			matchData = getMatchData(gameId, region)
			matchInfo["gameDuration"] = gameDuration(matchData["gameDuration"])
			matchInfo["gameCreation"] = matchData["gameCreation"]
			participantDataMap = dict()
			accountIdToInfo = dict()
			matchInfo["isComplete"] = True
			for participant in matchData["participantIdentities"]:
				data = dict()
				info = dict()
				data["summonerName"] = participant["player"]["summonerName"]
				participantId = participant["participantId"]
				participantInfo = matchData["participants"][participantId-1]
				info["spell1Id"] = summonerSpell[str(participantInfo["spell1Id"])]
				info["spell2Id"] = summonerSpell[str(participantInfo["spell2Id"])]
				stats = participantInfo["stats"]
				info["rune"] = getRunes(stats)
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
					itemList.append(stats["item" + str(i)])
				info["trinket"] = stats["item6"]
				info["items"] = itemList
				championId = matchData["participants"][participantId-1]["championId"]
				champion = championDict[str(championId)]
				data["champion"] = champion
				info["champion"] = champion
				info["championName"] = champToChampName[champion]["name"]
				accountIdToInfo[participant["player"]["accountId"]] = info
				data["accountId"] = participant["player"]["accountId"]
				participantDataMap[championId] = data
				if participantId < 6:
					unsortedChampListBlue.append(championId)
				else:
					unsortedChampListRed.append(championId)
			matchInfo["participantData"] = getParticipantData(champion_roles, participantDataMap, unsortedChampListBlue, unsortedChampListRed)
			matchInfo["infoByAccountId"] = accountIdToInfo
			jsonStr = json.dumps(matchInfo)
			MatchInfo.objects.create(gameId = region + str(gameId), gameData = jsonStr)
		matchInfo["timeStatus"] = timeStatus(matchInfo["gameCreation"])
		infoByAccountId = matchInfo.pop("infoByAccountId")
		matchInfo["info"] = infoByAccountId[accountId]
		matchList.append(matchInfo)
	return matchList

class Container():

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
		matchResults = getMatchResults(matches["matches"], accountId, region)
		return {"matchResults": matchResults, "numGames": len(matchResults)}

	def getPageInfo(summonerName, region):
		QUEUE_TYPE = "RANKED_SOLO_5x5"

		summonerIdResponse = requestSummonerId(summonerName, region)
		if summonerIdResponse.status_code == 404:
			return config.NO_SUMMONER_FOUND
		elif summonerIdResponse.status_code == 500:
			return config.REQUEST_500
		summonerId = summonerIdResponse.json()

		jsonDict = dict()
		id = summonerId["id"]
		currentMatchResult = getCurrentMatchResult(id, region)
		if currentMatchResult["status"] == 1:
			jsonDict["matchData"] = currentMatchResult["matchData"]
		jsonDict["accountId"] = summonerId["accountId"]
		jsonDict["summonerName"] = summonerId["name"]
		jsonDict["profileIconId"] = summonerId["profileIconId"]
		jsonDict["summonerLevel"] = summonerId["summonerLevel"]
		accountStats = getAccountStats(id, region)
		if accountStats == 404:
			return config.NO_RANK_FOUND
		jsonDict["ELO"] = accountStats["tier"].lower().capitalize() + " " + accountStats["rank"]
		jsonDict["rankUrl"] = getRankUrl(accountStats["tier"], accountStats["rank"])
		jsonDict["LP"] = str(accountStats["leaguePoints"]) + " LP"
		jsonDict["winloss"] = str(accountStats["wins"]) + "W " + str(accountStats["losses"]) + "L"
		jsonDict["winPercent"] = str(accountStats["wins"] * 100 // (accountStats["wins"] + accountStats["losses"])) + "%"
		return jsonDict