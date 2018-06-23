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