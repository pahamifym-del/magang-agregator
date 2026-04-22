from django.urls import path
from . import views

urlpatterns = [
    path("", views.InternshipListView.as_view(), name="internship-list"),
    path("stats/", views.api_stats, name="internship-stats"),
    path("<slug:slug>/", views.InternshipDetailView.as_view(), name="internship-detail"),
]