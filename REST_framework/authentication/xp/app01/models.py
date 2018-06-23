from django.db import models


class UserInfo(models.Model):
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=32)

class UserToken(models.Model):
    user = models.OneToOneField('UserInfo')
    token = models.CharField(max_length=64)


