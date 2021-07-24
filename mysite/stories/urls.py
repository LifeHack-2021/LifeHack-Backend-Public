from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('getAllStories', views.getAllStories),
    path('getStoriesByUser/<username>', views.getStoriesByUser),
    path('createStory', views.createStory)
]
