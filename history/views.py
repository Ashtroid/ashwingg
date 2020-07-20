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
	searches = request.session.get('searches', [])
	region = request.session.get('region', 'NA1')
	regions = Container.getRegionList()
	if request.method == 'GET' and 'username' in request.GET:
		username = request.GET['username']
		if username:
			response = Container.getPageInfo(username, region)
			if response == config.NO_RANK_FOUND or response == config.NO_SUMMONER_FOUND or response == config.REQUEST_500:
				return render(request, 'history/invalid.html', context = {'username': username, 'region': region, 'regions': regions, 'response': response})
			else:
				summonerName = response['summonerName']
				searches = LRU().add(summonerName, searches)
				request.session['searches'] = searches
				return render(request, 'history/index.html', context = {'dict': response, 'region': region, 'regions': regions, 'is_mobile': request.user_agent.is_mobile,'searches': searches, 'cdn': lol_version, 'patch': lol_patch})
	return render(request, 'history/homepage.html', context = {'searches': searches, 'region': region, 'regions': regions})

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
	extended_html = loader.render_to_string('history/extended.html', {'participantData': extendedData, 'cdn': lol_version, 'patch': lol_patch})
	output_data = {'extended_html': extended_html}
	return JsonResponse(output_data)

@ratelimit(key='ip', rate='10/m', block=True)
def changeRegion(request):
	request.session['region'] = request.POST.get('region')
	return JsonResponse({'region': request.session['region']})

@ratelimit(key='post:username', rate='6/m', block=True)
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
	region = request.session.get('region', 'NA1')
	regions = Container.getRegionList()
	return render(request, 'history/FAQ.html', context={'region': region, 'regions': regions})

def legal(request):
	region = request.session.get('region', 'NA1')
	regions = Container.getRegionList()
	return render(request, 'history/legal.html', context={'region': region, 'regions': regions})

def live_game(request):
	region = request.session.get('region', 'NA1')
	regions = Container.getRegionList()
	return render(request, 'history/live_game.html', context={'region': region, 'regions': regions})


