from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from accounts.models import (
    CustomUser, ClientCompany, EngineerProfile, Job, 
    Invoice, Payment, ServiceContract, Notification, TimeLog,Expense
)
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth import get_user_model
User = get_user_model()
@login_required
def redirect_dashboard(request):
    user_role = request.user.role
    
    if user_role == 'admin':
        return redirect('dashboard:admin_dashboard')
    elif user_role == 'manager':
        return redirect('dashboard:manager_dashboard')
    elif user_role == 'engineer':
        return redirect('dashboard:engineer_dashboard')
    elif user_role == 'client':
        return redirect('dashboard:client_dashboard')
    elif user_role == 'accounts':
        return redirect('dashboard:accounts_dashboard')
    else:
        return redirect('accounts:login')

@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:redirect_dashboard')
    
    # Get statistics for admin dashboard
    total_engineers = EngineerProfile.objects.count()
    active_engineers = EngineerProfile.objects.filter(is_available=True).count()
    total_jobs = Job.objects.count()
    ongoing_jobs = Job.objects.filter(status='in_progress').count()
    pending_invoices = Invoice.objects.filter(status='sent').count()
    total_clients = ClientCompany.objects.filter(is_active=True).count()
    
    # Recent activities
    recent_jobs = Job.objects.all().order_by('-created_at')[:5]
    recent_invoices = Invoice.objects.all().order_by('-created_at')[:5]
    
    context = {
        'total_engineers': total_engineers,
        'active_engineers': active_engineers,
        'total_jobs': total_jobs,
        'ongoing_jobs': ongoing_jobs,
        'pending_invoices': pending_invoices,
        'total_clients': total_clients,
        'recent_jobs': recent_jobs,
        'recent_invoices': recent_invoices,
    }
    
    return render(request, 'dashboard/admin.html', context)

@login_required
def manager_dashboard(request):
    if request.user.role != 'manager':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:redirect_dashboard')
    
    # Get statistics for manager dashboard
    active_projects = Job.objects.filter(status__in=['assigned', 'in_progress']).count()
    overdue_tasks = Job.objects.filter(
        Q(status='assigned') | Q(status='in_progress'),
        scheduled_date__lt=timezone.now()
    ).count()
    available_engineers = EngineerProfile.objects.filter(is_available=True).count()
    
    # Calculate completion rate
    total_jobs = Job.objects.count()
    completed_jobs = Job.objects.filter(status='completed').count()
    completion_rate = round((completed_jobs / total_jobs * 100), 2) if total_jobs > 0 else 0
    
    # Priority tasks
    priority_tasks = Job.objects.filter(
        Q(priority='high') | Q(priority='urgent'),
        status__in=['assigned', 'in_progress']
    ).order_by('scheduled_date')[:5]
    
    # Recent job assignments
    recent_assignments = Job.objects.all().order_by('-created_at')[:5]
    
    context = {
        'active_projects': active_projects,
        'overdue_tasks': overdue_tasks,
        'available_engineers': available_engineers,
        'completion_rate': completion_rate,
        'priority_tasks': priority_tasks,
        'recent_assignments': recent_assignments,
    }
    
    return render(request, 'dashboard/manager.html', context)

@login_required
def engineer_dashboard(request):
    if request.user.role != 'engineer':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:redirect_dashboard')
    
    try:
        engineer_profile = EngineerProfile.objects.get(user=request.user)
    except EngineerProfile.DoesNotExist:
        # Create a profile if it doesn't exist
        engineer_profile = EngineerProfile.objects.create(
            user=request.user,
            employee_id=f"ENG-{request.user.id:04d}",
            hourly_rate=50.00  # Default rate
        )
        messages.info(request, 'Your engineer profile has been created.')
    
    # Get engineer-specific data
    assigned_jobs = Job.objects.filter(assigned_engineer=engineer_profile, status__in=['assigned', 'in_progress'])
    completed_jobs = Job.objects.filter(assigned_engineer=engineer_profile, status='completed')
    
    # Calculate hours this week
    week_start = timezone.now() - timedelta(days=timezone.now().weekday())
    hours_this_week = TimeLog.objects.filter(
        engineer=engineer_profile,
        start_time__gte=week_start,
        is_approved=True
    ).aggregate(total_hours=Sum('duration'))['total_hours'] or timedelta(0)
    hours_this_week = hours_this_week.total_seconds() / 3600  # Convert to hours
    
    # Pending approvals
    pending_approvals = TimeLog.objects.filter(
        engineer=engineer_profile,
        is_approved=False
    ).count()
    
    # Calculate completion rate
    total_assigned = assigned_jobs.count() + completed_jobs.count()
    completion_rate = round((completed_jobs.count() / total_assigned * 100), 2) if total_assigned > 0 else 0
    
    # Today's schedule
    today = timezone.now().date()
    todays_schedule = Job.objects.filter(
        assigned_engineer=engineer_profile,
        scheduled_date__date=today,
        status__in=['assigned', 'in_progress']
    ).order_by('scheduled_date')
    
    # Recent updates
    recent_updates = Notification.objects.filter(user=request.user).order_by('-created_at')[:3]
    
    context = {
        'engineer_profile': engineer_profile,
        'assigned_jobs': assigned_jobs.count(),
        'hours_this_week': round(hours_this_week, 1),
        'pending_approvals': pending_approvals,
        'completion_rate': completion_rate,
        'todays_schedule': todays_schedule,
        'recent_updates': recent_updates,
    }
    
    return render(request, 'dashboard/engineer.html', context)
