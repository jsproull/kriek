from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
import base64, time, datetime

from raspbrew.common.models import Probe,Status,SSR
from raspbrew.ferm.models import FermConfiguration
from raspbrew.brew.models import BrewConfiguration
from django.views.decorators.csrf import csrf_exempt, csrf_protect
import json

#
# returns the ferm.html template
#
def ferm(request):
    try:
        p = FermConfiguration.objects.all()
    except Probe.DoesNotExist:
        raise Http404
        
    return render_to_response('ferm.html', {'fermConfs': p},
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
#
@csrf_exempt
def update(request):
    if request.method == 'POST':
    	try:	
    		#print 'Raw Data: "%s"' % request.body
    		obs = request.POST.get('json', '')
    		probes=json.loads(obs)
    			
    		if 'probes' in probes:
    			for probe in probes['probes']:
    				p=Probe.objects.get(pk=probe['pk'])
    				p.target_temperature=probe['target_temperature']
    				print p.target_temperature
    				p.save()
    				
    	except KeyError as e:	
    		print e
    		
    	return HttpResponse(json.dumps({"ok":True}), mimetype='application/json')
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
	return HttpResponse(json.dumps(j), mimetype='application/json')
