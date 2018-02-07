from django.shortcuts import redirect


def redirect_previous(request):
    if 'redirect' in request.GET:
        return redirect(request.GET['redirect'])
    elif 'HTTP_REFERER' in request.META:
        return redirect(request.META['HTTP_REFERER'])
    else:
        return redirect('home')


def permission_required(permission):

    def decorator(func):

        def func_wrapper(*args, **kwargs):
            request = args[0]
            if not request.user.has_perm(permission):
                return redirect_previous(request)
            return func(*args, **kwargs)

        return func_wrapper

    return decorator
