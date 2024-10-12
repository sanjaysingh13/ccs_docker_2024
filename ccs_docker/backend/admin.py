from django.contrib import admin

from .models import CrimeNewsSheet
from .models import DailyArrest


@admin.register(CrimeNewsSheet)
class CrimeNewsSheetAdmin(admin.ModelAdmin):
    fields = ("cns", "cns_date")


@admin.register(DailyArrest)
class DailyArrestAdmin(admin.ModelAdmin):
    fields = ("cns", "da_date")


# admin.site.register(District)
# admin.site.register(PoliceStation)
