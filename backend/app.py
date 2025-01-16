from flask import Flask, send_from_directory, request, jsonify
import requests
from flask_cors import CORS
import json
import mysql.connector
from mysql.connector import Error
import pandas as pd
import psycopg2

app= Flask(__name__, static_folder='build', static_url_path='/')
CORS(app)

## Postgres database connection parameters
HOST = "openalex.postgres.database.azure.com"
DATABASE = "postgres"
USER = "postgres"
PASSWORD = "collabnext1!"


def execute_query(query, params):
    """
    Utility function to execute a query and fetch results from the database.
    Handles connection and cursor management.
    """
    try:
        with psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,            
            database=DATABASE,
            sslmode="disable"
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)                
                return cursor.fetchall()
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_author_ids(author_name):  
    query = """SELECT get_author_id(%s);"""
    results = execute_query(query, (author_name,))
    if results:
        # psycopg2 returns a list of tuples with each tuple representing a row
        # we only return the first row because the SQL function is designed to return a single/a list of JSON object(s)
        return results[0][0]
    return None

def get_institution_id(institution_name):
    query = """SELECT get_institution_id(%s);"""
    results = execute_query(query, (institution_name,))
    if results:
        # psycopg2 returns a list of tuples with each tuple representing a row
        # we only return the first row because the SQL function is designed to return a single/a list of JSON object(s)
        return results[0][0]['institution_id']
    return None

def search_by_author_institution_topic(author_name, institution_name, topic_name):
    author_ids = get_author_ids(author_name)
    if not author_ids:
        print("No author IDs found.")
        return None
    # always pick the first author
    author_id = author_ids[0]['author_id']

    institution_id = get_institution_id(institution_name)

    query = """SELECT search_by_author_institution_topic(%s, %s, %s);"""
    results = execute_query(query, (author_id, institution_id, topic_name))
    if results:
        # psycopg2 returns a list of tuples with each tuple representing a row
        # we only return the first row because the SQL function is designed to return a single/a list of JSON object(s)
        return results[0][0]
    return None

def search_by_author_institution(author_name, institution_name):
    author_ids = get_author_ids(author_name)
    if not author_ids:
        print("No author IDs found.")
        return None
    # always pick the first author
    author_id = author_ids[0]['author_id']

    institution_id = get_institution_id(institution_name)

    query = """SELECT search_by_author_institution(%s, %s);"""
    results = execute_query(query, (author_id, institution_id))
    if results:
        # psycopg2 returns a list of tuples with each tuple representing a row
        # we only return the first row because the SQL function is designed to return a single/a list of JSON object(s)
        return results[0][0]
    return None

def search_by_institution_topic(institution_name, topic_name):
    institution_id = get_institution_id(institution_name)

    query = """SELECT search_by_institution_topic(%s, %s);"""
    results = execute_query(query, (institution_id, topic_name))
    if results:
        # psycopg2 returns a list of tuples with each tuple representing a row
        # we only return the first row because the SQL function is designed to return a single/a list of JSON object(s)
        return results[0][0]
    return None

def search_by_author_topic(author_name, topic_name):
    author_ids = get_author_ids(author_name)
    if not author_ids:
        print("No author IDs found.")
        return None
    # always pick the first author
    author_id = author_ids[0]['author_id']

    query = """SELECT search_by_author_topic(%s, %s);"""
    results = execute_query(query, (author_id, topic_name))
    if results:
        # psycopg2 returns a list of tuples with each tuple representing a row
        # we only return the first row because the SQL function is designed to return a single/a list of JSON object(s)
        return results[0][0]
    return None

def search_by_topic(topic_name):
    query = """SELECT search_by_topic(%s);"""
    results = execute_query(query, (topic_name,))
    if results:
        # psycopg2 returns a list of tuples with each tuple representing a row
        # we only return the first row because the SQL function is designed to return a single/a list of JSON object(s)
        return results[0][0]
    return None

