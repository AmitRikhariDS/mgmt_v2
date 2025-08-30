# # dashboard/views.py
# import csv
# from django.http import JsonResponse, HttpResponse
# from django.shortcuts import render
# from django.db.models import Q, Sum, Avg, Count
# from django.contrib.auth.decorators import login_required, user_passes_test
# from django.utils import timezone
# from datetime import datetime, timedelta
# import random

# def is_manager(user):
#     return user.is_authenticated and user.role == 'manager'

# @login_required
# @user_passes_test(is_manager)
# def manager_report_dashboard(request):
#     """Render the manager report dashboard"""
#     return render(request, 'dashboard/manager_report.html')

# @login_required
# @user_passes_test(is_manager)
# def get_filter_options(request):
#     """API endpoint to get filter options"""
#     try:
#         # For now, return static options - replace with database queries later
#         status_options = [
#             {'value': 'completed', 'label': 'Completed'},
#             {'value': 'in_progress', 'label': 'In Progress'},
#             {'value': 'pending', 'label': 'Pending'},
#             {'value': 'cancelled', 'label': 'Cancelled'},
#         ]
        
#         # Sample clients and engineers - replace with actual database queries
#         clients = [
#             {'id': 1, 'name': 'TechCorp Inc.'},
#             {'id': 2, 'name': 'Global Solutions Ltd.'},
#             {'id': 3, 'name': 'Innovate Systems'},
#             {'id': 4, 'name': 'DataWorks International'},
#         ]
        
#         engineers = [
#             {'id': 1, 'first_name': 'John', 'last_name': 'Smith'},
#             {'id': 2, 'first_name': 'Sarah', 'last_name': 'Johnson'},
#             {'id': 3, 'first_name': 'Mike', 'last_name': 'Brown'},
#             {'id': 4, 'first_name': 'Emily', 'last_name': 'Davis'},
#         ]
        
#         return JsonResponse({
#             'success': True,
#             'clients': clients,
#             'engineers': engineers,
#             'status_options': status_options
#         })
        
#     except Exception as e:
#         return JsonResponse({
#             'success': False,
#             'error': str(e)
#         }, status=500)

# @login_required
# @user_passes_test(is_manager)
# def get_report_data(request):
#     """API endpoint to fetch filtered report data"""
#     try:
#         # Get filter parameters
#         job_id = request.GET.get('job_id', '').strip()
#         client_id = request.GET.get('client_id', '')
#         engineer_id = request.GET.get('engineer_id', '')
#         status = request.GET.get('status', '')
#         start_date = request.GET.get('start_date', '')
#         end_date = request.GET.get('end_date', '')
        
#         # Generate sample data for testing
#         sample_data = generate_sample_data()
        
#         # Apply filters to sample data
#         filtered_data = sample_data
        
#         if job_id:
#             filtered_data = [item for item in filtered_data if job_id.lower() in item['job_id'].lower()]
        
#         if client_id:
#             filtered_data = [item for item in filtered_data if item['client_id'] == int(client_id)]
        
#         if engineer_id:
#             filtered_data = [item for item in filtered_data if item['engineer_id'] == int(engineer_id)]
        
#         if status:
#             filtered_data = [item for item in filtered_data if item['status'] == status]
        
#         if start_date:
#             try:
#                 start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
#                 filtered_data = [item for item in filtered_data if datetime.strptime(item['date'], '%Y-%m-%d').date() >= start_date_obj]
#             except ValueError:
#                 pass
        
#         if end_date:
#             try:
#                 end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
#                 filtered_data = [item for item in filtered_data if datetime.strptime(item['date'], '%Y-%m-%d').date() <= end_date_obj]
#             except ValueError:
#                 pass
        
#         return JsonResponse({
#             'success': True,
#             'data': filtered_data,
#             'total_count': len(filtered_data)
#         })
        
