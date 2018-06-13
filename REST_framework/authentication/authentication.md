# REST framework authentication

### 一、

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

我们来看一下rest_framework是如何实现TOKEN认证的


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
            raise AuthenticationFailed('认证失败')
        else:
            return ('wxq','xxxx')
```

在视图里用上MyAuthentication认证类
```
# urls.py
class UserView(APIView):
    authentication_classes = [MyAuthentication,]    # 让视图用起来
    def get(self,request, *args,**kwargs):
        return HttpResponse('user.get')
```

这样用户发送请求就必须带上token(或URL/?token=xxx,或在请求体里)
```
http://127.0.0.1:8000/api/user/?token=sdf
```


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