@login_required

@login_required
def client_dashboard(request):
    if request.user.role != 'client':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:redirect_dashboard')
    
    # Get client company
    try:
        client_contact = request.user.clientcontact
        client_company = client_contact.company
    except:
        # If user doesn't have a client contact, show demo data
        client_company = None
        messages.info(request, 'Client profile not found. Showing demo data.')
    
    if client_company:
        # Get client-specific data
        active_tickets = Job.objects.filter(client=client_company, status__in=['assigned', 'in_progress']).count()
        scheduled_visits = Job.objects.filter(client=client_company, status='assigned').count()
        pending_invoices = Invoice.objects.filter(client=client_company, status='sent').count()
        
        # Service history
        service_history = Job.objects.filter(client=client_company).order_by('-scheduled_date')[:10]
        
        # Upcoming visits
        upcoming_visits = Job.objects.filter(
            client=client_company,
            scheduled_date__gte=timezone.now(),
            status__in=['assigned', 'in_progress']
        ).order_by('scheduled_date')[:3]
        
        # Active service contracts
        active_contracts = ServiceContract.objects.filter(
            client=client_company,
            status='active'
        )
    else:
        # Demo data
        active_tickets = 3
        scheduled_visits = 1
        pending_invoices = 2
        service_history = []
        upcoming_visits = []
        active_contracts = []
    
    # Calculate satisfaction rate (this would typically come from ratings)
    satisfaction_rate = 95  # Placeholder - would calculate from actual ratings
    
    context = {
        'client_company': client_company,
        'active_tickets': active_tickets,
        'scheduled_visits': scheduled_visits,
        'pending_invoices': pending_invoices,
        'satisfaction_rate': satisfaction_rate,
        'service_history': service_history,
        'upcoming_visits': upcoming_visits,
        'active_contracts': active_contracts,
    }
    
    return render(request, 'dashboard/client.html', context)

