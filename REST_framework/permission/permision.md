## Rest_framework permission


### 一、framework permission基本使用

```

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


