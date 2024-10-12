import urllib
import uuid as unique_universal_identifier
from datetime import datetime

from celery.result import AsyncResult
from dateutil.parser import parse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.core.cache import cache
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from neomodel import db

from ccs_docker.backend.models import CourtDate
from ccs_docker.backend.models import Crime
from ccs_docker.backend.models import Criminal
from ccs_docker.backend.models import Image
from ccs_docker.backend.models import Witness
from ccs_docker.graphs.tasks import get_ps_network_of_criminal


# Backend
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
  'WITH node MATCH (ps:PoliceStation)--(node) RETURN {label:ps.name + " " + node.case_no + "/"+node.year, title:ps.name + " P.S. C/No. " + node.case_no + " dated "+coalesce(node.case_date , node.year) + " u/s " + coalesce(node.sections, "Not Given") , id:node.uuid, group:labels(node)[0]} AS node',
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


def get_ajax_gist(request):
    unique_id = request.GET.get("unique_id", None)
    gist = Crime.nodes.get(uuid=unique_id).gist
    data = {"gist": gist}
    return JsonResponse(data)


def get_criminal_name(request):
    uuid = request.GET.get("uuid", None)
    criminal = Criminal.nodes.get_or_none(uuid=uuid)
    if criminal:
        data = {
            "name": (criminal.first_name if criminal.first_name else "")
            + (" " + criminal.last_name if criminal.last_name else ""),
        }
        return JsonResponse(data)
    data = {"name": "That is not a correct ID for any criminal"}
    return JsonResponse(data)


@login_required
@permission_required("users.add_user", raise_exception=True)
@csrf_protect
def update_witness(request):
    data = request.GET

    unique_id = data["row_id"]
    gist_of_deposition = data["gist_of_deposition"]
    dates_of_examination = data["dates_of_examination"]
    favourable = data["favourable"]
    if favourable.lower() == "yes":
        favourable = True
    elif favourable.lower() == "no":
        favourable = False
    else:
        favourable = None
    witness = Witness.nodes.get(uuid=unique_id)
    witness.gist_of_deposition = gist_of_deposition
    witness.dates_of_examination = dates_of_examination
    witness.favourable = favourable
    witness.save()
    return JsonResponse({"status": 200})


@login_required
@permission_required("users.add_user", raise_exception=True)
@csrf_protect
def update_or_create_court_date(request):
    data = request.GET.dict()
    if "row_id" in data:
        unique_id = data["row_id"]
        hearing_date = data["hearing_date"]
        comment = data["comment"]
        next_date = data["next_date"]
        next_date_for_comment = data["next_date_for_comment"]
        court_date = CourtDate.nodes.get(uuid=unique_id)
        try:
            court_date.hearing_date = datetime.strptime(hearing_date, "%Y/%m/%d").date()
        except Exception as e:
            print(str(e))
            try:
                court_date.hearing_date = parse(hearing_date).date()
            except Exception as e:
                print(str(e))
                court_date.hearing_date = None
        court_date.comment = comment
        try:
            court_date.next_date = datetime.strptime(next_date, "%Y/%m/%d").date()
        except Exception as e:
            print(str(e))
            try:
                court_date.next_date = parse(next_date).date()
            except Exception as e:
                print(str(e))
                court_date.next_date = None
        court_date.next_date_for_comment = next_date_for_comment
        court_date.save()
        crime_id = data["crime_uuid"]
        crime = Crime.nodes.get(uuid=crime_id)
        crime.court_dates.connect(court_date)
    else:
        crime_id = data["crime_uuid"]
        crime = Crime.nodes.get(uuid=crime_id)
        del data["crime_uuid"]
        try:
            data["hearing_date"] = datetime.strptime(
                data["hearing_date"],
                "%Y/%m/%d",
            ).date()
        except Exception as e:
            print(str(e))
            try:
                data["hearing_date"] = parse(data["hearing_date"]).date()
            except Exception as e:
                print(str(e))
                del data["hearing_date"]
        try:
            data["next_date"] = datetime.strptime(data["next_date"], "%Y/%m/%d").date()
        except Exception as e:
            print(str(e))
            try:
                data["next_date"] = parse(data["next_date"]).date()
            except Exception as e:
                print(str(e))
                del data["next_date"]
        court_date = CourtDate(**data)
        court_date.uuid = unique_universal_identifier.uuid4()
        court_date.save()
        crime.court_dates.connect(court_date)
    return JsonResponse({"status": 200})


