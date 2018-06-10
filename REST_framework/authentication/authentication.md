# REST framework authentication

### 一、



### 二、framework authentication源码解析

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
