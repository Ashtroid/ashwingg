from django.shortcuts import render
from django.http import JsonResponse
from django.template import loader
from django.views.decorators.csrf import csrf_protect
from .functions import Container
from . import config
from .structures import LRU
from ratelimit.decorators import ratelimit

@csrf_protect
@ratelimit(key='ip', rate='10/m', block=True)
def home(request):
	searches = request.session.get('searches', [])
	region = request.session.get('region', 'NA1')
	if request.method == 'GET' and 'username' in request.GET:
		username = request.GET['username']
		if username:
			response = Container.getPageInfo(username, region)
			if response == config.NO_RANK_FOUND or response == config.NO_SUMMONER_FOUND or response == config.REQUEST_500:
				return render(request, 'history/invalid.html', context = {'username': username, 'region': region, 'response': response})
			else:
				summonerName = response['summonerName']
				searches = LRU().add(summonerName, searches)
				request.session['searches'] = searches
				return render(request, 'history/index.html', context = {'dict': response, 'region': region, 'searches': searches})
	regions = ['NA1', 'EUW1', 'KR', 'BR1', 'EUN1', 'JP1', 'LA1', 'LA2', 'OC1', 'TR1', 'RU']
	return render(request, 'history/homepage.html', context = {'region': region, 'searches': searches, 'regions': regions})

@csrf_protect
@ratelimit(key='ip', rate='30/m', block=True)
@ratelimit(key='post:username', rate='2/s', block=True)
def match(request):
	region = request.session.get('region', 'NA1')
	startGame = request.POST.get('startGame')
	accountId = request.POST.get('accountId')
	matchData = Container.getMatchInfo(accountId, region, startGame)
	match_html = loader.render_to_string('history/match.html', {'matchData': matchData["matchResults"]})
	output_data = {'match_html': match_html, 'numGames': matchData["numGames"]}
	return JsonResponse(output_data)

@csrf_protect
@ratelimit(key='ip', rate='10/m', block=True)
def loadGameExtension(request):
	region = request.session.get('region', 'NA1')
	gameId = request.POST.get('gameId')
	extendedData = Container.getExtendedData(gameId, region)
	extended_html = loader.render_to_string('history/extended.html', {'participantData': extendedData})
	output_data = {'extended_html': extended_html}
	return JsonResponse(output_data)

@csrf_protect
@ratelimit(key='ip', rate='10/m', block=True)
def changeRegion(request):
	request.session['region'] = request.POST.get('region')
	print(request.session['region'])
	return JsonResponse({'region': request.session['region']})

def riot(request):
	return render(request, 'history/riot.txt')
	
def FAQ(request):
	return render(request, 'history/FAQ.html')