def get_daily_report(request):
    task_id = request.GET.get("task_id", None)
    result = AsyncResult(task_id.strip())
    data = {"state": result.state, "info": result.info}
    if result.state != "FAILURE":
        return JsonResponse(data)
    return JsonResponse({"state": result.state, "info": "foo"})


# Graphs
def nodes_single_path(request):
    start_node = request.GET.get("start_node", None)
    end_node = request.GET.get("end_node", None)

    query = """
            MATCH (source:Criminal {uuid: $start_node}), (target:Criminal {uuid: $end_node}),  path = shortestPath((source)-[:INVOLVED_IN*]-(target))
            WITH path
            WITH apoc.path.elements(path) AS elements
            UNWIND range(0, size(elements)-2) AS index
            WITH elements, index
            WHERE index %2 = 0
            WITH elements[index] AS subject, elements[index+1] AS predicate, elements[index+2] AS object
            WITH  apoc.coll.toSet(collect(DISTINCT subject)+collect(DISTINCT object)) as nodes, collect(DISTINCT predicate) as relationships
            UNWIND nodes as node
            WITH node,relationships
            CALL apoc.case([
                labels(node)[0] = "Crime",
              'WITH node MATCH (ps:PoliceStation)--(node) RETURN {label:ps.name + " " + node.case_no + "/"+node.year, title:ps.name + " P.S. C/No. " + node.case_no + " dated "+coalesce(node.case_date , node.year) + " u/s " + coalesce(node.sections, "Not Given") , id:node.uuid, group:labels(node)[0]} AS node',
              labels(node)[0] = "Criminal",
              'WITH node OPTIONAL MATCH (node)--(add:Address)  RETURN {label:coalesce(node.first_name , "")+ " " + coalesce(node.last_name , ""), title:" s/o "+coalesce(node.guardian_first_name , "") + " r/o " + coalesce(add.name , ""), id:node.uuid, group:labels(node)[0]} AS node LIMIT 1'
              ],

              "",{node:node})
            YIELD value
            WITH [node in collect(value)| node.node] as nodes,
                 [rel in relationships | rel {.*, from:startNode(rel).uuid, to:endNode(rel).uuid}] as rels
            WITH {nodes:nodes, relationships:rels} as json
            RETURN apoc.convert.toJson(json) as paths
        """
    results, meta = db.cypher_query(
        query,
        params={"start_node": start_node, "end_node": end_node},
    )
    data = {"results": results, "status_code": 200}
    return JsonResponse(data)


def check_ajax_task(request):
    task_id = request.GET.get("task_id", None)
    result = AsyncResult(task_id.strip())
    data = {"state": result.state, "info": result.info}
    return JsonResponse(data)


