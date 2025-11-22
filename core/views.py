from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Avg, Count, Max
from datetime import timedelta, date

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login
from django.http import JsonResponse

import logging

from .forms import (
    UnifiedRegisterForm,
    PatientLookupForm,
    HealthLogForm,
    PatientVisitForm,
    PatientTaskForm,
    TherapistFeedbackForm,
    TherapistNotesForm,
    ExerciseVideoForm,
    DoctorVisitForm,
    AppointmentForm,
    PatientProfileForm,
    DoctorProfileForm,
    VisitUpdateForm,
    PatientForm,
)

from .models import (
    User,
    HealthLog,
    PatientVisit,
    PatientTask,
    SOSAlert,
    ExerciseVideo,
    Appointment,
    MoodLog,
    ImprovementScore,
    VisitRecord,
    Hospital,
    Message,
)

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
#  UTILITIES
# -------------------------------------------------------------------

def calculate_age(dob):
    if dob:
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return None


def get_weekly_progress(user):
    today = timezone.now()
    week_ago = today - timedelta(days=7)

    task_count = PatientTask.objects.filter(
        patient=user,
        completed_at__gte=week_ago,
        status='completed'
    ).count()

    mood_summary = MoodLog.objects.filter(
        patient=user,
        logged_at__gte=week_ago
    ).values('mood').annotate(count=Count('mood'))

    avg_score = ImprovementScore.objects.filter(
        patient=user,
        recorded_at__gte=week_ago
    ).aggregate(avg=Avg('score'))['avg'] or 0

    return {
        'task_count': task_count,
        'mood_summary': mood_summary,
        'avg_score': round(avg_score, 1),
        'ai_summary': f"You’ve completed {task_count} tasks and improved your score to {round(avg_score)} this week."
    }

# -------------------------------------------------------------------
#  ROOT / HOME
# -------------------------------------------------------------------

def root_redirect(request):
    """Redirect root URL to register page"""
    return redirect('register')

# -------------------------------------------------------------------
#  AUTH / REGISTER / LOGIN
# -------------------------------------------------------------------

# 🔹 Register View – with role selection (patient/doctor/therapist)
def unified_register(request):
    selected_role = request.GET.get('role') or request.POST.get('role')

    if request.method == 'POST':
        data = request.POST.copy()

        if selected_role:
            data['role'] = selected_role

        form = UnifiedRegisterForm(data)
        if form.is_valid():
            user = form.save(commit=False)
            if selected_role:
                user.role = selected_role
            user.save()

            login(request, user)

            if user.role == 'patient':
                return redirect('patient_home')
            elif user.role == 'doctor':
                return redirect('doctor_profile')
            elif user.role == 'therapist':
                return redirect('therapist_profile')
    else:
        if selected_role:
            form = UnifiedRegisterForm(initial={'role': selected_role})
        else:
            form = UnifiedRegisterForm()

    return render(
        request,
        'core/register.html',
        {
            'form': form,
            'role': selected_role,
            'hide_nav': True
        }
    )


def login_doctor(request):
    return login_view(request, role='doctor')


def login_patient(request):
    return login_view(request, role='patient')


def login_therapist(request):
    return login_view(request, role='therapist')


# 🔹 Login View – role-aware
def login_view(request, role=None):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            if user.role == 'patient':
                return redirect('patient_home')
            elif user.role == 'doctor':
                return redirect('doctor_profile')
            elif user.role == 'therapist':
                return redirect('therapist_profile')
    else:
        form = AuthenticationForm()

    return render(request, 'core/login.html', {'form': form, 'role': role})

# -------------------------------------------------------------------
#  PATIENT HOME & TASKS
# -------------------------------------------------------------------