@login_required
def accounts_dashboard(request):
    if request.user.role != 'accounts':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:redirect_dashboard')
    
    # Get accounting data
    outstanding_invoices = Invoice.objects.filter(status='sent').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Received this month
    current_month = timezone.now().month
    current_year = timezone.now().year
    received_this_month = Payment.objects.filter(
        payment_date__month=current_month,
        payment_date__year=current_year
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    overdue_invoices = Invoice.objects.filter(
        status='sent',
        due_date__lt=timezone.now().date()
    ).count()
    
    invoices_this_month = Invoice.objects.filter(
        issue_date__month=current_month,
        issue_date__year=current_year
    ).count()
    
    # Recent invoices
    recent_invoices = Invoice.objects.all().order_by('-issue_date')[:10]
    
    # Top clients by revenue
    top_clients = ClientCompany.objects.annotate(
        total_revenue=Sum('invoice__total_amount')
    ).order_by('-total_revenue')[:5]
    
    context = {
        'outstanding_invoices': outstanding_invoices,
        'received_this_month': received_this_month,
        'overdue_invoices': overdue_invoices,
        'invoices_this_month': invoices_this_month,
        'recent_invoices': recent_invoices,
        'top_clients': top_clients,
    }
    
    return render(request, 'dashboard/accounts.html', context)

@login_required
def update_availability(request):
    if request.user.role != 'engineer':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            engineer_profile = EngineerProfile.objects.get(user=request.user)
            is_available = request.POST.get('available') == 'true'
            engineer_profile.is_available = is_available
            engineer_profile.save()
            
            return JsonResponse({'success': True, 'available': is_available})
        except EngineerProfile.DoesNotExist:
            return JsonResponse({'error': 'Engineer profile not found'}, status=404)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def check_in_location(request, job_id):
    if request.user.role != 'engineer':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            engineer_profile = EngineerProfile.objects.get(user=request.user)
            job = get_object_or_404(Job, id=job_id, assigned_engineer=engineer_profile)
            
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            address = request.POST.get('address', '')
            
            if latitude and longitude:
                # Update engineer's current location
                engineer_profile.current_location = address
                engineer_profile.latitude = latitude
                engineer_profile.longitude = longitude
                engineer_profile.last_location_update = timezone.now()
                engineer_profile.save()
                
                # Create location record
                GeoLocation.objects.create(
                    engineer=engineer_profile,
                    latitude=latitude,
                    longitude=longitude,
                    address=address,
                    timestamp=timezone.now()
                )
                
                # Create notification for manager
                managers = CustomUser.objects.filter(role='manager')
                for manager in managers:
                    Notification.objects.create(
                        user=manager,
                        notification_type='location_update',
                        title='Engineer Checked In',
                        message=f'{engineer_profile.user.get_full_name()} checked in at {address} for job {job.job_id}',
                        related_object_type='job',
                        related_object_id=job.id
                    )
                
                messages.success(request, 'Check-in successful!')
                return JsonResponse({'success': True, 'message': 'Check-in successful!'})
            else:
                return JsonResponse({'success': False, 'error': 'Location data missing'})
                
        except (EngineerProfile.DoesNotExist, Job.DoesNotExist):
            return JsonResponse({'success': False, 'error': 'Engineer or job not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def get_current_location(request):
    if request.user.role != 'engineer':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'GET':
        try:
            # Try to get current location using browser's Geolocation API
            return render(request, 'dashboard/get_location.html')
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum, Q, Avg

from accounts.models import (
    CustomUser, ClientCompany, EngineerProfile, Job, 
    Invoice, ServiceContract, Notification, TimeLog,
    ServiceType, ClientContact
)
from accounts.forms import ExpenseForm, JobForm

@login_required
def manager_jobs(request):
    if request.user.role != 'manager':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:redirect_dashboard')
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    
    # Get all jobs with optional filtering
    jobs = Job.objects.all().order_by('-created_at')
    
    if status_filter:
        jobs = jobs.filter(status=status_filter)
    if priority_filter:
        jobs = jobs.filter(priority=priority_filter)
    
    # Get counts for filters
    status_counts = Job.objects.values('status').annotate(count=Count('id'))
    priority_counts = Job.objects.values('priority').annotate(count=Count('id'))
    
    context = {
        'jobs': jobs,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'status_counts': status_counts,
        'priority_counts': priority_counts,
    }
    
    return render(request, 'dashboard/manager_jobs.html', context)

@login_required
def add_job(request):
    if request.user.role != 'manager':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:redirect_dashboard')
    
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.created_by = request.user
            job.save()
            
            messages.success(request, f'Job "{job.title}" has been created successfully!')
            return redirect('dashboard:manager_jobs')
    else:
        form = JobForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'dashboard/add_job.html', context)

@login_required
def job_detail(request, job_id):
    if request.user.role != 'manager':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:redirect_dashboard')
    
    job = get_object_or_404(Job, id=job_id)
    
    context = {
        'job': job,
    }
    
    return render(request, 'dashboard/job_detail.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum, Q, Avg

from accounts.models import (
    CustomUser, ClientCompany, EngineerProfile, Job, 
    Invoice, ServiceContract, Notification, TimeLog,
    ServiceType, ClientContact, JobNote
)
from accounts.forms import JobForm, JobNoteForm, TimeLogForm

@login_required
def engineer_jobs(request):
    if request.user.role != 'engineer':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:redirect_dashboard')
    
    try:
        engineer_profile = EngineerProfile.objects.get(user=request.user)
    except EngineerProfile.DoesNotExist:
        messages.error(request, 'Engineer profile not found.')
        return redirect('dashboard:redirect_dashboard')
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    
    # Get jobs assigned to this engineer
    jobs = Job.objects.filter(assigned_engineer=engineer_profile).order_by('-scheduled_date')
    
    if status_filter:
        jobs = jobs.filter(status=status_filter)
    
    # Get counts for filters
    status_counts = Job.objects.filter(assigned_engineer=engineer_profile).values('status').annotate(count=Count('id'))
    
    # Get today's jobs
    today = timezone.now().date()
    todays_jobs = jobs.filter(scheduled_date__date=today)
    
    context = {
        'jobs': jobs,
        'todays_jobs': todays_jobs,
        'status_filter': status_filter,
        'status_counts': status_counts,
        'engineer_profile': engineer_profile,
    }
    
    return render(request, 'dashboard/engineer_jobs.html', context)

@login_required
def engineer_job_detail(request, job_id):
    if request.user.role != 'engineer':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:redirect_dashboard')
    
    try:
        engineer_profile = EngineerProfile.objects.get(user=request.user)
    except EngineerProfile.DoesNotExist:
        messages.error(request, 'Engineer profile not found.')
        return redirect('dashboard:redirect_dashboard')
    
    job = get_object_or_404(Job, id=job_id, assigned_engineer=engineer_profile)
    notes = JobNote.objects.filter(job=job).order_by('-created_at')
    time_logs = TimeLog.objects.filter(job=job, engineer=engineer_profile).order_by('-start_time')
    
    # Forms
    note_form = JobNoteForm()
    time_log_form = TimeLogForm()
    
    context = {
        'job': job,
        'notes': notes,
        'time_logs': time_logs,
        'note_form': note_form,
        'time_log_form': time_log_form,
    }
    
    return render(request, 'dashboard/engineer_job_detail.html', context)

@login_required
@login_required
def update_job_status(request, job_id):
    if request.user.role != 'engineer':
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('dashboard:redirect_dashboard')
    
    if request.method == 'POST':
        try:
            engineer_profile = EngineerProfile.objects.get(user=request.user)
            job = get_object_or_404(Job, id=job_id, assigned_engineer=engineer_profile)
            
            new_status = request.POST.get('status')
            if new_status in dict(Job.JOB_STATUS).keys():
                old_status = job.status
                job.status = new_status
                
                # Set actual start/end times based on status
                if new_status == 'in_progress' and not job.actual_start_time:
                    job.actual_start_time = timezone.now()
                elif new_status == 'completed' and not job.actual_end_time:
                    job.actual_end_time = timezone.now()
                
                job.save()
                
                # Create notifications for all managers (PMO group)
                managers = CustomUser.objects.filter(role='manager')
                for manager in managers:
                    Notification.objects.create(
                        user=manager,
                        notification_type='job_updated',
                        title=f'Job Status Updated',
                        message=f'Job {job.job_id} status changed from {dict(Job.JOB_STATUS)[old_status]} to {job.get_status_display()} by {engineer_profile.user.get_full_name()}',
                        related_object_type='job',
                        related_object_id=job.id
                    )
                
                # Also notify the project manager who created the job
                if job.created_by and job.created_by != request.user:
                    Notification.objects.create(
                        user=job.created_by,
                        notification_type='job_updated',
                        title=f'Job Status Updated',
                        message=f'Job {job.job_id} status changed from {dict(Job.JOB_STATUS)[old_status]} to {job.get_status_display()} by {engineer_profile.user.get_full_name()}',
                        related_object_type='job',
                        related_object_id=job.id
                    )
                
                messages.success(request, f'Job status updated to {job.get_status_display()}')
                return redirect('dashboard:engineer_job_detail', job_id=job.id)
            else:
                messages.error(request, 'Invalid status')
        except EngineerProfile.DoesNotExist:
            messages.error(request, 'Engineer profile not found')
    
    return redirect('dashboard:engineer_job_detail', job_id=job_id)

@login_required
def add_job_note(request, job_id):
    if request.user.role != 'engineer':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            engineer_profile = EngineerProfile.objects.get(user=request.user)
            job = get_object_or_404(Job, id=job_id, assigned_engineer=engineer_profile)
            
            note_form = JobNoteForm(request.POST)
            if note_form.is_valid():
                note = note_form.save(commit=False)
                note.job = job
                note.author = request.user
                note.save()
                
                messages.success(request, 'Note added successfully')
            else:
                messages.error(request, 'Error adding note')
        except EngineerProfile.DoesNotExist:
            messages.error(request, 'Engineer profile not found')
    
    return redirect('dashboard:engineer_job_detail', job_id=job_id)

@login_required
def log_time(request, job_id):
    if request.user.role != 'engineer':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            engineer_profile = EngineerProfile.objects.get(user=request.user)
            job = get_object_or_404(Job, id=job_id, assigned_engineer=engineer_profile)
            
            time_log_form = TimeLogForm(request.POST)
            if time_log_form.is_valid():
                time_log = time_log_form.save(commit=False)
                time_log.job = job
                time_log.engineer = engineer_profile
                time_log.save()
                
                messages.success(request, 'Time logged successfully')
            else:
                messages.error(request, 'Error logging time')
        except EngineerProfile.DoesNotExist:
            messages.error(request, 'Engineer profile not found')
    
    return redirect('dashboard:engineer_job_detail', job_id=job_id)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from datetime import datetime

@login_required
def edit_job(request, job_id):
    if request.user.role != 'manager':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:redirect_dashboard')
    
    job = get_object_or_404(Job, id=job_id)
    
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, f'Job "{job.title}" has been updated successfully!')
            return redirect('dashboard:job_detail', job_id=job.id)
    else:
        form = JobForm(instance=job)
    
    context = {
        'form': form,
        'job': job,
        'edit_mode': True,
    }
    
    return render(request, 'dashboard/edit_job.html', context)

@login_required
def add_job_note_manager(request, job_id):
    if request.user.role != 'manager':
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('dashboard:redirect_dashboard')
    
    job = get_object_or_404(Job, id=job_id)
    
    if request.method == 'POST':
        note_form = JobNoteForm(request.POST)
        if note_form.is_valid():
            note = note_form.save(commit=False)
            note.job = job
            note.author = request.user
            note.save()
            
            messages.success(request, 'Note added successfully!')
        else:
            messages.error(request, 'Error adding note. Please check your input.')
    
    return redirect('dashboard:job_detail', job_id=job.id)

@login_required
def job_detail(request, job_id):
    if request.user.role != 'manager':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:redirect_dashboard')
    
    job = get_object_or_404(Job, id=job_id)
    available_engineers = EngineerProfile.objects.filter(is_available=True)
    
    context = {
        'job': job,
        'available_engineers': available_engineers,
    }
    
    return render(request, 'dashboard/job_detail.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Count, Avg, Sum
from datetime import timedelta

from accounts.models import EngineerProfile, CustomUser, Job, TimeLog
from accounts.forms import EngineerProfileForm

@login_required
def manager_engineers(request):
    if request.user.role != 'manager':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:redirect_dashboard')
    
    # Get filter parameters
    availability_filter = request.GET.get('availability', '')
    skill_filter = request.GET.get('skill', '')
    
    # Get all engineers
    engineers = EngineerProfile.objects.all().select_related('user')
    
    # Apply filters
    if availability_filter == 'available':
        engineers = engineers.filter(is_available=True)
    elif availability_filter == 'unavailable':
        engineers = engineers.filter(is_available=False)
    
    if skill_filter:
        engineers = engineers.filter(skills__name__icontains=skill_filter)
    
    # Get skills for filter dropdown
    skills = EngineerProfile.objects.values_list('skills__name', flat=True).distinct()
    
    # Get stats
    total_engineers = engineers.count()
    available_engineers = engineers.filter(is_available=True).count()
    
    context = {
        'engineers': engineers,
        'total_engineers': total_engineers,
        'available_engineers': available_engineers,
        'availability_filter': availability_filter,
        'skill_filter': skill_filter,
        'skills': skills,
    }
    
    return render(request, 'dashboard/manager_engineers.html', context)


from accounts.forms import CustomUserCreationForm, EngineerProfileForm

@login_required
def add_engineer(request):
    if request.user.role != 'manager':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:redirect_dashboard')
    
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        profile_form = EngineerProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            try:
                # Create user
                user = user_form.save()
                
                # Create engineer profile
                profile = profile_form.save(commit=False)
                profile.user = user
                
                # Generate employee ID if not provided
                if not profile.employee_id:
                    profile.employee_id = f"ENG-{user.id:04d}"
                    
                profile.save()
                profile_form.save_m2m()  # Save many-to-many data (skills)
                
                messages.success(request, f'Engineer {user.get_full_name()} has been created successfully!')
                return redirect('dashboard:manager_engineers')
                
            except Exception as e:
                messages.error(request, f'Error creating engineer: {str(e)}')
        else:
            # Combine form errors
            errors = []
            for form in [user_form, profile_form]:
                for field, error_list in form.errors.items():
                    field_label = form.fields[field].label if field in form.fields else field
                    for error in error_list:
                        errors.append(f"{field_label}: {error}")
            for error in errors:
                messages.error(request, error)
    else:
        user_form = CustomUserCreationForm()
        profile_form = EngineerProfileForm()
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    
    return render(request, 'dashboard/add_engineer.html', context)

@login_required
def engineer_detail(request, engineer_id):
    if request.user.role != 'manager':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:redirect_dashboard')
    
    engineer = get_object_or_404(EngineerProfile, id=engineer_id)
    
    # Get engineer stats
    assigned_jobs = Job.objects.filter(assigned_engineer=engineer)
    completed_jobs = assigned_jobs.filter(status='completed')
    ongoing_jobs = assigned_jobs.filter(status='in_progress')
    
    # Calculate average rating (placeholder - would come from actual ratings)
    avg_rating = 4.5  # This would be calculated from actual ratings
    
    # Calculate total hours worked
    time_logs = TimeLog.objects.filter(engineer=engineer, is_approved=True)
    total_hours = sum((log.duration.total_seconds() / 3600 for log in time_logs if log.duration), 0)
    
    # Recent jobs
    recent_jobs = assigned_jobs.order_by('-scheduled_date')[:5]
    
    context = {
        'engineer': engineer,
        'assigned_jobs_count': assigned_jobs.count(),
        'completed_jobs_count': completed_jobs.count(),
        'ongoing_jobs_count': ongoing_jobs.count(),
        'avg_rating': avg_rating,
        'total_hours': round(total_hours, 1),
        'recent_jobs': recent_jobs,
    }
    
    return render(request, 'dashboard/engineer_detail.html', context)

@login_required
def edit_engineer(request, engineer_id):
    if request.user.role != 'manager':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:redirect_dashboard')
    
    engineer = get_object_or_404(EngineerProfile, id=engineer_id)
    
    if request.method == 'POST':
        profile_form = EngineerProfileForm(request.POST, instance=engineer)
        
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, f'Engineer {engineer.user.get_full_name()} has been updated successfully!')
            return redirect('dashboard:engineer_detail', engineer_id=engineer.id)
        else:
            for field, errors in profile_form.errors.items():
                for error in errors:
                    messages.error(request, f"{profile_form.fields[field].label}: {error}")
    else:
        profile_form = EngineerProfileForm(instance=engineer)
    
    context = {
        'profile_form': profile_form,
        'engineer': engineer,
    }
    
    return render(request, 'dashboard/edit_engineer.html', context)


@login_required
def toggle_engineer_availability(request, engineer_id):
    if request.user.role != 'manager':
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('dashboard:redirect_dashboard')
    
    if request.method == 'POST':
        engineer = get_object_or_404(EngineerProfile, id=engineer_id)
        engineer.is_available = not engineer.is_available
        engineer.save()
        
        status = "available" if engineer.is_available else "unavailable"
        messages.success(request, f'{engineer.user.get_full_name()} is now {status}.')
    
    return redirect('dashboard:manager_engineers')

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import base64
import uuid
from datetime import datetime

@login_required
def add_voice_note(request, job_id):
    if request.user.role != 'engineer':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            engineer_profile = EngineerProfile.objects.get(user=request.user)
            job = get_object_or_404(Job, id=job_id, assigned_engineer=engineer_profile)
            
            # Handle audio file upload
            audio_file = request.FILES.get('audio_file')
            content = request.POST.get('content', '')
            
            if audio_file:
                # Create job note with voice recording
                note = JobNote(
                    job=job,
                    author=request.user,
                    note_type='voice',
                    content=content,
                    audio_file=audio_file
                )
                note.save()
                
                messages.success(request, 'Voice note added successfully!')
                return redirect('dashboard:engineer_job_detail', job_id=job.id)
            else:
                messages.error(request, 'No audio file provided.')
        except EngineerProfile.DoesNotExist:
            messages.error(request, 'Engineer profile not found.')
        except Exception as e:
            messages.error(request, f'Error adding voice note: {str(e)}')
    
    return redirect('dashboard:engineer_job_detail', job_id=job_id)

@login_required
def add_image_note(request, job_id):
    if request.user.role != 'engineer':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            engineer_profile = EngineerProfile.objects.get(user=request.user)
            job = get_object_or_404(Job, id=job_id, assigned_engineer=engineer_profile)
            
            # Handle image file upload
            image_file = request.FILES.get('image')
            content = request.POST.get('content', '')
            
            if image_file:
                # Create job note with image
                note = JobNote(
                    job=job,
                    author=request.user,
                    note_type='image',
                    content=content,
                    image=image_file
                )
                note.save()
                
                messages.success(request, 'Photo added successfully!')
                return redirect('dashboard:engineer_job_detail', job_id=job.id)
            else:
                messages.error(request, 'No image file provided.')
        except EngineerProfile.DoesNotExist:
            messages.error(request, 'Engineer profile not found.')
        except Exception as e:
            messages.error(request, f'Error adding photo: {str(e)}')
    
    return redirect('dashboard:engineer_job_detail', job_id=job_id)

@login_required
def add_expense(request, job_id):
    if request.user.role != 'engineer':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            engineer_profile = EngineerProfile.objects.get(user=request.user)
            job = get_object_or_404(Job, id=job_id, assigned_engineer=engineer_profile)
            
            # Handle expense data
            expense_amount = request.POST.get('expense_amount')
            expense_description = request.POST.get('expense_description', '')
            receipt_file = request.FILES.get('expense_receipt')
            
            if expense_amount and receipt_file:
                # Create job note with expense
                note = JobNote(
                    job=job,
                    author=request.user,
                    note_type='expense',
                    expense_description=expense_description,
                    expense_amount=expense_amount,
                    expense_receipt=receipt_file
                )
                note.save()
                
                messages.success(request, 'Expense submitted successfully!')
                return redirect('dashboard:engineer_job_detail', job_id=job.id)
            else:
                messages.error(request, 'Please provide both amount and receipt.')
        except EngineerProfile.DoesNotExist:
            messages.error(request, 'Engineer profile not found.')
        except Exception as e:
            messages.error(request, f'Error submitting expense: {str(e)}')
    
    return redirect('dashboard:engineer_job_detail', job_id=job_id)

@login_required
def capture_photo(request, job_id):
    if request.user.role != 'engineer':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST' and request.is_ajax():
        try:
            engineer_profile = EngineerProfile.objects.get(user=request.user)
            job = get_object_or_404(Job, id=job_id, assigned_engineer=engineer_profile)
            
            # Get base64 image data from request
            image_data = request.POST.get('image_data')
            content = request.POST.get('content', '')
            
            if image_data:
                # Convert base64 to image file
                format, imgstr = image_data.split(';base64,')
                ext = format.split('/')[-1]
                
                # Generate unique filename
                filename = f"job_notes/images/{job.job_id}_{uuid.uuid4().hex[:8]}.{ext}"
                data = ContentFile(base64.b64decode(imgstr), name=filename)
                
                # Create job note with image
                note = JobNote(
                    job=job,
                    author=request.user,
                    note_type='image',
                    content=content,
                    image=data
                )
                note.save()
                
                return JsonResponse({'success': True, 'message': 'Photo captured successfully!'})
            else:
                return JsonResponse({'success': False, 'error': 'No image data provided.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def record_audio(request, job_id):
    if request.user.role != 'engineer':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST' and request.is_ajax():
        try:
            engineer_profile = EngineerProfile.objects.get(user=request.user)
            job = get_object_or_404(Job, id=job_id, assigned_engineer=engineer_profile)
            
            # Get audio file from request
            audio_file = request.FILES.get('audio_file')
            content = request.POST.get('content', '')
            
            if audio_file:
                # Create job note with audio
                note = JobNote(
                    job=job,
                    author=request.user,
                    note_type='voice',
                    content=content,
                    audio_file=audio_file
                )
                note.save()
                
                return JsonResponse({'success': True, 'message': 'Audio recorded successfully!'})
            else:
                return JsonResponse({'success': False, 'error': 'No audio file provided.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

from accounts.models import Expense
@login_required
def accounts_notifications(request):
    if request.user.role != 'accounts':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:redirect_dashboard')
    
    # Get notifications for accounts team (expense-related)
    notifications = Notification.objects.filter(
        user=request.user,
        notification_type='expense_submitted'
    ).order_by('-created_at')
    
    # Mark as read
    notifications.update(is_read=True)
    
    context = {
        'notifications': notifications,
    }
    
    return render(request, 'dashboard/accounts_notifications.html', context)

@login_required
def get_unread_notifications_count(request):
    if request.user.role != 'manager':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})
@login_required

def manager_job_updates(request):
    if request.user.role != 'manager':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:redirect_dashboard')
    
    # Get filter parameters
    notification_type = request.GET.get('type', '')
    time_filter = request.GET.get('time', '')
    
    # Get unread count first
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    # Get notifications for this manager
    notifications = Notification.objects.filter(user=request.user)
    
    # Apply filters
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)
    
    if time_filter == 'today':
        notifications = notifications.filter(created_at__date=timezone.now().date())
    elif time_filter == 'week':
        notifications = notifications.filter(created_at__date__gte=timezone.now().date() - timezone.timedelta(days=7))
    
    # Order by most recent
    notifications = notifications.order_by('-created_at')
    
    # Get the notifications to display (slice after ordering)
    displayed_notifications = list(notifications[:50])
    
    # Mark all notifications as read (not just the displayed ones)
    notifications.update(is_read=True)
    
    context = {
        'notifications': displayed_notifications,
        'unread_count': unread_count,
        'notification_type': notification_type,
        'time_filter': time_filter,
    }
    
    return render(request, 'dashboard/manager_job_updates.html', context)

@login_required
def get_unread_notifications_count(request):
    if request.user.role not in ['manager', 'accounts']:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})
@login_required
def accounts_notifications(request):
    if request.user.role != 'accounts':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:redirect_dashboard')
    
    # Get filter parameters
    notification_type = request.GET.get('type', 'expense_submitted')
    time_filter = request.GET.get('time', '')
    
    # Get notifications for accounts team (primarily expense-related)
    notifications = Notification.objects.filter(
        user=request.user,
        notification_type='expense_submitted'
    )
    
    # Apply time filter
    if time_filter == 'today':
        notifications = notifications.filter(created_at__date=timezone.now().date())
    elif time_filter == 'week':
        notifications = notifications.filter(created_at__date__gte=timezone.now().date() - timezone.timedelta(days=7))
    
    # Get the IDs of notifications to mark as read
    notification_ids = list(notifications.values_list('id', flat=True))
    
    # Order by most recent
    notifications = notifications.order_by('-created_at')[:50]
    
    # Get unread count
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    # Mark all filtered notifications as read
    if notification_ids:
        Notification.objects.filter(id__in=notification_ids).update(is_read=True)
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
        'notification_type': notification_type,
        'time_filter': time_filter,
    }
    
    return render(request, 'dashboard/accounts_notifications.html', context)


