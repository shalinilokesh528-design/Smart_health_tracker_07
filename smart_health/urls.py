from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 🔹 Admin Panel
    path('admin/', admin.site.urls),

    # 🔹 Core App Routes
    path('', include('core.urls')),
]

# 🔹 Serve media files during development (e.g., profile photos)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
