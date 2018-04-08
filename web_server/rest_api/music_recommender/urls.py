from django.conf.urls import url, include
from .views import VkProfileViewSet, get_recommendation, index_page
from rest_framework import routers


router = routers.DefaultRouter()
router.register(r'save_parsed_data', VkProfileViewSet)

urlpatterns = [
    url(r'^$', index_page, name='music'),
    url(r'', include(router.urls)),
    url(r'get_rec_bands', get_recommendation)
]
