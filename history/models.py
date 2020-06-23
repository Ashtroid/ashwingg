from django.db import models

# Create your models here.
class MatchInfo(models.Model):
	gameId = models.CharField(max_length=100)
	gameData = models.TextField()

	def getData(self):
		return self.gameData

