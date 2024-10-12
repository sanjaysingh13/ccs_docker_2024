from dateutil.parser import parse
from django.db import models
from django.urls import reverse
from model_utils.models import TimeStampedModel

from ccs_docker.backend.models import District
from ccs_docker.backend.models import PoliceStation


class AdvancedCrimeSearchChart(TimeStampedModel):
    created_at = models.DateTimeField(auto_now_add=True)
    keywords = models.CharField(max_length=100, blank=True, default="")
    full_text_search_type = models.IntegerField(default=0)
    tags = models.CharField(max_length=100, blank=True, default="")
    search_any_tags = models.BooleanField(default=False)
    ps_list = models.CharField(max_length=500, blank=True, default="")
    districts = models.CharField(max_length=200, blank=True, default="")
    min_date = models.CharField(max_length=10, blank=True, default="")
    max_date = models.CharField(max_length=10, blank=True, default="")

    def get_absolute_url(self):
        return reverse("charts:crime_search_chart", kwargs={"pk": self.pk})

    def __str__(self):
        description = ""
        if self.keywords:
            description = f"Keywords : {self.keywords}"
        if self.tags:
            description = description + "\n" + f"Tags : {self.tags}"
        if self.ps_list:
            pss = [
                PoliceStation.nodes.get(uuid=uuid).name
                for uuid in list(filter(None, self.ps_list.split(",")))
            ]
            description = description + "\n" + f"PSs : {','.join(pss)}"
        if self.districts != "Null":
            description = (
                description
                + "\n"
                + f"District : {District.nodes.get(uuid=self.districts).name}"
            )
        if self.min_date:
            description = (
                description
                + "\n"
                + f"From : {parse(self.min_date).strftime('%d,%b,%Y')}"
            )
        if self.max_date:
            description = (
                description + "\n" + f"To : {parse(self.max_date).strftime('%d,%b,%Y')}"
            )
        return description


class AdvancedCriminalSearchChart(TimeStampedModel):
    created_at = models.DateTimeField(auto_now_add=True)
    keywords = models.CharField(max_length=100, blank=True, default="")
    full_text_search_type = models.IntegerField(default=0)
    tags = models.CharField(max_length=100, blank=True, default="")
    search_any_tags = models.BooleanField(default=False)
    ps_list = models.CharField(max_length=500, blank=True, default="")
    districts = models.CharField(max_length=200, blank=True, default="")
    min_date = models.CharField(max_length=10, blank=True, default="")
    max_date = models.CharField(max_length=10, blank=True, default="")
    first_name = models.CharField(max_length=50, blank=True, default="")
    last_name = models.CharField(max_length=50, blank=True, default="")
    guardian_first_name = models.CharField(max_length=50, blank=True, default="")
    aliases = models.CharField(max_length=50, blank=True, default="")
    exact_name_search = models.BooleanField(default=False)
    address = models.CharField(max_length=50, blank=True, default="")
    id_mark = models.CharField(max_length=50, blank=True, default="")

    def get_absolute_url(self):
        return reverse("charts:criminal_search_chart", kwargs={"pk": self.pk})

    def __str__(self):
        description = ""
        if self.keywords:
            description = f"Keywords : {self.keywords}"
        if self.tags:
            description = description + "\n" + f"Tags : {self.tags}"
        if self.ps_list:
            pss = [
                PoliceStation.nodes.get(uuid=uuid).name
                for uuid in list(filter(None, self.ps_list.split(",")))
            ]
            description = description + "\n" + f"PSs : {','.join(pss)}"
        if self.districts != "Null":
            description = (
                description
                + "\n"
                + f"District : {District.nodes.get(uuid=self.districts).name}"
            )
        if self.min_date:
            description = (
                description
                + "\n"
                + f"From : {parse(self.min_date).strftime('%d,%b,%Y')}"
            )
        if self.max_date:
            description = (
                description + "\n" + f"To : {parse(self.max_date).strftime('%d,%b,%Y')}"
            )
        return description
