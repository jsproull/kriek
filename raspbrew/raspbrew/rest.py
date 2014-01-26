import urllib, urllib2

class Rest():

	def __init__(self):

		self.user = 'pi'
		self.password = 'pi'

		password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
		password_manager.add_password(
			None, 'http://localhost:8000/', self.user, self.password
		)
		auth_handler = urllib2.HTTPBasicAuthHandler(password_manager)
		opener = urllib2.build_opener(auth_handler)
		urllib2.install_opener(opener)

	def sendRequest(self, url, postData=None):
		"""
		@param url: The relative url to send
		@param postData: A dictionary of post data
		@return: the json respons
		"""
		params = None
		if postData:
			params = urllib.urlencode(postData)

		json = urllib2.urlopen("http://localhost:8000/" + url, params).read()
		return json