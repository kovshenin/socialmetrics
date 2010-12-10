import datetime

import models
import services.twitter

# Collect the metrics data, fired via cron
def collect():
	# Fetch accounts that were not updated today
	accounts = models.Account.all()
	accounts.filter('updated < ', datetime.date.today())
	accounts = accounts.fetch(100)

	for account in accounts:
		twitter = services.twitter.restore(account.twitter['access_token'], account.twitter['access_token_secret'])
		followers = twitter.UsersShow(account.twitter['screen_name'])['followers_count']
		
		history = models.History(account=account, data = {'twitter': followers})
		history.put()
		
		account.updated = datetime.datetime.today()
		account.put()
