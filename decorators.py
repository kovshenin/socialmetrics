from google.appengine.api import users
import models

def login_required(method):
	def redirect_to_login(self, *args, **kwargs):
		self.redirect(users.create_login_url(self.request.uri))

	def new(self, *args, **kwargs):
		user = users.get_current_user()
		accounts = models.Account.all()
		accounts.filter('user =', user)
		account = accounts.get()
		
		if not user and not account:
			return redirect_to_login(self, *args, **kwargs)
			
		elif user and account:
			pass
		
		elif user and not account:
			account = models.Account(user=user)
			account.put()
			
		kwargs['user'] = user
		kwargs['account'] = account
		
		return method(self, *args, **kwargs)

	return new
	
def logout_required(method):
	def redirect_to_dashboard(self, *args, **kwargs):
		self.redirect("/dashboard/")
		
	def new(self, *args, **kwargs):
		user = users.get_current_user()
		
		if user:
			return redirect_to_dashboard(self, *args, **kwargs)
		else:
			return method(self, *args, **kwargs)
			
	return new
