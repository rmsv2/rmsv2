from django_ical.views import ICalFeed
from django.contrib.syndication.views import Feed
from rms.models import Reservation
from django.shortcuts import reverse
from django.http import HttpResponse
import base64
from django.contrib.auth import authenticate, login


class ReservationsFeed(ICalFeed):

    basic_auth_realm = 'RMSv2 iCal Feeds'

    product_id = '-//rmsv2//reservations'
    timezone = 'UTC'
    filename = 'reservations.ics'

    def items(self):
        return self.request.user.reservation_set.all().order_by('-start_date')

    def item_title(self, item):
        return '{} {}'.format(item.full_id, item.name)

    def item_description(self, item):
        description = ''
        if description is not None:
            description += item.description
            description += '\n\n'

        return description

    def item_start_datetime(self, item):
        return item.start_date

    def item_link(self, item):
        return reverse('reservation', kwargs={'reservation_id': item.id})

    def item_end_datetime(self, item):
        return item.end_date

    def __call__(self, request, *args, **kwargs):
        self.request = request
        # HTTP auth check inspired by http://djangosnippets.org/snippets/243/
        if request.user.is_authenticated:
            # already logged in
            return super(ReservationsFeed, self).__call__(request, *args, **kwargs)

        # check HTTP auth credentials
        if 'HTTP_AUTHORIZATION' in request.META:
            auth = request.META['HTTP_AUTHORIZATION'].split()
            if len(auth) == 2:
                # only basic auth is supported
                if auth[0].lower() == "basic":
                    uname, passwd = base64.b64decode(auth[1]).decode().split(':')
                    user = authenticate(username=uname, password=passwd)
                    if user is not None:
                        if user.is_active:
                            login(request, user)
                            request.user = user
                            return super(ReservationsFeed, self).__call__(request, *args, **kwargs)

        # missing auth header or failed authentication results in 401
        response = HttpResponse()
        response.status_code = 401
        response['WWW-Authenticate'] = 'Basic realm="%s"' % self.basic_auth_realm
        return response
