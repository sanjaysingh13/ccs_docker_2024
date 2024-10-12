from django.urls import path

from . import views

app_name = "searches"
urlpatterns = [
    path("crime_search/", views.crime_search, name="crime_search"),
    path(
        "advanced_crime_search/<int:pk>",
        views.crime_search_results,
        name="advanced_crime_search",
    ),
    # path('crime_search_results/', views.crime_search_results, name = 'crime_search_results'),
    # path('crime_search_results/', views.crime_search_results, name='crime_search_results'),
    path("criminal_search/", views.criminal_search, name="criminal_search"),
    path(
        "advanced_criminal_search/<int:pk>",
        views.criminal_search_results,
        name="advanced_criminal_search",
    ),
    # path('criminal_search_results/', views.criminal_search_results, name='criminal_search_results'),
    # path('crime_news_sheets/', views.CrimeNewsSheetCreateView.as_view(), name='crime_news_sheets')
]
