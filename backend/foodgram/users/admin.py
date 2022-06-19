from django.contrib import admin
from django.contrib.admin.decorators import register

from .models import Subscription, User


@register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email')
    list_filter = ('username', 'email')
    empty_value_display = '-пусто-'


@register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'subscriber', 'subscribed')
    list_display_links = ('id',)
    empty_value_display = '-пусто-'
    list_editable = ('subscriber', 'subscribed')
