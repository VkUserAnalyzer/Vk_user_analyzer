from django.db import models


class VkProfile(models.Model):
  modified = models.DateTimeField(auto_now=True)
  vk_id = models.CharField(max_length=30)


class Band(models.Model):
  user = models.ForeignKey(VkProfile, related_name='bands', on_delete=models.CASCADE, null=True, blank=True)
  band_name = models.CharField(max_length=128)


class Song(models.Model):
  band = models.ForeignKey(Band, related_name='songs', on_delete=models.CASCADE, null=True, blank=True)
  song_name = models.CharField(max_length=128)