def get_network_of_criminal(request):
    uuid = request.GET.get("uuid", None)
    tags = request.GET.get("tags", None)
    tags = list(filter(None, [tag.strip() for tag in tags.split(",") if tag]))
    if tags != []:
        query = """
        MATCH (c:Criminal ) WHERE  c.uuid=$uuid
        CALL {
        MATCH (whitelist:Crime)-[:HAS_TAG]->(tag:Tag)
        WHERE tag.name IN $tags
        RETURN whitelist
        UNION ALL
        MATCH (whitelist:Criminal)
        RETURN whitelist}
        WITH c, collect(whitelist) AS whitelistNodes
        CALL apoc.path.subgraphAll(c, {relationshipFilter:'INVOLVED_IN',whitelistNodes:whitelistNodes,maxLevel: 8})
        YIELD nodes
        UNWIND nodes as node
        WITH node
        WHERE node:Criminal
        RETURN node.uuid, coalesce(node.first_name, "") + " "+ coalesce(node.last_name,"")
        """
        results, meta = db.cypher_query(query, params={"uuid": str(uuid), "tags": tags})
    else:
        query = """
            MATCH (c:Criminal ) WHERE  c.uuid=$uuid
            CALL apoc.path.subgraphAll(c, {relationshipFilter:'INVOLVED_IN',maxLevel: 8})
            YIELD nodes
            UNWIND nodes as node
            WITH node
            WHERE node:Criminal
            RETURN node.uuid, coalesce(node.first_name, "") + " "+ coalesce(node.last_name,"")
            """
    results, meta = db.cypher_query(query, params={"uuid": str(uuid), "tags": tags})
    results.sort(key=lambda x: x[1])
    results = list(filter(lambda x: x[0] != uuid, results))
    data = {"criminal_network": results}
    return JsonResponse(data)


def nodes_paths(request):
    start_node = request.GET.get("start_node", None)
    end_node = request.GET.get("end_node", None)

    query = """
        MATCH (from:Criminal {uuid:$start_node}), (to:Criminal {uuid:$end_node})
CALL apoc.algo.allSimplePaths(from, to, 'INVOLVED_IN', 8)
YIELD path
WITH apoc.path.elements(path) AS elements
UNWIND range(0, size(elements)-2) AS index
WITH elements, index
WHERE index %2 = 0
WITH elements[index] AS subject, elements[index+1] AS predicate, elements[index+2] AS object
WITH  apoc.coll.toSet(collect(DISTINCT subject)+collect(DISTINCT object)) as nodes, collect(DISTINCT predicate) as relationships
UNWIND nodes as node
WITH node,relationships
CALL apoc.case([
    labels(node)[0] = "Crime",
  'WITH node MATCH (ps:PoliceStation)--(node) RETURN {label:ps.name + " " + node.case_no + "/"+node.year, title:ps.name + " P.S. C/No. " + node.case_no + " dated "+coalesce(node.case_date , node.year) + " u/s " + coalesce(node.sections, "Not Given") , id:node.uuid, group:labels(node)[0]} AS node',
  labels(node)[0] = "Criminal",
  'WITH node OPTIONAL MATCH (node)--(add:Address)  RETURN {label:coalesce(node.first_name , "")+ " " + coalesce(node.last_name , ""), title:" s/o "+coalesce(node.guardian_first_name , "") + " r/o " + coalesce(add.name , ""), id:node.uuid, group:labels(node)[0]} AS node LIMIT 1'
  ],

  "",{node:node})
YIELD value
WITH [node in collect(value)| node.node] as nodes,
     [rel in relationships | rel {.*, from:startNode(rel).uuid, to:endNode(rel).uuid}] as rels
WITH {nodes:nodes, relationships:rels} as json
RETURN apoc.convert.toJson(json) as paths
        """
    results, meta = db.cypher_query(
        query,
        params={"start_node": start_node, "end_node": end_node},
    )
    data = {"results": results, "status_code": 200}
    return JsonResponse(data)


def get_connected_criminals_of_ps_task_id(request):
    uuid = request.GET.get("uuid", "")
    ps_with_distt = str(request.GET.get("ps_with_distt", ""))
    ps_with_distt = ps_with_distt.strip()
    crime_type = int(request.GET.get("crime_type", ""))
    task = get_ps_network_of_criminal.apply_async(
        args=(uuid, ps_with_distt, crime_type),
    )
    task_id = task.id
    data = {"task_id": task_id}
    return JsonResponse(data)


def get_connected_criminals_of_ps(request):
    task_id = request.GET.get("task_id", None)
    result = AsyncResult(task_id.strip())
    data = {"state": result.state, "info": result.info}
    return JsonResponse(data)


