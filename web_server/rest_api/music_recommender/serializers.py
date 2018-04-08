from rest_framework import serializers
from .models import VkProfile, Band, Song


class SongSerializer(serializers.ModelSerializer):

  class Meta:
    model = Song
    fields = ["song_name"]


class BandSerializer(serializers.ModelSerializer):
  songs = SongSerializer(many=True)

  class Meta:
    model = Band
    fields = ['band_name', 'songs']


class VkProfileSerializer(serializers.ModelSerializer):
  bands = BandSerializer(many=True)

  class Meta:
    model = VkProfile
    fields = ['modified', 'vk_id', 'bands']

  def create(self, validated_data):
    bands_data = validated_data.pop('bands')
    user = VkProfile.objects.create(**validated_data)
    for band_data in bands_data:
      songs_data = band_data.pop('songs')
      band = Band.objects.create(user=user, **band_data)
      for song_data in songs_data:
        Song.objects.create(band=band, **song_data)

    return user

