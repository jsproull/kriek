from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
import base64, time, datetime

from raspbrew.common.models import Probe,Status,SSR
from raspbrew.ferm.models import FermConfiguration
from raspbrew.brew.models import BrewConfiguration
from django.views.decorators.csrf import csrf_exempt, csrf_protect
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
    		#print 'Raw Data: "%s"' % request.body
    		obs = request.POST.get('json', '')
    		_json=json.loads(obs)
    		_updatedAny = False
    		if 'probes' in _json:
				for probe in _json['probes']:
					if 'pk' in probe:
						edited=False
						p=Probe.objects.get(pk=probe['pk'])
						if 'target_temperature' in probe:
							print "updating temp" + str(probe['target_temperature'])
							p.target_temperature=probe['target_temperature']
							edited=True
						if edited:
							_updatedAny = True
							p.save()
    					
    		if 'ssrs' in _json:
    			for ssr in _json['ssrs']:
    				print ssr
    				if 'pk' in ssr:
						edited=False
						s=SSR.objects.get(pk=ssr['pk'])
						if 'enabled' in ssr:
							s.enabed=bool(ssr['enabled'])
						if edited:
							_updatedAny = True
							s.save()
    						
						print s
			
			#create a status
    		if _updatedAny:
    			Status.create().save()		
    	except KeyError as e:	
    		print e
    		
    	return HttpResponse(json.dumps({"ok":True}), content_type='application/json')
    else :	
		return HttpResponse(json.dumps({}), mimetype='application/json')
		
#
# Returns saved status Json objects
#
def jsonStatus(request, numberToReturn=50, startDate=-1, endDate=-1):
	total=Status.objects.count()
	allStatuses = []
	
	startDate=float(startDate)
	endDate=float(endDate)
	
	if numberToReturn > 1 and total > 0:
		step=1
		numberToReturn = int(numberToReturn)-1
		statusese = []
		if startDate > -1 and endDate > -1:
			startDate = datetime.datetime.fromtimestamp(startDate)
			endDate = datetime.datetime.fromtimestamp(endDate)
			statuses = Status.objects.filter(date__gte=startDate, date__lte=endDate)
		elif startDate > -1:
			startDate = datetime.datetime.fromtimestamp(startDate)
			statuses = Status.objects.filter(date__gte=startDate)
		else:
			statuses = Status.objects.all()
		
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
	
	j=[]
	for status in reversed(allStatuses):
		j.append(json.loads(base64.decodestring(status.status)))
	
	#debugging	
	#j.append({'step': step, 'total': total, 'numberToReturn': numberToReturn, 'startDate': startDate.strftime('%c')});	
	return HttpResponse(json.dumps(j), content_type='application/json')


#returns true if raspbrew.py is running
def isRaspbrewRunning():
	output = subprocess.check_output(['ps', '-A'])
	if 'raspbrew.py' in output:
		return True
	else:
		return False