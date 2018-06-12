# REST framework authentication

### 一、



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
cobbler system add --name=wxqxx --hostname=wxq.com --mac=00:0C:29:D1:78:E9 --ip-address=172.16.10.200 --profile=Suse11_sp4-i386 --interface=eth0cobbler system add --name=wxqxx --hostname=wxq.com --mac=00:0C:29:D1:78:E9 --ip-address=172.16.10.200 --profile=Suse11_sp4-i386 --interface=eth0
