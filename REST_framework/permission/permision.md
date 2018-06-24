## Rest_framework permission


### 一、framework permission基本使用

1.1 预先定义数据库`models.py`，可以看到不同类型用户其`user_type`值不一样，我们可以根据这个值区分不同权限
```
from django.db import models
class UserInfo(models.Model):
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=32)

    user_type_choices = (
        (1,'员工'),
        (2,'老板'),
    )
    user_type = models.IntegerField(default=1,choices=user_type_choices)

class UserToken(models.Model):
    user = models.OneToOneField('UserInfo')
    token = models.CharField(max_length=64)
```

1.2 路由`http://x.x.x.x/api/v1/salary/?token=xxxxxx`请求到来，用户不同携带的token也不同
```
url(r'^salary/$', views.SalaryView.as_view()),
```

1.3 权限依赖authentication认证，认证后得到request.user、request.auth,这个request.auth是一个`UserToken`对象，非常有用，request.auth.user就可以跨表`UserInfo`,能通过`request.auth.user.user_type`取得用户类型值，这样根据用户类型的不同区分不同的权限

1.4 理论走通了后就可以写权限类了

```
from rest_framework.permissions import BasePermission

class UserPermission(BasePermission):    # 普通用户都能查看
    def has_permission(self,request,view):
        print(request.auth)
        if getattr(request.auth, 'user', None):
            user_type_id = request.auth.user.user_type
            if user_type_id > 0:
                return True
        return False


class BossPermission(BasePermission):   # 老板才能查看
    def has_permission(self, request, view):
        print(request.auth)
        if getattr(request.auth, 'user', None):
            user_type_id = request.auth.user.user_type
            if user_type_id > 1:
                return True
        return False
```

1.5 把定义的权限类用在业务视图上实现权限区分
```
class SalaryView(APIView):
    permission_classes = [UserPermission,BossPermission]  # 且的关系
    def get(self,request,*args,**kwargs):
        return HttpResponse("get salary 100W")
```


### 二、framework permission源码解析


在前面代码的分析中我们知道请求会先经过`self.dispatch()`,
```
def dispatch(self, request, *args, **kwargs):
    # 其它代码略
    try:
        self.initial(request, *args, **kwargs) # 还是在这时进入
```

会依赖权限认证获得request.user/request.auth作为权限分配的依据
```
class APIView(View):
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

        # Ensure that the incoming request is permitted   # 经过权限认证了
        self.perform_authentication(request)     # 执行权限分配处理
        self.check_permissions(request)
```

执行perform_authentication(request)`方法，
```
class APIView(View):
    def check_permissions(self, request):
        """
        Check if the request should be permitted.
        Raises an appropriate exception if the request is not permitted.
        """
        for permission in self.get_permissions():
            # 1.权限对象.has_permission=False表示没有权限
            if not permission.has_permission(request, self):  # 权限对象必须要有has_permission方法
                self.permission_denied(
                    request, message=getattr(permission, 'message', None)
                )
            # 2.权限对象.has_permission=False=True表示有权限
```

`self.get_permissions()`是个什么鬼，原来套路一样，是一个权限对象列表
```
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        return [permission() for permission in self.permission_classes]
```

### 三、总结

* rest_framework的权限依赖rest_framework的认证
* rest_framework认证成功后返回认证用户的request.user,request.auth
* rest_framework认证成功后不返回request.user,request.auth，那么就取不到值request.auth.user.user_type，所以用了getattr
* 权限类必须要有has_permission方法，这个方法的返回值为True表示有权限，False表示没有权限

