import itertools
from difflib import SequenceMatcher

from django.core.management.base import BaseCommand

from ccs_docker.backend.models import Crime


class Command(BaseCommand):
    help = "Make criminal dups"

    def handle(self, *args, **options):
        try:
            # ps_uuids = [ps.uuid for ps in PoliceStation.nodes.all()]
            # chosen_ps = random.sample(ps_uuids, 100)
            # # add important tags to prioritize
            # query ="""
            # MATCH (crime:Crime)-[:BELONGS_TO_PS]-(ps:PoliceStation)
            # WHERE ps.uuid IN $chosen_ps
            # RETURN crime
            # """
            # results,meta = db.cypher_query(query,params={"chosen_ps":chosen_ps})
            # crimes = [Crime.inflate(row[0]) for row in results]
            crimes = Crime.nodes.all()

            # crimes = Crime.nodes.all(lazy=True)
            counter = 0
            self.stdout.write(self.style.SUCCESS(f"counter is {counter}"))
            j = 0
            for crime in crimes:
                j = j + 1
                criminals = crime.criminals.all()
                for a, b in itertools.combinations(criminals, 2):
                    a_name = (a.first_name if a.first_name else "") + (
                        a.last_name if a.last_name else ""
                    )
                    b_name = (b.first_name if b.first_name else "") + (
                        b.last_name if b.last_name else ""
                    )

                    if SequenceMatcher(None, a_name, b_name).ratio() > 8:
                        # likely hit
                        a_addreses = [address.name for address in a.addresses.all()]
                        b_addreses = [address.name for address in b.addresses.all()]
                        for a_address, b_address in list(
                            itertools.product(a_addreses, b_addreses),
                        ):
                            if SequenceMatcher(None, a_address, b_address).ratio() > 7:
                                self.stdout.write(self.style.SUCCESS(str(a)))
                                self.stdout.write(self.style.SUCCESS(str(b)))
                                if not a.similar_criminal.connect(b):
                                    a.similar_criminal.connect(b)
                                    counter = counter + 1
                                    break
                    if (counter == 500) or (j == 200000):
                        break
                if (counter == 500) or (j == 200000):
                    break
            # matching_criminals = Criminal.nodes.filter(first_name=criminal.first_name,last_name=criminal.last_name)
            # for matching_criminal in  matching_criminals:
            #   if criminal != matching_criminal:
            #       criminal.similar_criminal.connect(matching_criminal)
        except Exception as e:
            self.stdout.write(self.style.SUCCESS(f"failed in making dups {e}"))
            return

        self.stdout.write(self.style.SUCCESS("Successfully duped"))
        self.stdout.write(self.style.SUCCESS(counter))
        self.stdout.write(self.style.SUCCESS(j))
        return
