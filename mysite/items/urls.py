from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create', views.createNewItem, name='image'),
    path('getAllItems',views.getAllItems),
    path('editStory', views.editStory),
    path('getAllStories',views.getAllStories),
    path('getPendingItems', views.getPendingItems),
    path('editStatus', views.editStatus),
    path('getItem/<index>', views.getItem),
    path('deleteItem', views.deleteItem),
    path('createWish', views.createWish),
    path('getWishlist/<username>', views.getWishlist),
    path('setRecipient',views.setRecipient),
    path('getDonorItems', views.getDonorItems),
    path('getRecipientItems', views.getRecipientItems),
    path('setRating', views.setRating),
    path('getRatings', views.getRatings),
    path('editPriority', views.editPriority)
]