def search_by_institution(institution_name):
    institution_id = get_institution_id(institution_name)

    query = """SELECT search_by_institution(%s);"""
    results = execute_query(query, (institution_id,))
    if results:
        # psycopg2 returns a list of tuples with each tuple representing a row
        # we only return the first row because the SQL function is designed to return a single/a list of JSON object(s)
        return results[0][0]
    return None

def search_by_author(author_name):
    author_ids = get_author_ids(author_name)
    if not author_ids:
        print("No author IDs found.")
        return None

    # always pick the first author
    author_id = author_ids[0]['author_id']    

    query = """SELECT search_by_author(%s);"""
    results = execute_query(query, (author_id,))
    if results:
        # psycopg2 returns a list of tuples with each tuple representing a row
        # we only return the first row because the SQL function is designed to return a single/a list of JSON object(s)
        return results[0][0]
    return None


## Creates lists for autofill functionality from the institution and keyword csv files
with open('institutions.csv', 'r') as file:
    autofill_inst_list = file.read().split(',\n')
with open('subfields.csv', 'r') as file:
    autofill_subfields_list = file.read().split('\n')
SUBFIELDS = True
if not SUBFIELDS:
  with open('keywords.csv', 'r') as fil:
      autofill_topics_list = fil.read().split('\n')


@app.route('/')
def index():
  return send_from_directory(app.static_folder, 'index.html')

@app.route('/initial-search', methods=['POST'])
def initial_search():
  """
  Api call for searches from the user. Calls other methods depending on what the user inputted.

  Expects the frontend to pass in the following values:
  organization : input from the "organization" search box
  researcher : input from the "researcher name" search box
  topic : input from the "topic keyword" search box
  type : input from the "type" search box (for now, this is always HBCU)

  Returns:
  metadata : the metadata for the search
  graph : the graph for the search in the form {nodes: [], edges: []}
  list : the list view for the search
  """
  institution = request.json.get('organization')
  researcher = request.json.get('researcher')
  researcher = researcher.title()
  type = request.json.get('type')
  topic = request.json.get('topic')
  if institution and researcher and topic:
    results = get_institution_researcher_subfield_results(institution, researcher, topic)
  elif institution and researcher:
    results = get_institution_and_researcher_results(institution, researcher)
  elif institution and topic:
    results = get_institution_and_subfield_results(institution, topic)
  elif researcher and topic:
    results = get_researcher_and_subfield_results(researcher, topic)
  elif topic:
    results = get_subfield_results(topic)
  elif institution:
    results = get_institution_results(institution)
  elif researcher:
    results = get_researcher_result(researcher)
  return results

