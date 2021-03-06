# Rest_framework throttle

Rest_framework throttle用于用户访问频率限制，也称节流，如1分钟内允许访问30次： 30/1m

### 一、Rest_framework throttle基本使用
 
 如何做到1分钟内允许访问30次的限制，1分钟过后计数可不能清零，因为是一段时间内30次，不能简单count计数来实现？
 
 解决办法： 
 
 可以把用户访问时间戳依次从后往前排记录到列表中，【1529831934.682146 ,1529831924.682146 ,1529831914.682146 , 1529831904.682146】
 
 每欠用户来访问时，用(当前时间戳-60秒),比这个时间戳还小的从列表中移除，以保证列表中记录保持在30个以内，大于30个时拒绝当前请求，这样就实现了访问频率限制
 
 那么问题来了，这个类似{'throttle_user_xx.pk':[1529831934.682146 ,1529831924.682146 ]}的东西放在哪里呢，其实是放在Django缓存里，这里方便起见，先放在file缓存里，其它缓存配置[参考](http://www.cnblogs.com/wupeiqi/articles/5246483.html)
 
```
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': 'E:\hrce-new\django_cache',
    }
}

REST_FRAMEWORK = {
    # ...
    'DEFAULT_THROTTLE_RATES':{
        'user': '3/m',
    },

}

```
 
视图函数自定义throttle类，这里相当于重写了原生`UserRateThrottle`类，并对`allow_request`进行了扩展，扩展依赖`authentication`,己在全局先前设定.根据用户类型的不同设定了不同的访问频率

```
from rest_framework.throttling import SimpleRateThrottle

class UserRateThrottle(SimpleRateThrottle):
    scope = 'user'

    def get_cache_key(self, request, view):
        if request.user:
            ident = request.user

        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }

    def allow_request(self, request, view):
        if request.auth.user.user_type == 1:
            pass
        else:
            self.num_requests = 600  # 次数  # request.auth.user.user_type == 2 是管理员或老板
            self.duration = 60     # 60s

        return super(UserRateThrottle,self).allow_request(request,view)
````

视图函数使用自定义的throttle类
```
 class UserView(APIView):
    # @csrf_exempt
    # def dispatch(self,request, *args, **kwargs):
    #     return super(UserView,self).dispatch(request,*args,**kwargs)

    # versioning_class = URLPathVersioning
    # authentication_classes = [MyAuthenticate,]
    throttle_classes = [UserRateThrottle, ]

    def get(self,request, *args,**kwargs):
        self.dispatch
        return HttpResponse('get.user')
```

这样写起来个人感觉良好...

 
### 二、Rest_framework throttle源码解析
  
如你所知请求先到达self.dispath, 再依次往下疏理Rest_framework throttle处理流程，才能明白如何定义我们的throttle实现访问频率限制
```
def dispatch(self, request, *args, **kwargs):
  # 其它代码略
  try:
      self.initial(request, *args, **kwargs)
```

```
def initial(self, request, *args, **kwargs):
    # 其它代码略
    # Ensure that the incoming request is permitted
    self.perform_authentication(request)
    self.check_permissions(request)
    self.check_throttles(request)     # 执行check_throttles方法
```

```
def check_throttles(self, request):
    """
    Check if request should be throttled.
    Raises an appropriate exception if the request is throttled.
    """
    for throttle in self.get_throttles():   # 找到self.get_throttles()
        if not throttle.allow_request(request, self):
            self.throttled(request, throttle.wait())
```

可以看到套路完全一样，返回throttle对象列表，也就是执行trottle类的`__init__`方法，再执行对象.allow_request(request, view)
```
def get_throttles(self):
    """
    Instantiates and returns the list of throttles that this view uses.
    """
    return [throttle() for throttle in self.throttle_classes]
```

上面是整个Rest_framework throttle处理流程，可以看到先执行trottle类的`__init__`方法，再执行对象.allow_request(request, view)，那么我们来看下这部份代码都干了什么

那么业务视图函数先定义了throttle类UserRateThrottle,找它的`__init__`方法

```
#views.py
from rest_framework.throttling import UserRateThrottle
class SalaryView(APIView):
    permission_classes = [UserPermission,BossPermission]
    throttle_classes = [UserRateThrottle,]
    def get(self,request,*args,**kwargs):
        return HttpResponse("get salary 100W")
```

`__init__`方法,其实就是解析settings.py里定义的rate,分别赋值self.num_requests,self.duration
```
class UserRateThrottle(SimpleRateThrottle):   # __init__方法在父类SimpleRateThrottle里
    """
    Limits the rate of API calls that may be made by a given user.

    The user id will be used as a unique cache key if the user is
    authenticated.  For anonymous requests, the IP address of the request will
    be used.
    """
    scope = 'user'  # 注意这里定义了

    def get_cache_key(self, request, view):  # 这里也就返回字串throttle_user_xx.pk,便于区分不同用户记录
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }
```

```
class SimpleRateThrottle(BaseThrottle):
    """
    A simple cache implementation, that only requires `.get_cache_key()`
    to be overridden.

    The rate (requests / seconds) is set by a `rate` attribute on the View
    class.  The attribute is a string of the form 'number_of_requests/period'.

    Period should be one of: ('s', 'sec', 'm', 'min', 'h', 'hour', 'd', 'day')

    Previous request information used for throttling is stored in the cache.
    """
    cache = default_cache
    timer = time.time
    cache_format = 'throttle_%(scope)s_%(ident)s'
    scope = None   # 这里是None，但不会找到这里，每次重头找
    THROTTLE_RATES = api_settings.DEFAULT_THROTTLE_RATES  # 会在settings.py配置文件里找DEFAULT_THROTTLE_RATES

    def __init__(self):
        if not getattr(self, 'rate', None):
            self.rate = self.get_rate()  # 执行get_rate()，记得从头找，其实self.rate=THROTTLE_RATES['user'],配置文件可以自定义了
        self.num_requests, self.duration = self.parse_rate(self.rate)   # 执行.parse_rate()，记得从头找，把定义的rate传进去
