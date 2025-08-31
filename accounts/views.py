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
    return redirect('dashboard:home')

# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib import messages

User = get_user_model()

def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        role = request.POST.get("role")  # client or engineer

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("register")

        # ✅ Create user in CustomUser
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role  # assuming your CustomUser has a role field
        )

        # ✅ Add user to respective group
        try:
            group = Group.objects.get(name=role.capitalize())  # "Client" or "Engineer"
        except Group.DoesNotExist:
            group = Group.objects.create(name=role.capitalize())
        user.groups.add(group)

        login(request, user)
        messages.success(request, f"Account created successfully as {role}.")
        return redirect('accounts:login') # redirect after signup

    return render(request, "accounts/register.html")

@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')