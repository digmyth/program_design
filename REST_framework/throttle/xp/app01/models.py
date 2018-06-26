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


