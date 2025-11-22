from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    # 🔹 Root redirect to register
    path('', views.root_redirect, name='root'),
    
    # 🔹 Registration and Login
    path('register/', views.unified_register, name='register'),
    path('login/', views.login_view, name='login'),
    path('login/doctor/', views.login_doctor, name='login_doctor'),
    path('login/patient/', views.login_patient, name='login_patient'),
    path('login/therapist/', views.login_therapist, name='login_therapist'),

    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # 🔹 Role-Based Profiles
    path('profile/patient/', views.patient_profile, name='patient_profile'),
    path('profile/patient/delete-photo/', views.delete_profile_photo, name='delete_profile_photo'),
    path('profile/doctor/', views.doctor_profile, name='doctor_profile'),
    path('profile/therapist/', views.therapist_profile, name='therapist_profile'),

    # 🔹 Dashboards
    path('home/', views.patient_home, name='patient_home'),
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/sos-center/', views.doctor_sos_center, name='doctor_sos_center'),
    path('doctor/videos/', views.doctor_exercise_library, name='doctor_exercise_library'),
    path('therapist/dashboard/', views.therapist_dashboard, name='therapist_dashboard'),

    # 🔹 Therapist sends appointment reminder to patient
    path(
        'therapist/appointment-reminder/<int:appointment_id>/',
        views.send_appointment_reminder,
        name='send_appointment_reminder'
    ),

    # 🔹 Visit and Health Log
    path('details/', views.visit_details, name='visit_details'),
    path('submit-log/', views.submit_health_log, name='submit_health_log'),

    # 🔹 Visit Actions
    path('doctor/log_visit/<int:appointment_id>/', views.log_visit_by_id, name='log_visit_by_id'),
    path('visit/update/<int:visit_id>/', views.update_visit_record, name='update_visit_record'),

    # 🔹 Patient Lookup and Profile View
    path('lookup/', views.lookup_patient, name='lookup_patient'),
    path('patient/<str:unique_id>/', views.view_patient_profile, name='view_patient_profile'),
    path('progress-chart/<int:patient_id>/', views.patient_progress_chart, name='patient_progress_chart'),

    # 🔹 Therapist Actions
    path('feedback/<int:task_id>/', views.add_feedback, name='add_feedback'),
    path('visit/notes/inline/<int:visit_id>/', views.add_therapist_notes_inline, name='add_therapist_notes_inline'),

    # 🔹 Task Management
    path('task/start/', views.start_task, name='start_task'),
    path('task/complete/<int:task_id>/', views.complete_task, name='complete_task'),

    # 🔹 Appointment System (doctor side)
    path('appointment/confirm/<int:appointment_id>/', views.confirm_appointment, name='confirm_appointment'),
    path('appointment/cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),

    # 🔹 Hospital AJAX
    path('ajax/load-hospitals/', views.load_hospitals, name='ajax_load_hospitals'),

    # 🔹 Mood Logging
    path('log-mood/', views.log_mood, name='log_mood'),

    # 🔹 Messaging System
    path('messages/', views.message_box, name='message_box'),
    path('send-message/', views.send_message, name='send_message'),
    path('delete-message/<int:message_id>/', views.delete_message, name='delete_message'),

    # 🔹 Emergency SOS System
    path('sos/send/', views.send_sos_alert, name='send_sos_alert'),
    path('sos/acknowledge/<int:alert_id>/', views.acknowledge_sos_alert, name='acknowledge_sos_alert'),
    path('sos/resolve/<int:alert_id>/', views.resolve_sos_alert, name='resolve_sos_alert'),

    # 🔹 Exercise Video System
    path('videos/upload/', views.upload_exercise_video, name='upload_exercise_video'),
    path('videos/therapist/', views.therapist_videos, name='therapist_videos'),
    path('videos/', views.view_exercise_videos, name='view_exercise_videos'),
    path('videos/watch/<int:video_id>/', views.watch_video, name='watch_video'),
    path('videos/delete/<int:video_id>/', views.delete_video, name='delete_video'),

    # 🔹 Therapist tools
    path('therapist/videos/', views.exercise_video_library, name='exercise_video_library'),
    path('therapist/alerts/', views.emergency_alerts_page, name='emergency_alerts_page'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
