from . import models
from django.utils import timezone


def categories(request):
    return {
        'top_categories': models.Category.objects.filter(top_category=None).order_by('name')
    }


def menu_notifications(request):
    if request.user.is_authenticated:
        danger_reservations = models.Reservation.objects\
            .filter(owners=request.user, end_date__lt=timezone.localtime(timezone.now()))\
            .exclude(reservationcheckoutinstance=None).count()
        return {
            'danger_reservations_count': danger_reservations
        }
    return {}
