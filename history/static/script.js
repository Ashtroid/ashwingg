var startGame = 0;
var totalGames = 0;

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
			totalGames = response.totalGames;
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
	document.getElementById("load-form-value").value = "Load More (" + startGame + "/" + totalGames + ")";
	if(startGame < totalGames) {
		$(".load").show();
	}
}

function showGameExtension(gameId) {
	var game = document.getElementById(gameId);
	var display = game.style.display;
	if(game.style.display == "block") {
		game.style.display = "none";
	} else {
		game.style.display = "block";
	}
}