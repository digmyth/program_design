#!/usr/bin/env python3

from django.shortcuts import render,HttpResponse,redirect

# from django.views import View
from rest_framework.views import APIView

# from django.views.decorators.csrf import csrf_exempt

from rest_framework.versioning import URLPathVersioning

from django.http import JsonResponse

from app01 import models
from uuid import uuid4


class AuthView(APIView):
    authentication_classes = []
    def post(self,request,*args,**kwargs):
        ret = {'code':2000}
        print(request.data)
        user = request.data.get('username')
        pwd = request.data.get('password')
        user_obj = models.UserInfo.objects.filter(username=user,password=pwd).first()
        if not user_obj:
            ret['code'] = 2001
            ret['msg'] = '用户名或密码错误'
            # return HttpResponse("用户名或密码错误")
            return JsonResponse(ret, json_dumps_params={'ensure_ascii': False})
        token = str(uuid4())
        models.UserToken.objects.update_or_create(user=user_obj,defaults={'token':token})
        ret['token'] = token
        return JsonResponse(ret,json_dumps_params={'ensure_ascii':False})


from app01.utils.throttle import  UserRateThrottle

class UserView(APIView):
    # @csrf_exempt
    # def dispatch(self,request, *args, **kwargs):
    #     return super(UserView,self).dispatch(request,*args,**kwargs)

    # versioning_class = URLPathVersioning
    # authentication_classes = [MyAuthenticate,]
    throttle_classes = [UserRateThrottle, ]

    def get(self,request, *args,**kwargs):
        self.dispatch
        print(request.version,request.versioning_scheme)
        # request._request.GET
        # token = request.query_params.get('token')
        # if not token:
        #     return HttpResponse('not token')
        print(request.user,request.auth)
        print(self.authentication_classes)
        return HttpResponse('get.user')

    def post(self,request,*args,**kwargs):
        print(request.version,request.versioning_scheme)
        print(self.authentication_classes)
        return HttpResponse('post.user')

from rest_framework.permissions import BasePermission

class UserPermission(BasePermission):
    def has_permission(self,request,view):
        print(request.auth)
        if getattr(request.auth, 'user', None):
            user_type_id = request.auth.user.user_type
            if user_type_id > 0:
                return True
        return False


class BossPermission(BasePermission):
    def has_permission(self, request, view):
        print(request.auth)
        if getattr(request.auth, 'user', None):
            user_type_id = request.auth.user.user_type
            if user_type_id > 1:
                return True
        return False


class SalaryView(APIView):
    permission_classes = [UserPermission,BossPermission]

    def get(self,request,*args,**kwargs):
        return HttpResponse("get salary 100W")