@login_required
def add_expense(request, job_id):
    if request.user.role != 'engineer':
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('dashboard:redirect_dashboard')
    
    try:
        engineer_profile = EngineerProfile.objects.get(user=request.user)
        job = get_object_or_404(Job, id=job_id, assigned_engineer=engineer_profile)
        
        if request.method == 'POST':
            # Handle expense data
            category = request.POST.get('category')
            description = request.POST.get('description')
            amount = request.POST.get('amount')
            date_incurred = request.POST.get('date_incurred')
            receipt = request.FILES.get('receipt')
            
            # Validate required fields
            if not all([category, description, amount, receipt]):
                messages.error(request, 'Please fill all required fields.')
                return redirect('dashboard:engineer_job_detail', job_id=job.id)
            
            try:
                # Create expense
                expense = Expense(
                    job=job,
                    engineer=engineer_profile,
                    category=category,
                    description=description,
                    amount=amount,
                    date_incurred=date_incurred or timezone.now().date(),
                    receipt=receipt
                )
                expense.save()
                
                # Create notification for account team
                account_team = CustomUser.objects.filter(role='accounts')
                for account_user in account_team:
                    Notification.objects.create(
                        user=account_user,
                        notification_type='expense_submitted',
                        title='New Expense Requires Review',
                        message=f'Engineer {engineer_profile.user.get_full_name()} submitted a ${amount} expense for job {job.job_id} ({job.client.name})',
                        related_object_type='expense',
                        related_object_id=expense.id
                    )
                
                # Also notify managers
                managers = CustomUser.objects.filter(role='manager')
                for manager in managers:
                    Notification.objects.create(
                        user=manager,
                        notification_type='expense_submitted',
                        title='New Expense Submitted',
                        message=f'Engineer {engineer_profile.user.get_full_name()} submitted a ${amount} expense for job {job.job_id}',
                        related_object_type='expense',
                        related_object_id=expense.id
                    )
                
                messages.success(request, 'Expense submitted successfully! Sent to account team for review.')
                return redirect('dashboard:engineer_job_detail', job_id=job.id)
                
            except (ValueError, IntegrityError) as e:
                messages.error(request, f'Error saving expense: {str(e)}')
                
    except (EngineerProfile.DoesNotExist, Job.DoesNotExist):
        messages.error(request, 'Engineer profile or job not found.')
    
    return redirect('dashboard:engineer_job_detail', job_id=job_id)