@login_required
def patient_home(request):
    if request.user.role != 'patient':
        messages.error(request, "Access denied.")
        return redirect('login')

    active_task = PatientTask.objects.filter(
        patient=request.user,
        status='in_progress'
    ).first()

    task_form = PatientTaskForm(request.POST or None)
    appointment_form = AppointmentForm()
    latest_appointment = Appointment.objects.filter(
        patient=request.user
    ).order_by('-created_at').first()

    if request.method == 'POST':
        if 'task_type' in request.POST:
            # Task submit
            task_form = PatientTaskForm(request.POST)
            if task_form.is_valid():
                task = task_form.save(commit=False)
                task.patient = request.user
                task.status = 'in_progress'
                task.started_at = timezone.now()
                task.task_name = dict(PatientTask.TASK_TYPE_CHOICES).get(task.task_type, "Unknown Task")
                task.save()
                messages.success(request, "Task started successfully.")
                return redirect('patient_home')
        else:
            # Appointment submit
            appointment_form = AppointmentForm(request.POST)
            if appointment_form.is_valid():
                appointment = appointment_form.save(commit=False)
                appointment.patient = request.user
                appointment.status = 'pending'
                appointment.save()
                messages.success(request, "Appointment request submitted.")
                return redirect('patient_home')

    return render(request, 'core/patient_home.html', {
        'user': request.user,
        'form': task_form,
        'appointment_form': appointment_form,
        'active_task': active_task,
        'latest_appointment': latest_appointment,
        'now': timezone.now()
    })


@login_required
def start_task(request):
    if request.user.role != 'patient':
        return redirect('login')

    if request.method == 'POST':
        form = PatientTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.patient = request.user
            task.started_at = timezone.now()
            task.status = 'in_progress'
            task.task_name = dict(PatientTask.TASK_TYPE_CHOICES).get(task.task_type, "Unknown Task")
            task.save()
            messages.success(request, f"Task '{task.task_name}' started.")
            return redirect('patient_home')
    else:
        form = PatientTaskForm()

    active_task = PatientTask.objects.filter(
        patient=request.user,
        status='in_progress'
    ).first()
    return render(request, 'core/patient_home.html', {
        'form': form,
        'active_task': active_task,
        'now': timezone.now()
    })


@login_required
def complete_task(request, task_id):
    if request.user.role != 'patient':
        messages.error(request, "Access denied.")
        return redirect('login')

    task = get_object_or_404(PatientTask, id=task_id, patient=request.user)

    if task.status == 'in_progress':
        now = timezone.now()

        if task.started_at:
            duration = (now - task.started_at).total_seconds() / 60
            task.duration_minutes = max(1, round(duration))
        else:
            task.duration_minutes = 1

        task.completed_at = now
        task.status = 'completed'
        task.save()

        messages.success(
            request,
            f"Task '{task.task_name}' completed in {task.duration_minutes} minutes."
        )
    else:
        messages.warning(request, "Task is not currently in progress or already completed.")

    return redirect('patient_home')

# -------------------------------------------------------------------
#  PATIENT PROFILE
# -------------------------------------------------------------------

@login_required
def patient_profile(request):
    if request.user.role != 'patient':
        messages.error(request, "Access denied.")
        return redirect('login')

    user = request.user

    if request.method == 'POST':
        form = PatientForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Profile updated successfully.")
    else:
        form = PatientForm(instance=user)

    age = calculate_age(user.date_of_birth) if user.date_of_birth else None

    tasks = PatientTask.objects.filter(
        patient=user,
        completed_at__isnull=False
    ).order_by('-completed_at')

    mood_logs = MoodLog.objects.filter(patient=user)

    scores = ImprovementScore.objects.filter(patient=user)
    avg_score = scores.aggregate(avg=Avg('score'))['avg'] or 0
    avg_score = round(avg_score, 2)

    progress_data = {
        'task_count': tasks.count(),
        'mood_summary': list(mood_logs),
        'avg_score': avg_score,
        'ai_summary': "You're making steady progress this week!"
    }

    mood_color = "#2196f3"
    if mood_logs.exists():
        latest_mood = mood_logs.latest('logged_at').mood
        mood_color_map = {
            "happy": "#4caf50",
            "neutral": "#9e9e9e",
            "sad": "#2196f3",
            "anxious": "#ff5722",
            "excited": "#ffeb3b",
            "tired": "#795548"
        }
        mood_color = mood_color_map.get(latest_mood, "#2196f3")

    return render(request, 'core/patient_profile.html', {
        'form': form,
        'age': age,
        'tasks': tasks,
        'progress_data': progress_data,
        'mood_color': mood_color,
        'unique_id': user.unique_id,
    })

