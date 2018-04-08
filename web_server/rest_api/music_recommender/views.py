from recommedation_client.rpc_client import RpcClient
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from .models import VkProfile, Band, Song
from .serializers import VkProfileSerializer, BandSerializer, SongSerializer
import time


def index_page(request):

    return render(request, 'music_recommender/music_template.html')


@api_view(['GET', 'POST'])
def get_recommendation(request):

  if request.method == 'POST':
    recommender = RpcClient(host='queue', routing_key='rpc_recommendations')
    request_data = JSONParser().parse(request)
    user_id = request_data["user_id"]
    predicted_bands = recommender.call({'user_id': user_id})

    return JsonResponse(predicted_bands, safe=False)


class VkProfileViewSet(viewsets.ModelViewSet):
  queryset = VkProfile.objects.all()
  serializer_class = VkProfileSerializer

  def perform_create(self, serializer):
    user_id = self.request.data['vk_id']
    inst = VkProfile.objects.filter(vk_id=user_id)
    if inst.exists():
      inst.delete()
    serializer.save()
