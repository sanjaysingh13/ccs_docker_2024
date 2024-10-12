# Create your tasks here

# from demoapp.models import Widget
from neomodel import db

from config.celery_app import app


@app.task
def criminal_subgraph(unique_id):
    print(f"Criminal id is {unique_id}")
    query = """
    MATCH (c:Criminal ) WHERE  c.uuid=$uuid
    MATCH (blacklist:Crime)
    WHERE blacklist.sections =~ ".*399.*402.*"
    WITH c, collect(blacklist) AS blacklistNodes
    CALL apoc.path.subgraphAll(c, {relationshipFilter:'INVOLVED_IN',blacklistNodes:blacklistNodes,maxLevel: 8})
    YIELD nodes
    UNWIND nodes as node
    WITH node
    WHERE node:Criminal
    RETURN node.uuid, coalesce(node.first_name, "") + " "+ coalesce(node.last_name,"")
    """
    results, meta = db.cypher_query(query, params={"uuid": unique_id})
    nodes = results[0]
    return nodes


@app.task
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
  'WITH node MATCH (ps:PoliceStation)--(node) RETURN {label:ps.name + " " + node.case_no + "/"+node.year, title:ps.name + " P.S. C/No. " + node.case_no + " dated "+coalesce(node.case_date,node.year) + " u/s " + coalesce(node.sections, "Not Given") , id:node.uuid, group:labels(node)[0]} AS node',
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


@app.task(soft_time_limit=600)
def get_ps_network_of_criminal(uuid, police_station_with_distt, crime_type):
    police_station_with_distt = police_station_with_distt.strip()
    if crime_type == 0:
        query = """
        MATCH (ps:PoliceStation{ps_with_distt:$ps_with_distt})-[:BELONGS_TO_PS]-(crime:Crime)-[:INVOLVED_IN*1..9]-(:Criminal{uuid:$uuid}),(crime)-[:HAS_TAG]-(t:Tag )
        WHERE t.name in ['Dacoity','Robbery','Theft']
        WITH crime
        MATCH (source:Crime {uuid: crime.uuid}), (target:Criminal {uuid: $uuid}),  path = shortestPath((source)-[:INVOLVED_IN*]-(target))
        WITH path
        WITH apoc.path.elements(path) AS elements
        RETURN DISTINCT elements[2].uuid, coalesce(elements[2].first_name, "") + " "+ coalesce(elements[2].last_name,"")
        """
    else:
        query = """
        MATCH (ps:PoliceStation{ps_with_distt:$ps_with_distt})-[:BELONGS_TO_PS]-(crime:Crime)-[:INVOLVED_IN*1..9]-(:Criminal{uuid:$uuid}),(crime)-[:HAS_TAG]-(t:Tag {name:'Murder'})
        WITH crime
        MATCH (source:Crime {uuid: crime.uuid}), (target:Criminal {uuid: $uuid}),  path = shortestPath((source)-[:INVOLVED_IN*]-(target))
        WITH path
        WITH apoc.path.elements(path) AS elements
        RETURN DISTINCT elements[2].uuid, coalesce(elements[2].first_name, "") + " "+ coalesce(elements[2].last_name,"")
        """
    params = {"uuid": str(uuid), "ps_with_distt": police_station_with_distt}
    print(params)
    results, meta = db.cypher_query(query, params=params)
    results.sort(key=lambda x: x[1])
    results = list(filter(lambda x: x[0] != uuid, results))
    data = {"criminal_network": results}
    return data
