# REST framework version


写接口方法：

1 可以基于FBV if request.method 不同做不同的代码逻辑处理

2 可以基于原生CBV 根据request.method不同自动执行不同的方法

3 那就用restframework框架来写接口

```
pip3 install djangorestframework
```

version: settings/urls/views/

其中`DEFAULT_VERSIONING_CLASS`是为了全局生效，不然要在每个视图函数定义`versioning_class`
```
#settings.py
INSTALLED_APPS = [
    #...
    'rest_framework',  # 友好显示TemplateDoesNotExist报错
]
REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS':'rest_framework.versioning.URLPathVersioning',  # 全局生效
    'ALLOWED_VERSIONS':['v1','v2'],
    'DEFAULT_VERSION':'v1',
}
```

```
# urls.py
from django.conf.urls import url
from app01 import views
urlpatterns = [
    url(r'^(?P<version>\w+)/user/$', views.UserView.as_view()),
    # url(r'^user/$', views.UserView.as_view()),
]
```

之初写的CBV都是继承`from rest_framework.views import  View`的View,用了framework后就继承`from rest_framework.views import  APIView`的APIView，那么视图就变成了如下
```
# views.py
# pip3  install djangorestframework
from django.shortcuts import render,HttpResponse,redirect

from django.views import View
from rest_framework.views import APIView
from rest_framework.versioning import URLPathVersioning,QueryParameterVersioning

class UserView(APIView):
    #versioning_class = URLPathVersioning  # 局部生效
    # versioning_class = QueryParameterVersioning

    def get(self,request,*args,**kwargs):
        print(request.version)
        self.dispatch
        return HttpResponse("user.get")

    def post(self,request,*args,**kwargs):
        return HttpResponse("user.post")
```

