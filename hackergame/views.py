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


def running(request):
    if request.user.is_authenticated and request.user.is_staff:
        return True
    else:
        return settings.SITE['starttime'] <= time() <= settings.SITE['endtime']


@require_safe
def hub(request):
    problems = Problem.objects.order_by('score', 'pid')
    try:
        solved = set(s.problem for s in request.user.solved_set.all())
    except AttributeError:
        solved = set()
    if request.user.is_authenticated and request.user.is_staff:
        before = False
    else:
        before = time() < settings.SITE['starttime']
    return render(request, 'hackergame/hub.html',
                  {'site': settings.SITE,
                   'title': 'Hub',
                   'before': before,
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
    if not running(request):
        messages.error(request, '比赛未在进行')
        return redirect(hub)
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
    if not running(request):
        messages.error(request, '比赛未在进行')
        return redirect(hub)
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


@require_safe
def init(request):
    import os
    if not os.path.exists('.inited'):
        open('.inited', 'w').close()
        from django.contrib.auth.models import User
        os.system('python3 manage.py collectstatic')
        os.system('python3 manage.py migrate')
        User.objects.create_superuser(os.environ.get('ROOT_USERNAME', 'root'),
                                      os.environ.get('ROOT_EMAIL', None),
                                      os.environ.get('ROOT_PASSWORD', None))
        messages.success(request, 'Successfully inited')
    return redirect(hub)


def reg(request):
    if request.method == 'POST':
        user, created = User.objects.get_or_create(
            username='U_' + request.POST['username'])
        auth_login(request, user)
        messages.info(request, '您已登录')
        return redirect(hub)
    return render(request, 'hackergame/reg.html',
                  {'site': settings.SITE,
                   'title': '校外登录入口'})


@staff_member_required
def board(request):
    totalscore = sum(p.score for p in Problem.objects.all())
    problems = Problem.objects.order_by('score').all()
    first_solved = []
    for problem in problems:
        fs = Solved.objects.order_by('time').filter(problem=problem).first()
        if (fs): first_solved.append(fs)
    data = dict()
    for user in User.objects.all():
        info = []
        for problem in problems:
            s = Solved.objects.order_by('time').filter(user=user, problem=problem).first()
            if s in first_solved: info.append((s.time,1))
            else: info.append((s.time,0) if s else (None,0))
        data[user] = {
            'name': user.username,
            'info': info,
            'score': 0,
            'time': 0
        }


    for s in Solved.objects.all():
        data[s.user]['score'] += s.problem.score
        data[s.user]['time'] = max(data[s.user]['time'], s.time.timestamp())
    data = list(sorted(data.values(), reverse=True, key=lambda u: (u['score'], -u['time'])))

    _rank_cnt = 0
    for u in data:
        if u['name'].startswith('U_'):
            rank_str = '*'
        else:
            _rank_cnt += 1
            rank_str = str(_rank_cnt)
        u['rank'] = rank_str

    return render(request, 'hackergame/board.html',
                  {'site': settings.SITE,
                   'title': '当前排名',
                   'rank': data,
                   'problems': problems
                   })