#     except Exception as e:
#         return JsonResponse({
#             'success': False,
#             'error': str(e)
#         }, status=500)

# @login_required
# @user_passes_test(is_manager)
# def get_report_statistics(request):
#     """API endpoint to fetch report statistics"""
#     try:
#         # Get the same filtered data
#         job_id = request.GET.get('job_id', '').strip()
#         client_id = request.GET.get('client_id', '')
#         engineer_id = request.GET.get('engineer_id', '')
#         status = request.GET.get('status', '')
#         start_date = request.GET.get('start_date', '')
#         end_date = request.GET.get('end_date', '')
        
#         sample_data = generate_sample_data()
#         filtered_data = sample_data
        
#         # Apply same filters
#         if job_id:
#             filtered_data = [item for item in filtered_data if job_id.lower() in item['job_id'].lower()]
        
#         if client_id:
#             filtered_data = [item for item in filtered_data if item['client_id'] == int(client_id)]
        
#         if engineer_id:
#             filtered_data = [item for item in filtered_data if item['engineer_id'] == int(engineer_id)]
        
#         if status:
#             filtered_data = [item for item in filtered_data if item['status'] == status]
        
#         if start_date:
#             try:
#                 start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
#                 filtered_data = [item for item in filtered_data if datetime.strptime(item['date'], '%Y-%m-%d').date() >= start_date_obj]
#             except ValueError:
#                 pass
        
#         if end_date:
#             try:
#                 end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
#                 filtered_data = [item for item in filtered_data if datetime.strptime(item['date'], '%Y-%m-%d').date() <= end_date_obj]
#             except ValueError:
#                 pass
        
#         # Calculate statistics
#         total_jobs = len(filtered_data)
#         total_revenue = sum(item['revenue'] for item in filtered_data)
#         completed_jobs = sum(1 for item in filtered_data if item['status'] == 'completed')
#         avg_hours = sum(item['hours_worked'] for item in filtered_data) / total_jobs if total_jobs > 0 else 0
        
#         return JsonResponse({
#             'success': True,
#             'statistics': {
#                 'total_jobs': total_jobs,
#                 'total_revenue': float(total_revenue),
#                 'completed_jobs': completed_jobs,
#                 'avg_hours': float(avg_hours)
#             }
#         })
        
#     except Exception as e:
#         return JsonResponse({
#             'success': False,
#             'error': str(e)
#         }, status=500)

# @login_required
# @user_passes_test(is_manager)
# def export_reports_csv(request):
#     """Export filtered reports as CSV"""
#     try:
#         # Get filter parameters
#         job_id = request.GET.get('job_id', '').strip()
#         client_id = request.GET.get('client_id', '')
#         engineer_id = request.GET.get('engineer_id', '')
#         status = request.GET.get('status', '')
#         start_date = request.GET.get('start_date', '')
#         end_date = request.GET.get('end_date', '')
        
#         # Get filtered data
#         sample_data = generate_sample_data()
#         filtered_data = sample_data
        
#         # Apply filters
#         if job_id:
#             filtered_data = [item for item in filtered_data if job_id.lower() in item['job_id'].lower()]
        
#         if client_id:
#             filtered_data = [item for item in filtered_data if item['client_id'] == int(client_id)]
        
#         if engineer_id:
#             filtered_data = [item for item in filtered_data if item['engineer_id'] == int(engineer_id)]
        
#         if status:
#             filtered_data = [item for item in filtered_data if item['status'] == status]
        
#         if start_date:
#             try:
#                 start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
#                 filtered_data = [item for item in filtered_data if datetime.strptime(item['date'], '%Y-%m-%d').date() >= start_date_obj]
#             except ValueError:
#                 pass
        
#         if end_date:
#             try:
#                 end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
#                 filtered_data = [item for item in filtered_data if datetime.strptime(item['date'], '%Y-%m-%d').date() <= end_date_obj]
#             except ValueError:
#                 pass
        
