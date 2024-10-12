import csv
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from ccs_docker.users.models import District
from ccs_docker.users.models import PoliceStation


class Command(BaseCommand):
    help = "Import Police Stations and Districts from CSV file"

    def handle(self, *args, **options):
        csv_file_path = Path("staticfiles/CACHE/police_stations_districts.csv")

        with csv_file_path.open() as file:
            csv_reader = csv.DictReader(file)

            with transaction.atomic():
                for row in csv_reader:
                    district, _ = District.objects.get_or_create(
                        name=row["District Name"],
                    )

                    PoliceStation.objects.get_or_create(
                        police_stationId=row["Police Station ID"],
                        defaults={
                            "name": row["Police Station Name"],
                            "ps_with_distt": row["Full Name"],
                            "latitude": float(row["Latitude"])
                            if row["Latitude"]
                            else None,
                            "longitude": float(row["Longitude"])
                            if row["Longitude"]
                            else None,
                            "address": row["Address"],
                            "officer_in_charge": row["Officer in Charge"],
                            "office_telephone": row["Office Telephone"],
                            "telephones": row["Telephones"],
                            "emails": row["Emails"],
                            "district": district,
                        },
                    )

        self.stdout.write(
            self.style.SUCCESS("Successfully imported Police Stations and Districts")
        )
