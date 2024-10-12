import re
from abc import ABCMeta

non_alpha_numeric = re.compile(r"[^0-9a-zA-Z\s\.\-,?]+")


class NodeUtils:
    __metaclass__ = ABCMeta

    def serialize_relationships(self, nodes):
        serialized_nodes = []
        for node in nodes:
            # serialize node
            serialized_node = node.serialize

            # UNCOMMENT to get relationship type
            # results, colums = self.cypher('''
            #     START start_node=node({self}), end_node=node({end_node})
            #     MATCH (start_node)-[rel]-(end_node)
            #     RETURN type(rel) as node_relationship
            #     ''',
            #     {'end_node': node.id}
            # )
            # serialized_node['node_relationship'] = results[0][0]

            serialized_nodes.append(serialized_node)

        return serialized_nodes


def basic_criminal_search(
    first_name,
    last_name,
    guardian_first_name,
    aliases,
    id_mark,
    address,
    exact_name_search,
):
    query = []
    search_terms = 0
    first_name_params = None
    last_name_params = None
    guardian_first_name_params = None
    adresses_params = None
    id_mark_params = None
    aliases_params = None

    if exact_name_search:
        if first_name != "" and last_name == "":
            first_name = re.sub(non_alpha_numeric, " ", first_name)
            query.append(
                """MATCH (criminal:Criminal)
                WHERE criminal.first_name = $first_name
                RETURN criminal as node, 1 as score, 'full_name' as category""",
            )
            search_terms += 1
        elif last_name != "" and first_name == "":
            last_name = re.sub(non_alpha_numeric, " ", last_name)
            query.append(
                """MATCH (criminal:Criminal)
                WHERE criminal.last_name = $last_name
                RETURN criminal as node, 1 as score, 'full_name' as category""",
            )
            search_terms += 1
        elif last_name != "" and first_name != "":
            first_name = re.sub(non_alpha_numeric, " ", first_name)
            last_name = re.sub(non_alpha_numeric, " ", last_name)
            query.append(
                """MATCH (criminal:Criminal)
                WHERE criminal.first_name = $first_name and criminal.last_name = $last_name
                RETURN criminal as node, 1 as score, 'full_name' as category""",
            )
            search_terms += 1
    else:
        if first_name != "":
            first_name = re.sub(non_alpha_numeric, " ", first_name)
            first_name_params = f'{" AND ".join([first_nam.strip()+"~1" for first_nam in first_name.split(" ") if first_nam])}'
            query.append(
                """CALL db.index.fulltext.queryNodes('first_name', $first_name_params)
        YIELD node, score
        RETURN node, score, 'first_name' as category""",
            )
            search_terms += 1
        if last_name != "":
            last_name = re.sub(non_alpha_numeric, " ", last_name)
            last_name_params = f'{" AND ".join([last_nam.strip()+"~1" for last_nam in last_name.split(" ") if last_nam])}'
            query.append(
                """CALL db.index.fulltext.queryNodes('last_name', $last_name_params)
        YIELD node, score
        RETURN node, score, 'last_name' as category""",
            )
            search_terms += 1
    if guardian_first_name != "":
        guardian_first_name = re.sub(non_alpha_numeric, " ", guardian_first_name)
        guardian_first_name_params = f'{" AND ".join([guardian_first_nam.strip()+"~1" for guardian_first_nam in guardian_first_name.split(" ") if guardian_first_nam])}'
        query.append(
            """CALL db.index.fulltext.queryNodes('guardian_first_name', $guardian_first_name_params)
    YIELD node, score
    RETURN node, score, 'guardian_first_name' as category""",
        )
        search_terms += 1
    if aliases != "":
        aliases = re.sub(non_alpha_numeric, " ", aliases)
        aliases_params = f"{aliases}~1"
        query.append(
            """CALL db.index.fulltext.queryNodes('aliases', $aliases_params)
    YIELD node, score
    RETURN node, score, 'aliases' as category""",
        )
        search_terms += 1
    if address != "":
        address = re.sub(non_alpha_numeric, " ", address)
        adresses_params = f'{" AND ".join([address_word.strip() for address_word in address.split(" ") if address_word])}'
        query.append(
            """CALL db.index.fulltext.queryNodes('address', $adresses_params)
    YIELD node as address, score
    WITH address,score
    MATCH (node:Criminal)-[:HAS_ADDRESS]->(address)
    RETURN  DISTINCT node ,score , 'address' as category""",
        )
        search_terms += 1

    if id_mark != "":
        id_mark = re.sub(non_alpha_numeric, " ", id_mark)
        id_mark_params = f'{" AND ".join(["*"+id_mar.strip()+"*"  for id_mar in id_mark.split(" ") if id_mar])}'
        query.append(
            """CALL db.index.fulltext.queryNodes('id_mark', $id_mark_params)
    YIELD node as id_mark, score
    WITH id_mark,score
    MATCH (node:Criminal)-[:HAS_IDENTIFICATION_MARK]->(id_mark)
    RETURN  DISTINCT node ,score , 'id_mark' as category""",
        )
        search_terms += 1
    compiled_query = """
     UNION ALL
    """.join(
        query,
    )
    compiled_query = (
        """CALL {
  """
        + compiled_query
        + "}"
        + """
    WITH node, sum(score) AS totalScore, size(collect(DISTINCT category)) as categories
    WITH node, totalScore, categories
    WHERE categories = $search_terms
    RETURN node as criminal, totalScore, 'basic' as search
    ORDER BY totalScore DESC"""
    )
    params = {
        "first_name": first_name,
        "last_name": last_name,
        "first_name_params": first_name_params,
        "last_name_params": last_name_params,
        "guardian_first_name_params": guardian_first_name_params,
        "aliases_params": aliases_params,
        "adresses_params": adresses_params,
        "id_mark_params": id_mark_params,
        "search_terms": search_terms,
    }
    return compiled_query, params
