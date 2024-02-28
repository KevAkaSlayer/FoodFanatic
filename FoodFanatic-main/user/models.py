from django.contrib.auth.models import User
from django.db import models

class AccountModel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name='account')
    is_activated = models.BooleanField(default=False,null=True , blank = True)
    email_token= models.CharField(max_length=200,null=True , blank = True)