from django.contrib import admin
from django.contrib.admin.decorators import register
from .models import User, Subscription


@register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name')
    search_fields = ('username',)
    empty_value_display = '-пусто-'


@register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('subscriber', 'subscribed')
    empty_value_display = '-пусто-'
