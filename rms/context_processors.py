from . import models


def categories(request):
    return {
        'top_categories': models.Category.objects.filter(top_category=None).order_by('name')
    }
