# dashboard/forms.py
from django import forms
from django.contrib.auth import get_user_model

# Adjust imports if your models are elsewhere
try:
    from accounts.models import Job, EngineerProfile, ClientCompany
except Exception:
    # fallback — adjust to your actual 
    # 
    # location, e.g. from core.models import Job, Engineer, Client
    from accounts.models import Job, EngineerProfile, ClientCompany

User = get_user_model()

# Fields the manager can include in report
FIELD_CHOICES = [
    ('job_id', 'Job ID'),
    ('job_title', 'Job Title'),
    ('client', 'ClientCompany'),
    ('engineer', 'EngineerProfile'),
    ('status', 'Status'),
    ('created_at', 'Created At'),
    ('scheduled_date', 'Scheduled Date'),
    ('completed_at', 'Completed At'),
    ('location', 'Location'),
    ('description', 'Description'),
    ('cost', 'Cost'),
]

# dashboard/forms.py
from django import forms
from accounts.models import Job, EngineerProfile, ClientCompany

class ReportFilterForm(forms.Form):
    engineer = forms.ModelChoiceField(
        queryset=EngineerProfile.objects.all().order_by('id'),
        required=False,
        empty_label="All Engineers",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    client = forms.ModelChoiceField(
        queryset=ClientCompany.objects.all().order_by('id'),
        required=False,
        empty_label="All Clients",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    job = forms.ModelChoiceField(
        queryset=Job.objects.all().order_by('id'),
        required=False,
        empty_label="All Jobs",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )

    fields = forms.MultipleChoiceField(
        choices=[
            ('id', 'Job ID'),
            ('client', 'Client'),
            ('assigned_engineer', 'Engineer'),
            ('service_type', 'Service Type'),
            ('created_at', 'Created Date'),
            ('updated_at', 'Updated Date'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    def clean(self):
        cleaned = super().clean()
        # if no fields selected, provide sensible defaults
        if not cleaned.get('fields'):
            # default columns
            cleaned['fields'] = ['job_id', 'job_title', 'client', 'engineer', 'status', 'created_at']
        return cleaned



from django import forms
from accounts.models import ClientCompany, ClientContact

class ClientCompanyForm(forms.ModelForm):
    class Meta:
        model = ClientCompany
        fields = [
            "name", "contact_email", "contact_phone", "address",
            "industry", "website", "is_active"
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "contact_email": forms.EmailInput(attrs={"class": "form-control"}),
            "contact_phone": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "industry": forms.TextInput(attrs={"class": "form-control"}),
            "website": forms.URLInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ClientContactForm(forms.ModelForm):
    class Meta:
        model = ClientContact
        fields = ["company", "user", "position", "is_primary"]
        widgets = {
            "company": forms.Select(attrs={"class": "form-select"}),
            "user": forms.Select(attrs={"class": "form-select"}),
            "position": forms.TextInput(attrs={"class": "form-control"}),
            "is_primary": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
