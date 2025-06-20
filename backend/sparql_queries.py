import requests

"""
This file contains the methods involved in querying the sparql database to retrieve search results. These methods are primarily
used in basic_searches.py to as a fallback if the queried object is not in the postgres database.
Below is the endpoint used for SPARQL queries
"""

SEMOPENALEX_SPARQL_ENDPOINT = "https://semopenalex.org/sparql"

def query_SPARQL_endpoint(app, endpoint_url, query):
    """
    Queries the endpoint to execute the SPARQL query.
    """
    app.logger.debug(f"Executing SPARQL query: {query}")
    try:
        response = requests.post(endpoint_url, data={"query": query}, headers={'Accept': 'application/json'})
        response.raise_for_status()  # Raises an HTTPError for bad responses
        data = response.json()
        return_value = []
        for entry in data['results']['bindings']:
            my_dict = {}
            for e in entry:
                my_dict[e] = entry[e]['value']
            return_value.append(my_dict)
        app.logger.info(f"SPARQL query returned {len(return_value)} results")
        return return_value
    except requests.exceptions.RequestException as e:
        app.logger.error(f"SPARQL query failed: {str(e)}")
        return []
    
def get_author_metadata_sparql(app, author):
  """
  Given an author, queries the SemOpenAlex endpoint to retrieve metadata on the author

  Returns:
  metadata : information on the author as a dictionary with the following keys:
    name, cited_by_count, orcid, work_count, current_institution, oa_link, institution_url
  """

  query = f"""
    SELECT ?cite_count ?orcid ?works_count ?current_institution_name ?author ?current_institution
    WHERE {'{'}
    ?author <http://xmlns.com/foaf/0.1/name> "{author}" .
    ?author <https://semopenalex.org/ontology/citedByCount> ?cite_count .
    OPTIONAL {"{"}?author <https://dbpedia.org/ontology/orcidId> ?orcid .{"}"}
    ?author <https://semopenalex.org/ontology/worksCount> ?works_count .
    ?author <http://www.w3.org/ns/org#memberOf> ?current_institution .
    ?current_institution <http://xmlns.com/foaf/0.1/name> ?current_institution_name .
    {'}'}
  """
  results = query_SPARQL_endpoint(app, SEMOPENALEX_SPARQL_ENDPOINT, query)
  if results == []:
    return {}
  cited_by_count = results[0]['cite_count']
  orcid = results[0]['orcid'] if 'orcid' in results[0] else ''
  work_count = results[0]['works_count']
  current_institution = results[0]['current_institution_name']
  oa_link = results[0]['author']
  oa_link = oa_link.replace('semopenalex', 'openalex').replace('author', 'authors')
  institution_link = results[0]['current_institution'].replace('semopenalex', 'openalex').replace('institution', 'institutions')

  return {"name": author, "cited_by_count": cited_by_count, "orcid": orcid, "work_count": work_count, "current_institution": current_institution, "oa_link": oa_link, "institution_url": institution_link}

