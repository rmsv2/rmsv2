from ..models import *
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http.response import HttpResponse, JsonResponse


@login_required
def tag_search_view(request):
    if 'search' in request.GET:
        tags = Tag.objects.filter(name__contains=request.GET['search'])
        return_value = []
        for tag in tags:
            return_value.append(tag.name)
        return JsonResponse(return_value, status=200, safe=False)
    return HttpResponse('', 400)


@csrf_exempt
@login_required
def tag_add_view(request):
    if request.method == 'POST' and 'name' in request.POST:
        tag = Tag(name=request.POST['name'])
        tag.save()
        return HttpResponse('', 201)
    return HttpResponse('', 400)
