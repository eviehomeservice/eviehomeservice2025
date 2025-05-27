from django.urls import path
from . import views

urlpatterns = [
    path('', views.service_list, name='service_list'),
    path('service/<int:service_id>/', views.user_service, name='user_service'),
    path('service/<int:service_id>/order/', views.create_order, name='create_order'),
    path('order/<str:order_token>/', views.view_order, name='view_order'),
    path('order/<str:order_token>/complete/', views.user_complete_order, name='user_complete_order'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('admin/order/<int:order_id>/accept/', views.accept_order, name='accept_order'),
    path('admin/order/<int:order_id>/complete/', views.complete_order, name='complete_order'),
    path('admin/service/create/', views.create_service, name='create_service'),
    path('admin/service/<int:service_id>/edit/', views.edit_service, name='edit_service'),
    path('api/order/<str:order_token>/', views.api_order_detail, name='api_order_detail'),
]
