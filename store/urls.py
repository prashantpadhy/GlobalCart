
from django.urls import path
from . import views

urlpatterns = [
    path('',views.product_store,name='store'),
    path('<slug:category_slug>/',views.product_store,name='product_by_store'),
    path('<slug:category_slug>/<slug:product_slug>/',views.product_details,name='product_detail')

]