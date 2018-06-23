# REST framework authentication

### 一、framework authentication基本使用

先来说个提外话， 视图为CBV情况下通过`@csrf_exempt`避免csrf_token认证报错,当然还有其它方法（与本文无关）
```
from django.shortcuts import render,HttpResponse
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt

class UserView(APIView):
    @csrf_exempt    # 请求处理前先经过dispatch方法
    def dispatch(self,request, *args, **kwargs):
        return super(UserView,self).dispatch(request,*args,**kwargs)

    def get(self,request, *args,**kwargs):
        return HttpResponse('user.get')

    def post(self,request, *args,**kwargs):
        return HttpResponse('user.post')
```

如果需要token认证，那么手写代码可能是这样的
```
class UserView(APIView):
    def get(self,request, *args,**kwargs):
        # request.query_params = request._request.GET
        token = request.query_params.get('token')
        if not token:
            return HttpResponse('not token')
        return HttpResponse('user.get')

    def post(self,request, *args,**kwargs):
        token = request.query_params.get('token')
        if not token:
            return HttpResponse('not token')
        return HttpResponse('user.post')
```

我们来看一下rest_framework是如何实现TOKEN认证的,注意不是指`rest_framework`内置`TokenAuthentication`


自己写一个认证类MyAuthentication
```
# urls.py
from django.shortcuts import render,HttpResponse
from rest_framework.views import APIView
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

class MyAuthentication(BaseAuthentication):  # 自己写一个认证类
    def authenticate(self, request):
        '''
        :param request:
        :return:
        (user,auth_obj) 表示认证成功，并将分别赋值给request.user,request.auth
        raise AuthenticationFailed('认证失败') 表示认证失败
        None 表示匿名用户
        '''
        token = request.query_params.get('token')
        if not token:
            raise  AuthenticationFailed("认证未携带")
        token_obj = models.UserToken.objects.filter(token=token).first()
        if not token_obj:
            raise AuthenticationFailed("token己失效或错误")
        return (token_obj.user.username,token_obj)  # 返回request.user/request.auth
```

在视图里用上MyAuthentication认证类

```
# urls.py
class UserView(APIView):
    authentication_classes = [MyAuthentication,]    # 让视图用起来
    def get(self,request, *args,**kwargs):
        return HttpResponse('user.get')
```

note that: 直接写上`authentication_classes = [MyAuthentication,]`这样是不对的，后面我会在全局加上，因为默认就有2个认证

*  'rest_framework.authentication.SessionAuthentication',
*  'rest_framework.authentication.BasicAuthentication'

这样用户发送请求就必须带上token(或URL/?token=xxx,或在请求体里)
```
http://127.0.0.1:8000/api/user/?token=sdf
```

如果有基于数据库的用户名、密码认证系统，post过来登录成功那一刻就为用户生成token,
```
# models.py
from django.db import models

class UserInfo(models.Model):
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=32)

class UserToken(models.Model):
    user = models.OneToOneField('UserInfo')
    token = models.CharField(max_length=64)
```

有一个对应视图
```
url(r'^auth/', views.AuthView.as_view()),
```

视图函数代码
```
# urls.py
class AuthView(APIView):
    def post(self,request,*args,**kwargs):
        response = {'code':1000}
        user = request.data.get('username')
        pwd = request.data.get('password')

        user_obj = models.UserInfo.objects.filter(username=user,password=pwd).first()
        if not user_obj:
            response['code'] = 10001
            response['msg'] = '用户名或密码错误'
            return JsonResponse(response,json_dumps_params={'ensure_ascii':False})

        token = str(uuid4())
        response['token'] = token
        models.UserToken.objects.update_or_create(user=user_obj,defaults={'token':token}) # 验证成功token写入数据库
        # 并把token返回给用户，便于下次携带上
        return JsonResponse(response,json_dumps_params={'ensure_ascii':False})
```

requests模拟post请求看看效果
```
# test.py
import requests

ret = requests.post(
    url='http://127.0.0.1:8000/api/auth/',
    json={'username':'wxq','password':123},
    headers={'Content-Type':'application/json'},
    )

print(ret.text)
```

得到的token下次带上用于业务请求，让请求真正到达业务的get/post等方法
```
http://127.0.0.1:8000/api/user/?token=sdf
```

这里只是让一个类有MyAuthentication,所以我们需要把认证放在全局配置文件settings.py

```
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
#        'rest_framework.authentication.BasicAuthentication',
#        'rest_framework.authentication.SessionAuthentication',
        'app01.utils.auth.MyAuthentication',
    ]
}
```

app01/utils/auth.py
```
#!/usr/bin/env python3
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import  AuthenticationFailed
from app01 import models

class MyAuthentication(BaseAuthentication):
    def authenticate(self,request,*args,**kwargs):
        token = request.query_params.get('token')
        if not token:
            raise  AuthenticationFailed("认证未携带")
        token_obj = models.UserToken.objects.filter(token=token).first()
        if not token_obj:
            raise AuthenticationFailed("token己失效或错误")
        return (token_obj.user.username,token_obj)
```

完整示例代码参见[]()


### 二、framework authentication源码解析

```
class APIView(View):
    def perform_authentication(self, request):
        """
        Perform authentication on the incoming request.

        Note that if you override this and simply 'pass', then authentication
        will instead be performed lazily, the first time either
        `request.user` or `request.auth` is accessed.
        """
        request.user
```
```
class APIView(View):
    def perform_authentication(self, request):
        """
        Perform authentication on the incoming request.

        Note that if you override this and simply 'pass', then authentication
        will instead be performed lazily, the first time either
        `request.user` or `request.auth` is accessed.
        """
        request.user
```

```
class Request(object):
    @property
    def user(self):
        """
        Returns the user associated with the current request, as authenticated
        by the authentication classes provided to the request.
        """
        if not hasattr(self, '_user'):
            with wrap_attributeerrors():
                self._authenticate()
        return self._user
```

### 三、总结