def merge_given_list(list_of_criminals):
    query = """
        MATCH (p:Criminal)
        WHERE p.uuid in $list_of_criminals
        WITH collect(p) as nodes
        CALL apoc.refactor.mergeNodes(nodes, {properties: "discard" , mergeRels:true
        })
        YIELD node
        MATCH (node)-[r:SIMILAR_CRIMINAL]-(node)
        DELETE r
        RETURN count(*),node.uuid
        """
    results, meta = db.cypher_query(
        query,
        params={"list_of_criminals": list_of_criminals},
    )
    return results


def remove_similarity_relationship(list_of_criminals):
    query = """
        MATCH (a:Criminal)-[r:SIMILAR_CRIMINAL]-(b:Criminal)
        WHERE a.uuid in $list_of_criminals or b.uuid in $list_of_criminals
        DELETE r
        """
    results, meta = db.cypher_query(
        query,
        params={"list_of_criminals": list_of_criminals},
    )


@login_required
@permission_required("users.add_user", raise_exception=True)
@csrf_protect
def merge_duplicate_criminals(request):
    list_of_suggested_duplicates = request.GET.get("list_of_suggested_duplicates", None)
    list_of_suggested_duplicates = list_of_suggested_duplicates.split(",")
    merger_action_to_be_taken = request.GET.get("merger_action_to_be_taken", None)
    accepted_duplicates = request.GET.get("accepted_duplicates", None)
    accepted_duplicates = accepted_duplicates.split(",")
    if merger_action_to_be_taken in ["1", "2"]:
        merged_node = merge_given_list(accepted_duplicates)
        print(merged_node)
    elif merger_action_to_be_taken == "4":
        remove_similarity_relationship(list_of_suggested_duplicates)
    elif merger_action_to_be_taken == "3":
        merged_node = merge_given_list(accepted_duplicates)
        print(merged_node)
        removable_similarities = list(
            set(list_of_suggested_duplicates).symmetric_difference(
                set(accepted_duplicates),
            ),
        )
        remove_similarity_relationship(removable_similarities)
    return HttpResponse("OK")


@login_required
@permission_required("users.add_user", raise_exception=True)
@csrf_protect
def manage_tags(request):
    list_of_tags = request.GET.get("list_of_tags", None)
    list_of_tags = list_of_tags.split(",")
    merger_action_to_be_taken = request.GET.get("merger_action_to_be_taken", None)
    if merger_action_to_be_taken == "1":
        query = """
        MATCH (p:Tag)
        WHERE p.uuid in $list_of_tags
        WITH collect(p) as nodes
        CALL apoc.refactor.mergeNodes(nodes, {properties: "discard" , mergeRels:true
        })
        YIELD node
        RETURN count(*)
        """

    elif merger_action_to_be_taken == "2":
        query = """
        MATCH (p:Tag)
        WHERE p.uuid in $list_of_tags
        DETACH DELETE p
        """
    elif merger_action_to_be_taken == "3":
        query = """
        MATCH (p:Tag)
        WHERE p.uuid in $list_of_tags
        SET p:ModusOperandi
        REMOVE p:Tag
        """
    params = {"list_of_tags": list_of_tags}
    results, meta = db.cypher_query(query, params=params)
    cache.delete("availableTags")
    return HttpResponse("OK")


@login_required
@permission_required("users.add_user", raise_exception=True)
@csrf_protect
def merge_matched_criminal(request):
    accepted_match = request.GET.get("accepted_match", None)
    avatar_url = request.GET.get("avatar_url", None)
    avatar_url = urllib.parse.unquote(avatar_url)
    criminal = Criminal.nodes.get_or_none(uuid=accepted_match)
    if criminal:
        image = Image.nodes.get(avatar_url=avatar_url)
        image.matched_by_face_search = "true"
        image.save()
        criminal.images.connect(image)
    data = {
        "avatar_url": avatar_url,
        "accepted_match": accepted_match,
        "status_code": 200,
    }
    return JsonResponse(data)
