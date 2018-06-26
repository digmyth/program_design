
from django.conf.urls import url
from app01 import views

urlpatterns = [
    url(r'^auth/$', views.AuthView.as_view()),
    url(r'^user/$', views.UserView.as_view()),
    url(r'^salary/$', views.SalaryView.as_view()),
]