@login_required
def engineer_job_detail(request, job_id):
    if request.user.role != 'engineer':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:redirect_dashboard')
    
    try:
        engineer_profile = EngineerProfile.objects.get(user=request.user)
    except EngineerProfile.DoesNotExist:
        messages.error(request, 'Engineer profile not found.')
        return redirect('dashboard:redirect_dashboard')
    
    job = get_object_or_404(Job, id=job_id, assigned_engineer=engineer_profile)
    notes = JobNote.objects.filter(job=job).order_by('-created_at')
    time_logs = TimeLog.objects.filter(job=job, engineer=engineer_profile).order_by('-start_time')
    expenses = Expense.objects.filter(job=job, engineer=engineer_profile).order_by('-created_at')
    
    # Forms
    note_form = JobNoteForm()
    expense_form = ExpenseForm()
    
    context = {
        'job': job,
        'notes': notes,
        'time_logs': time_logs,
        'expenses': expenses,
        'note_form': note_form,
        'expense_form': expense_form,
    }
    
    return render(request, 'dashboard/engineer_job_detail.html', context)
@login_required
def manager_job_updates_real_time(request):
    if request.user.role != 'manager':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:redirect_dashboard')
    
    # Get the latest update timestamp from the request
    last_update = request.GET.get('last_update')
    
    if last_update:
        try:
            last_update_dt = timezone.datetime.fromisoformat(last_update.replace('Z', '+00:00'))
            # Get jobs updated since the last check
            updated_jobs = Job.objects.filter(
                last_updated__gt=last_update_dt
            ).order_by('-last_updated')
        except (ValueError, TypeError):
            updated_jobs = Job.objects.none()
    else:
        # Get all jobs ordered by most recent update
        updated_jobs = Job.objects.all().order_by('-last_updated')[:20]
    
    # Get recent notifications
    recent_notifications = Notification.objects.filter(
        user=request.user,
        notification_type__in=['job_updated', 'job_assigned', 'expense_submitted', 'location_update']
    ).order_by('-created_at')[:10]
    
    # Prepare response data
    response_data = {
        'current_time': timezone.now().isoformat(),
        'updated_jobs': [
            {
                'id': job.id,
                'job_id': job.job_id,
                'title': job.title,
                'client': job.client.name,
                'status': job.get_status_display(),
                'priority': job.get_priority_display(),
                'assigned_engineer': job.assigned_engineer.user.get_full_name() if job.assigned_engineer else 'Unassigned',
                'last_updated': job.last_updated.isoformat(),
                'updated_by': job.updated_by.get_full_name() if job.updated_by else 'System',
            }
            for job in updated_jobs
        ],
        'notifications': [
            {
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.notification_type,
                'created_at': notification.created_at.isoformat(),
                'related_object_type': notification.related_object_type,
                'related_object_id': notification.related_object_id,
            }
            for notification in recent_notifications
        ]
    }
    
    return JsonResponse(response_data)