# -------------------------------------------------------------------
#  DOCTOR & THERAPIST PROFILES
# -------------------------------------------------------------------

@login_required
def doctor_profile(request):
    if request.user.role != 'doctor':
        messages.error(request, "Access denied.")
        return redirect('login')

    if request.method == 'POST':
        form = DoctorProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('doctor_profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = DoctorProfileForm(instance=request.user)

    return render(request, 'core/doctor_profile.html', {
        'form': form,
        'user': request.user,
    })


@login_required
def therapist_profile(request):
    if request.user.role != 'therapist':
        messages.error(request, "Access denied.")
        return redirect('login')

    if request.method == 'POST':
        form = DoctorProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data.get('delete_photo') and user.profile_photo:
                user.profile_photo.delete(save=False)
                user.profile_photo = None
            user.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('therapist_profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = DoctorProfileForm(instance=request.user)

    return render(request, 'core/therapist_profile.html', {'form': form})


@login_required
def delete_profile_photo(request):
    user = request.user

    if user.profile_photo:
        user.profile_photo.delete(save=False)
        user.profile_photo = None
        user.save()
        messages.success(request, "Profile photo deleted successfully.")
    else:
        messages.info(request, "No profile photo to delete.")

    if user.role == 'patient':
        return redirect('patient_profile')
    elif user.role == 'doctor':
        return redirect('doctor_profile')
    elif user.role == 'therapist':
        return redirect('therapist_profile')
    else:
        messages.error(request, "Unknown role. Redirecting to login.")
        return redirect('login')

# -------------------------------------------------------------------
#  LOOKUP & VIEW PATIENT PROFILE (DOCTOR / THERAPIST)
# -------------------------------------------------------------------

@login_required
def lookup_patient(request):
    if request.user.role not in ['doctor', 'therapist']:
        messages.error(request, "Access denied.")
        return redirect('login')

    form = PatientLookupForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            patient_id = form.cleaned_data['patient_id']
            return redirect('view_patient_profile', unique_id=patient_id)
        else:
            messages.error(request, "Invalid input. Please enter a valid Patient ID.")

    return render(request, 'core/lookup_patient.html', {'form': form})


@login_required
def view_patient_profile(request, unique_id):
    if request.user.role not in ['doctor', 'therapist']:
        messages.error(request, "Access denied.")
        return redirect('login')

    patient = get_object_or_404(User, unique_id=unique_id, role='patient')
    tasks = PatientTask.objects.filter(patient=patient).order_by('-completed_at')
    visits = PatientVisit.objects.filter(patient=patient).order_by('-visit_date')
    visit_records = VisitRecord.objects.filter(patient=patient).order_by('visit_date')

    notes_forms = {visit.id: TherapistNotesForm(instance=visit) for visit in visits}

    completed_tasks = tasks.filter(status='completed')
    task_stats = completed_tasks.aggregate(
        total=Count('id'),
        avg_duration=Avg('duration_minutes'),
        last_completed=Max('completed_at')
    )

    long_tasks = tasks.filter(
        status='in_progress',
        started_at__lt=timezone.now() - timedelta(minutes=60)
    )

    missed_tasks = tasks.filter(
        status='pending',
        started_at__isnull=True
    )

    chart_dates = [v.visit_date.strftime('%d %b') for v in visit_records]
    chart_scores = [v.improvement_score for v in visit_records]

    return render(request, 'core/view_patient_profile.html', {
        'patient': patient,
        'tasks': tasks,
        'visits': visits,
        'visit_records': visit_records,
        'notes_forms': notes_forms,
        'task_stats': task_stats,
        'long_tasks': long_tasks,
        'missed_tasks': missed_tasks,
        'chart_dates': chart_dates,
        'chart_scores': chart_scores,
    })

# -------------------------------------------------------------------
#  VISITS & HEALTH LOGS
# -------------------------------------------------------------------

@login_required
def visit_details(request):
    if request.user.role == 'therapist':
        visits = PatientVisit.objects.all()
    else:
        visits = PatientVisit.objects.filter(patient=request.user)

    form = PatientVisitForm()
    if request.method == 'POST' and request.user.role == 'patient':
        form = PatientVisitForm(request.POST, request.FILES)
        if form.is_valid():
            visit = form.save(commit=False)
            visit.patient = request.user
            visit.save()
            messages.success(request, "Visit details submitted.")
            return redirect('visit_details')

    return render(request, 'core/details.html', {'form': form, 'visits': visits})


@login_required
def submit_health_log(request):
    if request.user.role != 'patient':
        messages.error(request, "Access denied.")
        return redirect('login')

    form = HealthLogForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        log = form.save(commit=False)
        log.patient = request.user
        log.save()
        messages.success(request, "Health log submitted.")
        return redirect('submit_health_log')

    logs = HealthLog.objects.filter(patient=request.user).order_by('-date')
    return render(request, 'core/submit_health_log.html', {'form': form, 'logs': logs})

# -------------------------------------------------------------------
#  THERAPIST DASHBOARD + FEEDBACK + NOTES
# -------------------------------------------------------------------

@login_required
def therapist_dashboard(request):
    if request.user.role != 'therapist':
        messages.error(request, "Access denied.")
        return redirect('login')

    patients = User.objects.filter(role='patient')

   

    active_sos_alerts = SOSAlert.objects.filter(status='active').order_by('-created_at')
    acknowledged_sos_alerts = SOSAlert.objects.filter(
        status='acknowledged'
    ).order_by('-created_at')[:10]

    therapist_videos = ExerciseVideo.objects.filter(
        therapist=request.user
    ).order_by('-created_at')[:8]

    return render(request, 'core/therapist_dashboard.html', {
        'patients': patients,
        'active_sos_alerts': active_sos_alerts,
        'acknowledged_sos_alerts': acknowledged_sos_alerts,
       
        'therapist_videos': therapist_videos,
    })


@login_required
def add_feedback(request, task_id):
    if request.user.role != 'therapist':
        messages.error(request, "Access denied.")
        return redirect('login')

    task = get_object_or_404(PatientTask, id=task_id)
    form = TherapistFeedbackForm(request.POST or None, instance=task)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Feedback added successfully.")
        return redirect('view_patient_profile', unique_id=task.patient.unique_id)

    return render(request, 'core/add_feedback.html', {'form': form, 'task': task})


@login_required
def add_therapist_notes_inline(request, visit_id):
    if request.user.role != 'therapist':
        messages.error(request, "Access denied.")
        return redirect('login')

    visit = get_object_or_404(PatientVisit, id=visit_id)
    form = TherapistNotesForm(request.POST, instance=visit)

    if form.is_valid():
        form.save()
        messages.success(request, "Therapist notes updated.")
    else:
        messages.error(request, "Failed to update notes.")

    return redirect('view_patient_profile', unique_id=visit.patient.unique_id)

# -------------------------------------------------------------------
#  DOCTOR DASHBOARD / APPOINTMENTS / VISITS
# -------------------------------------------------------------------

@login_required
def doctor_dashboard(request):
    if request.user.role != 'doctor':
        messages.error(request, "Access denied.")
        return redirect('login')

    lookup_form = PatientLookupForm()
    if request.method == 'POST':
        lookup_form = PatientLookupForm(request.POST)
        if lookup_form.is_valid():
            patient_id = lookup_form.cleaned_data['patient_id']
            # You may have a patient_detail view; otherwise keep view_patient_profile
            return redirect('view_patient_profile', unique_id=patient_id)

    pending_appointments = Appointment.objects.filter(
        doctor=request.user,
        status='pending'
    ).order_by('date', 'time')

    confirmed_appointments = Appointment.objects.filter(
        doctor=request.user,
        status='confirmed'
    ).order_by('date', 'time')

    cancelled_appointments = Appointment.objects.filter(
        doctor=request.user,
        status='cancelled'
    ).order_by('date', 'time')

    completed_appointments = Appointment.objects.filter(
        doctor=request.user,
        status='completed'
    ).order_by('-date', '-time')

    # Upcoming appointments for next 2 days (doctor specific)
    today = timezone.localdate()
    in_two_days = today + timedelta(days=2)

    upcoming_appointments_doctor = Appointment.objects.filter(
        doctor=request.user,
        date__range=[today, in_two_days],
        status__in=['pending', 'confirmed']
    ).order_by('date', 'time')

    recent_visits = PatientVisit.objects.filter(
        doctor=request.user
    ).order_by('-visit_date')[:10]

    visit_records = VisitRecord.objects.filter(
        doctor=request.user
    ).order_by('-visit_date')

    active_sos_alerts = SOSAlert.objects.filter(status='active').order_by('-created_at')
    acknowledged_sos_alerts = SOSAlert.objects.filter(
        status='acknowledged'
    ).order_by('-created_at')[:10]

    return render(request, 'core/doctor_dashboard.html', {
        'user': request.user,
        'lookup_form': lookup_form,
        'pending_appointments': pending_appointments,
        'confirmed_appointments': confirmed_appointments,
        'cancelled_appointments': cancelled_appointments,
        'completed_appointments': completed_appointments,
        'recent_visits': recent_visits,
        'visit_records': visit_records,
        'active_sos_alerts': active_sos_alerts,
        'acknowledged_sos_alerts': acknowledged_sos_alerts,
        'upcoming_appointments_doctor': upcoming_appointments_doctor,
    })


@login_required
def doctor_sos_center(request):
    if request.user.role != 'doctor':
        messages.error(request, "Access denied.")
        return redirect('login')

    alerts = SOSAlert.objects.select_related('patient')
    active_alerts = alerts.filter(status='active')
    acknowledged_alerts = alerts.filter(status='acknowledged')
    recent_resolved_alerts = alerts.filter(status='resolved').order_by('-resolved_at')[:15]

    total_alerts = alerts.count()
    responded_alerts = acknowledged_alerts.count() + recent_resolved_alerts.count()
    stats = {
        'active_count': active_alerts.count(),
        'acknowledged_count': acknowledged_alerts.count(),
        'resolved_this_week': alerts.filter(
            status='resolved',
            resolved_at__gte=timezone.now() - timedelta(days=7)
        ).count(),
        'response_rate': round((responded_alerts / total_alerts) * 100, 1) if total_alerts else 0,
        'latest_alert': alerts.order_by('-created_at').first(),
    }

    return render(request, 'core/doctor_sos_center.html', {
        'active_alerts': active_alerts,
        'acknowledged_alerts': acknowledged_alerts,
        'recent_resolved_alerts': recent_resolved_alerts,
        'stats': stats,
    })


@login_required
def confirm_appointment(request, appointment_id):
    if request.user.role != 'doctor':
        messages.error(request, "Access denied.")
        return redirect('doctor_dashboard')

    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user)

    if appointment.status == 'pending':
        appointment.status = 'confirmed'
        appointment.save()
        messages.success(
            request,
            f"Appointment with {appointment.patient.get_full_name()} confirmed."
        )
    else:
        messages.warning(request, "This appointment is not pending or has already been processed.")

    return redirect('doctor_dashboard')


@login_required
def cancel_appointment(request, appointment_id):
    if request.user.role != 'doctor':
        messages.error(request, "Access denied.")
        return redirect('doctor_dashboard')

    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user)
    appointment.status = 'cancelled'
    appointment.save()
    messages.warning(request, "Appointment cancelled.")
    return redirect('doctor_dashboard')


