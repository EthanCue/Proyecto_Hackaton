from django.urls import path, include
from rest_framework.documentation import include_docs_urls
from rest_framework import routers
from optimization_model import views

# api versioning
router = routers.DefaultRouter()

urlpatterns = [
    path("api/v1/", include(router.urls)),
    path('api/v1/optimize/', views.optimizeScript, name='optimize'),
    path('docs/', include_docs_urls(title="Optimization API"))
]