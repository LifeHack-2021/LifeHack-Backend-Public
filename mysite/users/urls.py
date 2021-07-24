from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('authLogin', views.authLogin),
    path('createDonor', views.createDonor),
    path('createRecipient', views.createRecipient),
    path('getUserInfo/<username>', views.getUserInfo),
    path('getRecommendedItems/<username>', views.getRecommendedItems),
    path('acceptItem', views.acceptItem),
    path('rejectItem', views.rejectItem),
    path('getAllUsersInfo', views.getAllUsersInfo),
    path('editBackstory', views.editBackstory)
]
