from flask import Flask, send_from_directory, request, jsonify
import requests
from flask_cors import CORS
import json
import mysql.connector
from mysql.connector import Error
import pandas as pd

app= Flask(__name__, static_folder='build', static_url_path='/')
CORS(app)
with open('institutions.csv', 'r') as fil:
    autofill_inst_list = fil.read().split(',\n')
with open('keywords.csv', 'r') as fil:
    autofill_topics_list = fil.read().split('\n')


@app.route('/')
def index():
  return send_from_directory(app.static_folder, 'index.html')

### NEW API CALLS

@app.route('/initial-search', methods=['POST'])
def initial_search():
  institution = request.json.get('organization')
  researcher = request.json.get('researcher')
  type = request.json.get('type')
  topic = request.json.get('topic')
  if institution and researcher and topic:
    data = get_institution_and_topic_and_researcher_metadata(institution, topic, researcher)
    work_list, graph, extra_metadata = get_work_info(topic, researcher, data['topic_oa_link'], data['researcher_oa_link'])
    data['work_count'] = extra_metadata['work_count']
    data['cited_by_count'] = extra_metadata['cited_by_count']
    graph['nodes'].append({ 'id': data['institution_oa_link'], 'label': institution, 'type': 'INSTIUTION' })
    graph['edges'].append({ 'id': f"""{data['researcher_oa_link']}-{data['institution_oa_link']}""", 'start': data['researcher_oa_link'], 'end': data['institution_oa_link'], "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
    results = {"metadata": data, "graph": graph, "list": work_list}
  elif institution and researcher:
    data = get_researcher_and_institution_metadata(researcher, institution)
    topic_list, graph = get_author_info_oa(data['researcher_oa_link'], researcher, institution)
    results = {"metadata": data, "graph": graph, "list": topic_list}
  elif institution and topic:
    data = get_institution_and_topic_metadata(institution, topic)
    topic_list, graph, extra_metadata = get_institution_topic_info(institution, data['institution_oa_link'], topic, data['topic_oa_link'])
    data['work_count'] = extra_metadata['work_count']
    data['people_count'] = extra_metadata['num_people']
    results = {"metadata": data, "graph": graph, "list": topic_list}
  elif researcher and topic:
    data = get_topic_and_researcher_metadata(topic, researcher)
    work_list, graph, extra_metadata = get_work_info(topic, researcher, data['topic_oa_link'], data['researcher_oa_link'])
    data['work_count'] = extra_metadata['work_count']
    data['cited_by_count'] = extra_metadata['cited_by_count']
    results = {"metadata": data, "graph": graph, "list": work_list}
  elif topic:
    data = get_keyword_metadata(topic)
    topic_list, graph = get_topic_info_oa(topic, data['oa_link'])
    results = {"metadata": data, "graph": graph, "list": topic_list}
  elif institution:
    data = get_institution_metadata(institution)
    topic_list, graph = get_topics_oa(data['ror'], data['name'], data['oa_link'])
    results = {"metadata": data, "graph": graph, "list": topic_list}
  elif researcher:
    data = get_author_metadata(researcher)
    topic_list, graph = get_author_info_oa(data['oa_link'], data['name'], data['current_institution'])
    results = {"metadata": data, "graph": graph, "list": topic_list}
  return results

def get_authors(institution, topic):
   # DONE
   if institution and topic:
      query = f"""
      PREFIX soa: <https://semopenalex.org/ontology/>
      PREFIX dct: <http://purl.org/dc/terms/>
      PREFIX foaf: <http://xmlns.com/foaf/0.1/>
      PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

      SELECT DISTINCT ?name ?institution ?topic ?author ?workTitle
      WHERE {'{'}
        ?institution foaf:name "{institution}" .
        ?topic skos:prefLabel "{topic}" .
        ?author <http://www.w3.org/ns/org#memberOf> ?institution .
        ?work dct:creator ?author .
        << ?work soa:hasTopic ?topic >> ?p ?o .
        ?author foaf:name ?name .
        ?work <http://purl.org/dc/terms/title> ?workTitle .
      {'}'}LIMIT 10
      """
      results = query_endpoint(query)
      authors = []
      connecting_works = {}
      if results == []:
        return {"names": authors}, {"nodes": [], "edges": []}
      for entry in results:
         oa_link = entry['author']
         author_id = oa_link.replace('semopenalex', 'openalex').replace('author', 'authors')
         if author_id in connecting_works:
           connecting_works[author_id].append(entry['workTitle'])
         else:
           authors.append((entry['name'], author_id))
           institution_id = entry['institution'].replace('semopenalex', 'openalex').replace('institution', 'institutions')
           topic_id = entry['topic'].replace('semopenalex', 'openalex').replace('topic', 'topics')
           connecting_works[author_id] = [entry['workTitle']]
      nodes = []
      edges = []
      institution_node = { 'id': institution_id, 'label': institution, "type": "INSTITUTION" }
      topic_node = { 'id': topic_id, 'label': topic, "type": "TOPIC" }
      nodes.append(institution_node)
      nodes.append(topic_node)
      for entry in authors:
        author_name = entry[0]
        author_id = entry[1]
        author_node = { 'id': author_id, 'label': author_name, "type": "AUTHOR" }
        workTitles = ', '.join(connecting_works[author_id])
        topic_edge = { 'id': f"""{author_id}-{topic_id}""", 'start': author_id, 'end': topic_id, "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC", "connecting_works": workTitles}
        institution_edge = { 'id': f"""{author_id}-{institution_id}""" ,'start': author_id, 'end': institution_id, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"}
        nodes.append(author_node)
        if not topic_edge in edges:
          edges.append(topic_edge)
        if not institution_edge in edges:
          edges.append(institution_edge)

      return {"names": authors}, {"nodes": nodes, "edges": edges}

def get_topics(author, institution):
   # DONE
   if author and institution:
      query = f"""
      PREFIX soa: <https://semopenalex.org/ontology/>
      PREFIX dct: <http://purl.org/dc/terms/>
      PREFIX foaf: <http://xmlns.com/foaf/0.1/>
      PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

      SELECT DISTINCT ?name ?author ?institution ?topic (GROUP_CONCAT(DISTINCT ?workTitle; SEPARATOR=", ") AS ?workTitles)
      WHERE {'{'}
        ?author foaf:name "{author}" .
        ?institution foaf:name "{institution}" .
        ?work dct:creator ?author .
        ?work soa:hasAuthorship ?authorship .
        ?authorship soa:hasOrganization ?institution .
        << ?work soa:hasTopic ?topic >> ?p ?o .
        ?work <http://purl.org/dc/terms/title> ?workTitle .
        ?topic skos:prefLabel ?name .
      {'}'}GROUP BY ?name ?author ?institution ?topic
      """
      results = query_endpoint(query)
      topics = []
      for entry in results:
         topic_name = entry['name']
         work_titles = entry['workTitles']
         topic_id = entry['topic'].replace('semopenalex', 'openalex').replace('topic', 'topics')
         topics.append((topic_name, topic_id, work_titles))
         institution_id = entry['institution'].replace('semopenalex', 'openalex').replace('institution', 'institutions')
         author_id = entry['author'].replace('semopenalex', 'openalex').replace('author', 'authors')
      edges = []
      nodes = []
      institution_node = { 'id': institution_id, 'label': institution, "type": "INSTITUTION" }
      author_node = { 'id': author_id, 'label': author, "type": "AUTHOR" }
      nodes.append(institution_node)
      nodes.append(author_node)
      edges.append({'id': f"""{author_id}-{institution_id}""", 'start': author_id, 'end': institution_id, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
      for entry in topics:
        topic_name = entry[0]
        topic_id = entry[1]
        works = entry[2]
        topic_node = { 'id': topic_id, 'label': topic_name, "type": "TOPIC" }
        topic_edge = { 'id': f"""{author_id}-{topic_id}""", 'start': author_id, 'end': topic_id, "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC", "connecting_works": works}
        nodes.append(topic_node)
        if not topic_edge in edges:
          edges.append(topic_edge)
      topic_list = []
      for a in topics:
        topic_list.append(a[0])

      return {"names": topic_list}, {"nodes": nodes, "edges": edges}

def get_works(author, topic, institution):
   if author and topic and institution:
      # DONE
      query = f"""
      PREFIX soa: <https://semopenalex.org/ontology/>
      PREFIX dct: <http://purl.org/dc/terms/>
      PREFIX foaf: <http://xmlns.com/foaf/0.1/>
      PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

      SELECT DISTINCT ?name ?author ?topic ?institution
      WHERE {'{'}
        ?author foaf:name "{author}" .
        ?institution foaf:name "{institution}" .
        ?topic skos:prefLabel "{topic}" .
        ?work dct:creator ?author .
        ?work soa:hasAuthorship ?authorship .
        ?authorship soa:hasOrganization ?institution .
        << ?work soa:hasTopic ?topic >> ?p ?o .
        ?work dct:title ?name .
      {'}'}
      """
      results = query_endpoint(query)
      titles = []
      if results == []:
        return {"titles": titles}, {"nodes": [], "edges": []}
      for entry in results:
         author_id = entry['author'].replace('semopenalex', 'openalex').replace('author', 'authors')
         topic_id = entry['topic'].replace('semopenalex', 'openalex').replace('topic', 'topics')
         institution_id = entry['institution'].replace('semopenalex', 'openalex').replace('institution', 'institutions')
         titles.append(entry['name'])

      nodes = []
      edges = []
      author_node = { 'id': author_id, 'label': author, 'type': 'AUTHOR' }
      topic_node = { 'id': topic_id, 'label': topic, 'type': 'TOPIC' }
      institution_node = { 'id': institution_id, 'label': institution, 'type': 'INSTITUTION' }
      nodes.append(author_node)
      nodes.append(topic_node)
      nodes.append(institution_node)
      edges.append({'id': f"""{author_id}-{institution_id}""", 'start': author_id, 'end': institution_id, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
      for work in titles:
        work_node = { 'id': work, 'label': work, 'type': 'WORK' }
        work_edge = { 'id': f"""{work}-{author_id}""", 'start': work, 'end': author_id, 'label': 'authored' }
        topic_edge = { 'id': f"""{work}-{topic_id}""", 'start': work, 'end': topic_id, 'label': 'hasTopic' }
        nodes.append(work_node)
        edges.append(work_edge)
        if not topic_edge in edges:
          edges.append(topic_edge)

      return {"titles": titles}, {"nodes": nodes, "edges": edges}
   elif author and topic:
      query = f"""
      PREFIX soa: <https://semopenalex.org/ontology/>
      PREFIX dct: <http://purl.org/dc/terms/>
      PREFIX foaf: <http://xmlns.com/foaf/0.1/>
      PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

      SELECT DISTINCT ?name ?author ?topic
      WHERE {'{'}
        ?author foaf:name "{author}" .
        ?topic skos:prefLabel "{topic}" .
        ?work dct:creator ?author .
        << ?work soa:hasTopic ?topic >> ?p ?o .
        ?work dct:title ?name .
      {'}'}
      """
      results = query_endpoint(query)
      titles = []
      if results == []:
        return {"titles": titles}, {"nodes": [], "edges": []}
      for entry in results:
         author_id = entry['author'].replace('semopenalex', 'openalex').replace('author', 'authors')
         topic_id = entry['topic'].replace('semopenalex', 'openalex').replace('topic', 'topics')
         titles.append(entry['name'])

      nodes = []
      edges = []
      author_node = { 'id': author_id, 'label': author, 'type': 'AUTHOR' }
      topic_node = { 'id': topic_id, 'label': topic, 'type': 'TOPIC' }
      nodes.append(author_node)
      nodes.append(topic_node)
      for work in titles:
        work_node = { 'id': work, 'label': work, 'type': 'WORK' }
        work_edge = { 'id': f"""{work}-{author_id}""", 'start': work, 'end': author_id, 'label': 'authored' }
        topic_edge = { 'id': f"""{work}-{topic_id}""", 'start': work, 'end': topic_id, 'label': 'hasTopic' }
        nodes.append(work_node)
        edges.append(work_edge)
        if not topic_edge in edges:
          edges.append(topic_edge)

      return {"titles": titles}, {"nodes": nodes, "edges": edges}

def get_institution_metadata(institution):
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
  results = query_endpoint(query)
  ror = results[0]['ror']
  works_count = results[0]['workscount']
  cited_count = results[0]['citedcount']
  homepage = results[0]['homepage']
  author_count = results[0]['peoplecount']
  oa_link = results[0]['institution']
  oa_link = oa_link.replace('semopenalex', 'openalex').replace('institution', 'institutions')
  hbcu = is_HBCU(oa_link)
  return {"name": institution, "ror": ror, "works_count": works_count, "cited_count": cited_count, "homepage": homepage, "author_count": author_count, 'oa_link': oa_link, "hbcu": hbcu}

def get_researcher_and_institution_metadata(researcher, institution):
  researcher_data = get_author_metadata(researcher)
  institution_data = get_institution_metadata(institution)

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

def get_topic_and_researcher_metadata(topic, researcher):
  researcher_data = get_author_metadata(researcher)
  topic_data = get_keyword_metadata(topic)

  researcher_name = researcher
  keyword_name = topic
  orcid = researcher_data['orcid']
  current_org = researcher_data['current_institution']
  work_count = researcher_data['work_count']
  cited_by_count = researcher_data['cited_by_count']
  topic_cluster = topic_data['topic_clusters']
  researcher_oa = researcher_data['oa_link']
  topic_oa = topic_data['oa_link']
  return {"researcher_name": researcher_name, "topic_name": keyword_name, "orcid": orcid, "current_institution": current_org, "work_count": work_count, "cited_by_count": cited_by_count, "topic_clusters": topic_cluster, "researcher_oa_link": researcher_oa, "topic_oa_link": topic_oa}

def get_institution_and_topic_metadata(institution, topic):
  institution_data = get_institution_metadata(institution)
  topic_data = get_keyword_metadata(topic)

  institution_name = institution
  keyword_name = topic
  ror = institution_data['ror']
  topic_cluster = topic_data['topic_clusters']
  topic_oa = topic_data['oa_link']
  institution_oa = institution_data['oa_link']
  institution_url = institution_data['homepage']
  work_count = institution_data['works_count']
  cited_by_count = institution_data['cited_count']
  people_count = institution_data['author_count']
  return {"institution_name": institution_name, "topic_name": keyword_name, "work_count": work_count, "cited_by_count": cited_by_count, "ror": ror, "topic_clusters": topic_cluster, "people_count": people_count, "topic_oa_link": topic_oa, "institution_oa_link": institution_oa, "homepage": institution_url}

def get_institution_and_topic_and_researcher_metadata(institution, topic, researcher):
  institution_data = get_institution_metadata(institution)
  topic_data = get_keyword_metadata(topic)
  researcher_data = get_author_metadata(researcher)

  institution_url = institution_data['homepage']
  orcid = researcher_data['orcid']
  work_count = researcher_data['work_count']
  cited_by_count = researcher_data['cited_by_count']
  topic_cluster = topic_data['topic_clusters']
  topic_oa = topic_data['oa_link']
  institution_oa = institution_data['oa_link']
  researcher_oa = researcher_data['oa_link']
  ror = institution_data['ror']

  return {"institution_name": institution, "topic_name": topic, "researcher_name": researcher, "topic_oa_link": topic_oa, "institution_oa_link": institution_oa, "homepage": institution_url, "orcid": orcid, "topic_clusters": topic_cluster, "researcher_oa_link": researcher_oa, "work_count": work_count, "cited_by_count": cited_by_count}

def get_topic_metadata(topic):
   query = f"""
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT DISTINCT ?works_count ?cited_by_count ?note ?topic
    WHERE {'{'}
        ?topic skos:prefLabel "{topic}" .
        ?topic <https://semopenalex.org/ontology/worksCount> ?works_count .
        ?topic <https://semopenalex.org/ontology/citedByCount> ?cited_by_count .
        ?topic <http://www.w3.org/2004/02/skos/core#note> ?note .
    {'}'}
   """
   query2 = f"""
    SELECT DISTINCT ?institutionName ?institution
    WHERE {'{'}
    ?topic <http://www.w3.org/2004/02/skos/core#prefLabel> "{topic}" .
    << ?work <https://semopenalex.org/ontology/hasTopic> ?topic >> ?p ?o .
    ?work <http://purl.org/dc/terms/creator> ?person .
    ?person <http://www.w3.org/ns/org#memberOf> ?institution .
    ?institution <http://xmlns.com/foaf/0.1/name> ?institutionName .
    {'}'}LIMIT 10
   """
   results = query_endpoint(query)
   works_count = results[0]['works_count']
   cited_by_count = results[0]['cited_by_count']
   description = results[0]['note']
   oa_link = results[0]['topic']
   oa_link = oa_link.replace('semopenalex', 'openalex').replace('topic', 'topics')

   nodes = []
   edges = []
   nodes.append({ 'id': oa_link, 'label': topic, 'type': 'TOPIC' })
   results2 = query_endpoint(query2)
   for inst in results2:
     name = inst['institutionName']
     institution_id = inst['institution']
     node = {'id': institution_id, 'label': name, 'type': 'INSTITUTION' }
     node_edge = { 'id': f"""{institution_id}-{oa_link}""", 'start': institution_id, 'end': oa_link, "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"}
     nodes.append(node)
     edges.append(node_edge)

   return {"name": topic, "works_count": works_count, "cited_by_count": cited_by_count, "description": description, "oa_link": oa_link}, {"nodes": nodes, "edges": edges}

def get_author_metadata(author):
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
   results = query_endpoint(query)
   cited_by_count = results[0]['cite_count']
   orcid = results[0]['orcid'] if 'orcid' in results[0] else ''
   work_count = results[0]['works_count']
   current_institution = results[0]['current_institution_name']
   oa_link = results[0]['author']
   oa_link = oa_link.replace('semopenalex', 'openalex').replace('author', 'authors')
   institution_link = results[0]['current_institution'].replace('semopenalex', 'openalex').replace('institution', 'institutions')

   return {"name": author, "cited_by_count": cited_by_count, "orcid": orcid, "work_count": work_count, "current_institution": current_institution, "oa_link": oa_link, "institution_url": institution_link}

def query_endpoint(query):
  endpoint_url = "https://semopenalex.org/sparql"
  response = requests.post(endpoint_url, data={"query": query}, headers={'Accept': 'application/json'})
  return_value = []
  data = response.json()
  for entry in data['results']['bindings']:
    my_dict = {}
    for e in entry:
      my_dict[e] = entry[e]['value']
    return_value.append(my_dict)
  return return_value

@app.route('/get-default-graph', methods=['POST'])
def get_default_graph():
  with open("default.json", "r") as file:
    graph = json.load(file)
  nodes = []
  edges = []
  cur_nodes = graph['nodes']
  cur_edges = graph['edges']
  most = {}
  needed_topics = set()
  for edge in cur_edges:
    if edge['start'] in most:
      if edge['connecting_works'] > most[edge['start']]:
        most[edge['start']] = edge['connecting_works']
    else:
      most[edge['start']] = edge['connecting_works']
  for edge in cur_edges:
    if most[edge['start']] == edge['connecting_works']:
      edges.append(edge)
      needed_topics.add(edge['end'])
  for node in cur_nodes:
    if node['type'] == 'TOPIC':
      if node['id'] in needed_topics:
        nodes.append(node)
    else:
      nodes.append(node)
  final_graph = {"nodes": nodes, "edges": edges}
  count = 0
  for a in cur_nodes:
    if a['type'] == "INSTITUTION":
      count = count + 1
  print(count)
  return {"graph": final_graph}

@app.route('/get-topic-space-default-graph', methods=['POST'])
def get_topic_space():
  nodes= [{ "id": 1, 'label': "Physical Sciences", 'type': 'DOMAIN'}, { "id": 2, 'label': "Life Sciences", 'type': 'DOMAIN'}, { "id": 3, 'label': "Social Sciences", 'type': 'DOMAIN'}, { "id": 4, 'label': "Health Sciences", 'type': 'DOMAIN'}]
  edges = []
  graph = {"nodes": nodes, "edges": edges}
  return {"graph": graph}

@app.route('/search-topic-space', methods=['POST'])
def search_topic_space():
  search = request.json.get('topic')
  with open('topic_default.json', 'r') as file:
    graph = json.load(file)
  nodes = []
  edges = []
  for node in graph['nodes']:
    node_additions = []
    edge_additions = []
    if node['label'] == search or node['subfield_name'] == search or node['field_name'] == search or node['domain_name'] == search or search in node['keywords'].split("; "):
      topic_node = { 'id': node['id'], 'label': node['label'], 'type': 'TOPIC', "keywords":node['keywords'], "summary": node['summary'], "wikipedia_url": node['wikipedia_url']}
      node_additions.append(topic_node)
      subfield_node = { "id": node["subfield_id"], 'label': node['subfield_name'], 'type': 'SUBFIELD'}
      node_additions.append(subfield_node)
      field_node = { "id": node["field_id"], 'label': node['field_name'], 'type': 'FIELD'}
      node_additions.append(field_node)
      domain_node = { "id": node["domain_id"], 'label': node['domain_name'], 'type': 'DOMAIN'}
      node_additions.append(domain_node)
      topic_subfield = { 'id': f"""{node['id']}-{node['subfield_id']}""" ,'start': node['id'], 'end': node['subfield_id'], "label": "hasSubfield", "start_type": "TOPIC", "end_type": "SUBFIELD"}
      edge_additions.append(topic_subfield)
      subfield_field = { 'id': f"""{node['subfield_id']}-{node['field_id']}""" ,'start': node['subfield_id'], 'end': node['field_id'], "label": "hasField", "start_type": "SUBFIELD", "end_type": "FIELD"}
      edge_additions.append(subfield_field)
      field_domain = { 'id': f"""{node['field_id']}-{node['domain_id']}""" ,'start': node['field_id'], 'end': node['domain_id'], "label": "hasDomain", "start_type": "FIELD", "end_type": "DOMAIN"}
      edge_additions.append(field_domain)
    for a in node_additions:
      if a not in nodes:
        nodes.append(a)
    for a in edge_additions:
      if a not in edges:
        edges.append(a)
  final_graph = {"nodes": nodes, "edges": edges}
  return {'graph': final_graph}

def create_connection(host_name, user_name, user_password, db_name):
  """Create a database connection and return the connection object."""
  connection = None
  try:
      connection = mysql.connector.connect(
          host=host_name,
          user=user_name,
          passwd=user_password,
          database=db_name
      )
      print("Connection to MySQL DB successful")
  except Error as e:
      print(f"The error '{e}' occurred")

  return connection

def execute_read_query(connection, query):
  """Execute a read query and return the results."""
  cursor = connection.cursor()
  try:
      cursor.execute(query)
      result = cursor.fetchall()
      return result
  except Error as e:
      print(f"The error '{e}' occurred")

def is_HBCU(id):
  connection = create_connection('openalexalpha.mysql.database.azure.com', 'openalexreader', 'collabnext2024reader!', 'openalex')
  id = id.replace('https://openalex.org/institutions/', "")
  query = f"""SELECT HBCU FROM institutions_filtered WHERE id = "{id}";"""
  result = execute_read_query(connection, query)
  if result == [(1,)]:
    return True
  else:
    return False

@app.route('/autofill-institutions', methods=['POST'])
def autofill_institutions():
  inst = request.json.get('institution')
  possible_searches = []
  for i in autofill_inst_list:
    if inst.lower() in i.lower():
      possible_searches.append(i)
  return {"possible_searches": possible_searches}

@app.route('/autofill-topics', methods=['POST'])
def autofill_topics():
  topic = request.json.get('topic')
  possible_searches = []
  if len(topic) > 2:
    for i in autofill_topics_list:
      if topic.lower() in i.lower():
        possible_searches.append(i)
  return {"possible_searches": possible_searches}

def get_topics_from_keyword(keyword):
  keyword = keyword.title()
  query = f"""
  SELECT DISTINCT ?topicName
    WHERE {'{'}
    ?keyword <http://www.w3.org/2004/02/skos/core#prefLabel> "{keyword}" .
    ?topic <https://semopenalex.org/ontology/hasKeyword> ?keyword .
    ?topic <http://www.w3.org/2004/02/skos/core#prefLabel> ?topicName
    {'}'}
  """
  results = query_endpoint(query)
  topic_list = []
  for a in results:
    topic_list.append(a['topicName'])
  return topic_list

def get_keywords_from_topics(topic):
  query = f"""
  SELECT DISTINCT ?keywordName
    WHERE {'{'}
    ?topic <http://www.w3.org/2004/02/skos/core#prefLabel> "{topic}" .
    ?topic <https://semopenalex.org/ontology/hasKeyword> ?keyword .
    ?keyword <http://www.w3.org/2004/02/skos/core#prefLabel> ?keywordName
    {'}'}
  """
  results = query_endpoint(query)
  keyword_list = []
  for a in results:
    keyword_list.append(a['keywordName'])
  return keyword_list

def combine_graphs(graph1, graph2):
  dup_nodes = graph1['nodes'] + graph2['nodes']
  dup_edges = graph1['edges'] + graph2['edges']
  final_nodes = list({tuple(d.items()): d for d in dup_nodes}.values())
  final_edges = list({tuple(d.items()): d for d in dup_edges}.values())
  return {"nodes": final_nodes, "edges": final_edges}

def get_topics_oa(ror, name, id):
  final_topic_count = {}
  headers = {'Accept': 'application/json'}
  response = requests.get(f'https://api.openalex.org/authors?per-page=200&filter=last_known_institutions.ror:{ror}&cursor=*', headers=headers)
  data = response.json()
  authors = data['results']
  next_page = data['meta']['next_cursor']
  while next_page is not None:
    for a in authors:
      topics = a['topics']
      for topic in topics:
        if topic['display_name'] in final_topic_count:
          final_topic_count[topic['display_name']] = final_topic_count[topic['display_name']] + 1
        else:
          final_topic_count[topic['display_name']] = 1
    response = requests.get(f'https://api.openalex.org/authors?per-page=200&filter=last_known_institutions.ror:{ror}&cursor=' + next_page, headers=headers)
    data = response.json()
    authors = data['results']
    next_page = data['meta']['next_cursor']
  final_keyword_count = {}
  for x in final_topic_count:
    with open('topics_keywords.json', 'r') as file:
      topic_keywords = json.load(file)
    if x in topic_keywords:
      keywords = topic_keywords[x]
    else:
      print("Missing: " + str(x))
      keywords = []
    for key in keywords:
      if key in final_keyword_count:
        final_keyword_count[key] = final_keyword_count[key] + final_topic_count[x]
      else:
        final_keyword_count[key] = final_topic_count[x]
  # Sorting the dictionary by values in descending order
  sorted_keywords = sorted([(k, v) for k, v in final_keyword_count.items() if v > 5], key=lambda x: x[1], reverse=True)
  # Printing the sorted keywords and their values

  # Make the graph
  nodes = []
  edges = []
  nodes.append({ 'id': id, 'label': name, 'type': 'INSTITUTION' })
  for keyword, number in sorted_keywords:
    nodes.append({'id': keyword, 'label': keyword, 'type': "TOPIC"})
    number_id = keyword + ":" + str(number)
    nodes.append({'id': number_id, 'label': number, 'type': "NUMBER"})
    edges.append({ 'id': f"""{id}-{keyword}""", 'start': id, 'end': keyword, "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})
    edges.append({ 'id': f"""{keyword}-{number_id}""", 'start': keyword, 'end': number_id, "label": "number", "start_type": "TOPIC", "end_type": "NUMBER"})
  graph = {"nodes": nodes, "edges": edges}

  return sorted_keywords, graph

def get_author_info_oa(id, name, institution):
  final_topic_count = {}
  headers = {'Accept': 'application/json'}
  search_id = id.replace('https://openalex.org/authors/', '')
  response = requests.get(f'https://api.openalex.org/authors/{search_id}', headers=headers)
  data = response.json()
  topics = data['topics']
  with open('topics_keywords.json', 'r') as file:
    topic_keywords = json.load(file)
  for t in topics:
    if t['display_name'] in topic_keywords:
      keywords = topic_keywords[t['display_name']]
    else:
      keywords = []
    for key in keywords:
      if key in final_topic_count:
        final_topic_count[key] = final_topic_count[key] + t['count']
      else:
        final_topic_count[key] = t['count']
  sorted_keywords = sorted(final_topic_count.items(), key=lambda x: x[1], reverse=True)

  nodes = []
  edges = []
  nodes.append({ 'id': institution, 'label': institution, 'type': 'INSTITUTION' })
  edges.append({ 'id': f"""{id}-{institution}""", 'start': id, 'end': institution, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
  nodes.append({ 'id': id, 'label': name, "type": "AUTHOR"})
  for keyword, number in sorted_keywords:
    nodes.append({'id': keyword, 'label': keyword, 'type': "TOPIC"})
    number_id = keyword + ":" + str(number)
    nodes.append({'id': number_id, 'label': number, 'type': "NUMBER"})
    edges.append({ 'id': f"""{id}-{keyword}""", 'start': id, 'end': keyword, "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})
    edges.append({ 'id': f"""{keyword}-{number_id}""", 'start': keyword, 'end': number_id, "label": "number", "start_type": "TOPIC", "end_type": "NUMBER"})
  graph = {"nodes": nodes, "edges": edges}

  return sorted_keywords, graph

def get_topic_info_oa(keyword, id):
  headers = {'Accept': 'application/json'}
  associated_topics = get_topics_from_keyword(keyword)
  topic_list = []

  for institution in autofill_inst_list:
    response = requests.get(f'https://api.openalex.org/institutions?select=display_name,topics&filter=display_name.search:{institution}', headers=headers)
    try:
      data = response.json()
      data = data['results'][0]
      inst_topics = data['topics']
      count = 0
      for t in inst_topics:
        if t['display_name'] in associated_topics:
          count = count + t['count']
      if count > 0:
        topic_list.append((institution, count))
    except:
      continue

  topic_list.sort(key=lambda x: x[1], reverse=True)

  nodes = []
  edges = []
  nodes.append({ 'id': id, 'label': keyword, 'type': 'TOPIC' })
  for i, c in topic_list:
    if not c == 0:
      nodes.append({ 'id': i, 'label': i, 'type': 'INSTITUTION' })
      nodes.append({'id': c, 'label': c, 'type': "NUMBER"})
      edges.append({ 'id': f"""{id}-{i}""", 'start': id, 'end': i, "label": "researches", "start_type": "TOPIC", "end_type": "INSTITUTION"})
      edges.append({ 'id': f"""{i}-{c}""", 'start': i, 'end': c, "label": "numResearchers", "start_type": "INSTITUTION", "end_type": "NUMBER"})
  graph = {"nodes": nodes, "edges": edges}
  return topic_list, graph

def get_work_info(keyword, researcher, keyword_id, researcher_id, all_institutions=True):
  query = f"""
  SELECT DISTINCT ?work ?name ?cited_by_count WHERE {"{"}
  ?author <http://xmlns.com/foaf/0.1/name> "{researcher}" .
  ?work <http://purl.org/dc/terms/creator> ?author .
  << ?work <https://semopenalex.org/ontology/hasTopic> ?topic >> ?p ?o .
  ?topic <https://semopenalex.org/ontology/hasKeyword> ?keyword .
  ?keyword <http://www.w3.org/2004/02/skos/core#prefLabel> "{keyword}" .
  ?work <http://purl.org/dc/terms/title> ?name .
  ?work <https://semopenalex.org/ontology/citedByCount> ?cited_by_count .
  {'}'}
  """
  results = query_endpoint(query)
  work_list = []
  for a in results:
    work_list.append((a['work'], a['name'], int(a['cited_by_count'])))
  final_work_list = []
  for a in work_list:
    final_work_list.append((a[1], a[2]))
  final_work_list.sort(key=lambda x: x[1], reverse=True)

  nodes = []
  edges = []

  # Get an author's institutions
  if all_institutions:
    headers = {'Accept': 'application/json'}
    search_id = researcher_id.replace('https://openalex.org/authors/', '')
    response = requests.get(f'https://api.openalex.org/authors/{search_id}', headers=headers)
    data = response.json()
    institutions = data['affiliations']
    all_institutions = []
    for a in institutions:
      all_institutions.append((a['institution']['display_name'], a['institution']['id']))
    for a, i in all_institutions:
      nodes.append({ 'id': i, 'label': a, 'type': 'INSTIUTION' })
      edges.append({ 'id': f"""{researcher_id}-{i}""", 'start': researcher_id, 'end': i, "label": "hasAffiliation", "start_type": "AUTHOR", "end_type": "INSTITUTION"})

  nodes.append({ 'id': researcher_id, 'label': researcher, 'type': 'AUTHOR' })
  nodes.append({ 'id': keyword_id, 'label': keyword, 'type': 'TOPIC' })
  edges.append({ 'id': f"""{researcher_id}-{keyword_id}""", 'start': researcher_id, 'end': keyword_id, "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})
  cited_by_count = 0
  for id, w, c in work_list:
    cited_by_count = cited_by_count + c
    if not c == 0:
      nodes.append({ 'id': id, 'label': w, 'type': 'WORK' })
      nodes.append({'id': c, 'label': c, 'type': "NUMBER"})
      edges.append({ 'id': f"""{researcher_id}-{id}""", 'start': researcher_id, 'end': id, "label": "authored", "start_type": "AUTHOR", "end_type": "WORK"})
      edges.append({ 'id': f"""{id}-{c}""", 'start': id, 'end': c, "label": "citedBy", "start_type": "WORK", "end_type": "NUMBER"})
  graph = {"nodes": nodes, "edges": edges}
  return final_work_list, graph, {"work_count": len(final_work_list), "cited_by_count": cited_by_count}

def get_institution_topic_info(institution, institution_id, topic, topic_id):
  query = """
  SELECT DISTINCT ?author ?name (GROUP_CONCAT(DISTINCT ?work; SEPARATOR=", ") AS ?works) WHERE {
  ?institution <http://xmlns.com/foaf/0.1/name> "Fisk University" .
  ?author <http://www.w3.org/ns/org#memberOf> ?institution .
  ?author <http://xmlns.com/foaf/0.1/name> ?name .
  ?work <http://purl.org/dc/terms/creator> ?author .
  ?keyword a <https://semopenalex.org/ontology/Keyword> .
  ?keyword <http://www.w3.org/2004/02/skos/core#prefLabel> "Computer Vision" .
  ?topic <https://semopenalex.org/ontology/hasKeyword> ?keyword .
  << ?work <https://semopenalex.org/ontology/hasTopic> ?topic >> ?p ?o .
  }
  GROUP BY ?author ?name
  """
  results = query_endpoint(query)
  works_list = []
  final_list = []
  work_count = 0
  for a in results:
    works_list.append((a['author'], a['name'], a['works'].count(",") + 1))
    final_list.append((a['name'], a['works'].count(",") + 1))
    work_count = work_count + a['works'].count(",") + 1
  final_list.sort(key=lambda x: x[1], reverse=True)

  nodes = []
  edges = []
  nodes.append({ 'id': topic_id, 'label': topic, 'type': 'TOPIC' })
  nodes.append({ 'id': institution_id, 'label': institution, 'type': 'INSTITUTION' })
  edges.append({ 'id': f"""{institution_id}-{topic_id}""", 'start': institution_id, 'end': topic_id, "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})
  for a in works_list:
    author_name = a[1]
    author_id = a[0]
    num_works = a[2]
    nodes.append({ 'id': author_id, 'label': author_name, 'type': 'AUTHOR' })
    nodes.append({ 'id': num_works, 'label': num_works, 'type': 'NUMBER' })
    edges.append({ 'id': f"""{author_id}-{num_works}""", 'start': author_id, 'end': num_works, "label": "numWorks", "start_type": "AUTHOR", "end_type": "NUMBER"})
    edges.append({ 'id': f"""{author_id}-{institution_id}""", 'start': author_id, 'end': institution_id, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
  return final_list, {"nodes": nodes, "edges": edges}, {"num_people": len(final_list), "work_count": work_count}
  


def get_keyword_metadata(keyword):
  associated_topics = get_topics_from_keyword(keyword)
  headers = {'Accept': 'application/json'}
  # This should work in the future, but for now the keyword metadata is not complete in OA
  response = requests.get(f'https://api.openalex.org/keywords/{keyword.replace(" ", "-")}', headers=headers)
  data = response.json()
  oa_link = data['id']
  cited_by_count = 0
  work_count = 0
  researchers = 0

  for topic in associated_topics:
    response = requests.get(f'https://api.openalex.org/topics?filter=display_name.search:{topic}', headers=headers)
    data = response.json()
    data = data['results'][0]
    cited_by_count = cited_by_count + data['cited_by_count']
    work_count = work_count + data['works_count']
    #Author information not yet complete
    id = data['id']
    response = requests.get(f'https://api.openalex.org/authors?filter=topics.id:{id.replace("https://openalex.org/", "")}', headers=headers)
    data = response.json()
    data = data['meta']['count']
    researchers += data
  return {"name": keyword.title(), "topic_clusters": associated_topics, "cited_by_count": cited_by_count, "work_count": work_count, "researchers": researchers, "oa_link": oa_link}


if __name__ =='__main__':
  app.run()