@login_required
def log_visit_by_id(request, appointment_id):
    if request.user.role != 'doctor':
        messages.error(request, "Access denied.")
        return redirect('doctor_dashboard')

    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user)

    visit_exists = VisitRecord.objects.filter(
        doctor=request.user,
        patient=appointment.patient,
        visit_date=appointment.date
    ).exists()

    if visit_exists:
        messages.warning(request, "Visit already logged for this appointment.")
        return redirect('doctor_dashboard')

    VisitRecord.objects.create(
        doctor=request.user,
        patient=appointment.patient,
        visit_date=appointment.date,
        hospital_name=appointment.hospital.name if appointment.hospital else "",
        doctor_name=request.user.get_full_name(),
        current_status='pending',
        improvement_score=0,
        doctor_notes='Visit logged. Awaiting update.'
    )

    appointment.status = 'completed'
    appointment.save()

    messages.success(
        request,
        f"Visit for {appointment.patient.get_full_name()} recorded successfully. Appointment marked as completed."
    )

    return redirect('doctor_dashboard')


@login_required
def update_visit_record(request, visit_id):
    visit = get_object_or_404(VisitRecord, id=visit_id, doctor=request.user)

    if request.method == 'POST':
        form = VisitUpdateForm(request.POST, instance=visit)
        if form.is_valid():
            form.save()
            messages.success(request, f"Visit for {visit.patient.get_full_name()} updated successfully.")
            return redirect('doctor_dashboard')
        else:
            messages.error(request, "There was an error updating the visit. Please check the form.")
    else:
        form = VisitUpdateForm(instance=visit)

    return render(request, 'core/update_visit.html', {
        'form': form,
        'visit': visit
    })


