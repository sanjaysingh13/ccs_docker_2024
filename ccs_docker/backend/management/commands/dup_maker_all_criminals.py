import datetime
from zoneinfo import ZoneInfo

from crime_criminal_search.backend.models import Criminal
from django.core.management.base import BaseCommand
from neomodel import db


class Command(BaseCommand):
    help = "Make criminal dups"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(datetime.datetime.now(tz=ZoneInfo("Asia/Kolkata")))
        )
        criminals = Criminal.nodes.all()
        i = 0
        j = 0
        for criminal in criminals:
            try:
                j = j + 1

                if (
                    isinstance(criminal.first_name, str)
                    and isinstance(criminal.last_name, str)
                    and isinstance(criminal.guardian_first_name, str)
                ):
                    if (
                        criminal.first_name.replace(" ", "") != ""
                        and criminal.last_name.replace(" ", "") != ""
                        and criminal.guardian_first_name.replace(" ", "") != ""
                    ):
                        number_of_words_in_first_name = len(criminal.first_name.split())
                        number_of_words_in_guardian_first_name = len(
                            criminal.guardian_first_name.split(),
                        )
                        query = """
                        CALL {
                              CALL db.index.fulltext.queryNodes('first_name', $first_name)
                                    YIELD node, score
                                      WHERE score>9*$number_of_words_in_first_name

                                    RETURN node, score, 'first_name' as category
                                 UNION ALL
                                CALL db.index.fulltext.queryNodes('last_name', $last_name)
                                    YIELD node, score
                                      WHERE score>9

                                    RETURN node, score, 'last_name' as category
                                    UNION ALL
                                CALL db.index.fulltext.queryNodes('guardian_first_name', $guardian_first_name)
                                    YIELD node, score
                                      WHERE score>9*$number_of_words_in_guardian_first_name

                                    RETURN node, score, 'guardian_first_name' as category

                                 }
                                WITH node, sum(score) AS totalScore, size(collect(DISTINCT category)) as categories
                                WITH node, totalScore, categories
                                WHERE categories = 3
                                RETURN node as criminal, totalScore, 'basic' as search
                                ORDER BY totalScore DESC
                        """
                        results, meta = db.cypher_query(
                            query,
                            params={
                                "first_name": criminal.first_name,
                                "last_name": criminal.last_name,
                                "guardian_first_name": criminal.guardian_first_name,
                                "number_of_words_in_first_name": number_of_words_in_first_name,
                                "number_of_words_in_guardian_first_name": number_of_words_in_guardian_first_name,
                            },
                        )
                        if results != []:
                            matching_criminals = [
                                Criminal.inflate(row[0]) for row in results
                            ][:4]  # selecting only 3 likely matches
                            for matching_criminal in matching_criminals:
                                if matching_criminal != criminal and (
                                    not criminal.similar_criminal.is_connected(
                                        matching_criminal,
                                    )
                                ):
                                    criminal.similar_criminal.connect(matching_criminal)
                                    i = i + 1
                            # if i > 2000:
                            #   self.stdout.write(self.style.SUCCESS(f"counter is {i}"))
                            #   break
            except Exception as e:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"failed in making dups {e} because of",
                        f" {criminal.first_name} {criminal.last_name}",
                        f" {criminal.guardian_first_name}",
                    ),
                )
        self.stdout.write(
            self.style.SUCCESS(f"Successfully duped . processed {j} criminals"),
        )
        self.stdout.write(
            self.style.SUCCESS(datetime.datetime.now(tz=ZoneInfo("Asia/Kolkata")))
        )
