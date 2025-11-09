from django.contrib import admin
from .models import User, Log, TokenPlan, UserTokenUsage

admin.site.register(User)
admin.site.register(Log)
admin.site.register(TokenPlan)
admin.site.register(UserTokenUsage)