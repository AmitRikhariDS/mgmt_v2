from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse
from .models import CustomUser, ClientCompany, ClientContact, EngineerProfile
from django.contrib import messages

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user has the selected role
            if user.role == role:
                login(request, user)
                return redirect('dashboard:redirect_dashboard')
            else:
                messages.error(request, f'You are not registered as a {role}')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Set default role to engineer
            user.role = 'engineer'
            user.save()
            
            # Create corresponding profile based on role
            if user.role == 'engineer':
                EngineerProfile.objects.create(
                    user=user,
                    employee_id=f"ENG-{user.id:04d}",
                    hourly_rate=50.00
                )
            
            messages.success(request, 'Account created successfully. Please log in.')
            return redirect('accounts:login')
    else:
        form = UserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')

# accounts/views.py
import csv
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.db.models import Q, Sum, Avg, Count
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from datetime import datetime, timedelta
import random
from .models import JobReport, ClientCompany, CustomUser

def is_manager(user):
    return user.is_authenticated and user.role == 'manager'

@login_required
@user_passes_test(is_manager)
def manager_report_dashboard(request):
    """Render the manager report dashboard"""
    return render(request, 'dashboard/manager_report.html')

@login_required
@user_passes_test(is_manager)
def get_filter_options(request):
    """API endpoint to get filter options"""
    try:
        clients = list(ClientCompany.objects.values('id', 'name').order_by('name'))
        engineers = list(CustomUser.objects.filter(role='engineer')
                        .values('id', 'first_name', 'last_name')
                        .order_by('first_name'))
        
        status_options = [
            {'value': 'completed', 'label': 'Completed'},
            {'value': 'in_progress', 'label': 'In Progress'},
            {'value': 'pending', 'label': 'Pending'},
            {'value': 'cancelled', 'label': 'Cancelled'},
        ]
        
        return JsonResponse({
            'success': True,
            'clients': clients,
            'engineers': engineers,
            'status_options': status_options
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@user_passes_test(is_manager)
def get_report_data(request):
    """API endpoint to fetch filtered report data"""
    try:
        # Get filter parameters
        job_id = request.GET.get('job_id', '').strip()
        client_id = request.GET.get('client_id', '')
        engineer_id = request.GET.get('engineer_id', '')
        status = request.GET.get('status', '')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        
        # Build query
        query = Q()
        
        if job_id:
            query &= Q(job_id__icontains=job_id)
        
        if client_id:
            query &= Q(client_id=client_id)
        
        if engineer_id:
            query &= Q(engineer_id=engineer_id)
        
        if status:
            query &= Q(status=status)
        
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                query &= Q(date__gte=start_date_obj)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                query &= Q(date__lte=end_date_obj)
            except ValueError:
                pass
        
        # Fetch data with related objects
        reports = JobReport.objects.filter(query)\
            .select_related('client', 'engineer')\
            .order_by('-date')
        
        # Prepare response data
        report_data = []
        for report in reports:
            report_data.append({
                'id': report.id,
                'job_id': report.job_id,
                'client_id': report.client.id,
                'client': report.client.name,
                'engineer_id': report.engineer.id,
                'engineer': f"{report.engineer.first_name} {report.engineer.last_name}",
                'date': report.date.isoformat(),
                'hours_worked': float(report.hours_worked),
                'status': report.status,
                'revenue': float(report.revenue),
                'description': report.description
            })
        
        return JsonResponse({
            'success': True,
            'data': report_data,
            'total_count': reports.count()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@user_passes_test(is_manager)
def get_report_statistics(request):
    """API endpoint to fetch report statistics"""
    try:
        # Get filter parameters
        job_id = request.GET.get('job_id', '').strip()
        client_id = request.GET.get('client_id', '')
        engineer_id = request.GET.get('engineer_id', '')
        status = request.GET.get('status', '')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        
        # Build query
        query = Q()
        
        if job_id:
            query &= Q(job_id__icontains=job_id)
        
        if client_id:
            query &= Q(client_id=client_id)
        
        if engineer_id:
            query &= Q(engineer_id=engineer_id)
        
        if status:
            query &= Q(status=status)
        
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                query &= Q(date__gte=start_date_obj)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                query &= Q(date__lte=end_date_obj)
            except ValueError:
                pass
        
        # Calculate statistics
        reports = JobReport.objects.filter(query)
        
        total_jobs = reports.count()
        total_revenue = reports.aggregate(Sum('revenue'))['revenue__sum'] or 0
        completed_jobs = reports.filter(status='completed').count()
        avg_hours = reports.aggregate(Avg('hours_worked'))['hours_worked__avg'] or 0
        
        return JsonResponse({
            'success': True,
            'statistics': {
                'total_jobs': total_jobs,
                'total_revenue': float(total_revenue),
                'completed_jobs': completed_jobs,
                'avg_hours': float(avg_hours) if avg_hours else 0
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@user_passes_test(is_manager)
def export_reports_csv(request):
    """Export filtered reports as CSV"""
    try:
        # Get filter parameters
        job_id = request.GET.get('job_id', '').strip()
        client_id = request.GET.get('client_id', '')
        engineer_id = request.GET.get('engineer_id', '')
        status = request.GET.get('status', '')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        
        # Build query
        query = Q()
        
        if job_id:
            query &= Q(job_id__icontains=job_id)
        
        if client_id:
            query &= Q(client_id=client_id)
        
        if engineer_id:
            query &= Q(engineer_id=engineer_id)
        
        if status:
            query &= Q(status=status)
        
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                query &= Q(date__gte=start_date_obj)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                query &= Q(date__lte=end_date_obj)
            except ValueError:
                pass
        
        # Fetch data
        reports = JobReport.objects.filter(query)\
            .select_related('client', 'engineer')\
            .order_by('-date')
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="manager_reports_{}.csv"'.format(
            timezone.now().strftime('%Y%m%d_%H%M%S')
        )
        
        writer = csv.writer(response)
        writer.writerow([
            'Job ID', 'Client', 'Engineer', 'Date', 
            'Hours Worked', 'Status', 'Revenue', 'Description'
        ])
        
        for report in reports:
            writer.writerow([
                report.job_id,
                report.client.name,
                f"{report.engineer.first_name} {report.engineer.last_name}",
                report.date.strftime('%Y-%m-%d'),
                report.hours_worked,
                report.get_status_display(),
                report.revenue,
                report.description
            ])
        
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)