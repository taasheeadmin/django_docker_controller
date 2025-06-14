# Django Imports
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.permissions import AllowAny

schema_view = get_schema_view(
   openapi.Info(
      title="Docker Controller",
      default_version='v1',
      description="Here are the list of API's Used",
      contact=openapi.Contact(email="manikanta.a@taashee.com, adithya.k@taashee.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(AllowAny,),
   authentication_classes=[],
)

swagger_view = schema_view.with_ui('swagger', cache_timeout=0)
