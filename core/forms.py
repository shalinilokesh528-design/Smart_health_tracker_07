from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from core.models import (
    PatientVisit, HealthLog, PatientTask,
    VisitRecord, Location, Hospital, Appointment, ExerciseVideo
)

User = get_user_model()

# 🔹 Unified Registration Form
class UnifiedRegisterForm(UserCreationForm):
    ROLE_CHOICES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('therapist', 'Therapist'),
    )

    role = forms.ChoiceField(choices=ROLE_CHOICES, label="Register as")
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=True, label="Phone Number")

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'role', 'password1', 'password2']
        help_texts = {
            'username': None,
            'password1': None,
            'password2': None,
        }

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        role = self.cleaned_data.get('role')
        if role in ['doctor', 'therapist'] and not password.startswith('admin'):
            raise ValidationError("Invalid Password. Doctor/Therapist passwords must start with 'admin'.")
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['username']
        user.last_name = self.cleaned_data['phone']
        if commit:
            user.save()
        return user

# 🔹 Patient ID Lookup Form
class PatientLookupForm(forms.Form):
    patient_id = forms.CharField(label="Enter Patient ID", max_length=100)

# 🔹 Patient Visit Form
class PatientVisitForm(forms.ModelForm):
    class Meta:
        model = PatientVisit
        fields = ['visit_date', 'hospital_name', 'doctor_name', 'report_file', 'prescription_file', 'medicine_details']
        widgets = {
            'visit_date': forms.DateInput(attrs={'type': 'date'}),
            'medicine_details': forms.Textarea(attrs={'rows': 3}),
        }



# 🔹 Patient Profile Form
from django.contrib.auth import get_user_model

User = get_user_model()
# Replace with your actual model if different

class PatientForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'location', 'date_of_birth', 'profile_photo'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

# 🔹 Health Log Submission Form
class HealthLogForm(forms.ModelForm):
    class Meta:
        model = HealthLog
        fields = ['blood_pressure', 'heart_rate', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

# 🔹 Patient Task Form
class PatientTaskForm(forms.ModelForm):
    class Meta:
        model = PatientTask
        fields = ['duration_minutes', 'task_type']
        widgets = {
            'duration_minutes': forms.NumberInput(attrs={'placeholder': 'Duration in minutes'}),
            'task_type': forms.Select()
        }

# 🔹 Therapist Feedback Form
class TherapistFeedbackForm(forms.ModelForm):
    class Meta:
        model = PatientTask
        fields = ['feedback']
        widgets = {
            'feedback': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter feedback...'})
        }

# 🔹 Therapist Notes Form
class TherapistNotesForm(forms.ModelForm):
    class Meta:
        model = PatientVisit
        fields = ['therapist_notes']
        widgets = {
            'therapist_notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter therapist notes here...'})
        }

# 🔹 Doctor Visit Form
class DoctorVisitForm(forms.ModelForm):
    class Meta:
        model = VisitRecord
        fields = ['visit_date', 'hospital_name', 'doctor_name', 'current_status',
                  'improvement_score', 'doctor_notes', 'prescription_file', 'report_file']
        widgets = {
            'visit_date': forms.DateInput(attrs={'type': 'date'}),
            'doctor_notes': forms.Textarea(attrs={'rows': 3}),
        }

# 🔹 Appointment Form
class AppointmentForm(forms.ModelForm):
    location = forms.ModelChoiceField(queryset=Location.objects.all(), required=True)
    hospital = forms.ModelChoiceField(queryset=Hospital.objects.none(), required=True)
    doctor = forms.ModelChoiceField(queryset=User.objects.filter(role='doctor'), required=True)

    class Meta:
        model = Appointment
        fields = ['location', 'hospital', 'doctor', 'date', 'time', 'reason']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'location' in self.data:
            try:
                location_id = int(self.data.get('location'))
                self.fields['hospital'].queryset = Hospital.objects.filter(location_id=location_id)
            except (ValueError, TypeError):
                self.fields['hospital'].queryset = Hospital.objects.none()
        elif self.instance.pk:
            self.fields['hospital'].queryset = Hospital.objects.filter(location=self.instance.location)

# 🔹 Visit Update Form
class VisitUpdateForm(forms.ModelForm):
    class Meta:
        model = VisitRecord
        fields = ['current_status', 'improvement_score', 'doctor_notes']

# 🔹 Doctor Profile Form
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class DoctorProfileForm(forms.ModelForm):
    delete_photo = forms.BooleanField(
        required=False,
        label="Delete Profile Photo",
        help_text="Check to remove your current profile picture"
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'role',
            'profile_photo',
        ]
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email',
            'phone': 'Phone Number',
            'role': 'Role',
            'profile_photo': 'Upload New Photo',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'Enter first name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Enter last name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter email'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Enter phone number'}),
            'role': forms.TextInput(attrs={'readonly': 'readonly'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)

        # Handle photo deletion
        if self.cleaned_data.get('delete_photo'):
            if user.profile_photo:
                user.profile_photo.delete(save=False)
                user.profile_photo = None

        # Handle photo upload
        if self.cleaned_data.get('profile_photo'):
            user.profile_photo = self.cleaned_data['profile_photo']

        if commit:
            user.save()
        return user


        

# 🔹 Patient Profile Form (Reusable for All Roles)
class PatientProfileForm(forms.ModelForm):
    delete_photo = forms.BooleanField(
        required=False,
        label="Delete Profile Photo",
        help_text="Check to remove your current profile picture"
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'date_of_birth',
            'location',
            'role',
            'profile_photo',
        ]
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email',
            'phone': 'Phone Number',
            'date_of_birth': 'Date of Birth',
            'location': 'Location',
            'role': 'Role',
            'profile_photo': 'Upload New Photo',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'Enter first name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Enter last name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter email'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Enter phone number'}),
            'location': forms.TextInput(attrs={'placeholder': 'Enter location'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'role': forms.TextInput(attrs={'readonly': 'readonly'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)

        # Handle photo deletion
        if self.cleaned_data.get('delete_photo'):
            if user.profile_photo:
                user.profile_photo.delete(save=False)
                user.profile_photo = None

        # Handle photo upload
        uploaded_photo = self.cleaned_data.get('profile_photo')
        if uploaded_photo:
            user.profile_photo = uploaded_photo

        if commit:
            user.save()
        return user

# 🔹 Exercise Video Upload Form
class ExerciseVideoForm(forms.ModelForm):
    class Meta:
        model = ExerciseVideo
        fields = ['title', 'description', 'exercise_type', 'video_file', 'thumbnail', 
                  'duration_minutes', 'difficulty_level', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter video title (e.g., "Morning Yoga Routine")'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the exercise, instructions, and benefits...'
            }),
            'exercise_type': forms.Select(attrs={'class': 'form-control'}),
            'video_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'video/*'
            }),
            'thumbnail': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Estimated duration in minutes',
                'min': 1
            }),
            'difficulty_level': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
        labels = {
            'title': 'Video Title',
            'description': 'Description',
            'exercise_type': 'Exercise Type',
            'video_file': 'Video File',
            'thumbnail': 'Thumbnail Image (Optional)',
            'duration_minutes': 'Duration (minutes)',
            'difficulty_level': 'Difficulty Level',
            'is_active': 'Make Visible to Patients'
        }
