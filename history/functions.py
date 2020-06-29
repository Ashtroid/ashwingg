import requests
import json
import os
import timeago, datetime
from league.settings import BASE_DIR, API_KEY
from . import config
from .models import MatchInfo

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

def getCurrentMatchResult(summonerId, region):
	response = getSummonersInActiveGame(summonerId, region)
	match = response.json()
	if response.status_code != 200 or match["gameQueueConfigId"] != 420:
		return {"status": 0}
	result = getLiveMatchData(match, summonerId, region)
	ret = {"status": 1, "matchData": [result]}
	return ret

def getLiveMatchData(match, summonerId, region):
	championDict = json.load(open(os.path.join(BASE_DIR, "history/static/championKey.json")))
	summonerSpell = json.load(open(os.path.join(BASE_DIR, "history/static/summonerSpell.json")))
	champToChampName = requests.get("https://ddragon.leagueoflegends.com/cdn/10.12.1/data/en_US/champion.json").json()["data"]
	matchInfo = dict()
	matchInfo["timeStatus"] = timeStatus(match["gameStartTime"])
	matchInfo["gameDuration"] = "In progress"
	matchInfo["isComplete"] = False
	participantDataBlue = []
	participantDataRed = []
	info = {}
	for participant in match["participants"]:
		data = dict()
		data["summonerName"] = participant["summonerName"]
		champion = championDict[str(participant["championId"])]
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
			info["matchStatus"] = "pending"
			info["KDA"] = "LIVE"
		if participant["teamId"] == 100:
			participantDataBlue.append(data)
		else:
			participantDataRed.append(data)
	participantData = []
	participantData.append(participantDataBlue)
	participantData.append(participantDataRed)
	matchInfo["participantData"] = participantData
	matchInfo["info"] = info
	return matchInfo

def getMatchResults(matches, accountId, region):
	championDict = json.load(open(os.path.join(BASE_DIR, "history/static/championKey.json")))
	summonerSpell = json.load(open(os.path.join(BASE_DIR, "history/static/summonerSpell.json")))
	champToChampName = requests.get("https://ddragon.leagueoflegends.com/cdn/10.12.1/data/en_US/champion.json").json()["data"]
	matchList = []
	for match in matches:
		gameId = match["gameId"]
		game = MatchInfo.objects.filter(gameId = gameId)
		if game.exists():
			gameFromDB = game.first()
			gameData = gameFromDB.getData()
			matchInfo = json.loads(gameData)
		else:
			matchInfo = dict()
			matchInfo["isComplete"] = True;
			matchData = getMatchData(gameId, region)
			matchInfo["gameDuration"] = gameDuration(matchData["gameDuration"])
			matchInfo["gameCreation"] = matchData["gameCreation"]
			participantDataBlue = []
			participantDataRed = []
			accountIdToInfo = dict()
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
				info["matchStatus"] = stats["win"]
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
				if participantId < 6:
					participantDataBlue.append(data)
				else:
					participantDataRed.append(data)
			participantData = []
			participantData.append(participantDataBlue)
			participantData.append(participantDataRed)
			matchInfo["participantData"] = participantData
			matchInfo["infoByAccountId"] = accountIdToInfo
			jsonStr = json.dumps(matchInfo)
			MatchInfo.objects.create(gameId = gameId, gameData = jsonStr)
		matchInfo["timeStatus"] = timeStatus(matchInfo["gameCreation"])
		infoByAccountId = matchInfo.pop("infoByAccountId")
		matchInfo["info"] = infoByAccountId[accountId]
		matchList.append(matchInfo)
	return matchList

class Container():

	def getMatchInfo(accountId, startGame):
		region = "NA1"
		matches = requestMatchesById(accountId, region, startGame)
		matchResults = getMatchResults(matches["matches"], accountId, region)
		return {"matchResults": matchResults, "totalGames": matches["totalGames"], "numGames": len(matchResults)}

	def getPageInfo(summonerName):
		region = "NA1"
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