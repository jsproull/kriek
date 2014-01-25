from django.contrib.auth.models import User, Group
from rest_framework import viewsets, generics
from raspbrew.common.serializers import UserSerializer, StatusSerializer, ProbeSerializer, SSRSerializer, PIDSerializer, ProbeStatusSerializer, BrewConfSerializer, FermConfSerializer
from raspbrew.common.models import PID, Probe, Status, SSR
from raspbrew.status.models import ProbeStatus, SSRStatus
from raspbrew.brew.models import BrewConfiguration
from raspbrew.ferm.models import FermConfiguration
from rest_framework import permissions
from .permissions import IsOwnerOrReadOnly, IsOwner, IsAnyone
from django.utils import timezone
from raspbrew.dates import unix_time, unix_time_millis

import datetime

from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt

class UserViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows users to be viewed or edited.
	"""
	queryset = User.objects.all()
	serializer_class = UserSerializer

class ProbeViewSet(viewsets.ModelViewSet):
	"""
	This viewset automatically provides `list`, `create`, `retrieve`,
	`update` and `destroy` actions.

	Additionally we also provide an extra `highlight` action.
	"""
	queryset = Probe.objects.all()
	serializer_class = ProbeSerializer
	permission_classes = (IsOwner,)

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
	permission_classes = (IsOwner,)

	def pre_save(self, obj):
		obj.owner = self.request.user

class BrewConfViewSet(viewsets.ModelViewSet):
	"""
	This viewset automatically provides `list`, `create`, `retrieve`,
	`update` and `destroy` actions.

	Additionally we also provide an extra `highlight` action.
	"""
	queryset = BrewConfiguration.objects.all()
	serializer_class = BrewConfSerializer
	permission_classes = (IsOwner,)

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
	permission_classes = (IsOwner,)

	def pre_save(self, obj):
		obj.owner = self.request.user

class ProbeStatusViewSet(viewsets.ModelViewSet):
	"""
	This viewset automatically provides `list`, `create`, `retrieve`,
	`update` and `destroy` actions.

	Additionally we also provide an extra `highlight` action.
	"""
	queryset = ProbeStatus.objects.all()
	serializer_class = ProbeStatusSerializer
	permission_classes = (IsOwner,)

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
		confId = int(self.request.QUERY_PARAMS.get('confId', -1))
		numberToReturn = int(self.request.QUERY_PARAMS.get('numberToReturn', 10))
		startDate = self.request.QUERY_PARAMS.get('startDate', None) #unix_time_millis(timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)))

		endDate = self.request.QUERY_PARAMS.get('endDate', None)

		total=Status.objects.count()
		numberToReturn = int(numberToReturn)
		print "Getting Statuses : " + str(numberToReturn)

		j=[]
		#if startDate == -1:
		#	startDate = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

		if numberToReturn > 1 and total > 0:
			print str(timezone.now())
			numberToReturn = numberToReturn-1

			try:
				if confId and _type=="brew":
					q=Q(brewconfig=BrewConfiguration.objects.get(pk=confId))
				elif confId and _type=="ferm":
					q=Q(fermconfig=FermConfiguration.objects.get(pk=confId))
				else:
					return []
			except ObjectDoesNotExist:
				return []

			#zerotime = timezone.make_aware(datetime.datetime.fromtimestamp(0),timezone.get_default_timezone())
			if startDate and endDate:
				startDate=float(startDate)/1000
				endDate=float(endDate)/1000
				startDate = datetime.datetime.fromtimestamp(startDate)
				endDate = datetime.datetime.fromtimestamp(endDate)
				q = q & Q(date__gte=startDate) & Q(date__lte=endDate)
			elif startDate:
				startDate=float(startDate)/1000
				startDate = datetime.datetime.fromtimestamp(startDate)
				q = q & Q(date__gte=startDate)

			statuses = Status.objects.filter(q).order_by("-date")
			print "got all statues from db"
			print str(timezone.now())

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

			print "filtered statues from db"
			print str(timezone.now())

			if (allStatuses and len(allStatuses) > 0) :
				for probe in allStatuses[0].probes.all():
					for ssrstat in SSRStatus.objects.filter(probe=probe):
						ssrstat.ssr.getETA()

			print "Done"
			print str(timezone.now())
			print "-----------"

			return allStatuses

		elif numberToReturn == 1 and total > 0:
			status = Status.objects.order_by('-date')[0]
			return [status]

		return []
