from xml.etree.ElementTree import fromstring
from urllib.request import urlopen
from time import time
from django.shortcuts import render, redirect, Http404
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.conf import settings

from .models import Problem, Solved

__all__ = 'hub', 'login', 'logout'


def hub(request):
    problems = Problem.objects.order_by('score', 'pid')
    try:
        solved = set(s.problem for s in request.user.solved_set.all())
    except AttributeError:
        solved = set()
    msg = request.session.get('msg', {'type': None})
    request.session['msg'] = {'type': None}
    return render(request, 'hackergame/hub.html',
                  {'site': settings.SITE,
                   'title': 'Hub',
                   'msg': msg,
                   'problems': problems,
                   'solved': solved})


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
    request.session['msg'] = {'type': 'info', 'content': '您已登录'}
    return redirect(hub)


def sudo(request, username):
    if not settings.DEBUG:
        raise Http404
    user, created = User.objects.get_or_create(username=username)
    auth_login(request, user)
    return redirect(hub)


def logout(request):
    auth_logout(request)
    request.session['msg'] = {'type': 'info',
                              'content': '您已注销，请注意未登录时提交将不会被记录'}
    return redirect(hub)


def problem(request, pid):
    try:
        p = Problem.objects.get(pid=pid)
    except Problem.DoesNotExist:
        request.session['msg'] = {'type': 'error', 'content': '查看题目失败，请重试'}
        return redirect(hub)
    msg = request.session.get('msg', {'type': None})
    request.session['msg'] = {'type': None}
    return render(request, 'hackergame/problem.html',
                  {'site': settings.SITE,
                   'title': p.title,
                   'msg': msg,
                   'problem': p})


def submit(request, pid):
    try:
        p = Problem.objects.get(pid=pid)
    except Problem.DoesNotExist:
        request.session['msg'] = {'type': 'error', 'content': '提交失败，请重试'}
        return redirect(hub)
    result = request.POST['flag'] == p.flag
    if not result:
        request.session['msg'] = {'type': 'fail', 'content': '回答错误，请继续努力'}
        return redirect(problem, pid=pid)
    elif request.user.is_authenticated:
        Solved.objects.filter(user=request.user, problem=p) \
            .get_or_create(user=request.user, problem=p)
        request.session['msg'] = {'type': 'success', 'content': '恭喜，答案正确'}
        return redirect(hub)
    else:
        request.session['msg'] = {'type': 'success',
                                  'content': '恭喜，答案正确（但请注意您并未登录，结果将不会被记录！）'}
        return redirect(hub)
