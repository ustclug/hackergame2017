from xml.etree.ElementTree import fromstring
from urllib.request import urlopen
from time import time
from django.views.decorators.http import require_safe, require_POST
from django.shortcuts import render, redirect, Http404
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.conf import settings

from .models import Problem, Solved

__all__ = 'hub', 'login', 'logout'


@require_safe
def hub(request):
    problems = Problem.objects.order_by('score', 'pid')
    try:
        solved = set(s.problem for s in request.user.solved_set.all())
    except AttributeError:
        solved = set()
    return render(request, 'hackergame/hub.html',
                  {'site': settings.SITE,
                   'title': 'Hub',
                   'problems': problems,
                   'solved': solved})


@require_safe
def login(request):
    with urlopen(settings.SITE['validate'] % request.GET['ticket']) as req:
        data = fromstring(req.read())
    result = data.getchildren()[0]
    if result.tag != '{http://www.yale.edu/tp/cas}authenticationSuccess':
        messages.error(request, '登录出错，请重试')
        return redirect(hub)
    name = result.getchildren()[0].text
    user, created = User.objects.get_or_create(username=name)
    auth_login(request, user)
    messages.info(request, '您已登录')
    return redirect(hub)


@require_safe
def su(request, username):
    if not settings.DEBUG:
        raise Http404
    user, created = User.objects.get_or_create(username=username)
    auth_login(request, user)
    return redirect(hub)


@require_POST
def logout(request):
    auth_logout(request)
    messages.info(request, '您已注销，请注意未登录时提交将不会被记录' +
                  '<img src="%s" style="display:none" />'
                  % settings.SITE['logout'])
    return redirect(hub)


@require_safe
def problem(request, pid):
    try:
        p = Problem.objects.get(pid=pid)
    except Problem.DoesNotExist:
        messages.error(request, '查看题目失败，请重试')
        return redirect(hub)
    return render(request, 'hackergame/problem.html',
                  {'site': settings.SITE,
                   'title': p.title,
                   'problem': p})


@require_POST
def submit(request, pid):
    if time() >= settings.SITE['endtime']:
        messages.info(request, '比赛已结束')
        return redirect(hub)
    try:
        p = Problem.objects.get(pid=pid)
    except Problem.DoesNotExist:
        messages.error(request, '提交失败，请重试')
        return redirect(hub)
    result = request.POST['flag'] == p.flag
    if not result:
        messages.info(request, '回答错误，请继续努力')
        return redirect(problem, pid=pid)
    elif request.user.is_authenticated:
        Solved.objects.filter(user=request.user, problem=p) \
            .get_or_create(user=request.user, problem=p)
        messages.success(request, '恭喜，答案正确')
        return redirect(hub)
    else:
        messages.success(request, '恭喜，答案正确（但请注意您并未登录，结果将不会被记录！）')
        return redirect(hub)


@require_safe
@staff_member_required
def rank(request):
    totalscore = sum(p.score for p in Problem.objects.all())
    data = {u: {'name': u.username, 'score': 0, 'time': 0}
            for u in User.objects.all()}
    for s in Solved.objects.all():
        data[s.user]['score'] += s.problem.score
        data[s.user]['time'] = max(data[s.user]['time'], s.time.timestamp())
    data = list(sorted(data.values(), reverse=True,
                       key=lambda u: (u['score'], -u['time'])))
    for u in data:
        u['percentage'] = u['score'] * 100 // totalscore
    return render(request, 'hackergame/rank.html',
                  {'site': settings.SITE,
                   'title': '当前排名',
                   'rank': data})
