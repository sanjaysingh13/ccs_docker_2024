from django.shortcuts import render
from django.views.generic.base import TemplateView
from neomodel import db


class HomeOld(TemplateView):
    def get(self, request, *args, **kwargs):
        context = {}
        query = """
        MATCH (n:Vehicle)
        RETURN count(n) as count
        """
        results, meta = db.cypher_query(query)
        context["vehicle_count"] = results[0][0]
        query = query.replace("Vehicle", "Crime")
        results, meta = db.cypher_query(query)
        context["crime_count"] = results[0][0]
        query = query.replace("Crime", "Criminal")
        results, meta = db.cypher_query(query)
        context["criminal_count"] = results[0][0]
        query = """
        MATCH ()-[n:INVOLVED_IN]-()
        RETURN count(n) as count
        """
        results, meta = db.cypher_query(query)
        context["involvement_count"] = results[0][0] / 2
        return render(request, "pages/home_old.html", context=context)
