from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import random
from datetime import date

# 🔹 Custom User Model
class User(AbstractUser):
    ROLE_CHOICES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('therapist', 'Therapist'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    unique_id = models.CharField(max_length=20, blank=True, null=True, unique=True)
    phone = models.CharField(max_length=15, blank=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        if not self.unique_id:
            prefix = self.role[:3].upper() if self.role else "USR"
            self.unique_id = f"{prefix}_{random.randint(1000, 9999)}"
        super().save(*args, **kwargs)

    def get_age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

# 🔹 Location and Hospital Models
class Location(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Hospital(models.Model):
    name = models.CharField(max_length=100)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.location.name})"

# 🔹 Appointment Model
class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_appointments')
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.username} → {self.doctor.username} on {self.date} at {self.time}"

# 🔹 Health Log Model
class HealthLog(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'patient'}
    )
    date = models.DateField(auto_now_add=True)
    blood_pressure = models.CharField(max_length=20)
    heart_rate = models.CharField(max_length=20)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"HealthLog: {self.patient.username} on {self.date}"

# 🔹 Patient Visit Model
class PatientVisit(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'patient'}
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'doctor'},
        related_name='visits_as_doctor',
        default=12
    )
    visit_date = models.DateField()
    hospital_name = models.CharField(max_length=100)
    doctor_name = models.CharField(max_length=100)
    report_file = models.FileField(upload_to='reports/', blank=True, null=True)
    prescription_file = models.FileField(upload_to='prescriptions/', blank=True, null=True)
    medicine_details = models.TextField(blank=True)
    therapist_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Visit: {self.patient.username} with Dr. {self.doctor_name} on {self.visit_date}"

# 🔹 Visit Record Model
class VisitRecord(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='visits')
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_visits')
    visit_date = models.DateField(default=timezone.now)
    hospital_name = models.CharField(max_length=100)
    doctor_name = models.CharField(max_length=100)
    current_status = models.CharField(
        max_length=100,
        choices=[
            ('stable', 'Stable'),
            ('improving', 'Improving'),
            ('critical', 'Critical'),
            ('recovered', 'Recovered'),
        ]
    )
    improvement_score = models.PositiveIntegerField(default=0)
    doctor_notes = models.TextField(blank=True, null=True)
    prescription_file = models.FileField(upload_to='prescriptions/', blank=True, null=True)
    report_file = models.FileField(upload_to='reports/', blank=True, null=True)
    summary = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.patient.username} - {self.visit_date}"

    def save(self, *args, **kwargs):
        if not self.summary:
            self.summary = f"{self.visit_date}: {self.current_status} ({self.improvement_score}%)"
        super().save(*args, **kwargs)

# 🔹 Patient Task Model
class PatientTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    TASK_TYPE_CHOICES = [
        ('adaptive_sports', 'Adaptive Sports'),
        ('creative_arts', 'Creative Arts'),
        ('music_therapy', 'Music Therapy'),
        ('speech_therapy', 'Speech Therapy'),
        ('exercise', 'Exercise'),
        ('yoga', 'Yoga'),
        ('sensory_play', 'Sensory Play'),
        ('social_skills', 'Social Skills Training'),
        ('language_learning', 'Language Learning'),
        ('gardening', 'Gardening'),
    ]

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'patient'}
    )
    task_name = models.CharField(max_length=255)
    task_type = models.CharField(max_length=30, choices=TASK_TYPE_CHOICES, default='exercise')
    started_at = models.DateTimeField(blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    feedback = models.TextField(blank=True)

    def __str__(self):
        return f"Task: {self.patient.username} - {self.task_name} ({self.status})"

# 🔹 Mood Log Model
class MoodLog(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    mood = models.CharField(max_length=20)
    logged_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.username} - {self.mood} ({self.logged_at.date()})"

# 🔹 Improvement Score Model
class ImprovementScore(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    score = models.IntegerField()
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.username} - {self.score}"

# 🔹 Messaging Model
class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username}: {self.content[:30]}"

# 🔹 Emergency SOS Alert Model
class SOSAlert(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
    ]

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'patient'},
        related_name='sos_alerts'
    )
    message = models.TextField(blank=True, null=True, help_text="Optional emergency message from patient")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    acknowledged_by_doctor = models.BooleanField(default=False)
    acknowledged_by_therapist = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"SOS Alert: {self.patient.username} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

# 🔹 Exercise Video Model
class ExerciseVideo(models.Model):
    EXERCISE_TYPE_CHOICES = [
        ('adaptive_sports', 'Adaptive Sports'),
        ('creative_arts', 'Creative Arts'),
        ('music_therapy', 'Music Therapy'),
        ('speech_therapy', 'Speech Therapy'),
        ('exercise', 'Exercise'),
        ('yoga', 'Yoga'),
        ('sensory_play', 'Sensory Play'),
        ('social_skills', 'Social Skills Training'),
        ('language_learning', 'Language Learning'),
        ('gardening', 'Gardening'),
        ('physiotherapy', 'Physiotherapy'),
        ('occupational_therapy', 'Occupational Therapy'),
    ]

    therapist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'therapist'},
        related_name='uploaded_videos'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    exercise_type = models.CharField(max_length=30, choices=EXERCISE_TYPE_CHOICES, default='exercise')
    video_file = models.FileField(upload_to='exercise_videos/', help_text="Upload video file (MP4, AVI, MOV, etc.)")
    thumbnail = models.ImageField(upload_to='video_thumbnails/', blank=True, null=True, help_text="Optional thumbnail image")
    duration_minutes = models.PositiveIntegerField(blank=True, null=True, help_text="Estimated duration in minutes")
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='beginner'
    )
    is_active = models.BooleanField(default=True, help_text="Uncheck to hide from patients")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Exercise Video'
        verbose_name_plural = 'Exercise Videos'

    def __str__(self):
        return f"{self.title} - {self.get_exercise_type_display()}"

    def increment_views(self):
        """Increment view count"""
        self.views_count += 1
        self.save(update_fields=['views_count'])