def patient_progress_chart(request, patient_id):
    visits = VisitRecord.objects.filter(patient_id=patient_id).order_by('visit_date')
    dates = [v.visit_date.strftime('%d %b') for v in visits]
    scores = [v.improvement_score for v in visits]
    return render(request, 'core/progress_chart.html', {
        'dates': dates,
        'scores': scores,
        'patient': visits[0].patient if visits else None
    })

# -------------------------------------------------------------------
#  APPOINTMENT BOOKING (PATIENT)
# -------------------------------------------------------------------

@login_required
def book_appointment(request):
    if request.user.role != 'patient':
        messages.error(request, "Access denied.")
        return redirect('login')
    hospitals = Hospital.objects.all()

    if request.method == 'POST':
        

        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.status = 'pending'
            appointment.save()
            messages.success(request, "Appointment request submitted.")
            return redirect('patient_home')
    else:
        form = AppointmentForm()

    return render(request, 'core/book_appointment.html', {
    'form': form,
    'hospitals': hospitals
})

# -------------------------------------------------------------------
#  HOSPITAL AJAX
# -------------------------------------------------------------------

def load_hospitals(request):
    location_id = request.GET.get('location')
    hospitals = Hospital.objects.filter(location_id=location_id).values('id', 'name')
    return JsonResponse(list(hospitals), safe=False)

