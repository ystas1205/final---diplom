"""
URL configuration for product_service project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from baton.autodiscover import admin
# from django.contrib import admin
from django.urls import path, include, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, \
    SpectacularSwaggerView
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static


# def trigger_error(request):
#     division_by_zero = 1 / 0


# urlpatterns = [
#     path('sentry-debug/', trigger_error),
#     # ...
# ]


urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('baton/', include('baton.urls')),
                  path('api/v1/',
                       include('backend.urls', namespace='backend')),
                  path('auth/',
                       include('rest_framework_social_oauth2.urls',
                               namespace='social')),
                  path("__debug__/", include("debug_toolbar.urls")),

                  path('api/schema/', SpectacularAPIView.as_view(),
                       name='schema'),
                  # Optional UI:
                  path('api/docs/',
                       SpectacularSwaggerView.as_view(url_name='schema'),
                       name='swagger-ui'),
                  path('api/schema/redoc/',
                       SpectacularRedocView.as_view(url_name='schema'),
                       name='redoc'),

                  # path('sentry-debug/', trigger_error),

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "Панель администрирования"
admin.site.index_title = "Сервис заказа товаров для розничных сетей"
