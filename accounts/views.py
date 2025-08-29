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