#         # Create CSV response
#         response = HttpResponse(content_type='text/csv')
#         response['Content-Disposition'] = 'attachment; filename="manager_reports_{}.csv"'.format(
#             timezone.now().strftime('%Y%m%d_%H%M%S')
#         )
        
#         writer = csv.writer(response)
#         writer.writerow([
#             'Job ID', 'Client', 'Engineer', 'Date', 
#             'Hours Worked', 'Status', 'Revenue', 'Description'
#         ])
        
#         for item in filtered_data:
#             writer.writerow([
#                 item['job_id'],
#                 item['client'],
#                 item['engineer'],
#                 item['date'],
#                 item['hours_worked'],
#                 item['status'],
#                 item['revenue'],
#                 item['description']
#             ])
        
#         return response
        
#     except Exception as e:
#         return JsonResponse({
#             'success': False,
#             'error': str(e)
#         }, status=500)

# def generate_sample_data():
#     """Generate sample data for testing"""
#     clients = [
#         {'id': 1, 'name': 'TechCorp Inc.'},
#         {'id': 2, 'name': 'Global Solutions Ltd.'},
#         {'id': 3, 'name': 'Innovate Systems'},
#         {'id': 4, 'name': 'DataWorks International'},
#     ]
    
#     engineers = [
#         {'id': 1, 'name': 'John Smith'},
#         {'id': 2, 'name': 'Sarah Johnson'},
#         {'id': 3, 'name': 'Mike Brown'},
#         {'id': 4, 'name': 'Emily Davis'},
#     ]
    
#     statuses = ['completed', 'in_progress', 'pending', 'cancelled']
#     descriptions = [
#         'Regular maintenance work completed successfully',
#         'System installation and configuration',
#         'Emergency repair service',
#         'Scheduled inspection and testing',
#         'Client training and handover',
#         'Software update and patch installation',
#     ]
    
#     data = []
#     for i in range(1, 51):
#         client = random.choice(clients)
#         engineer = random.choice(engineers)
#         status = random.choice(statuses)
#         date = (datetime.now() - timedelta(days=random.randint(0, 90))).strftime('%Y-%m-%d')
        
#         data.append({
#             'id': i,
#             'job_id': f"JOB-{i:03d}",
#             'client_id': client['id'],
#             'client': client['name'],
#             'engineer_id': engineer['id'],
#             'engineer': engineer['name'],
#             'date': date,
#             'hours_worked': round(random.uniform(2.0, 12.0), 1),
#             'status': status,
#             'revenue': round(random.uniform(200.0, 2500.0), 2),
#             'description': random.choice(descriptions)
#         })
    
#     return data

# # dashboard/models.py
# from django.db import models
# from django.contrib.auth import get_user_model

# User = get_user_model()

# class JobReport(models.Model):
#     STATUS_CHOICES = [
#         ('completed', 'Completed'),
#         ('in_progress', 'In Progress'),
#         ('pending', 'Pending'),
#         ('cancelled', 'Cancelled'),
#     ]

#     job_id = models.CharField(max_length=100, unique=True)
#     client = models.ForeignKey('accounts.ClientCompany', on_delete=models.CASCADE, related_name='reports')
#     engineer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_reports')
#     date = models.DateField()
#     hours_worked = models.DecimalField(max_digits=5, decimal_places=2)
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
#     revenue = models.DecimalField(max_digits=10, decimal_places=2)
#     description = models.TextField(blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         ordering = ['-date']
#         indexes = [
#             models.Index(fields=['date']),
#             models.Index(fields=['status']),
#             models.Index(fields=['client']),
#             models.Index(fields=['engineer']),
#         ]

#     def __str__(self):
#         return f"{self.job_id} - {self.client.name}"

#     @property
#     def engineer_name(self):
#         return f"{self.engineer.first_name} {self.engineer.last_name}"

#     @property
#     def client_name(self):
#         return self.client.name