from django.contrib import admin
from .models import User, Log, TokenPlan, UserTokenUsage, ConnectionRequest, Connection

admin.site.register(User)
admin.site.register(Log)
admin.site.register(TokenPlan)
admin.site.register(UserTokenUsage)
admin.site.register(ConnectionRequest)
admin.site.register(Connection)