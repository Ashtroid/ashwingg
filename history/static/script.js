var startGame = 0;

$(document).ready(function() {
	loadGames();
});

$("#load-form").submit(function(e) {
	e.preventDefault();
	loadGames();
});

function submitSearchForm() {
	document.getElementById("search-form").submit();
}

function loadGames() {
	if($.active != 0) {
		return;
	}
	$(".load").hide();
	$(".loading").fadeIn();
	$.ajax({
		type: "POST",
		url: match,
		data: {
            'startGame': startGame,
            'accountId': accountId,
            'csrfmiddlewaretoken': jQuery("[name=csrfmiddlewaretoken]").val()
    	},
		success: function(response) {
			$(".matchContainer").append(response.match_html);
			startGame += response.numGames;
			showLoad();
		},
		error: function (response) {
			showLoad();
		}
	});
}

function showLoad() {
	$(".loading").hide();
	$(".load").show();
}

$(window).scroll(function() {
	if($.active == 0 && $(window).scrollTop() >= $(document).height() - $(window).height()) {
		// ajax call get data from server and append to the div
		loadGames();
    }
});

function showGameExtension(gameId, isComplete) {
	var game = document.getElementById(gameId);
	var arrow = document.getElementById("a" + gameId)
	$(arrow).toggleClass('flip');
	var display = game.style.display;
	if(game.style.display == "block") {
		game.style.display = "none";
	} else {
		if(!isComplete) {
			game.insertAdjacentHTML('afterbegin', "Game is Still Live");
		} else if(game.style.display != "none") {
			$.ajax({
				type: "POST",
				url: extended,
				data: {
		            'gameId': gameId,
		            'csrfmiddlewaretoken': $("[name=csrfmiddlewaretoken]").val()
		    	},
				success: function(response) {
					game.insertAdjacentHTML('afterbegin', response.extended_html);
				},
				error: function (response) {
				}
			});
		}
		game.style.display = "block";
	}
}