```

```
def get_rate(self):
    """
    Determine the string representation of the allowed request rate.
    """
    if not getattr(self, 'scope', None):
        msg = ("You must set either `.scope` or `.rate` for '%s' throttle" %
               self.__class__.__name__)
        raise ImproperlyConfigured(msg)

    try:
        return self.THROTTLE_RATES[self.scope]  # 注意： self.scope='user'
    except KeyError:
        msg = "No default throttle rate set for '%s' scope" % self.scope
        raise ImproperlyConfigured(msg)
```

# settings.py
那么就有了`DEFAULT_THROTTLE_RATES`这段代码定义
```
REST_FRAMEWORK = {
    # ...
    'DEFAULT_THROTTLE_RATES':{'user': '3/m',},
}
```

实例化`__init__`方法后，执行throttle类UserRateThrottle的allow_request方法，没有就找父类的allow_request方法

```
class SimpleRateThrottle(BaseThrottle):
    def allow_request(self, request, view):
        """
        Implement the check to see if the request should be throttled.

        On success calls `throttle_success`.
        On failure calls `throttle_failure`.
        """
        if self.rate is None:
            return True

        self.key = self.get_cache_key(request, view) # 主要执行UserRateThrottle类的get_cache_key(request, view)方法
        if self.key is None:
            return True

        self.history = self.cache.get(self.key, [])  # cache其实就是用户记录的那个字典记录，我们写到缓存里了，所以会去缓存里读
        self.now = self.timer()

        # Drop any requests from the history which have now passed the
        # throttle duration
        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()
        if len(self.history) >= self.num_requests:
            return self.throttle_failure()
        return self.throttle_success()
```


```
class UserRateThrottle(SimpleRateThrottle):
    """
    Limits the rate of API calls that may be made by a given user.

    The user id will be used as a unique cache key if the user is
    authenticated.  For anonymous requests, the IP address of the request will
    be used.
    """
    scope = 'user'

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:   # 登录后的用户
            ident = request.user.pk
        else:
            ident = self.get_ident(request)   # 没有登录的用户

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }
```

```
class SimpleRateThrottle(BaseThrottle):
    def allow_request(self, request, view):
        """
        Implement the check to see if the request should be throttled.

        On success calls `throttle_success`.
        On failure calls `throttle_failure`.
        """
        if self.rate is None:
            return True

        self.key = self.get_cache_key(request, view)  # throttle_user_userpk
        if self.key is None:
            return True

        self.history = self.cache.get(self.key, [])   # 获取列表
        self.now = self.timer()

        # Drop any requests from the history which have now passed the
        # throttle duration
        while self.history and self.history[-1] <= self.now - self.duration:  # 列表中最后的那个时间戳-时间，作比较
            self.history.pop()  # 去掉时间较早的
        if len(self.history) >= self.num_requests:  # 达到上限就拒绝请求
            return self.throttle_failure()
        return self.throttle_success() # 否则请求成功
```

```
class SimpleRateThrottle(BaseThrottle):
    def throttle_success(self):
        """
        Inserts the current request's timestamp along with the key
        into the cache.
        """
        self.history.insert(0, self.now)  # 请求成功添加此次记录
        self.cache.set(self.key, self.history, self.duration)  # 更新字典记录
        return True
```

 ### 三、总结
 
* 认证用户根据用户类型或用户pk区分不同频率控制

* 匿名用户根据客户端地址区分不同频率控制

* 访问频率控制不应该设在全局，应该部份URL或视图函数受限
 
 
 
