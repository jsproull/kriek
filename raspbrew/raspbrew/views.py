from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Q
from django.core.serializers.json import DjangoJSONEncoder
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.utils import timezone

import base64, time, datetime

from raspbrew.common.models import Probe,SSR
from raspbrew.globalsettings.models import GlobalSettings
from raspbrew.ferm.models import FermConfiguration
from raspbrew.brew.models import BrewConfiguration
from raspbrew.status.models import Status
import json

import subprocess

#
# returns the ferm.html template
#
def ferm(request):
	try:
		p = FermConfiguration.objects.all()
	except Probe.DoesNotExist:
		raise Http404
		
	return render_to_response('ferm.html', {'fermConfs': p, 'status': {'serverrunning': isRaspbrewRunning()} },
		context_instance=RequestContext(request))

#
# returns the brew.html template
#
def brew(request):
	try:
		p = BrewConfiguration.objects.all()
	except Probe.DoesNotExist:
		raise Http404
		
	return render_to_response('brew.html', {'brewConfs': p},
		context_instance=RequestContext(request))

#
# updates and returns json
# TODO - remove this below
@csrf_exempt
def update(request):
	if request.method == 'POST':
		try:	
			_json=json.loads(request.body)
			_updatedAny = False
			if 'probes' in _json:
				for probe in _json['probes']:
					if 'pk' in probe:
						edited=False
						p=Probe.objects.get(pk=probe['pk'])
						if 'target_temperature' in probe:
							p.target_temperature=probe['target_temperature']
							edited=True
						if edited:
							_updatedAny = True
							p.save()
						
			if 'ssrs' in _json:
				for ssr in _json['ssrs']:
					if 'pk' in ssr:
						edited=False
						s=SSR.objects.get(pk=ssr['pk'])
						if 'enabled' in ssr:
							s.enabled=bool(ssr['enabled'])
							edited=True
							
						if 'pid' in ssr:
							newp=ssr['pid']
						
							#update the pid
							pid=s.pid
							if 'power' in newp:
								pid.power=int(newp['power'])
							if 'k_param' in newp:
								pid.power=int(pid['k_param'])
							if 'i_param' in newp:
								pid.power=int(pid['i_param'])
							if 'd_param' in newp:
								pid.power=int(pid['d_param'])	
								
							pid.save()
							
						if edited:
							_updatedAny = True
							s.save()
					
		except KeyError as e:	
			print "KeyError"
			print e
			
		return HttpResponse(json.dumps({"ok":True}), content_type='application/json')
	else :	
		return HttpResponse(json.dumps({}), mimetype='application/json')

#
# Returns saved status Json objects for the given FermConfiguration id
#
def jsonFermStatus(request, fermConfId, numberToReturn=50, startDate=-1, endDate=-1):
	return jsonStatus(request, numberToReturn, startDate, endDate, Q(fermconfig__pk=fermConfId))

#
# Returns saved status Json objects for the given BrewConfiguration id
#
def jsonBrewStatus(request, brewConfId, numberToReturn=50, startDate=-1, endDate=-1):
	return jsonStatus(request, numberToReturn, startDate, endDate, Q(brewconfig__pk=brewConfId))
	
#
# Returns saved status Json objects
#
def jsonStatus(request, numberToReturn=50, startDate=-1, endDate=-1, addQ=None):
	total=Status.objects.count()
	allStatuses = []
	startDate=float(startDate)/1000
	endDate=float(endDate)/1000
	numberToReturn = int(numberToReturn)
		
	j=[]
	if numberToReturn > 1 and total > 0:
		step=1
		numberToReturn = int(numberToReturn)-1
		statuses = []
		q=None
		
		#default to All
		statuses = Status.objects.all().order_by('date')
		if startDate >= 0 and endDate >= 0:
			startDate = datetime.datetime.fromtimestamp(startDate)
			endDate = datetime.datetime.fromtimestamp(endDate)
			q = Q(date__gte=startDate) & Q(date__lte=endDate)
		elif startDate > -1:
			startDate = datetime.datetime.fromtimestamp(startDate)
			q = Q(date__gte=startDate)

		if addQ:
			if q:
				q = q & addQ
			else:
				q = addQ
		
		if q:
			statuses = statuses.filter(q)
			
		#get the number of items requested
		total=len(statuses)
		allStatuses=statuses
			
		if total > numberToReturn:
			step=total/numberToReturn
			allStatuses=statuses[step:total-step:step]
	
			#add the first and last one on everytime
			if len(statuses) > 1:
				allStatuses.insert(0, statuses[0])
				allStatuses.append(statuses[len(statuses)-1])
		
		
		count=0
		for status in reversed(allStatuses):
			addEta=False
			
			if count == 0:
				addEta=True
			_json = status.toJson()
				
			if _json:
				j.append(json.loads(_json)) #json.loads(base64.decodestring(status.status)))
				count=count+1
		
		
	elif numberToReturn == 1 and total > 0:
		status = Status.objects.order_by('-date')[0]
		_json = status.toJson()
		if _json:
			j.append(json.loads(_json)) #json.loads(base64.decodestring(status.status)))
		
	#debugging	
	#j.append({'step': step, 'total': total, 'numberToReturn': numberToReturn, 'startDate': startDate.strftime('%c')});	
	return HttpResponse(json.dumps(j, cls=DjangoJSONEncoder), content_type='application/json')


#returns true if raspbrew.py is running
def isRaspbrewRunning():
	output = subprocess.check_output(['ps', '-A'])
	if 'raspbrew.py' in output:
		return True
	else:
		return False
		
#
# returns the system status via json
#
def systemStatus(request):
	j={}
	units=GlobalSettings.objects.get_setting('UNITS')
	j['units'] = units.value
	j['serverrunning'] = isRaspbrewRunning()
	return HttpResponse(json.dumps(j), content_type='application/json')
