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

[完整示例代码参见](https://github.com/digmyth/program_design/tree/master/REST_framework/authentication/xp)


### 二、framework authentication源码解析

在rest_framework version源码分析中CBV我们明白了请求会传递到self.dispatch(),这里我就直接跳到self.dispatch代码
```
def dispatch(self, request, *args, **kwargs):
    """
    # APIView.dispatch
    `.dispatch()` is pretty much the same as Django's regular dispatch,
    but with extra hooks for startup, finalize, and exception handling.
    """
    self.args = args
    self.kwargs = kwargs
    request = self.initialize_request(request, *args, **kwargs)   # 这里会先对数据封装
    self.request = request
    self.headers = self.default_response_headers  # deprecate?
    # 代码还有，略...
    
    try:
        self.initial(request, *args, **kwargs)   # 这里会对前面封装的数据作进一步处理
```

我们先来看一下`self.initialize_request(request, *args, **kwargs)`对数据的处理
```
def initialize_request(self, request, *args, **kwargs):
    """
    Returns the initial request object.
    """
    parser_context = self.get_parser_context(request)

    return Request(
        request,
        parsers=self.get_parsers(),
        authenticators=self.get_authenticators(),   # 认证相关
        negotiator=self.get_content_negotiator(),
        parser_context=parser_context
    )
```

这里可以看到request.authenticators=【authentication_classes实例化对象,...】,是一个列表，保存了`authentication_classes`实例化对象
```
def get_authenticators(self):
    """
    Instantiates and returns the list of authenticators that this view can use.
    """
    return [auth() for auth in self.authentication_classes]  
```

我们回来看一下`self.initial(request, *args, **kwargs)`对封装后的数据处理
```
def initial(self, request, *args, **kwargs):
    """
    Runs anything that needs to occur prior to calling the method handler.
    """
    self.format_kwarg = self.get_format_suffix(**kwargs)

    # Perform content negotiation and store the accepted info on the request
    neg = self.perform_content_negotiation(request)
    request.accepted_renderer, request.accepted_media_type = neg

    # Determine the API version, if versioning is in use.
    version, scheme = self.determine_version(request, *args, **kwargs)
    request.version, request.versioning_scheme = version, scheme

    # Ensure that the incoming request is permitted
    self.perform_authentication(request)     # 这里是处理认证相关
    self.check_permissions(request)
    self.check_throttles(request)
```

`self.perform_authentication(request)`处理函数如下
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

来看下`reqeust.user`如何处理
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
                self._authenticate()  # 会走这一步
        return self._user
```

```
class Request(object):
    def _authenticate(self):
        """
        Attempt to authenticate the request using each authentication instance
        in turn.
        """
        for authenticator in self.authenticators:
            try:
                user_auth_tuple = authenticator.authenticate(self)   # 执行authentication_classes对象.authenticate(self)方法
            except exceptions.APIException:
                self._not_authenticated()
                raise

            if user_auth_tuple is not None:
                self._authenticator = authenticator   # authenticator就是authentication_classes对象
                self.user, self.auth = user_auth_tuple # 对象.authenticate(self)方法返回元组分别赋值request.user,request.auth
                return

        self._not_authenticated()
```

从源码可以看出我们定义的认证类必须要有`authenticate`方法且返回元组，元组会分别赋值给request.user,request.auth，那么我们自己写的代码就有了如下

```
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

代码学习就该这样，这就牛逼多了，不言不合就仍给你代码...

### 三、总结
 * 用户提供用户名、密码post请求登录，通过后生成token入库并把token返回给用户
 * 用户携带token进行下一次业务请求，如果设置了authentication_classes,那么取出token取数据库作比对认证
 * token认证成功请求才真正处理关于业务的视图代码
 
