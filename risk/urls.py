from django.urls import path
from .views import CognitiveRadarAPI

urlpatterns = [
    # Matches /api/cognitive-radar/analyze/
    path('analyze/', CognitiveRadarAPI.as_view(), name='cognitive-radar-analyze'),
]
