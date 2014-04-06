import json
import subprocess

from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

from kriek.common.models import Probe, Status
from kriek.globalsettings.models import GlobalSettings
from kriek.ferm.models import FermConfiguration
from kriek.brew.models import BrewConfiguration

from kriek.common.tasks import purgeAllData

#
# main index page
#
def index(request):
	try:
		allFermConfs = FermConfiguration.objects.all().order_by('name')
		allBrewConfs = BrewConfiguration.objects.all().order_by('name')
	except:
		allFermConfs = None
		allBrewConfs = None
		#fermConf=None
	
	return render_to_response('index.html', {'allFermConfs':allFermConfs, 'allBrewConfs': allBrewConfs }, context_instance=RequestContext(request))


#
# returns the ferm.html template
#
@login_required
def ferm(request, conf=1):
	try:
		allFermConfs = FermConfiguration.objects.all().order_by('name')
		allBrewConfs = BrewConfiguration.objects.all().order_by('name')
		fermConf = FermConfiguration.objects.get(pk=int(conf))
	except FermConfiguration.DoesNotExist:
		raise Http404
		#fermConf=None

	return render_to_response('ferm.html', {'fermConf': fermConf, 'allFermConfs':allFermConfs, 'allBrewConfs': allBrewConfs }, context_instance=RequestContext(request))

#
# returns the brew.html template
#
@login_required
def brew(request, conf=1):
	try:
		allBrewConfs = BrewConfiguration.objects.all().order_by('name')
		allFermConfs = FermConfiguration.objects.all().order_by('name')
		brewConf = BrewConfiguration.objects.get(pk=int(conf))
	except BrewConfiguration.DoesNotExist:
		raise Http404
		#fermConf=None

	return render_to_response('brew.html', {'brewConf': brewConf, 'allBrewConfs': allBrewConfs, 'allFermConfs':allFermConfs}, context_instance=RequestContext(request))

#returns true if kriek.py is running
def is_kriek_running():
	try:
		output = subprocess.check_output(['/usr/bin/pgrep', '-lf', 'python.*kriek_'])
		if len(output) > 0:
			return True
		else:
			return False
	except subprocess.CalledProcessError:
		return False


#
# returns the system status via json
#
@login_required
def system_status(request):
	j = {}
	units = GlobalSettings.objects.get_setting('UNITS')
	j['units'] = units.value
	j['serverrunning'] = is_kriek_running()
	j['updatesenabled'] = GlobalSettings.objects.get_setting('UPDATES_ENABLED').value == "True"

	return HttpResponse(json.dumps(j), content_type='application/json')

# Updates a global setting via post
def update_global_setting(request):
	key = request.POST['key']
	value = request.POST['value']
	g, created = GlobalSettings.objects.get_or_create(key=key)
	g.value = value
	g.save()
	g, created = GlobalSettings.objects.get_or_create(key=key)
	return HttpResponse(json.dumps({"success": True}), content_type='application/json')

# removes ALL data
def purge_all_data(request):
	if request.method == "POST":
		confirm = request.POST['confirm']
		if confirm == "true":
			purgeAllData.delay()

	return HttpResponse(json.dumps({"success": True}), content_type='application/json')

# config
def config(request):
	return render_to_response('config.html', {}, context_instance=RequestContext(request))

#login
def login_view(request):
	username = request.POST['username']
	password = request.POST['password']
	user = authenticate(username=username, password=password)
	if user is not None:
		if user.is_active:
			login(request, user)
			return redirect('index')
			# Redirect to a success page.
		else:
			return redirect('index')
			pass
			# Return a 'disabled account' error message
	else:
		pass
		return redirect('index')
		# Return an 'invalid login' error message.


#logout
def logout_view(request):
	logout(request)
	return redirect('index')