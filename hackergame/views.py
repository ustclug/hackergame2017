from xml.etree.ElementTree import fromstring
from urllib.request import urlopen
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.models import User

__all__ = 'hub', 'login', 'logout'

SERVICE = 'http://home.ustc.edu.cn/~wzb15/cas.html'
CAS_L = 'https://passport.ustc.edu.cn/login?service=%s' % SERVICE
CAS_V = 'https://passport.ustc.edu.cn/serviceValidate?service=%s&ticket={0}' % SERVICE


def hub(request):
    logged = request.user.is_authenticated
    return render(request, 'hackergame/hub.html',
                  {'logged': logged,
                   'user': request.user.username if logged else '',
                   'login': CAS_L})


def login(request):
    with urlopen(CAS_V.format(request.GET['ticket'])) as req:
        data = fromstring(req.read())
    result = data.getchildren()[0]
    if result.tag != '{http://www.yale.edu/tp/cas}authenticationSuccess':
        return render(request, 'hackergame/message.html',
                      {'msg': 'There are some problems. Please retry.',
                       'url': CAS_L},
                      status=403)
    name = result.getchildren()[0].text
    user, created = User.objects.get_or_create(username=name)
    auth_login(request, user)
    return redirect('/')


def logout(request):
    auth_logout(request)
    return redirect('/')