@login_required
def manager_job_updates(request):
    if request.user.role != 'manager':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:redirect_dashboard')
    
    # Get recent job updates (status changes, new assignments, etc.)
    recent_updates = Notification.objects.filter(
        Q(notification_type='job_updated') | 
        Q(notification_type='job_assigned') |
        Q(notification_type='location_update') |
        Q(notification_type='expense_submitted'),
        user=request.user
    ).order_by('-created_at')[:50]
    
    # Mark notifications as read
    recent_updates.update(is_read=True)
    
    context = {
        'recent_updates': recent_updates,
    }
    
    return render(request, 'dashboard/manager_job_updates.html', context)

@login_required
def update_job_status(request, job_id):
    if request.user.role != 'engineer':
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('dashboard:redirect_dashboard')
    
    if request.method == 'POST':
        try:
            engineer_profile = EngineerProfile.objects.get(user=request.user)
            job = get_object_or_404(Job, id=job_id, assigned_engineer=engineer_profile)
            
            new_status = request.POST.get('status')
            if new_status in dict(Job.JOB_STATUS).keys():
                old_status = job.status
                job.status = new_status
                job.updated_by = request.user  # Set who made the update
                
                # Set actual start/end times based on status
                if new_status == 'in_progress' and not job.actual_start_time:
                    job.actual_start_time = timezone.now()
                elif new_status == 'completed' and not job.actual_end_time:
                    job.actual_end_time = timezone.now()
                
                job.save()
                
                messages.success(request, f'Job status updated to {job.get_status_display()}')
                return redirect('dashboard:engineer_job_detail', job_id=job.id)
            else:
                messages.error(request, 'Invalid status')
        except EngineerProfile.DoesNotExist:
            messages.error(request, 'Engineer profile not found')
    
    return redirect('dashboard:engineer_job_detail', job_id=job_id)

