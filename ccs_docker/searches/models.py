from django.db import models
from django.urls import reverse


class TimeStampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AdvancedCrimeSearch(TimeStampedModel):
    keywords = models.CharField(max_length=250, blank=True, default="")
    full_text_search_type = models.IntegerField(default=0)
    tags = models.CharField(max_length=250, blank=True, default="")
    search_any_tags = models.BooleanField(default=False)
    districts = models.CharField(max_length=250, blank=True, default="")
    ps_list = models.CharField(max_length=250, blank=True, default="")
    min_date = models.CharField(max_length=10, blank=True, default="")
    max_date = models.CharField(max_length=10, blank=True, default="")

    def get_absolute_url(self):
        return reverse("searches:advanced_crime_search", kwargs={"pk": self.pk})


class AdvancedCriminalSearch(models.Model):
    keywords = models.CharField(max_length=250, blank=True, default="")
    full_text_search_type = models.IntegerField(default=0)
    tags = models.CharField(max_length=250, blank=True, default="")
    search_any_tags = models.BooleanField(default=False)
    districts = models.CharField(max_length=250, blank=True, default="")
    ps_list = models.CharField(max_length=250, blank=True, default="")
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
        return reverse("searches:criminal_search_results", kwargs={"pk": self.pk})

    def __str__(self):
        return f"Criminal Search {self.id}"