def get_researcher_result(researcher):
  data = search_by_author(researcher)
  list = []
  metadata = data['author_metadata']

  if metadata['orcid'] is None:
    metadata['orcid'] = ''
  metadata['work_count'] = metadata['num_of_works']
  metadata['current_institution'] = metadata['last_known_institution']
  metadata['cited_by_count'] = metadata['num_of_citations']
  metadata['oa_link'] = metadata['openalex_url']
  if metadata['last_known_institution'] is None:
    last_known_institution = ""
  else:
    last_known_institution = metadata['last_known_institution']
  nodes = []
  edges = []
  nodes.append({ 'id': last_known_institution, 'label': last_known_institution, 'type': 'INSTITUTION' })
  edges.append({ 'id': f"""{metadata['openalex_url']}-{last_known_institution}""", 'start': metadata['openalex_url'], 'end': last_known_institution, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
  nodes.append({ 'id': metadata['openalex_url'], 'label': researcher, "type": "AUTHOR"})
  for entry in data['data']:
    topic = entry['topic']
    num_works = entry['num_of_works']
    list.append((topic, num_works))
    nodes.append({'id': topic, 'label': topic, 'type': "TOPIC"})
    number_id = topic + ":" + str(num_works)
    nodes.append({'id': number_id, 'label': num_works, 'type': "NUMBER"})
    edges.append({ 'id': f"""{metadata['openalex_url']}-{topic}""", 'start': metadata['openalex_url'], 'end': topic, "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})
    edges.append({ 'id': f"""{metadata['openalex_url']}-{number_id}""", 'start': topic, 'end': number_id, "label": "number", "start_type": "TOPIC", "end_type": "NUMBER"})
  graph = {"nodes": nodes, "edges": edges}
  return {"metadata": metadata, "graph": graph, "list": list}

def get_institution_results(institution):
  data = search_by_institution(institution)
  list = []
  metadata = data['institution_metadata']
  
  metadata['homepage'] = metadata['url']
  metadata['works_count'] = metadata['num_of_works']
  metadata['name'] = metadata['institution_name']
  metadata['cited_count'] = metadata['num_of_citations']
  metadata['oa_link'] = metadata['openalex_url']
  metadata['author_count'] = metadata['num_of_authors']

  nodes = []
  edges = []
  institution_id = metadata['openalex_url']
  nodes.append({ 'id': institution_id, 'label': institution, 'type': 'INSTITUTION' })
  for entry in data['data']:
    subfield = entry['topic_name']
    number = entry['num_of_authors']
    list.append((subfield, number))
    nodes.append({'id': subfield, 'label': subfield, 'type': "TOPIC"})
    number_id = subfield + ":" + str(number)
    nodes.append({'id': number_id, 'label': number, 'type': "NUMBER"})
    edges.append({ 'id': f"""{institution_id}-{subfield}""", 'start': institution_id, 'end': subfield, "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})
    edges.append({ 'id': f"""{subfield}-{number_id}""", 'start': subfield, 'end': number_id, "label": "number", "start_type": "TOPIC", "end_type": "NUMBER"})
  graph = {"nodes": nodes, "edges": edges}
  return {"metadata": metadata, "graph": graph, "list": list}

def get_subfield_results(topic):
  data = search_by_topic(topic)
  list = []
  metadata = {}

  topic_clusters = []
  for entry in data['subfield_metadata']:
    topic_cluster = entry['topic']
    topic_clusters.append(topic_cluster)
    subfield_oa_link = entry['subfield_url']
  metadata['topic_clusters'] = topic_clusters
  metadata['work_count'] = data['totals']['total_num_of_works']
  metadata['cited_by_count'] = data['totals']['total_num_of_citations']
  metadata['researchers'] = data['totals']['total_num_of_authors']
  metadata['oa_link'] = subfield_oa_link

  nodes = []
  edges = []
  topic_id = topic
  nodes.append({ 'id': topic_id, 'label': topic, 'type': 'TOPIC' })
  for entry in data['data']:
    institution = entry['institution_name']
    number = entry['num_of_authors']
    list.append((institution, number))
    nodes.append({ 'id': institution, 'label': institution, 'type': 'INSTITUTION' })
    nodes.append({'id': number, 'label': number, 'type': "NUMBER"})
    edges.append({ 'id': f"""{institution}-{topic_id}""", 'start': institution, 'end': topic_id, "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})
    edges.append({ 'id': f"""{institution}-{number}""", 'start': institution, 'end': number, "label": "number", "start_type": "INSTITUTION", "end_type": "NUMBER"})
  graph = {"nodes": nodes, "edges": edges}
  return {"metadata": metadata, "graph": graph, "list": list}

def get_researcher_and_subfield_results(researcher, topic):
  data = search_by_author_topic(researcher, topic)
  list = []
  metadata = {}
  
  topic_clusters = []
  for entry in data['subfield_metadata']:
    topic_cluster = entry['topic']
    topic_clusters.append(topic_cluster)
  metadata['topic_name'] = topic
  metadata['topic_clusters'] = topic_clusters
  metadata['work_count'] = data['totals']['total_num_of_works']
  metadata['cited_by_count'] = data['totals']['total_num_of_citations']
  metadata['topic_oa_link'] = ""

  if data['author_metadata']['orcid'] is None:
    metadata['orcid'] = ''
  else:
    metadata['orcid'] = data['author_metadata']['orcid']
  metadata['researcher_name'] = researcher
  metadata['researcher_oa_link'] = data['author_metadata']['openalex_url']
  if data['author_metadata']['last_known_institution'] is None:
    metadata['current_institution'] = ""
  else:
    metadata['current_institution'] = data['author_metadata']['last_known_institution']
  last_known_institution = metadata['current_institution']

  nodes = []
  edges = []
  researcher_id = metadata['researcher_oa_link']
  subfield_id = metadata['topic_oa_link']
  nodes.append({ 'id': last_known_institution, 'label': last_known_institution, 'type': 'INSTITUTION' })
  edges.append({ 'id': f"""{researcher_id}-{last_known_institution}""", 'start': researcher_id, 'end': last_known_institution, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
  nodes.append({ 'id': researcher_id, 'label': researcher, 'type': 'AUTHOR' })
  nodes.append({ 'id': subfield_id, 'label': topic, 'type': 'TOPIC' })
  edges.append({ 'id': f"""{researcher_id}-{subfield_id}""", 'start': researcher_id, 'end': subfield_id, "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})
  for entry in data['data']:
    work = entry['work_name']
    number = entry['num_of_citations']
    list.append((work, number))
    nodes.append({ 'id': work, 'label': work, 'type': 'WORK' })
    nodes.append({'id': number, 'label': number, 'type': "NUMBER"})
    edges.append({ 'id': f"""{researcher_id}-{work}""", 'start': researcher_id, 'end': work, "label": "authored", "start_type": "AUTHOR", "end_type": "WORK"})
    edges.append({ 'id': f"""{work}-{number}""", 'start': work, 'end': number, "label": "citedBy", "start_type": "WORK", "end_type": "NUMBER"})
  graph = {"nodes": nodes, "edges": edges}
  return {"metadata": metadata, "graph": graph, "list": list}

def get_institution_and_subfield_results(institution, topic):
  data = search_by_institution_topic(institution, topic)
  list = []
  metadata = {}

  topic_clusters = []
  for entry in data['subfield_metadata']:
    topic_cluster = entry['topic']
    topic_clusters.append(topic_cluster)
  metadata['topic_name'] = topic
  metadata['topic_clusters'] = topic_clusters
  metadata['work_count'] = data['totals']['total_num_of_works']
  metadata['cited_by_count'] = data['totals']['total_num_of_citations']
  metadata['people_count'] = data['totals']['total_num_of_authors']
  metadata['topic_oa_link'] = ""
  metadata['topic_name'] = topic

  metadata['homepage'] = data['institution_metadata']['url']
  metadata['institution_oa_link'] = data['institution_metadata']['openalex_url']
  metadata['ror'] = data['institution_metadata']['ror']
  metadata['institution_name'] = institution

  nodes = []
  edges = []
  subfield_id = metadata['topic_oa_link']
  institution_id = metadata['institution_oa_link']
  nodes.append({ 'id': subfield_id, 'label': topic, 'type': 'TOPIC' })
  nodes.append({ 'id': institution_id, 'label': institution, 'type': 'INSTITUTION' })
  edges.append({ 'id': f"""{institution_id}-{subfield_id}""", 'start': institution_id, 'end': subfield_id, "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})
  for entry in data['data']:
    author_id = entry['author_id']
    author_name = entry['author_name']
    number = entry['num_of_works']
    list.append((author_name, number))
    nodes.append({ 'id': author_id, 'label': author_name, 'type': 'AUTHOR' })
    nodes.append({ 'id': number, 'label': number, 'type': 'NUMBER' })
    edges.append({ 'id': f"""{author_id}-{number}""", 'start': author_id, 'end': number, "label": "numWorks", "start_type": "AUTHOR", "end_type": "NUMBER"})
    edges.append({ 'id': f"""{author_id}-{institution_id}""", 'start': author_id, 'end': institution_id, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
  graph = {"nodes": nodes, "edges": edges}
  return {"metadata": metadata, "graph": graph, "list": list}

def get_institution_and_researcher_results(institution, researcher):
  data = search_by_author_institution(researcher, institution)
  list = []
  metadata = {}

  metadata['homepage'] = data['institution_metadata']['url']
  metadata['institution_oa_link'] = data['institution_metadata']['openalex_url']
  metadata['ror'] = data['institution_metadata']['ror']
  metadata['institution_name'] = institution

  if data['author_metadata']['orcid'] is None:
    metadata['orcid'] = ''
  else:
    metadata['orcid'] = data['author_metadata']['orcid']
  metadata['researcher_name'] = researcher
  metadata['researcher_oa_link'] = data['author_metadata']['openalex_url']
  metadata['current_institution'] = ""
  last_known_institution = metadata['current_institution']
  metadata['work_count'] = data['author_metadata']['num_of_works']
  metadata['cited_by_count'] = data['author_metadata']['num_of_citations']

  nodes = []
  edges = []
  author_id = metadata['researcher_oa_link']
  nodes.append({ 'id': institution, 'label': institution, 'type': 'INSTITUTION' })
  edges.append({ 'id': f"""{author_id}-{institution}""", 'start': author_id, 'end': institution, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
  nodes.append({ 'id': author_id, 'label': researcher, "type": "AUTHOR"})
  for entry in data['data']:
    topic_name = entry['topic_name']
    num_works = entry["num_of_works"]
    list.append((topic_name, num_works))
    nodes.append({'id': topic_name, 'label': topic_name, 'type': "TOPIC"})
    number_id = topic_name + ":" + str(num_works)
    nodes.append({'id': number_id, 'label': num_works, 'type': "NUMBER"})
    edges.append({ 'id': f"""{author_id}-{topic_name}""", 'start': author_id, 'end': topic_name, "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})
    edges.append({ 'id': f"""{topic_name}-{number_id}""", 'start': topic_name, 'end': number_id, "label": "number", "start_type": "TOPIC", "end_type": "NUMBER"})
  graph = {"nodes": nodes, "edges": edges}
  return {"metadata": metadata, "graph": graph, "list": list}

def get_institution_researcher_subfield_results(institution, researcher, topic):
  data = search_by_author_institution_topic(researcher, institution, topic)
  list = []
  metadata = {}

  metadata['homepage'] = data['institution_metadata']['url']
  metadata['institution_oa_link'] = data['institution_metadata']['openalex_url']
  metadata['ror'] = data['institution_metadata']['ror']
  metadata['institution_name'] = institution

  if data['author_metadata']['orcid'] is None:
    metadata['orcid'] = ''
  else:
    metadata['orcid'] = data['author_metadata']['orcid']
  metadata['researcher_name'] = researcher
  metadata['researcher_oa_link'] = data['author_metadata']['openalex_url']
  metadata['current_institution'] = ""
  last_known_institution = metadata['current_institution']

  topic_clusters = []
  for entry in data['subfield_metadata']:
    topic_cluster = entry['topic']
    topic_clusters.append(topic_cluster)
    subfield_oa_link = entry['subfield_url']
  metadata['topic_name'] = topic
  metadata['topic_clusters'] = topic_clusters
  metadata['work_count'] = data['totals']['total_num_of_works']
  metadata['cited_by_count'] = data['totals']['total_num_of_citations']
  metadata['topic_oa_link'] = subfield_oa_link

  nodes = []
  edges = []
  institution_id = metadata['institution_oa_link']
  researcher_id = metadata['researcher_oa_link']
  subfield_id = metadata['topic_oa_link']
  nodes.append({ 'id': institution_id, 'label': institution, 'type': 'INSTITUTION' })
  edges.append({ 'id': f"""{researcher_id}-{institution_id}""", 'start': researcher_id, 'end': institution_id, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
  nodes.append({ 'id': researcher_id, 'label': researcher, 'type': 'AUTHOR' })
  nodes.append({ 'id': subfield_id, 'label': topic, 'type': 'TOPIC' })
  edges.append({ 'id': f"""{researcher_id}-{subfield_id}""", 'start': researcher_id, 'end': subfield_id, "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})
  for entry in data['data']:
    work_name = entry['work_name']
    number = entry['cited_by_count']
    list.append((work_name, number))
    nodes.append({ 'id': work_name, 'label': work_name, 'type': 'WORK' })
    nodes.append({'id': number, 'label': number, 'type': "NUMBER"})
    edges.append({ 'id': f"""{researcher_id}-{work_name}""", 'start': researcher_id, 'end': work_name, "label": "authored", "start_type": "AUTHOR", "end_type": "WORK"})
    edges.append({ 'id': f"""{work_name}-{number}""", 'start': work_name, 'end': number, "label": "citedBy", "start_type": "WORK", "end_type": "NUMBER"})
  graph = {"nodes": nodes, "edges": edges}
  return {"metadata": metadata, "graph": graph, "list":list}

@app.route('/autofill-institutions', methods=['POST'])
def autofill_institutions():
  """
  Handles autofill for instituions. Checks what institutions contain the phrase the user has already typed.

  Expects the frontend to pass in the following values:
  institution : what the user has typed into the organization box so far.

  Returns:
  A dictionary containing all the possible searches given what the user has typed.
  """
  inst = request.json.get('institution')
  possible_searches = []
  for i in autofill_inst_list:
    if inst.lower() in i.lower():
      possible_searches.append(i)
  return {"possible_searches": possible_searches}

@app.route('/autofill-topics', methods=['POST'])
def autofill_topics():
  """
  Handles autofill for topics. Checks what topics contain the phrase the user has already typed.
  Only searches if the user has typed in more than 2 characters in order to prevent the entire (large) keyword list from
  being returned.

  Expects the frontend to pass in the following values:
  topic : what the user has typed into the Topic Keyword box so far.

  Returns:
  A dictionary containing all the possible searches given what the user has typed.
  """
  topic = request.json.get('topic')
  possible_searches = []
  if len(topic) > 0:
    if SUBFIELDS:
      for i in autofill_subfields_list:
        if topic.lower() in i.lower():
          possible_searches.append(i)
    else:
      for i in autofill_topics_list:
        if topic.lower() in i.lower():
          possible_searches.append(i)
  return {"possible_searches": possible_searches}

@app.route('/get-default-graph', methods=['POST'])
def get_default_graph():
  """
  Returns the default graph. This is what the user sees if they do not fill in any of the search boxes.
  Loads the graph from the file default.json, which already contains all the necessary data.

  Returns:
  graph : returns a dictionary with one entry, the graph. The graph is in the same form as all others ({"nodes": [], "edges": []})
  """

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
  return {"graph": final_graph}

@app.route('/get-topic-space-default-graph', methods=['POST'])
def get_topic_space():
  """
  Returns the default graph for the topic space. This is what the user sees if they click "explore topics".
  Simply includes the 4 high level domain from OpenAlex.

  Returns:
  graph : returns a dictionary with one entry, the graph. The graph is in the same form as all others ({"nodes": [], "edges": []})
  """

  nodes= [{ "id": 1, 'label': "Physical Sciences", 'type': 'DOMAIN'}, { "id": 2, 'label': "Life Sciences", 'type': 'DOMAIN'}, { "id": 3, 'label': "Social Sciences", 'type': 'DOMAIN'}, { "id": 4, 'label': "Health Sciences", 'type': 'DOMAIN'}]
  edges = []
  graph = {"nodes": nodes, "edges": edges}
  return {"graph": graph}

@app.route('/search-topic-space', methods=['POST'])
def search_topic_space():
  """
  Api call for searches from the user when searching the topic space. Retrieves information from the topic_default.json file,
  which contains the OpenAlex topic space. Returns the result as a graph.

  topic : input from the topic search box.

  Returns:
  graph : the graph for the search in the form {nodes: [], edges: []}
  """

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

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    return send_from_directory(app.static_folder, 'index.html')

## Main 
if __name__ =='__main__':
  app.run()
