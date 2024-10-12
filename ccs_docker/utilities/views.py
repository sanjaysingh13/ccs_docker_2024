import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.core.cache import cache
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect
from django.shortcuts import render
from neomodel import db

from ccs_docker.backend.models import Tag


# Create your views here.
def duplicate_criminals(request):
    """
    View function to handle duplicate criminals.

    This function processes GET requests to fetch and display duplicate criminals.
    It uses a Cypher query to retrieve similar criminals from the database.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered template with duplicate criminals for GET requests.
        HttpResponseNotAllowed: For non-GET requests.
    """
    template_name = "utilities/duplicate_criminals.html"

    if request.method == "GET":
        context = {}
        query = """
            MATCH (criminal:Criminal)-[:SIMILAR_CRIMINAL]-()
            WITH (criminal)
            SKIP $N LIMIT 1
            CALL apoc.path.subgraphAll(criminal, {
            relationshipFilter: 'SIMILAR_CRIMINAL'
            })
            YIELD nodes, relationships
            WITH nodes, relationships

        // Select only the first five nodes
            WITH nodes[0..5] AS first_six_nodes

            UNWIND first_six_nodes AS node
            OPTIONAL MATCH (node)-[:HAS_ADDRESS]-(add:Address)
            OPTIONAL MATCH (node)-[:HAS_IMAGE]-(i:Image)

            RETURN coalesce(node.first_name, '') + ' ' +
            coalesce(node.last_name, '') + ' s/o ' +
            coalesce(node.guardian_first_name, '') + ' r/o ' +
            coalesce(add.name, '') as criminal,
            node.uuid as criminal_id,
            collect([(node)-[:INVOLVED_IN]->(c:Crime)-[:BELONGS_TO_PS]->(ps:PoliceStation) |
                ps.name + ' P.S. C/No. ' + c.case_no + '/' + c.year + ' u/s ' + coalesce(c.sections, '')]) AS crimes,
            i.avatar_url as image
            """

        results, meta = db.cypher_query(query, params={"N": random.randint(1, 100)})
        duplicate_criminals = results
        print(duplicate_criminals)
        for idx, criminal in enumerate(duplicate_criminals):
            criminal[2] = "\n".join(criminal[2][0])
            duplicate_criminals[idx] = criminal
        context["duplicate_criminals"] = duplicate_criminals
        context["duplicate_criminals_uuid"] = ",".join(
            [criminal[1] for criminal in duplicate_criminals],
        )
        print([criminal[1] for criminal in duplicate_criminals])
        return render(request, template_name, context)
    else:
        return HttpResponseNotAllowed(["GET"])


def duplicate_criminals_from_list(request):
    """
    View function to handle duplicate criminals from a list.

    This function renders a template for GET requests and potentially
    processes form data for POST requests (though currently not implemented).

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered template for GET requests.
        HttpResponseNotAllowed: For non-GET/POST requests.
    """
    template_name = "utilities/duplicate_criminals_from_list.html"

    if request.method == "GET":
        return render(request, template_name)
    elif request.method == "POST":
        # TODO: Implement POST request handling
        # Process the form data here
        return render(request, template_name)
    else:
        return HttpResponseNotAllowed(["GET", "POST"])


@login_required
@permission_required("users.view_user", raise_exception=True)
def tag_management(request):
    """
    View function for managing tags.

    This function handles GET requests to display all tags in the system.
    It requires the user to be logged in and have the 'view_user' permission.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered template with tag management context for GET requests.
        HttpResponseNotAllowed: For non-GET requests.
    """
    template_name = "utilities/tag_management.html"
    if request.method == "GET":
        context = {}
        # Retrieve all tags, strip whitespace from names, and include UUIDs
        all_tags = [(tag.name.strip(), tag.uuid) for tag in Tag.nodes.order_by("name")]
        # Sort tags alphabetically by name
        all_tags = sorted(all_tags, key=lambda x: x[0])
        context["all_tags"] = all_tags
        return render(request, template_name, context)

    # Handle non-GET requests
    return HttpResponseNotAllowed(["GET"])


@login_required
@permission_required("users.view_user", raise_exception=True)
def reset_ps_cache(request):
    cache.delete("ps_list")
    messages.info(request, "PS Cache refreshed")
    return redirect("utilities:tag_management")


@login_required
@permission_required("users.view_user", raise_exception=True)
def reset_tag_cache(request):
    cache.delete("availableTags")
    messages.info(request, "Tags Cache refreshed")
    return redirect("utilities:tag_management")
