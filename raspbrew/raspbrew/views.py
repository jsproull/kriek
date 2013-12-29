from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
import base64, time, datetime

from raspbrew.common.models import Probe,Status,SSR
from raspbrew.ferm.models import FermConfiguration
from raspbrew.brew.models import BrewConfiguration

import json

def ferm(request, something):
    try:
        p = FermConfiguration.objects.all()
    except Probe.DoesNotExist:
        raise Http404
        
    return render_to_response('ferm.html', {'fermConfs': p},
        context_instance=RequestContext(request))
    
def brew(request, numberToReturn=50):
    try:
        p = BrewConfiguration.objects.all()
    except Probe.DoesNotExist:
        raise Http404
        
    return render_to_response('brew.html', {'brewConfs': p},
        context_instance=RequestContext(request))
        
def jsonStatus(request, numberToReturn=50, startDate=-1, endDate=-1):
	total=Status.objects.count()
	step=1
	if total > numberToReturn:
		step=total/numberToReturn
	
	if startDate > -1 and endDate > -1:
		startDate = datetime.datetime.fromtimestamp(float(startDate))
		endDate = datetime.datetime.fromtimestamp(float(endDate))
		statuses = Status.objects.filter(date__gte=startDate, date__lte=endDate).order_by('-date')[0:numberToReturn:step]
	elif startDate > -1:
		startDate = datetime.datetime.fromtimestamp(float(startDate))
		statuses = Status.objects.filter(date__gte=startDate).order_by('-date')[0:numberToReturn:step]
	else:
		statuses = Status.objects.order_by('-date')[0:numberToReturn:step]
	
	j=[]
	for status in statuses:
		j.append(json.loads(base64.decodestring(status.status)))
		
	return HttpResponse(json.dumps(j), mimetype='application/json')
