"""hackergame2017 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin

from hackergame import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.hub, name='hub'),
    url(r'^login$', views.login),
    url(r'^su/(?P<username>.+)', views.su),
    url(r'^logout$', views.logout, name='logout'),
    url(r'^problem/(?P<pid>[a-zA-Z0-9_]+)', views.problem, name='problem'),
    url(r'^submit/(?P<pid>[a-zA-Z0-9_]+)', views.submit, name='submit'),
    url(r'^rank$', views.rank),
    url(r'^urank$', views.urank),
    url(r'^init$', views.init),
    url(r'^reg$', views.reg, name='reg'),
]
