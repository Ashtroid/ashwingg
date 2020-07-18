var startGame = 0;

$(document).ready(function() {
	loadGames();
});

$("#load-form").submit(function(e) {
	e.preventDefault();
	loadGames();
});

function loadGames() {
	loadGames(0);
}

function loadGames(retry_count) {
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
			$(response.match_html).hide().fadeIn(500).appendTo(".matchContainer");
			startGame += response.numGames;
			showLoad();
		},
		error: function (response) {
			if(retry_count < 2) {
				loadGames(retry_count+1);
			} else {
				showLoad();
			}
		}
	});
}

function showLoad() {
	$(".loading").hide();
	$(".load").show();
}

/*$(window).scroll(function() {
	if($.active == 0 && $(window).scrollTop() >= $(document).height() - $(window).height()) {
		//ajax call get data from server and append to the div
		loadGames();
    }
});*/

function showGameExtension(gameId, isComplete) {
	var game = document.getElementById(gameId);
	var arrow = document.getElementById("a" + gameId)
	$(arrow).toggleClass('flip');
	var display = game.style.display;
	if(game.style.display == "block") {
		game.style.display = "none";
	} else {
		if(!isComplete) {
			//Live game screen
		} else if(game.style.display != "none") {
			$.ajax({
				type: "POST",
				url: extended,
				data: {
		            'gameId': gameId,
		            'csrfmiddlewaretoken': $("[name=csrfmiddlewaretoken]").val()
		    	},
				success: function(response) {
					$(response.extended_html).hide().fadeIn(175).prependTo("#" + gameId);	
				},
				error: function (response) {
				}
			});
		}
		game.style.display = "block";
	}
}
