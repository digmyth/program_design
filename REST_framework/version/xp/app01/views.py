from django.shortcuts import render,HttpResponse,redirect

# from django.views import View
from rest_framework.views import APIView

# from django.views.decorators.csrf import csrf_exempt

from rest_framework.versioning import URLPathVersioning

class UserView(APIView):
    # @csrf_exempt
    # def dispatch(self,request, *args, **kwargs):
    #     return super(UserView,self).dispatch(request,*args,**kwargs)

    # versioning_class = URLPathVersioning
    def get(self,request, *args,**kwargs):
        self.dispatch
        print(request.version,request.versioning_scheme)
        return HttpResponse('get.user')

    def post(self,request,*args,**kwargs):
        print(request.version,request.versioning_scheme)
        return HttpResponse('post.user')

