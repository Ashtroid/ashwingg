from django.shortcuts import render
from django.http import JsonResponse, HttpResponse	
from django.template import loader
from .functions import Container
from . import config
from .structures import LRU
from ratelimit.decorators import ratelimit
from league.settings import lol_patch, lol_version

@ratelimit(key='ip', rate='10/m', block=True)
def home(request):
	if request.method == 'GET' and 'username' in request.GET and request.GET['username'] != '':
		return renderProfile(request, request.GET['username'])
	return render(request, 'history/homepage.html', context = getBaseContext(request))

def renderProfile(request, username):
	context = getBaseContext(request)
	response = Container.getPageInfo(username, context['region'])
	if response == config.NO_RANK_FOUND or response == config.NO_SUMMONER_FOUND or response == config.REQUEST_500:
		context['response'] = response
		context['username'] = username
		return render(request, 'history/invalid.html', context = context)
	else:
		summonerName = response['summonerName']
		searches = LRU().add(summonerName, context['searches'])
		request.session['searches'] = searches
		context['searches'] = searches
		context['dict'] = response
		context['is_mobile'] = request.user_agent.is_mobile
		context['cdn'] = lol_version
		context['patch'] = lol_patch
		return render(request, 'history/index.html', context = context)

@ratelimit(key='ip', rate='30/m', block=True)
@ratelimit(key='post:username', rate='2/s', block=True)
def loadMatches(request):
	region = request.session.get('region', 'NA1')
	startGame = request.POST.get('startGame')
	accountId = request.POST.get('accountId')
	matchData = Container.getMatchInfo(accountId, region, startGame)
	if matchData['status_code'] == "200":
		if request.user_agent.is_mobile:
			device_friendly_match_url = 'history/match_mobile.html'
		else:
			device_friendly_match_url = 'history/match.html'
		match_html = loader.render_to_string(device_friendly_match_url, {'matchData': matchData["matchResults"], 'cdn': lol_version, 'patch': lol_patch})
		output_data = {'match_html': match_html, 'numGames': matchData["numGames"]}
		return JsonResponse(output_data)
	else:
		return HttpResponse(status=matchData['status_code']) 

@ratelimit(key='ip', rate='10/m', block=True)
def loadGameExtension(request):
	region = request.session.get('region', 'NA1')
	gameId = request.POST.get('gameId')
	extendedData = Container.getExtendedData(gameId, region)
	if request.user_agent.is_mobile:
		device_friendly_extended_url = 'history/extended_mobile.html'
	else:
		device_friendly_extended_url = 'history/extended.html'
	extended_html = loader.render_to_string(device_friendly_extended_url, {'participantData': extendedData, 'cdn': lol_version, 'patch': lol_patch})
	output_data = {'extended_html': extended_html}
	return JsonResponse(output_data)

@ratelimit(key='ip', rate='10/m', block=True)
def changeRegion(request):
	request.session['region'] = request.POST.get('region')
	return JsonResponse({'region': request.session['region']})

@ratelimit(key='post:username', rate='15/m', block=True)
def checkLiveStatus(request):
	summonerId = request.POST.get('summonerId')
	region = request.POST.get('region')
	isInGameFunction = Container.isInGame(summonerId, region)
	if request.POST.get('isInGame') == "true":
		isInGamePOST = True
	else:
		isInGamePOST = False
	shouldRefresh = isInGameFunction != isInGamePOST
	return JsonResponse({'shouldRefresh': shouldRefresh})

def riot(request):
	return render(request, 'history/riot.txt')
	
def FAQ(request):
	return render(request, 'history/FAQ.html', context = getBaseContext(request))

def legal(request):
	return render(request, 'history/legal.html', context = getBaseContext(request))

def live_game(request):
	context = getBaseContext(request)
	if request.method == 'GET' and ('username' in request.GET or 'summonerId' in request.GET):
		if 'summonerId' in request.GET:
			game = Container.getLiveInfoWithSummonerId(request.GET.get('summonerId'), context['region'])
		else:
			game = Container.getLiveInfoWithSummonerName(request.GET.get('username'), context['region'])
		context['status'] = game['status']
		if game['status'] == 1:
			context['game'] = game['data']
			context['summonerId'] = game['summonerId']
			context['is_mobile'] = request.user_agent.is_mobile
			context['cdn'] = lol_version
			context['patch'] = lol_patch
		else:
			context['message'] = game['message']
	return render(request, 'history/live_game.html', context = context)

def lobby(request):
	context = getBaseContext(request)
	if request.method == 'GET' and 'usernames' in request.GET:
		lobby = request.GET.get('usernames')
		usernames = lobby.split(",")
		lobbyInfoList = []
		for summonerName in usernames:
			if summonerName:
				userInfo = Container.getUserInfo(summonerName, context['region'])
				if userInfo['was_found']:
					lobbyInfoList.append(userInfo['data'])
		if len(lobbyInfoList) == 1:
			return renderProfile(request, lobbyInfoList[0]['summonerName'])
		context['lobbyInfo'] = lobbyInfoList
		if len(lobbyInfoList) > 1:
			context['summonerId'] = lobbyInfoList[0]['summonerId']
	return render(request, 'history/lobby.html', context = context)

def getBaseContext(request):
	searches = request.session.get('searches', [])
	region = request.session.get('region', 'NA1')
	regions = Container.getRegionList()
	return {'searches': searches, 'region': region, 'regions': regions}