# -------------------------------------------------------------------
#  MOOD LOGGING
# -------------------------------------------------------------------

@login_required
def log_mood(request):
    if request.method == 'POST':
        mood = request.POST.get('mood')
        if mood:
            MoodLog.objects.create(patient=request.user, mood=mood)
    return redirect('patient_profile')

# -------------------------------------------------------------------
#  MESSAGING SYSTEM
# -------------------------------------------------------------------

@login_required
def message_box(request):
    role = request.GET.get('role')
    selected_user_id = request.GET.get('user')

    users = User.objects.filter(role=role).exclude(id=request.user.id) if role else []

    selected_user = User.objects.filter(id=selected_user_id).first()

    messages_qs = []
    if selected_user:
        messages_qs = Message.objects.filter(
            sender__in=[request.user, selected_user],
            receiver__in=[request.user, selected_user],
            is_deleted=False
        ).order_by('timestamp')

    return render(request, 'core/message_box.html', {
        'roles': ['doctor', 'therapist', 'patient'],
        'selected_role': role,
        'users': users,
        'selected_user': selected_user,
        'messages': messages_qs
    })


@login_required
def send_message(request):
    if request.method == 'POST':
        receiver_id = request.POST.get('receiver_id')
        content = request.POST.get('content')
        receiver = get_object_or_404(User, id=receiver_id)
        if content:
            Message.objects.create(sender=request.user, receiver=receiver, content=content)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})


@login_required
def delete_message(request, message_id):
    message_obj = get_object_or_404(Message, id=message_id, sender=request.user)
    message_obj.is_deleted = True
    message_obj.save()
    return JsonResponse({'status': 'deleted'})

# -------------------------------------------------------------------
#  EMERGENCY SOS SYSTEM
# -------------------------------------------------------------------