@login_required
def assign_engineer(request, job_id):
    if request.user.role != 'manager':
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('dashboard:redirect_dashboard')
    
    job = get_object_or_404(Job, id=job_id)
    
    if request.method == 'POST':
        engineer_id = request.POST.get('engineer_id')
        
        if engineer_id:
            try:
                engineer = EngineerProfile.objects.get(id=engineer_id)
                job.assigned_engineer = engineer
                job.status = 'assigned'
                job.updated_by = request.user  # Set who made the update
                job.save()
                
                # Create notification for the engineer
                Notification.objects.create(
                    user=engineer.user,
                    notification_type='job_assigned',
                    title='New Job Assignment',
                    message=f'You have been assigned to job {job.job_id}: {job.title}',
                    related_object_type='job',
                    related_object_id=job.id
                )
                
                messages.success(request, f'Job assigned to {engineer.user.get_full_name()} successfully!')
            except EngineerProfile.DoesNotExist:
                messages.error(request, 'Selected engineer not found.')
        else:
            # Unassign engineer
            job.assigned_engineer = None
            job.status = 'pending'
            job.updated_by = request.user  # Set who made the update
            job.save()
            messages.success(request, 'Engineer unassigned from job.')
    
    return redirect('dashboard:job_detail', job_id=job.id)

@login_required
def update_schedule(request, job_id):
    if request.user.role != 'manager':
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('dashboard:redirect_dashboard')
    
    job = get_object_or_404(Job, id=job_id)
    
    if request.method == 'POST':
        scheduled_date_str = request.POST.get('scheduled_date')
        estimated_duration = request.POST.get('estimated_duration')
        
        try:
            if scheduled_date_str:
                # Convert string to datetime object
                scheduled_date = datetime.fromisoformat(scheduled_date_str.replace('Z', '+00:00'))
                job.scheduled_date = scheduled_date
            
            if estimated_duration:
                job.estimated_duration = timedelta(minutes=int(estimated_duration))
            
            job.updated_by = request.user  # Set who made the update
            job.save()
            
            messages.success(request, 'Job schedule updated successfully!')
        except (ValueError, TypeError) as e:
            messages.error(request, f'Error updating schedule: {str(e)}')
    
    return redirect('dashboard:job_detail', job_id=job.id)

@login_required
def manager_real_time_dashboard(request):
    if request.user.role != 'manager':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:redirect_dashboard')
    
    context = {
        'updates_enabled': True,
    }
    
    return render(request, 'dashboard/manager_real_time_dashboard.html', context)