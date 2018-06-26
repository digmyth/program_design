#!/usr/bin/env python3

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
            self.num_requests = 6  # times 3
            self.duration = 60     # 60s

        return super(UserRateThrottle,self).allow_request(request,view)