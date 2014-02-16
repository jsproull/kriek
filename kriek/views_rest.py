import datetime

from django.contrib.auth.models import User
from rest_framework import viewsets, generics
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from kriek.common.serializers import UserSerializer, StatusSerializer, PIDSerializer, ProbeSerializer, SSRSerializer, ScheduleStepSerializer, ScheduleSerializer, ProbeStatusSerializer, BrewConfSerializer, FermConfSerializer
from kriek.common.models import PID, Probe, Status, SSR, Schedule, ScheduleStep
from kriek.status.models import ProbeStatus, SSRStatus
from kriek.brew.models import BrewConfiguration
from kriek.ferm.models import FermConfiguration
from .permissions import IsAnyone


class ScheduleViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows users to be viewed or edited.
	"""
	queryset = Schedule.objects.all()
	serializer_class = ScheduleSerializer


class ScheduleStepViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows users to be viewed or edited.
	"""
	queryset = ScheduleStep.objects.all().order_by('step_index')
	serializer_class = ScheduleStepSerializer


class UserViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows users to be viewed or edited.
	"""
	queryset = User.objects.all()
	serializer_class = UserSerializer


class PIDViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows users to be viewed or edited.
	"""
	queryset = PID.objects.all()
	serializer_class = PIDSerializer


class ProbeViewSet(viewsets.ModelViewSet):
	"""
	This viewset automatically provides `list`, `create`, `retrieve`,
	`update` and `destroy` actions.

	Additionally we also provide an extra `highlight` action.
	"""
	queryset = Probe.objects.all().order_by('name')
	serializer_class = ProbeSerializer
	permission_classes = (IsAnyone,)

	def pre_save(self, obj):
		obj.owner = self.request.user


class SSRViewSet(viewsets.ModelViewSet):
	"""
	This viewset automatically provides `list`, `create`, `retrieve`,
	`update` and `destroy` actions.

	Additionally we also provide an extra `highlight` action.
	"""
	queryset = SSR.objects.all()
	serializer_class = SSRSerializer
	permission_classes = (IsAnyone,)

	def pre_save(self, obj):
		obj.owner = self.request.user

		#disable all the other ssrs
		for bc in obj.brewconfiguration_set.all():
			if not bc.allow_multiple_ssrs:
				for ssr in bc.ssrs.all():
					if not obj.id == ssr.id:
						print "Disabling: " + str(ssr.id)
						ssr.enabled = False
						ssr.save()


class BrewConfViewSet(viewsets.ModelViewSet):
	"""
	This viewset automatically provides `list`, `create`, `retrieve`,
	`update` and `destroy` actions.

	Additionally we also provide an extra `highlight` action.
	"""
	queryset = BrewConfiguration.objects.all()
	serializer_class = BrewConfSerializer
	permission_classes = (IsAnyone,)

	def pre_save(self, obj):
		obj.owner = self.request.user


class FermConfViewSet(viewsets.ModelViewSet):
	"""
	This viewset automatically provides `list`, `create`, `retrieve`,
	`update` and `destroy` actions.

	Additionally we also provide an extra `highlight` action.
	"""
	queryset = FermConfiguration.objects.all()
	serializer_class = FermConfSerializer
	permission_classes = (IsAnyone,)

	def pre_save(self, obj):
		obj.owner = self.request.user


class ProbeStatusViewSet(viewsets.ModelViewSet):
	"""
	This viewset automatically provides `list`, `create`, `retrieve`,
	`update` and `destroy` actions.

	Additionally we also provide an extra `highlight` action.
	"""
	queryset = ProbeStatus.objects.all().order_by('name')
	serializer_class = ProbeStatusSerializer
	permission_classes = (IsAnyone,)

	# def get_queryset(self):
	# 	"""
	# 	This view should return a list of all the purchases
	# 	for the currently authenticated user.
	# 	"""
	# 	user = self.request.user
	# 	return ProbeStatus.objects.filter(pk=1)
	#
	# def pre_save(self, obj):
	# 	obj.owner = self.request.user


class StatusList(generics.ListAPIView):
	"""
		Returns a list of statuses filtered by date and number requested
	"""
	serializer_class = StatusSerializer
	permission_classes = (IsAnyone,)

	def get_queryset(self):
		"""
		Optionally restricts the returned purchases to a given user,
		by filtering against a `username` query parameter in the URL.
		"""
		# you can do something like this:
		# url('^purchases/(?P<username>.+)/$', PurchaseList.as_view()),
		# and then get username = self.kwargs['username']

		#or you can do it like this
		#username = self.request.QUERY_PARAMS.get('username', None)

		#get our options
		_type = self.request.QUERY_PARAMS.get('type', None)
		confid = int(self.request.QUERY_PARAMS.get('confId', -1))
		number_to_return = int(self.request.QUERY_PARAMS.get('numberToReturn', 10))
		startdate = self.request.QUERY_PARAMS.get('startDate', None)  # unix_time_millis(timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)))

		enddate = self.request.QUERY_PARAMS.get('endDate', None)

		total = Status.objects.count()
		number_to_return = int(number_to_return)

		if number_to_return > 1 and total > 0:
			#print str(timezone.now())
			number_to_return -= 1

			try:
				if confid and _type == "brew":
					q = Q(brewconfig=BrewConfiguration.objects.get(pk=confid))
				elif confid and _type == "ferm":
					q = Q(fermconfig=FermConfiguration.objects.get(pk=confid))
				else:
					return []
			except ObjectDoesNotExist:
				return []

			#zerotime = timezone.make_aware(datetime.datetime.fromtimestamp(0),timezone.get_default_timezone())
			if startdate and enddate:
				startdate = float(startdate)/1000
				enddate = float(enddate)/1000
				startdate = datetime.datetime.fromtimestamp(startdate)
				enddate = datetime.datetime.fromtimestamp(enddate)
				q = q & Q(date__gte=startdate) & Q(date__lte=enddate)
			elif startdate:
				startdate = float(startdate)/1000
				startdate = datetime.datetime.fromtimestamp(startdate)
				q = q & Q(date__gte=startdate)

			statuses = Status.objects.filter(q).order_by("-date")
			#print "got all statues from db"
			#print str(timezone.now())

			#get the number of items requested
			total = len(statuses)
			allstatuses = statuses

			if total > number_to_return:
				step = total/number_to_return
				allstatuses = statuses[step:total-step:step]

				#add the first and last one on everytime
				if len(statuses) > 1:
					allstatuses.insert(0, statuses[0])
					allstatuses.append(statuses[len(statuses)-1])

			#print "filtered statues from db"
			#print str(timezone.now())

			if allstatuses and len(allstatuses) > 0:
				for probe in allstatuses[0].probes.all():
					for ssrstat in SSRStatus.objects.filter(probe=probe):
						ssrstat.ssr.get_eta()

			#print "Done"
			#print str(timezone.now())
			#print "-----------"

			return allstatuses

		elif number_to_return == 1 and total > 0:
			status = Status.objects.order_by('-date')[0]
			return [status]

		return []