@login_required
def send_sos_alert(request):
    if request.user.role != 'patient':
        messages.error(request, "Access denied.")
        return redirect('login')

    if request.method == 'POST':
        message_text = request.POST.get('message')
        if message_text:
            SOSAlert.objects.create(
                patient=request.user,
                message=message_text,
                status='active'
            )
            messages.success(request, "🚨 Emergency SOS alert sent to all doctors and therapists!")
            return redirect('patient_home')

    return render(request, 'core/sos_alert.html')


@login_required
def acknowledge_sos_alert(request, alert_id):
    if request.user.role not in ['doctor', 'therapist']:
        messages.error(request, "Access denied.")
        return redirect('login')

    sos_alert = get_object_or_404(SOSAlert, id=alert_id)

    if request.user.role == 'doctor':
        sos_alert.acknowledged_by_doctor = True
    elif request.user.role == 'therapist':
        sos_alert.acknowledged_by_therapist = True

    if sos_alert.acknowledged_by_doctor and sos_alert.acknowledged_by_therapist:
        sos_alert.status = 'acknowledged'
        sos_alert.acknowledged_at = timezone.now()
    elif not sos_alert.acknowledged_at:
        sos_alert.acknowledged_at = timezone.now()

    sos_alert.save()

    messages.success(request, f"SOS alert from {sos_alert.patient.get_full_name()} acknowledged.")

    if request.user.role == 'doctor':
        return redirect('doctor_dashboard')
    else:
        return redirect('therapist_dashboard')


@login_required
def resolve_sos_alert(request, alert_id):
    if request.user.role not in ['doctor', 'therapist']:
        messages.error(request, "Access denied.")
        return redirect('login')

    sos_alert = get_object_or_404(SOSAlert, id=alert_id)
    sos_alert.status = 'resolved'
    sos_alert.resolved_at = timezone.now()
    sos_alert.save()

    messages.success(request, f"SOS alert from {sos_alert.patient.get_full_name()} resolved.")

    if request.user.role == 'doctor':
        return redirect('doctor_dashboard')
    else:
        return redirect('therapist_dashboard')


@login_required
def emergency_alerts_page(request):
    if request.user.role != 'therapist':
        messages.error(request, "Access denied.")
        return redirect('login')

    active_sos_alerts = SOSAlert.objects.filter(status='active')
    acknowledged_sos_alerts = SOSAlert.objects.filter(status='acknowledged')

    return render(request, 'core/emergency_alerts_page.html', {
        'active_sos_alerts': active_sos_alerts,
        'acknowledged_sos_alerts': acknowledged_sos_alerts,
    })

# -------------------------------------------------------------------
#  EXERCISE VIDEO SYSTEM
# -------------------------------------------------------------------

@login_required
def upload_exercise_video(request):
    if request.user.role != 'therapist':
        messages.error(request, "Access denied. Only therapists can upload videos.")
        return redirect('login')

    if request.method == 'POST':
        form = ExerciseVideoForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.save(commit=False)
            video.therapist = request.user
            video.save()
            messages.success(request, f"Video '{video.title}' uploaded successfully!")
            return redirect('therapist_videos')
    else:
        form = ExerciseVideoForm()

    return render(request, 'core/upload_video.html', {'form': form})


@login_required
def therapist_videos(request):
    if request.user.role != 'therapist':
        messages.error(request, "Access denied.")
        return redirect('login')

    videos = ExerciseVideo.objects.filter(therapist=request.user).order_by('-created_at')
    return render(request, 'core/therapist_videos.html', {'videos': videos})


@login_required
def view_exercise_videos(request):
    if request.user.role != 'patient':
        messages.error(request, "Access denied.")
        return redirect('login')

    exercise_type = request.GET.get('exercise_type', '')
    difficulty = request.GET.get('difficulty', '')

    videos = ExerciseVideo.objects.filter(is_active=True)

    if exercise_type:
        videos = videos.filter(exercise_type=exercise_type)
    if difficulty:
        videos = videos.filter(difficulty_level=difficulty)

    videos = videos.order_by('-created_at')

    exercise_types = ExerciseVideo.EXERCISE_TYPE_CHOICES
    difficulty_levels = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    return render(request, 'core/view_videos.html', {
        'videos': videos,
        'exercise_types': exercise_types,
        'difficulty_levels': difficulty_levels,
        'selected_type': exercise_type,
        'selected_difficulty': difficulty,
    })


