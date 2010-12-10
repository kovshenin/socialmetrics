from datetime import datetime, timedelta
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
		
		history = models.History.all()
		history.filter('account = ', account)
		history.order('-created')
		history = history.fetch(100)
		
		today = datetime.today()
		start = today - timedelta(days=30)
		point_start = int(time.mktime((start.year, start.month, start.day, 0, 0, 0, 0, 0, 0))) - time.timezone
		
		series = []
		twitter_data = []
		facebook_data = []
		
		for i in range(31):
			try:
				entry = history[i]
				entry.date = entry.created
				entry.twitter = entry.data.get('twitter')
				entry.facebook = entry.data.get('facebook')
				
				twitter_data.append(entry.twitter)
				facebook_data.append(entry.facebook)
			except:
				twitter_data.append(None)
				facebook_data.append(None)
				
		twitter_data.reverse()
		facebook_data.reverse()
			
		series.append({'name': 'Twitter', 'pointInterval': 24 * 3600 * 1000, 'pointStart': point_start * 1000, 'data': twitter_data})
		series.append({'name': 'Facebook', 'pointInterval': 24 * 3600 * 1000, 'pointStart': point_start * 1000, 'data': facebook_data})
		
		front.render(self, 'dashboard.html', {'point_start': point_start, 'history': history, 'account': account, 'logout_url': logout_url, 'series': simplejson.dumps(series)})
			
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

urls = [
	(r'/', Home),
	(r'/dashboard/?', Dashboard),
	(r'/connect/(\w+)/?', Connect),
	(r'/about/?', About),
	(r'/admin/(\w+)/?', Admin),
]

application = webapp.WSGIApplication(urls, debug=True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()
