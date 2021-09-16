from django.urls import path
from .views import CallbackView

app_name = 'app'

urlpatterns = [
    path('callback/', CallbackView.as_view(), name='callback_view'),
]