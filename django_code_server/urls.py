"""
URL configuration for django_code_server project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from django_code_server import swagger

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/swagger')),
    path('swagger', swagger.schema_view.with_ui('swagger', cache_timeout=0)),
    path('docs', swagger.schema_view.with_ui('redoc', cache_timeout=0)),
    path('', include('docker_swarm.urls')),
]
