from google.appengine.ext import db
from google.appengine.api import users
from django.utils import simplejson

import pickle

# Use this property to store objects.
class ObjectProperty(db.BlobProperty):
	def validate(self, value):
		try:
			result = pickle.dumps(value)
			return value
		except pickle.PicklingError, e:
			return super(ObjectProperty, self).validate(value)
		
	def get_value_for_datastore(self, model_instance):
		result = super(ObjectProperty, self).get_value_for_datastore(model_instance)
		result = pickle.dumps(result)
		return result
		
	def make_value_from_datastore(self, value):
		try:
			value = pickle.loads(str(value))
		except:
			pass
		return super(ObjectProperty, self).make_value_from_datastore(value)
		
class JsonProperty(db.BlobProperty):
	def validate(self, value):
		return value
		
	def get_value_for_datastore(self, model_instance):
		result = super(JsonProperty, self).get_value_for_datastore(model_instance)
		result = simplejson.dumps(result)
		return result
		
	def make_value_from_datastore(self, value):
		try:
			value = simplejson.loads(str(value))
		except:
			pass
			
		return super(JsonProperty, self).make_value_from_datastore(value)

class Account(db.Model):
	user = db.UserProperty()
	
	twitter = JsonProperty()
	facebook = JsonProperty()
	
	created = db.DateTimeProperty(auto_now_add=True)
	updated = db.DateTimeProperty(auto_now=True, auto_now_add=True)

class History(db.Model):
	account = db.ReferenceProperty(Account, collection_name='accounts')
	created = db.DateProperty(auto_now_add=True)
	
	data = JsonProperty()
