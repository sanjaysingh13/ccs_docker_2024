from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.shortcuts import render
from django.views.generic.detail import DetailView
from neomodel import db

from ccs_docker.backend.models import Criminal

from .forms import CrimeCategoriesForm
from .forms import CriminalPSConnectionForm
from .forms import CriminalsConnectionForm


def criminal_crime_record(unique_id):
    query = """
    MATCH (criminal:Criminal {uuid:$uuid})
CALL apoc.path.subgraphAll(criminal, {
relationshipFilter: "INVOLVED_IN",
maxLevel: 2
})
YIELD nodes, relationships
WITH nodes,relationships
UNWIND nodes as node
WITH node,relationships
CALL apoc.case([
    labels(node)[0] = "Crime",
  'WITH node MATCH (ps:PoliceStation)--(node) RETURN {label:ps.name + " " + node.case_no + "/"+node.year, title:ps.name + " P.S. C/No. " + node.case_no + " dated "+coalesce(node.case_date , node.year) + " u/s " + coalesce(node.sections , "") , id:node.uuid, group:labels(node)[0]} AS node',
  labels(node)[0] = "Criminal",
  'WITH node OPTIONAL MATCH (node)--(add:Address)  RETURN {label:coalesce(node.first_name , "")+ " " + coalesce(node.last_name , ""), title:" s/o "+coalesce(node.guardian_first_name , "") + " r/o " + coalesce(add.name , ""), id:node.uuid, group:labels(node)[0]} AS node LIMIT 1'
  ],

  "",{node:node})
YIELD value
WITH [node in collect(value)| node.node] as nodes,
     [rel in relationships | rel {.*, from:startNode(rel).uuid, to:endNode(rel).uuid}] as rels
WITH {nodes:nodes, relationships:rels} as json
RETURN apoc.convert.toJson(json) as crime_record

    """
    results, meta = db.cypher_query(query, params={"uuid": unique_id})
    network = results[0][0]
    return network


class CriminalDetailView(DetailView):
    model = Criminal
    template_name = "graphs/criminal_detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_context_data(self, **kwargs):
        """
        Add additional context for the Criminal Detail view.
        """
        context = super().get_context_data(**kwargs)

        # Simplify the album context creation
        context["album"] = list(enumerate(context["object"].album))

        context["identification_marks"] = context["object"].identification_marks
        # task = criminal_crime_record.apply_async(args=[self.kwargs.get("uuid")])

        return context


@login_required
@permission_required("users.view_user", raise_exception=True)
# http://127.0.0.1:8000/graphs/network_of_criminal/390c8653-ef86-419b-adb7-75a85e482dc5
def network_of_criminal(request, unique_id):
    template_name = "graphs/criminal_network.html"
    if request.method == "GET":
        form = CrimeCategoriesForm()
    return render(request, template_name, {"form": form})


# @cache_page(None)
def connection_of_criminals(request):
    template_name = "graphs/connection_of_criminals.html"
    if request.method == "GET":
        form = CriminalsConnectionForm()
    return render(request, template_name, {"form": form})


def connection_of_criminal_to_ps(request):
    template_name = "graphs/connection_of_criminal_to_ps.html"
    if request.method == "GET":
        form = CriminalPSConnectionForm()
    return render(request, template_name, {"form": form})
