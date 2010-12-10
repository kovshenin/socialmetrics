from google.appengine.ext.webapp import template

# Used to render templates with a global context
def render(obj, tpl='default.html', context={}):
	obj.response.out.write(template.render('templates/' + tpl, context))

# Used to render plain text (mostly for debugging purposes)
def rendertext(obj, text):
	obj.response.out.write(text)
