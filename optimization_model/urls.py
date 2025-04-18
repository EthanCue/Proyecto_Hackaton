from django.urls import path, include
from rest_framework.documentation import include_docs_urls
from rest_framework import routers
from optimization_model import views

# api versioning
router = routers.DefaultRouter()

urlpatterns = [
    path("api/v1/", include(router.urls)),
    path('api/v1/optimize/', views.optimizeData, name='optimize'),
    path('api/v1/process-data/', views.processData, name='process_data'),
    path('docs/', include_docs_urls(title="Optimization API"))
]