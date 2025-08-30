from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('manager/reports/', views.manager_report_dashboard, name='manager_report_dashboard'),
    path('api/manager/reports/data/', views.get_report_data, name='get_report_data'),
    path('api/manager/reports/statistics/', views.get_report_statistics, name='get_report_statistics'),
    path('api/manager/reports/export-csv/', views.export_reports_csv, name='export_reports_csv'),
    path('api/manager/reports/filter-options/', views.get_filter_options, name='get_filter_options'),
    
]