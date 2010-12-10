import random
from datetime import date, datetime, timedelta
import time

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import deferred
from django.utils import simplejson

import front
import services.twitter
import services.facebook
import models
import decorators
import tasks

class Dashboard(webapp.RequestHandler):
	@decorators.login_required
	def get(self, *args, **kwargs):
		user, account = kwargs.get('user'), kwargs.get('account')
		logout_url = users.create_logout_url('/')
		
		"""
		history = models.History.all()
		history = history.fetch(1000)
		for entry in history:
			entry.delete()

		for i in range(50):
			history = models.History(account=account, created=date(2010, 11, 1) + timedelta(days=i), data = {'twitter': random.randint(2000, 3000), 'facebook': random.randint(800, 2700)})
			history.put()
			
		return
		"""
		
		history = models.History.all()
		history.filter('account = ', account)
		history.filter('created <= ', datetime.today())
		history.order('-created')
		history = history.fetch(30)
		
		today = datetime.today()
		start = today - timedelta(days=29)
		point_start = int(time.mktime((start.year, start.month, start.day, 0, 0, 0, 0, 0, 0))) - time.timezone
		
		# There's some strange magic that'll be happening below this line. @todo: Refactor
		
		series = []
		twitter_data = []
		facebook_data = []
		
		data = {}

		for entry in history:
			entry.date = entry.created
			entry.twitter = entry.data.get('twitter')
			entry.facebook = entry.data.get('facebook')
			
			data[entry.date] = {'twitter': entry.twitter, 'facebook': entry.facebook}
			
		dates = data.keys()
		dates.sort()
		
		for d in range((dates[-1] - dates[0]).days + 1):
			diff = dates[0] + timedelta(days=d)
			st = data[diff] if diff in dates else None
			
			if st:
				twitter_data.append(st['twitter'])
				facebook_data.append(st['facebook'])
			else:
				twitter_data.append(None)
				facebook_data.append(None)

		twitter_data.reverse()
		facebook_data.reverse()
		
		twitter_final_data = []
		facebook_final_data = []
		
		for i in range(30):
			try:
				tw = twitter_data[i]
			except:
				tw = None
				
			try:
				fb = facebook_data[i]
			except:
				fb = None
				
			twitter_final_data.append(tw)
			facebook_final_data.append(fb)
			
		twitter_final_data.reverse()
		facebook_final_data.reverse()
		
		twitter_data = twitter_final_data
		facebook_data = facebook_final_data

		series.append({'name': 'Twitter', 'pointInterval': 24 * 3600 * 1000, 'pointStart': point_start * 1000, 'data': twitter_data})
		series.append({'name': 'Facebook', 'pointInterval': 24 * 3600 * 1000, 'pointStart': point_start * 1000, 'data': facebook_data})
		
		front.render(self, 'dashboard.html', {'point_start': point_start, 'history': history, 'account': account, 'logout_url': logout_url, 'series': simplejson.dumps(series), 'api_key': account.api_key})
			
class Connect(webapp.RequestHandler):
	@decorators.login_required
	def get(self, service, *args, **kwargs):
		user, account = kwargs.get('user'), kwargs.get('account')
		if service == 'twitter':
			twitter = services.twitter.new()
			credentials = twitter.getRequestToken()
			url = twitter.getAuthorizationURL(credentials)
			front.rendertext(self, '<a href="%s">%s</a><br />' % (url, url))
			front.rendertext(self, '<form action="/connect/twitter/" method="POST"><input type="text" name="oauth_verifier" /><input type="submit" /></form>')
			
			# Save the tokens.
			account.twitter = {'request_token': credentials['oauth_token'], 'request_token_secret': credentials['oauth_token_secret']}
			account.put()
			
	@decorators.login_required
	def post(self, service, *args, **kwargs):
		user, account = kwargs.get('user'), kwargs.get('account')		
		if service == 'twitter':
			oauth_verifier = self.request.POST.get('oauth_verifier')
			if oauth_verifier:
				twitter = services.twitter.new()
				request_tokens = {'oauth_token': account.twitter['request_token'], 'oauth_token_secret': account.twitter['request_token_secret']}
				credentials = twitter.getAccessToken(request_tokens, oauth_verifier)
				account.twitter = {'access_token': credentials['oauth_token'], 'access_token_secret': credentials['oauth_token_secret'], 'screen_name': credentials['screen_name']}
				account.put()
				
				front.rendertext(self, "You are now registered as @%s!" % account.twitter['screen_name'])

class About(webapp.RequestHandler):
	def get(self):
		front.rendertext(self, 'About')

class Home(webapp.RequestHandler):
	@decorators.logout_required
	def get(self):
		login_url = users.create_login_url("/dashboard/")
		front.render(self, 'home.html', {'login_url': login_url})

class Admin(webapp.RequestHandler):
	def get(self, action):
		if action == 'cron':
			task = self.request.get('task', None)
			
			if task == 'collect':
				#deferred.defer(tasks.collect, _countdown=1, _queue='collect')
				tasks.collect()
				
class Api(webapp.RequestHandler):
	def get(self, method, format):
		if method == 'get_metrics':
			api_key = self.request.get('api_key', None)
			
			account = models.Account.all()
			account.filter('api_key =', api_key)
			account = account.get()
			
			if account:
				history = models.History.all()
				history.filter('account =', account)
				history.filter('created <=', datetime.today())
				history.order('-created')
				data = history.fetch(1)
				
				if data:
					data = data[0]

					response = {'last_updated': data.created.ctime(), 'metrics': data.data}
					front.rendertext(self, simplejson.dumps(response))
					return
			else:
				front.rendertext(self, 'unknown key')

urls = [
	(r'/', Home),
	(r'/dashboard/?', Dashboard),
	(r'/connect/(\w+)/?', Connect),
	(r'/about/?', About),
	(r'/admin/(\w+)/?', Admin),
	(r'/api/(\w+)\.(xml|json)', Api),
]

application = webapp.WSGIApplication(urls, debug=True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()
