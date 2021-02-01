from django.urls import path
from rango import views

app_name = 'rango'

urlpatterns = [
path('', views.index, name='index'),
path('about/', views.about, name='about'),
#path('string to react to', 'view to call', 'name to reference the view by')
    ]


#git add *
#git commit -m "commit x"
#git push