@login_required
def doctor_exercise_library(request):
    if request.user.role != 'doctor':
        messages.error(request, "Access denied.")
        return redirect('login')

    exercise_type = request.GET.get('exercise_type', '')
    difficulty = request.GET.get('difficulty', '')

    videos = ExerciseVideo.objects.filter(is_active=True).select_related('therapist')

    if exercise_type:
        videos = videos.filter(exercise_type=exercise_type)
    if difficulty:
        videos = videos.filter(difficulty_level=difficulty)

    videos = videos.order_by('-created_at')

    exercise_types = ExerciseVideo.EXERCISE_TYPE_CHOICES
    difficulty_levels = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    total_active_videos = ExerciseVideo.objects.filter(is_active=True).count()
    latest_video = ExerciseVideo.objects.filter(is_active=True).order_by('-created_at').first()
    popular_types_qs = (
        ExerciseVideo.objects.filter(is_active=True)
        .values('exercise_type')
        .annotate(count=Count('id'))
        .order_by('-count')[:4]
    )

    type_label_map = dict(ExerciseVideo.EXERCISE_TYPE_CHOICES)
    popular_types = [
        {
            'value': item['exercise_type'],
            'label': type_label_map.get(item['exercise_type'], item['exercise_type']),
            'count': item['count'],
        }
        for item in popular_types_qs
    ]

    return render(request, 'core/doctor_exercise_library.html', {
        'videos': videos,
        'exercise_types': exercise_types,
        'difficulty_levels': difficulty_levels,
        'selected_type': exercise_type,
        'selected_difficulty': difficulty,
        'total_active_videos': total_active_videos,
        'latest_video': latest_video,
        'popular_types': popular_types,
    })


@login_required
def watch_video(request, video_id):
    if request.user.role not in ['patient', 'doctor', 'therapist']:
        messages.error(request, "Access denied.")
        return redirect('login')

    video = get_object_or_404(ExerciseVideo, id=video_id, is_active=True)

    # Increment view count
    video.increment_views()

    related_videos = ExerciseVideo.objects.filter(
        is_active=True,
        exercise_type=video.exercise_type
    ).exclude(id=video_id).order_by('-created_at')[:5]

    return render(request, 'core/watch_video.html', {
        'video': video,
        'related_videos': related_videos,
    })


@login_required
def delete_video(request, video_id):
    if request.user.role != 'therapist':
        messages.error(request, "Access denied.")
        return redirect('login')

    video = get_object_or_404(ExerciseVideo, id=video_id, therapist=request.user)

    if request.method == 'POST':
        video_title = video.title
        video.video_file.delete(save=False)
        if video.thumbnail:
            video.thumbnail.delete(save=False)
        video.delete()
        messages.success(request, f"Video '{video_title}' deleted successfully.")
        return redirect('therapist_videos')

    return render(request, 'core/delete_video.html', {'video': video})


def exercise_video_library(request):
    videos = ExerciseVideo.objects.all().order_by('-created_at')
    return render(request, 'core/exercise_video_library.html', {'videos': videos})

# -------------------------------------------------------------------
#  APPOINTMENT REMINDER (THERAPIST -> PATIENT)
# -------------------------------------------------------------------

@login_required
def send_appointment_reminder(request, appointment_id):
    """
    Therapist sends a reminder message to the patient
    for a specific appointment (usually 2 days before).
    """
    if request.user.role != 'therapist':
        messages.error(request, "Access denied.")
        return redirect('login')

    appointment = get_object_or_404(Appointment, id=appointment_id)
    patient = appointment.patient

    Message.objects.create(
        sender=request.user,
        receiver=patient,
        content=f"Reminder: Your appointment is scheduled on {appointment.date} at {appointment.time}."
    )

    messages.success(request, f"Reminder sent to {patient.get_full_name()}!")
    return redirect('therapist_dashboard')