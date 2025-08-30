# from django.contrib import admin

# # Register your models here.
# # dashboard/admin.py
# from django.contrib import admin
# from .models import JobReport

# @admin.register(JobReport)
# class JobReportAdmin(admin.ModelAdmin):
#     list_display = ['job_id', 'client', 'engineer', 'date', 'hours_worked', 'status', 'revenue']
#     list_filter = ['status', 'date', 'client', 'engineer']
#     search_fields = ['job_id', 'client__name', 'engineer__first_name', 'engineer__last_name']
#     date_hierarchy = 'date'
#     readonly_fields = ['created_at', 'updated_at']
#     list_per_page = 20
    
#     fieldsets = (
#         ('Basic Information', {
#             'fields': ('job_id', 'client', 'engineer', 'date')
#         }),
#         ('Job Details', {
#             'fields': ('hours_worked', 'status', 'revenue', 'description')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )