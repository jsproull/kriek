from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Q
from django.core.serializers.json import DjangoJSONEncoder
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.utils import timezone
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

import base64, time, datetime

from raspbrew.common.models import Probe,SSR
from raspbrew.globalsettings.models import GlobalSettings
from raspbrew.ferm.models import FermConfiguration
from raspbrew.brew.models import BrewConfiguration
from raspbrew.status.models import Status


import json

import subprocess
from django.contrib.auth import authenticate, login, logout

#
# returns the ferm.html template
#
@login_required
def ferm(request):
	try:
		p = FermConfiguration.objects.all().order_by('pk')
	except Probe.DoesNotExist:
		raise Http404
		
	return render_to_response('ferm.html', {'fermConfs': p, 'status': {'serverrunning': isRaspbrewRunning()} },
		context_instance=RequestContext(request))

#
# returns the brew.html template
#
@login_required
def brew(request):
	try:
		p = BrewConfiguration.objects.all().order_by('name')
	except Probe.DoesNotExist:
		raise Http404

	return render_to_response('brew.html', {'brewConfs': p},
		context_instance=RequestContext(request))

#returns true if raspbrew.py is running
def isRaspbrewRunning():
	try:
		output = subprocess.check_output(['/usr/bin/pgrep', '-lf', 'python.*raspbrew_'])
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
def systemStatus(request):
	j={}
	units=GlobalSettings.objects.get_setting('UNITS')
	j['units'] = units.value
	j['serverrunning'] = isRaspbrewRunning()
	return HttpResponse(json.dumps(j), content_type='application/json')

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

#logou
def logout_view(request):
	logout(request)
	return redirect('index')