def list_given_researcher_institution(app, id, name, institution):
    """
    When an user searches for a researcher only or a researcher and institution.
    Checks OpenAlex for what topics are attributed to the author.
    """
    app.logger.debug(f"Building list for researcher: {name} at institution: {institution}")
    final_subfield_count = {}
    headers = {'Accept': 'application/json'}
    search_id = id.replace('https://openalex.org/authors/', '')
    
    app.logger.debug(f"Fetching author data from OpenAlex for ID: {search_id}")
    response = requests.get(f'https://api.openalex.org/authors/{search_id}', headers=headers)
    data = response.json()
    topics = data['topics']
    
    for t in topics:
        subfield = t['subfield']['display_name']
        if subfield in final_subfield_count:
            final_subfield_count[subfield] = final_subfield_count[subfield] + t['count']
        else:
            final_subfield_count[subfield] = t['count']
    sorted_subfields = sorted(final_subfield_count.items(), key=lambda x: x[1], reverse=True)
    app.logger.debug(f"Found {len(sorted_subfields)} subfields for researcher")

    app.logger.debug("Building graph structure")
    nodes = []
    edges = []
    nodes.append({ 'id': institution, 'label': institution, 'type': 'INSTITUTION' })
    edges.append({ 'id': f"""{id}-{institution}""", 'start': id, 'end': institution, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
    nodes.append({ 'id': id, 'label': name, "type": "AUTHOR"})
    
    for s, number in sorted_subfields:
        nodes.append({'id': s, 'label': s, 'type': "TOPIC"})
        number_id = s + ":" + str(number)
        nodes.append({'id': number_id, 'label': number, 'type': "NUMBER"})
        edges.append({ 'id': f"""{id}-{s}""", 'start': id, 'end': s, "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})
        edges.append({ 'id': f"""{s}-{number_id}""", 'start': s, 'end': number_id, "label": "number", "start_type": "TOPIC", "end_type": "NUMBER"})
    graph = {"nodes": nodes, "edges": edges}

    app.logger.info(f"Successfully built list and graph for researcher: {name} at institution: {institution}")
    return sorted_subfields, graph

def get_institution_metadata_sparql(app, institution):
    """
    Given an institution, queries the SemOpenAlex endpoint to retrieve metadata on the institution
    """
    app.logger.debug(f"Fetching institution metadata from SPARQL for: {institution}")
    query = f"""
    SELECT ?ror ?workscount ?citedcount ?homepage ?institution (COUNT(distinct ?people) as ?peoplecount)
    WHERE {'{'}
    ?institution <http://xmlns.com/foaf/0.1/name> "{institution}" .
    ?institution <https://semopenalex.org/ontology/ror> ?ror .
    ?institution <https://semopenalex.org/ontology/worksCount> ?workscount .
    ?institution <https://semopenalex.org/ontology/citedByCount> ?citedcount .
    ?institution <http://xmlns.com/foaf/0.1/homepage> ?homepage .
    ?people <http://www.w3.org/ns/org#memberOf> ?institution .
    {'}'} GROUP BY ?ror ?workscount ?citedcount ?homepage ?institution
    """
    results = query_SPARQL_endpoint(app, SEMOPENALEX_SPARQL_ENDPOINT, query)
    if not results:
        app.logger.warning(f"No SPARQL results found for institution: {institution}")
        return {}

    app.logger.debug("Processing SPARQL results for institution")
    ror = results[0]['ror']
    works_count = results[0]['workscount']
    cited_count = results[0]['citedcount']
    homepage = results[0]['homepage']
    author_count = results[0]['peoplecount']
    oa_link = results[0]['institution']
    oa_link = oa_link.replace('semopenalex', 'openalex').replace('institution', 'institutions')
    # The hbcu field needs to be updated
    hbcu = False

    metadata = {
        "name": institution,
        "ror": ror,
        "works_count": works_count,
        "cited_count": cited_count,
        "homepage": homepage,
        "author_count": author_count,
        'oa_link': oa_link,
        "hbcu": hbcu
    }
    app.logger.info(f"Successfully retrieved metadata for institution: {institution}")
    return metadata

def list_given_institution(app, ror, name, id):
    """
    Uses OpenAlex to determine the subfields which a given institution study.
    Must iterate through all authors related to the institution and determine what topics OA attributes to them.
    """
    app.logger.debug(f"Fetching subfields for institution: {name} (ROR: {ror})")
    final_subfield_count = {}
    headers = {'Accept': 'application/json'}
    response = requests.get(f'https://api.openalex.org/authors?per-page=200&filter=last_known_institutions.ror:{ror}&cursor=*', headers=headers)
    data = response.json()
    authors = data['results']
    next_page = data['meta']['next_cursor']
    counter = 0
    
    app.logger.debug("Processing authors and their topics")
    while next_page is not None and counter < 10:
        for a in authors:
            topics = a['topics']
            for topic in topics:
                if topic['subfield']['display_name'] in final_subfield_count:
                    final_subfield_count[topic['subfield']['display_name']] += 1
                else:
                    final_subfield_count[topic['subfield']['display_name']] = 1
        response = requests.get(f'https://api.openalex.org/authors?per-page=200&filter=last_known_institutions.ror:{ror}&cursor=' + next_page, headers=headers)
        data = response.json()
        authors = data['results']
        next_page = data['meta']['next_cursor']
        counter += 1
    
    sorted_subfields = sorted([(k, v) for k, v in final_subfield_count.items() if v > 5], key=lambda x: x[1], reverse=True)
    app.logger.info(f"Found {len(sorted_subfields)} subfields with more than 5 authors")

    app.logger.debug("Building graph structure")
    nodes = []
    edges = []
    nodes.append({ 'id': id, 'label': name, 'type': 'INSTITUTION' })
    for subfield, number in sorted_subfields:
        nodes.append({'id': subfield, 'label': subfield, 'type': "TOPIC"})
        number_id = subfield + ":" + str(number)
        nodes.append({'id': number_id, 'label': number, 'type': "NUMBER"})
        edges.append({ 'id': f"""{id}-{subfield}""", 'start': id, 'end': subfield, "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})
        edges.append({ 'id': f"""{subfield}-{number_id}""", 'start': subfield, 'end': number_id, "label": "number", "start_type": "TOPIC", "end_type": "NUMBER"})
    graph = {"nodes": nodes, "edges": edges}

    app.logger.info(f"Successfully built subfield list and graph for institution: {name}")
    return sorted_subfields, graph

def get_author_from_id_sparql(app, id):
    """
    Queries SPARQL database to get an author name when given an author id.
    """
    app.logger.debug(f"Finding author with id: {id}")
    query = f"""
    SELECT ?name
    WHERE {'{'}
    <https://semopenalex.org/author/{id}> <http://xmlns.com/foaf/0.1/name> ?name .
    {'}'} GROUP BY ?name
    """
    results = query_SPARQL_endpoint(SEMOPENALEX_SPARQL_ENDPOINT, query)
    if not results:
        app.logger.warning(f"No SPARQL results found for author: {id}")
        return {}
    return results[0]['name']

def get_institution_from_id_sparql(app, id):
    app.logger.debug(f"Finding Institution with id: {id}")
    query = f"""
    SELECT ?name
    WHERE {'{'}
    <https://semopenalex.org/institution/{id}> <http://xmlns.com/foaf/0.1/name> ?name .
    {'}'} GROUP BY ?name
    """
    results = query_SPARQL_endpoint(SEMOPENALEX_SPARQL_ENDPOINT, query)
    if not results:
        app.logger.warning(f"No SPARQL results found for institution: {id}")
        return {}
    return results[0]['name']

def get_subfield_metadata_sparql(subfield):
  """
  Given a subfield, queries the OpenAlex endpoint to retrieve metadata on the subfield
  Doesn't query SemOpenAlex because the necessary data is faster to retrieve from OpenAlex, but this may change
  in the future.

  Researchers does not work as expected at the moment.

  Returns:
  metadata : information on the subfield as a dictionary with the following keys:
    name, topic_clusters, cited_by_count, work_count, researchers, oa_link
  """
  headers = {'Accept': 'application/json'}
  response = requests.get(f'https://api.openalex.org/subfields?filter=display_name.search:{subfield}', headers=headers) 
  data = response.json()['results'][0]
  oa_link = data['id']
  cited_by_count = data['cited_by_count']
  work_count = data['works_count']
  topic_clusters = []
  for topic in data['topics']:
    topic_clusters.append(topic['display_name'])
  researchers = 0
  return {"name": subfield, "topic_clusters": topic_clusters, "cited_by_count": cited_by_count, "work_count": work_count, "researchers": researchers, "oa_link": oa_link}

def get_institution_and_topic_metadata_sparql(app, institution, topic):
  """
  Given a topic and institution, collects the metadata for the 2 and returns as one dictionary.

  Returns:
  metadata : information on the topic and institution as a dictionary with the following keys:
    institution_name, topic_name, work_count, cited_by_count, ror, topic_clusters, people_count, topic_oa_link, institution_oa_link, homepage
  """
  institution_data = get_institution_metadata_sparql(app, institution)
  topic_data = get_subfield_metadata_sparql(topic)
  if topic_data == {} or institution_data == {}:
    return {}

  institution_name = institution
  subfield_name = topic
  ror = institution_data['ror']
  topic_cluster = topic_data['topic_clusters']
  topic_oa = topic_data['oa_link']
  institution_oa = institution_data['oa_link']
  institution_url = institution_data['homepage']
  work_count = institution_data['works_count']
  cited_by_count = institution_data['cited_count']
  people_count = institution_data['author_count']
  return {"institution_name": institution_name, "topic_name": subfield_name, "work_count": work_count, "cited_by_count": cited_by_count, "ror": ror, "topic_clusters": topic_cluster, "people_count": people_count, "topic_oa_link": topic_oa, "institution_oa_link": institution_oa, "homepage": institution_url}

def list_given_institution_topic(app, institution, institution_id, topic, topic_id):
    """
    When an user searches for an institution and topic
    Uses a SemOpenAlex query to retrieve authors who work at the given institution and have published
    papers relating to the provided subfield.
    """
    app.logger.debug(f"Building list for institution: {institution} and topic: {topic}")
    query = f"""
    SELECT DISTINCT ?author ?name (GROUP_CONCAT(DISTINCT ?work; SEPARATOR=", ") AS ?works) WHERE {"{"}
    ?institution <http://xmlns.com/foaf/0.1/name> "{institution}" .
    ?author <http://www.w3.org/ns/org#memberOf> ?institution .
    ?author <http://xmlns.com/foaf/0.1/name> ?name .
    ?work <http://purl.org/dc/terms/creator> ?author .
    ?subfield a <https://semopenalex.org/ontology/Subfield> .
    ?subfield <http://www.w3.org/2004/02/skos/core#prefLabel> "{topic}" .
    ?topic <http://www.w3.org/2004/02/skos/core#broader> ?subfield .
    ?work <https://semopenalex.org/ontology/hasTopic> ?topic .
    {"}"}
    GROUP BY ?author ?name
    """
    results = query_SPARQL_endpoint(app, SEMOPENALEX_SPARQL_ENDPOINT, query)
    works_list = []
    final_list = []
    work_count = 0
    app.logger.debug("Processing SPARQL results")
    for a in results:
        works_list.append((a['author'], a['name'], a['works'].count(",") + 1))
        final_list.append((a['name'], a['works'].count(",") + 1))
        work_count = work_count + a['works'].count(",") + 1

    final_list.sort(key=lambda x: x[1], reverse=True)
    num_people = len(final_list)

    app.logger.debug("Building graph structure")
    nodes = []
    edges = []
    nodes.append({ 'id': topic_id, 'label': topic, 'type': 'TOPIC' })
    nodes.append({ 'id': institution_id, 'label': institution, 'type': 'INSTITUTION' })
    edges.append({ 'id': f"""{institution_id}-{topic_id}""", 'start': institution_id, 'end': topic_id, "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})
    
    for author, name, num_works in works_list:
        nodes.append({ 'id': author, 'label': name, 'type': 'AUTHOR' })
        nodes.append({ 'id': num_works, 'label': num_works, 'type': 'NUMBER' })
        edges.append({ 'id': f"""{author}-{institution_id}""", 'start': author, 'end': institution_id, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
        edges.append({ 'id': f"""{author}-{num_works}""", 'start': author, 'end': num_works, "label": "numWorks", "start_type": "AUTHOR", "end_type": "NUMBER"})
    
    graph = {"nodes": nodes, "edges": edges}
    extra_metadata = {"work_count": work_count, "num_people": num_people}
    
    app.logger.info(f"Successfully built list and graph for institution: {institution} and topic: {topic}")
    return final_list, graph, extra_metadata

def get_topic_and_researcher_metadata_sparql(app, topic, researcher):
  """
  Given a topic and researcher, collects the metadata for the 2 and returns as one dictionary.

  Returns:
  metadata : information on the topic and researcher as a dictionary with the following keys:
    researcher_name, topic_name, orcid, current_institution, work_count, cited_by_count, topic_clusters, researcher_oa_link, topic_oa_link
  """

  researcher_data = get_author_metadata_sparql(app, researcher)
  topic_data = get_subfield_metadata_sparql(app, topic)
  if researcher_data == {} or topic_data == {}:
    return {}

  researcher_name = researcher
  subfield_name = topic
  orcid = researcher_data['orcid']
  current_org = researcher_data['current_institution']
  work_count = researcher_data['work_count']
  cited_by_count = researcher_data['cited_by_count']
  topic_cluster = topic_data['topic_clusters']
  researcher_oa = researcher_data['oa_link']
  topic_oa = topic_data['oa_link']
  institution_oa = researcher_data['institution_url']
  return {"researcher_name": researcher_name, "topic_name": subfield_name, "orcid": orcid, "current_institution": current_org, "work_count": work_count, "cited_by_count": cited_by_count, "topic_clusters": topic_cluster, "researcher_oa_link": researcher_oa, "topic_oa_link": topic_oa, "institution_oa_link": institution_oa}

def list_given_researcher_topic(app, topic, researcher, institution, topic_id, researcher_id, institution_id):
    """
    When an user searches for a researcher and topic
    Uses a SemOpenAlex query to retrieve works by the author that are related to the topic.
    """
    app.logger.debug(f"Building list for researcher: {researcher} and topic: {topic}")
    query = f"""
    SELECT DISTINCT ?work ?title ?cited_by_count WHERE {"{"}
    ?author <http://xmlns.com/foaf/0.1/name> "{researcher}" .
    ?work <http://purl.org/dc/terms/creator> ?author .
    ?work <http://xmlns.com/foaf/0.1/name> ?title .
    ?work <https://semopenalex.org/ontology/citedByCount> ?cited_by_count .
    ?subfield a <https://semopenalex.org/ontology/Subfield> .
    ?subfield <http://www.w3.org/2004/02/skos/core#prefLabel> "{topic}" .
    ?topic <http://www.w3.org/2004/02/skos/core#broader> ?subfield .
    ?work <https://semopenalex.org/ontology/hasTopic> ?topic .
    {"}"}
    """
    results = query_SPARQL_endpoint(app, SEMOPENALEX_SPARQL_ENDPOINT, query)
    work_list = []
    total_citations = 0
    app.logger.debug("Processing SPARQL results")
    for r in results:
        work_list.append((r['title'], int(r['cited_by_count'])))
        total_citations = total_citations + int(r['cited_by_count'])
    work_list.sort(key=lambda x: x[1], reverse=True)

    app.logger.debug("Building graph structure")
    nodes = []
    edges = []
    nodes.append({ 'id': institution_id, 'label': institution, 'type': 'INSTITUTION' })
    edges.append({ 'id': f"""{researcher_id}-{institution_id}""", 'start': researcher_id, 'end': institution_id, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
    nodes.append({ 'id': researcher_id, 'label': researcher, 'type': 'AUTHOR' })
    nodes.append({ 'id': topic_id, 'label': topic, 'type': 'TOPIC' })
    edges.append({ 'id': f"""{researcher_id}-{topic_id}""", 'start': researcher_id, 'end': topic_id, "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})
    
    for work, number in work_list:
        nodes.append({ 'id': work, 'label': work, 'type': 'WORK' })
        nodes.append({'id': number, 'label': number, 'type': "NUMBER"})
        edges.append({ 'id': f"""{researcher_id}-{work}""", 'start': researcher_id, 'end': work, "label": "authored", "start_type": "AUTHOR", "end_type": "WORK"})
        edges.append({ 'id': f"""{work}-{number}""", 'start': work, 'end': number, "label": "citedBy", "start_type": "WORK", "end_type": "NUMBER"})
    
    graph = {"nodes": nodes, "edges": edges}
    extra_metadata = {"work_count": len(work_list), "cited_by_count": total_citations}
    
    app.logger.info(f"Successfully built list and graph for researcher: {researcher} and topic: {topic}")
    return work_list, graph, extra_metadata

def get_researcher_and_institution_metadata_sparql(app, researcher, institution):
  """
  Given an institution and researcher, collects the metadata for the 2 and returns as one dictionary.

  Returns:
  metadata : information on the institution and researcher as a dictionary with the following keys:
    institution_name, researcher_name, homepage, institution_oa_link, researcher_oa_link, orcid, work_count, cited_by_count, ror
  """

  researcher_data = get_author_metadata_sparql(app, researcher)
  institution_data = get_institution_metadata_sparql(app, institution)
  if researcher_data == {} or institution_data == {}:
    return {}

  institution_name = institution
  researcher_name = researcher
  institution_url = institution_data['homepage']
  institution_oa = institution_data['oa_link']
  researcher_oa = researcher_data['oa_link']
  orcid = researcher_data['orcid']
  work_count = researcher_data['work_count']
  cited_by_count = researcher_data['cited_by_count']
  ror = institution_data['ror']

  return {"institution_name": institution_name, "researcher_name": researcher_name, "homepage": institution_url, "institution_oa_link": institution_oa, "researcher_oa_link": researcher_oa, "orcid": orcid, "work_count": work_count, "cited_by_count": cited_by_count, "ror": ror}

def get_institution_and_topic_and_researcher_metadata_sparql(app, institution, topic, researcher):
    """
    Given an institution, topic, and researcher, collects the metadata for the 3 and returns as one dictionary.
    """
    app.logger.debug(f"Fetching metadata for institution: {institution}, topic: {topic}, researcher: {researcher}")

    institution_data = get_institution_metadata_sparql(app, institution)
    topic_data = get_subfield_metadata_sparql(topic)
    researcher_data = get_author_metadata_sparql(app, researcher)
    
    if researcher_data == {} or institution_data == {} or topic_data == {}:
        app.logger.warning("Missing metadata from one or more entities")
        return {}

    app.logger.debug("Processing combined metadata")
    institution_url = institution_data['homepage']
    orcid = researcher_data['orcid']
    work_count = researcher_data['work_count']
    cited_by_count = researcher_data['cited_by_count']
    topic_cluster = topic_data['topic_clusters']
    topic_oa = topic_data['oa_link']
    institution_oa = institution_data['oa_link']
    researcher_oa = researcher_data['oa_link']
    ror = institution_data['ror']

    metadata = {
        "institution_name": institution, 
        "topic_name": topic, 
        "researcher_name": researcher, 
        "topic_oa_link": topic_oa, 
        "institution_oa_link": institution_oa, 
        "homepage": institution_url, 
        "orcid": orcid, 
        "topic_clusters": topic_cluster, 
        "researcher_oa_link": researcher_oa, 
        "work_count": work_count, 
        "cited_by_count": cited_by_count, 
        'ror': ror
    }

    app.logger.info(f"Successfully compiled metadata for {researcher} at {institution} researching {topic}")
    return metadata

def list_given_topic(subfield, id, autofill_inst_list):
  """
  When an user searches for a topic only.
  Searches through each HBCU and partner institution and returns which institutions research the subfield.

  Parameters:
  subfield : name of subfield searched
  id : id of the subfield

  Returns:
  subfield_list : the subfields which OpenAlex attributes to a given institution
  graph : a graphical representation of subfield_list.
  """
  headers = {'Accept': 'application/json'}
  subfield_list = []
  extra_metadata = {}
  total_work_count = 0

  for institution in autofill_inst_list:
    response = requests.get(f'https://api.openalex.org/institutions?select=display_name,topics&filter=display_name.search:{institution}', headers=headers)
    try:
      data = response.json()
      data = data['results'][0]
      inst_topics = data['topics']
      count = 0
      for t in inst_topics:
        if t['subfield']['display_name'] == subfield:
          count = count + t['count']
          total_work_count = total_work_count + t['count']
      if count > 0:
        subfield_list.append((institution, count))
    except:  # noqa: E722
      continue

  subfield_list.sort(key=lambda x: x[1], reverse=True)
  extra_metadata['work_count'] = total_work_count

  nodes = []
  edges = []
  nodes.append({ 'id': id, 'label': subfield, 'type': 'TOPIC' })
  for i, c in subfield_list:
    if not c == 0:
      nodes.append({ 'id': i, 'label': i, 'type': 'INSTITUTION' })
      nodes.append({'id': c, 'label': c, 'type': "NUMBER"})
      edges.append({ 'id': f"""{i}-{id}""", 'start': i, 'end': id, "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})
      edges.append({ 'id': f"""{i}-{c}""", 'start': i, 'end': c, "label": "number", "start_type": "INSTITUTION", "end_type": "NUMBER"})
  graph = {"nodes": nodes, "edges": edges}
  return subfield_list, graph, extra_metadata

