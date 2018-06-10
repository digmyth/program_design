# REST framework version

### 一、REST framework版本定义

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

### 二、REST framework版本源码

 这里简单疏理下framework version的源码流程：
 
 执行UserView类的.as_view方法,显然没有，就要在父类APIView中找as_view方法
 ```
 url(r'^user/$', views.UserView.as_view()),
 ```

APIView中找as_view方法，`super(APIView, cls).as_view(**initkwargs)`就是执行View类的as_view方法
```
@classmethod
def as_view(cls, **initkwargs):
    view = super(APIView, cls).as_view(**initkwargs)
    view.cls = cls
    view.initkwargs = initkwargs

    # Note: session based authentication is explicitly CSRF validated,
    # all other authentication is CSRF exempt.
    return csrf_exempt(view)
```

执行View类的as_view返回view函数，是python闭包的用法
```
def as_view(cls, **initkwargs):
    """
    Main entry point for a request-response process.
    """
    for key in initkwargs:
        if key in cls.http_method_names:
            raise TypeError("You tried to pass in the %s method name as a "
                            "keyword argument to %s(). Don't do that."
                            % (key, cls.__name__))
        if not hasattr(cls, key):
            raise TypeError("%s() received an invalid keyword %r. as_view "
                            "only accepts arguments that are already "
                            "attributes of the class." % (cls.__name__, key))

    def view(request, *args, **kwargs):
        self = cls(**initkwargs)
        if hasattr(self, 'get') and not hasattr(self, 'head'):
            self.head = self.get
        self.request = request
        self.args = args
        self.kwargs = kwargs
        return self.dispatch(request, *args, **kwargs)
    view.view_class = cls
    view.view_initkwargs = initkwargs

    # take name and docstring from class
    update_wrapper(view, cls, updated=())

    # and possible attributes set by decorators
    # like csrf_exempt from dispatch
    update_wrapper(view, cls.dispatch, assigned=())
    return view
```

最终执行self.dispatch方法,注意这里就要从头找dispatch方法，也就是UserView.dispatch开始找
```
def dispatch(self, request, *args, **kwargs):
    """
    `.dispatch()` is pretty much the same as Django's regular dispatch,
    but with extra hooks for startup, finalize, and exception handling.
    """
    # 第一步： 处理请求及认证相关数据
    self.args = args
    self.kwargs = kwargs
    request = self.initialize_request(request, *args, **kwargs)
    self.request = request
    self.headers = self.default_response_headers  # deprecate?

    try:
        # 第二步： 视图前预处理（framework处理全在这里）
        self.initial(request, *args, **kwargs)
        # 第三步： 处理视图函数
        # Get the appropriate handler method
        if request.method.lower() in self.http_method_names:
            handler = getattr(self, request.method.lower(),
                              self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed
    
        response = handler(request, *args, **kwargs)

    except Exception as exc:
        response = self.handle_exception(exc)

    self.response = self.finalize_response(request, response, *args, **kwargs)
    return self.response
```

最后明白了CBV入口其实就是`self.dispatch()`方法，近一步看一下`self.initial(request, *args, **kwargs)`，真正framework处理入口

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
    version, scheme = self.determine_version(request, *args, **kwargs)  # 处理版本
    request.version, request.versioning_scheme = version, scheme

    # Ensure that the incoming request is permitted
    self.perform_authentication(request)  # 处理认证
    self.check_permissions(request)       # 处理权根
    self.check_throttles(request)         # 限制访问频率
```

处理版本的函数
```
def determine_version(self, request, *args, **kwargs):
    """
    If versioning is being used, then determine any API version for the
    incoming request. Returns a two-tuple of (version, versioning_scheme)
    """
    if self.versioning_class is None:
        return (None, None)
    scheme = self.versioning_class()   # 所以我们要定义一个versioning_class类来处理版本
    return (scheme.determine_version(request, *args, **kwargs), scheme)
```

`APIView`类中可看到`framework`全局可定义变量
```
class APIView(View):
    # The following policies may be set at either globally, or per-view.
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
    parser_classes = api_settings.DEFAULT_PARSER_CLASSES
    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES
    throttle_classes = api_settings.DEFAULT_THROTTLE_CLASSES
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES
    content_negotiation_class = api_settings.DEFAULT_CONTENT_NEGOTIATION_CLASS
    metadata_class = api_settings.DEFAULT_METADATA_CLASS
    versioning_class = api_settings.DEFAULT_VERSIONING_CLASS
```

### 三、总结
* CBV入口在self.dispatch
* 配置文件定义`'DEFAULT_VERSIONING_CLASS':'rest_framework.versioning.URLPathVersioning'
* `urls.py`定义`url(r'^user/$', views.UserView.as_view()),`
* 视图继承`class UserView(APIView)`
* 出现未定义的版本报错友好显示在templates模板里，为了能找到模板，settings.py里注册`rest_framework`app


