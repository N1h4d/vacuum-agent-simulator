from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/environment/generate", views.generate_environment, name="api-generate"),
    path("api/simulation/run", views.run_simulation, name="api-run"),
    path("api/comparison/run", views.run_comparison, name="api-compare"),
]
