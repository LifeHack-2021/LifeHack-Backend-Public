from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('addDriver',views.addDriver),
    path('addItem',views.addItem)
]
