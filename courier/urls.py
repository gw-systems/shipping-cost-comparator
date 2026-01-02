"""
URL configuration for courier app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'orders', views.OrderViewSet, basename='order')

urlpatterns = [
    # Public endpoints
    path('health', views.health_check, name='health'),
    path('compare-rates', views.compare_rates, name='compare-rates'),
    path('pincode/<int:pincode>/', views.lookup_pincode, name='lookup-pincode'),

    # Order management (includes ViewSet routes)
    path('', include(router.urls)),

    # Admin endpoints
    path('admin/rates', views.get_all_rates, name='admin-get-rates'),
    path('admin/rates/update', views.update_rates, name='admin-update-rates'),
    path('admin/rates/add', views.add_carrier, name='admin-add-carrier'),
]
