
from postgres_queries import search_by_author, search_by_institution, fetch_last_known_institutions, search_by_topic, search_by_institution_topic, search_by_author_topic, search_by_author_institution, search_by_author_institution_topic
from sparql_queries import get_author_metadata_sparql, list_given_researcher_institution, get_institution_metadata_sparql, list_given_institution, get_author_from_id_sparql, get_institution_from_id_sparql, get_institution_and_topic_metadata_sparql, list_given_institution_topic, get_topic_and_researcher_metadata_sparql, list_given_researcher_topic, get_researcher_and_institution_metadata_sparql, get_institution_and_topic_and_researcher_metadata_sparql
"""
This file contains the methods perform each of the primary search types possible within the app.
"""
def get_researcher_result(app, researcher, page=1, per_page=20):
    """
    Gets the results when user only inputs a researcher
    Uses database to get result, defaults to SPARQL if researcher is not in database
    """
    coordinates_metadata = []
    data = search_by_author(app, researcher)
    if data is None:
        app.logger.info("No database results, falling back to SPARQL...")
        data = get_author_metadata_sparql(app, researcher)
        if data == {}:
            app.logger.warning("No results found in SPARQL for researcher")
            return {}
        topic_list, graph = list_given_researcher_institution(app, data['oa_link'], data['name'], data['current_institution'])
        results = {"metadata": data, "graph": graph, "list": topic_list}
        app.logger.info(f"Successfully retrieved SPARQL results for researcher: {researcher}")
        return results

    app.logger.debug("Processing database results for researcher")
    metadata = data['author_metadata']

    metadata['orcid'] = '' if metadata['orcid'] is None else metadata['orcid']
    metadata['work_count'] = metadata.pop('num_of_works')
    metadata['current_institution'] = metadata.pop('last_known_institution')
    metadata['cited_by_count'] = metadata.pop('num_of_citations')
    metadata['oa_link'] = metadata.pop('openalex_url')
    metadata['current_institution'], metadata['institution_url'] = determine_last_known_institution(app, metadata['last_known_institution'], metadata['oa_link'])

    coordinates_metadata.append((metadata['institution_url'], metadata['current_institution'], 1))

    app.logger.debug("Building graph structure")
    
    total_topics = len(data['data'])
    start = (page - 1) * per_page
    end = start + per_page

    list = construct_list(app, data['data'], "topic", "num_of_works", start, end)
    graph = construct_graph(app, list, data['subfield_metadata'], 'topic_display_name', metadata['work_count'], 'SUBFIELD', 'TOPIC', 'has_topic', 50)

    app.logger.info(f"Successfully built result for researcher: {researcher}")
    return {
        "metadata": metadata,
        "metadata_pagination": {
            "total_pages": (total_topics + per_page - 1) // per_page,
            "current_page": page,
            "total_topics": total_topics,
        },
        "graph": graph, 
        "list": list, 
        "coordinates": coordinates_metadata
    }

def construct_list(app, data, item_name, count_name, start, end):
    list = []
    for entry in data[start:end]:
        item = entry[item_name]
        count = entry[count_name]
        list.append((item, count))
    app.logger.info(f"Successfully built list.")
    return list

def construct_graph(app, list, destination_data, destination_name, total_count, source_type, destination_type, edge_label, scale_factor):
    nodes = []
    edges = []
    for entry in list:
        source = entry[0]
        count = entry[1]
        nodes.append({'id': source, 'label': source, 'type': source_type, 'size': (count / total_count) * scale_factor })
        for destination in destination_data[source]:
            nodes.append({'id': destination[destination_name], 'label': destination['destination_name'], 'type': destination_type})
            edges.append({ 'id': f"""{source}-{destination[destination_name]}""", 'start': source, 'end': destination[destination_name], "label": edge_label, "start_type": source_type, "end_type": destination_type})
    graph = {"nodes": nodes, "edges": edges}
    app.logger.info(f"Successfully built graph.")
    return graph

def construct_simple_graph(app, list, source_node_id, source_node_type, source_type, total_count, scale_factor, edge_label):
    nodes = []
    edges = []
    nodes.append({ 'id': source_node_id, 'label': source_node_id, 'type': source_node_type })
    for entry in list:
        source = entry[0]
        count = entry[1]
        nodes.append({'id': source, 'label': source, 'type': source_type, 'size': (count / total_count) * scale_factor })
        edges.append({ 'id': f"""{source}-{source_node_id}""", 'start': source, 'end': source_node_id, "label": edge_label, "start_type": source_type, "end_type": source_node_type})
    graph = {"nodes": nodes, "edges": edges}
    app.logger.info(f"Successfully built graph.")
    return graph

def determine_last_known_institution(app, last_known_institution, oa_link):
    """
    Determines the last known institution if the metadata does not contain one
    """
    if last_known_institution is None:
        app.logger.debug("Fetching last known institutions from OpenAlex")
        institution_object = fetch_last_known_institutions(app, oa_link)
        if institution_object == []:
            app.logger.warning("No last known institution found")
            last_known_institution = ""
        else:
            institution_object = institution_object[0]
            last_known_institution = institution_object['display_name']
            institution_url = institution_object['id']
    else:
        institution_url = ""
    return last_known_institution, institution_url

def get_institution_results(app, institution, page=1, per_page=10):
    """
    Gets the results when user only inputs an institution
    Uses database to get result, defaults to SPARQL if institution is not in database
    """
    coordinates_metadata = []
    data = search_by_institution(app, institution)
    if data is None:
        app.logger.info("No database results, falling back to SPARQL...")
        data = get_institution_metadata_sparql(app, institution)
        if data == {}:
            app.logger.warning("No results found in SPARQL for institution")
            return {}
        topic_list, graph = list_given_institution(app, data['ror'], data['name'], data['oa_link'])
        results = {"metadata": data, "graph": graph, "list": topic_list}
        app.logger.info(f"Successfully retrieved SPARQL results for institution: {institution}")
        return results
    
    app.logger.debug("Processing database results for institution")
    metadata = data['institution_metadata']

    metadata['homepage'] = metadata.pop('url')
    metadata['works_count'] = metadata.pop('num_of_works')
    metadata['name'] = metadata.pop('institution_name')
    metadata['cited_count'] = metadata.pop('num_of_citations')
    metadata['oa_link'] = metadata.pop('openalex_url')
    metadata['author_count'] = metadata.pop('num_of_authors')

    coordinates_metadata.append((metadata['oa_link'], institution, metadata['author_count']))
    
    app.logger.debug("Building graph structure")

    total_topics = len(data['data'])
    start = (page - 1) * per_page
    end = start + per_page

    list = construct_list(app, data['data'], 'topic_subfield', 'num_of_authors', start, end)
    graph = construct_graph(app, list, data['subfield_metadata'], 'topic_display_name', metadata['author_count'], "SUBFIELD", "TOPIC", "has_topic", 100)

    app.logger.info(f"Successfully built result for institution: {institution}")
    return {
        "metadata": metadata,
        "metadata_pagination": {
            "total_pages": (total_topics + per_page - 1) // per_page,
            "current_page": page,
            "total_topics": total_topics,
        },
        "extra_metadata": {},
        "graph": graph,
        "list": list,
        "coordinates": coordinates_metadata
    }

def get_subfield_results(app, topic, page=1, per_page=20, map_limit=100):
    """
    Gets the results when user only inputs a subfield
    Uses database to get result (database contains all topics)
    """
    coordinates_metadata = []
    data = search_by_topic(app, topic)
    if data is None:
        app.logger.warning(f"No results found for topic: {topic}")
        return {"metadata": None, "graph": None, "list": None}

    app.logger.debug("Processing database results for topic")
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
    metadata['name'] = topic.title()

    app.logger.debug("Building graph structure")

    total_topics = len(data['data'])
    start = (page - 1) * per_page
    end = start + per_page

    list = construct_list(app, data['data'], 'institution_name', 'num_of_authors', start, end)
    graph = construct_simple_graph(app, list, topic, 'SUBFIELD', 'INSTITUTION', metadata['researchers'], 100, 'Researches')
    
    for entry in data['data'][:map_limit]:
        institution = entry['institution_name']
        number = entry['num_of_authors']
        oa_link = entry['institution_id']
        coordinates_metadata.append((oa_link, institution, number))

    app.logger.info(f"Successfully built result for topic: {topic}")
    return {"metadata": metadata, 
            "metadata_pagination": {
            "total_pages": (total_topics + per_page - 1) // per_page,
            "current_page": page,
            "total_topics": total_topics,
        }, "graph": graph, "list": list, "coordinates": coordinates_metadata}

def get_multiple_researcher_results(app, researchers, page=1, per_page=19):
    """
    Gets the results when user inputs a csv file containing multiple institution OpenAlex IDs
    Uses database to get result, defaults to SPARQL if institution is not in database
    """
    metadata = {}
    nodes = []
    edges = []
    final_metadata = {}
    coordinates_metadata = []
    for researcher in researchers:
        data = search_by_author("", "https://openalex.org/" + researcher)
        if data is None:
            app.logger.info("No database results, falling back to SPARQL...")
            researcher = get_author_from_id_sparql(app, researcher)
            data = get_author_metadata_sparql(app, researcher)
            if data == {}:
                app.logger.warning("No results found in SPARQL for researcher")
                return {}
            else:
                metadata[researcher] = data
                found = False
                for c in coordinates_metadata:
                    if c[0] == metadata[researcher]['institution_url']:
                        c[2] += 1
                        found = True
                        break
                if not found:
                    coordinates = (metadata[researcher]['institution_url'], metadata[researcher]['current_institution'], 1)
                    coordinates_metadata.append(coordinates)
                topic_list, g = list_given_researcher_institution(app, data['oa_link'], data['name'], data['current_institution'])
                nodes.append({'id': researcher, 'label': researcher, 'type': "AUTHOR" })
                for subfield, count in topic_list:
                    nodes.append({'id': subfield, 'label': subfield, 'type': "SUBFIELD" })
                    edges.append({ 'id': f"""{researcher}-{subfield}""", 'start': researcher, 'end': subfield, "label": "researches", "start_type": "RESEARCHER", "end_type": "SUBFIELD"})
                app.logger.info(f"Successfully retrieved SPARQL results for researcher: {researcher}")
        else:
            app.logger.debug("Processing database results for researcher")
            topic_list = []
            researcher = data['author_metadata']['name']
            metadata[researcher] = data['author_metadata']
            if metadata[researcher]['orcid'] is None:
                metadata[researcher]['orcid'] = ''
            metadata[researcher]['work_count'] = metadata[researcher]['num_of_works']
            metadata[researcher]['cited_by_count'] = metadata[researcher]['num_of_citations']
            metadata[researcher]['oa_link'] = metadata[researcher]['openalex_url']
            if metadata[researcher]['last_known_institution'] is None:
                app.logger.debug("Fetching last known institutions from OpenAlex")
                institution_object = fetch_last_known_institutions(app, metadata[researcher]['oa_link'])
                if institution_object == []:
                    app.logger.warning("No last known institution found")
                    last_known_institution = ""
                else:
                    institution_object = institution_object[0]
                    last_known_institution = institution_object['display_name']
                    institution_url = institution_object['id']
            else:
                last_known_institution = metadata[researcher]['last_known_institution']
            metadata[researcher]['current_institution'] = last_known_institution
            metadata[researcher]['institution_url'] = institution_url
            
            found = False
            for c in coordinates_metadata:
                if c[0] == metadata[researcher]['institution_url']:
                    c[2] += 1
                    found = True
                    break
            if not found:
                coordinates = (metadata[researcher]['institution_url'], metadata[researcher]['current_institution'], 1)
                coordinates_metadata.append(coordinates)
            
            app.logger.debug("Building graph structure")
            total_topics = len(data['data'])
            start = (page - 1) * per_page
            end = start + per_page
            nodes.append({'id': researcher, 'label': researcher, 'type': "AUTHOR" })
            for entry in data['data'][start:end]:
                subfield = entry['topic']
                number = entry['num_of_works']
                topic_list.append((subfield, number))
                nodes.append({'id': subfield, 'label': subfield, 'type': "SUBFIELD" })
                edges.append({ 'id': f"""{researcher}-{subfield}""", 'start': researcher, 'end': subfield, "label": "researches", "start_type": "AUTHOR", "end_type": "SUBFIELD"})
            app.logger.info(f"Successfully built result for researcher: {researcher}")
        final_metadata[researcher] = {}
        final_metadata[researcher]['researcher_name'] = metadata[researcher]['name']
        final_metadata[researcher]['orcid_link'] = metadata[researcher]['orcid']
        final_metadata[researcher]['works_count'] = metadata[researcher]['work_count']
        final_metadata[researcher]['open_alex_link'] = metadata[researcher]['oa_link']
        final_metadata[researcher]['cited_count'] = metadata[researcher]['cited_by_count']
        final_metadata[researcher]['institution_name'] = metadata[researcher]['current_institution']
        final_metadata[researcher]['institution_url'] = metadata[researcher]['institution_url']
        final_metadata[researcher]['topics'] = topic_list
    graph = {"nodes": nodes, "edges": edges}
    return {
        "metadata": final_metadata,
        "extra_metadata": final_metadata,
        "metadata_pagination": {
            "total_pages": (total_topics + per_page - 1) // per_page,
            "current_page": page,
            "total_topics": total_topics,
        },
        "graph": graph,
        "list": [],
        "coordinates": coordinates_metadata
    }

def get_multiple_institution_results(app, institutions, page=1, per_page=19, ids=False):
    metadata = {}
    nodes = []
    edges = []
    final_metadata = {}
    coordinates_metadata = []
    for institution in institutions:
        list = []
        if ids:
            data = search_by_institution(app, "", "https://openalex.org/" + institution.upper())
        else:
            data = search_by_institution(app, institution)
        if data is None:
            app.logger.info("No database results, falling back to SPARQL...")
            if ids:
                institution = get_institution_from_id_sparql(app, institution)
            data = get_institution_metadata_sparql(app, institution)
            if data == {}:
                app.logger.warning("No results found in SPARQL for institution")
            else:
                metadata[institution] = data
                metadata[institution]['homepage'] = data['homepage']
                metadata[institution]['works_count'] = data['works_count']
                metadata[institution]['name'] = data['name']
                metadata[institution]['cited_count'] = data['cited_count']
                metadata[institution]['oa_link'] = data['oa_link']
                metadata[institution]['author_count'] = data['author_count']
                topic_list, g = list_given_institution(app, data['ror'], data['name'], data['oa_link'])
                nodes.append({'id': institution, 'label': institution, 'type': "INSTITUTION" })
                coordinates_metadata.append((metadata[institution]['oa_link'], institution, metadata[institution]['author_count']))
                for subfield, count in topic_list:
                    nodes.append({'id': subfield, 'label': subfield, 'type': "SUBFIELD" })
                    edges.append({ 'id': f"""{institution}-{subfield}""", 'start': institution, 'end': subfield, "label": "researches", "start_type": "INSTITUTION", "end_type": "SUBFIELD"})
                app.logger.info(f"Successfully retrieved SPARQL results for institution: {institution}")
        else:
            app.logger.debug("Processing database results for institution")
            if ids:
                institution = data['institution_metadata']['institution_name']
            metadata[institution] = data['institution_metadata']
            metadata[institution]['homepage'] = metadata[institution]['url']
            metadata[institution]['works_count'] = metadata[institution]['num_of_works']
            metadata[institution]['name'] = metadata[institution]['institution_name']
            metadata[institution]['cited_count'] = metadata[institution]['num_of_citations']
            metadata[institution]['oa_link'] = metadata[institution]['openalex_url']
            metadata[institution]['author_count'] = metadata[institution]['num_of_authors']
            coordinates_metadata.append((metadata[institution]['oa_link'], institution, metadata[institution]['author_count']))

            app.logger.debug("Building graph structure")
            # institution_id = metadata['openalex_url']

            total_topics = len(data['data'])
            start = (page - 1) * per_page
            end = start + per_page
            nodes.append({'id': institution, 'label': institution, 'type': "INSTITUTION" })
            for entry in data['data'][start:end]:
                subfield = entry['topic_subfield']
                number = entry['num_of_authors']
                list.append((subfield, number))
                nodes.append({'id': subfield, 'label': subfield, 'type': "SUBFIELD" })
                edges.append({ 'id': f"""{institution}-{subfield}""", 'start': institution, 'end': subfield, "label": "researches", "start_type": "INSTITUTION", "end_type": "SUBFIELD"})
            app.logger.info(f"Successfully built result for institution: {institution}")
        final_metadata[institution] = {}
        final_metadata[institution]["institution_name"] = metadata[institution]['name']
        final_metadata[institution]["cited_count"] = metadata[institution]['cited_count']
        final_metadata[institution]["author_count"] = metadata[institution]['author_count']
        final_metadata[institution]["works_count"] = metadata[institution]['works_count']
        final_metadata[institution]["institution_url"] = metadata[institution]['homepage']
        final_metadata[institution]["open_alex_link"] = metadata[institution]['oa_link']
        final_metadata[institution]["ror_link"] = metadata[institution]['ror']
        final_metadata[institution]["topics"] = list
    graph = {"nodes": nodes, "edges": edges}
    return {
        "metadata": metadata,
        "extra_metadata": final_metadata,
        "metadata_pagination": {
            "total_pages": (total_topics + per_page - 1) // per_page,
            "current_page": page,
            "total_topics": total_topics,
        },
        "graph": graph,
        "list": [],
        "coordinates": coordinates_metadata
    }

def get_institution_and_subfield_results(app, institution, topic, page=1, per_page=20):
    """
    Gets the results when user inputs an institution and subfield
    Uses database to get result, defaults to SPARQL if institution is not in database
    """
    data = search_by_institution_topic(app, institution, topic)
    if data is None:
        app.logger.info("Using SPARQL for institution and topic search...")
        data = get_institution_and_topic_metadata_sparql(app, institution, topic)
        if data == {}:
            app.logger.warning("No results found in SPARQL for institution and topic")
            return {}
        topic_list, graph, extra_metadata = list_given_institution_topic(app, institution, data['institution_oa_link'], topic, data['topic_oa_link'])
        data['work_count'] = extra_metadata['work_count']
        data['people_count'] = extra_metadata['num_people']
        results = {"metadata": data, "graph": graph, "list": topic_list}
        app.logger.info(f"Successfully retrieved SPARQL results for institution: {institution} and topic: {topic}")
        return results

    app.logger.debug("Processing database results for institution and topic")
    metadata = {}

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
    metadata['topic_name'] = topic

    metadata['homepage'] = data['institution_metadata']['url']
    metadata['institution_oa_link'] = data['institution_metadata']['openalex_url']
    metadata['ror'] = data['institution_metadata']['ror']
    metadata['institution_name'] = institution

    app.logger.debug("Building graph structure")

    total_topics = len(data['data'])
    metadata['people_count'] = total_topics
    start = (page - 1) * per_page
    end = start + per_page
    
    list = construct_list(app, data['data'], 'author_name', 'num_of_works', start, end)
    graph = construct_simple_graph(app, list, institution, 'INSTITUTION', 'AUTHOR', metadata['work_count'], 10, 'Authored')
    graph['nodes'].append({ 'id': topic, 'label': topic, 'type': 'TOPIC' })
    graph['edges'].append({ 'id': f"""{institution}-{topic}""", 'start': institution, 'end': topic, "label": "Researches", "start_type": "INSTITUTION", "end_type": "SUBFIELD"})

    app.logger.info(f"Successfully built result for institution: {institution} and topic: {topic}")
    return {
        "metadata": metadata,
        "metadata_pagination": {
            "total_pages": (total_topics + per_page - 1) // per_page,
            "current_page": page,
            "total_topics": total_topics,
        },
        "graph": graph,
        "list": list
    }

def get_multiple_institution_and_subfield_results(app, institution, topic, page, per_page):
    new_list = []
    nodes = []
    edges = []
    first = True
    for inst in institution:
        nodes.append({ 'id': inst, 'label': inst, 'type': 'INSTITUTION' })
        res = get_institution_and_subfield_results(app, inst, topic, page, per_page)
        for t in res['metadata']['topic_clusters']:
            nodes.append({ 'id': t, 'label': t, 'type': 'TOPIC'})
            edges.append({ 'id': f"""{inst}-{t}""", 'start': inst, 'end': t, "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})
        new_list.append((inst, res['metadata']['people_count']))
        if first:
            results = res
            first = False
    results['graph'] = {"nodes": nodes, "edges": edges}
    results['list'] = new_list
    return results

def get_researcher_and_subfield_results(app, researcher, topic, page=1, per_page=20):
    """
    Gets the results when user inputs a researcher and subfield
    Uses database to get result, defaults to SPARQL if researcher is not in database
    """
    data = search_by_author_topic(app, researcher, topic)
    if data is None:
        app.logger.info("No database results, falling back to SPARQL...")
        data = get_topic_and_researcher_metadata_sparql(app, topic, researcher)
        if data == {}:
            app.logger.warning("No results found in SPARQL for researcher and topic")
            return {}
        work_list, graph, extra_metadata = list_given_researcher_topic(app, topic, researcher, data['current_institution'], data['topic_oa_link'], data['researcher_oa_link'], data['institution_oa_link'])
        data['work_count'] = extra_metadata['work_count']
        data['cited_by_count'] = extra_metadata['cited_by_count']
        results = {"metadata": data, "graph": graph, "list": work_list}
        app.logger.info(f"Successfully retrieved SPARQL results for researcher: {researcher} and topic: {topic}")
        return results

    app.logger.debug("Processing database results for researcher and topic")
    metadata = {}
    
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

    metadata['orcid'] = '' if data['author_metadata']['orcid'] is None else data['author_metadata']['orcid']
    metadata['researcher_name'] = researcher
    metadata['researcher_oa_link'] = data['author_metadata']['openalex_url']
    metadata['current_institution'], metadata['institution_url'] = determine_last_known_institution(app, data['author_metadata']['last_known_institution'], metadata['researcher_oa_link'])

    app.logger.debug("Building graph structure")

    total_topics = len(data['data'])
    start = (page - 1) * per_page
    end = start + per_page

    list = construct_list(app, data['data'], 'work_name', 'num_of_citations', start, end)
    graph = construct_simple_graph(app, list, researcher, 'AUTHOR', 'WORK', metadata['work_count'], 10, 'Authored')
    graph['nodes'].append({ 'id': metadata['current_institution'], 'label': metadata['current_institution'], 'type': 'INSTITUTION' })
    graph['nodes'].append({ 'id': topic, 'label': topic, 'type': 'TOPIC' })
    graph['edges'].append({ 'id': f"""{researcher}-{metadata['current_institution']}""", 'start': researcher, 'end': metadata['current_institution'], "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
    graph['edges'].append({ 'id': f"""{researcher}-{topic}""", 'start': researcher, 'end': topic, "label": "Researches", "start_type": "AUTHOR", "end_type": "SUBFIELD"})

    app.logger.info(f"Successfully built result for researcher: {researcher} and topic: {topic}")
    return {"metadata": metadata, 
            "metadata_pagination": {
            "total_pages": (total_topics + per_page - 1) // per_page,
            "current_page": page,
            "total_topics": total_topics,
        }, "graph": graph, "list": list}

def get_institution_and_researcher_results(app, institution, researcher, page=1, per_page=20):
    """
    Gets the results when user inputs an institution and researcher
    Uses database to get result, defaults to SPARQL if institution or researcher is not in database
    """
    data = search_by_author_institution(app, researcher, institution)
    if data is None:
        app.logger.info("Using SPARQL for institution and researcher search...")
        data = get_researcher_and_institution_metadata_sparql(app, researcher, institution)
        if data == {}:
            app.logger.warning("No results found in SPARQL for institution and researcher")
            return {}
        topic_list, graph = list_given_researcher_institution(app, data['researcher_oa_link'], researcher, institution)
        results = {"metadata": data, "graph": graph, "list": topic_list}
        app.logger.info(f"Successfully retrieved SPARQL results for researcher: {researcher} and institution: {institution}")
        return results
    
    app.logger.debug("Processing database results for institution and researcher")
    metadata = {}

    metadata['homepage'] = data['institution_metadata']['url']
    metadata['institution_oa_link'] = data['institution_metadata']['openalex_url']
    metadata['ror'] = data['institution_metadata']['ror']
    metadata['institution_name'] = institution

    metadata['orcid'] = '' if data['author_metadata']['orcid'] is None else data['author_metadata']['orcid']
    metadata['researcher_name'] = researcher
    metadata['researcher_oa_link'] = data['author_metadata']['openalex_url']
    metadata['current_institution'], metadata['institution_url'] = determine_last_known_institution(app, data['author_metadata']['last_known_institution'], metadata['researcher_oa_link'])
    metadata['work_count'] = data['author_metadata']['num_of_works']
    metadata['cited_by_count'] = data['author_metadata']['num_of_citations']

    app.logger.debug("Building graph structure")
    
    total_topics = len(data['data'])
    start = (page - 1) * per_page
    end = start + per_page

    list = construct_list(app, data['data'], 'topic_name', 'num_of_works', start, end)
    graph = construct_graph(app, list, data['subfield_metadata'], 'topic_display_name', metadata['work_count'], 'SUBFIELD', 'TOPIC', 'has_topic', 100)

    app.logger.info(f"Successfully built result for researcher: {researcher} and institution: {institution}")
    return {"metadata": metadata,
            "metadata_pagination": {
            "total_pages": (total_topics + per_page - 1) // per_page,
            "current_page": page,
            "total_topics": total_topics,
        }, "graph": graph, "list": list}

def get_institution_researcher_subfield_results(app, institution, researcher, 
                                                topic, page=1, per_page=20):
    """
    Gets the results when user inputs an institution, researcher, and subfield
    Uses database to get result, defaults to SPARQL if institution or researcher is not in database
    """
    data = search_by_author_institution_topic(app, researcher, institution, topic)
    if data is None:
        app.logger.info("Using SPARQL for institution, researcher, and topic search...")
        data = get_institution_and_topic_and_researcher_metadata_sparql(app, institution, topic, researcher)
        if data == {}:
            app.logger.warning("No results found in SPARQL for institution, researcher, and topic")
            return {}
        work_list, graph, extra_metadata = list_given_researcher_topic(topic, researcher, institution, data['topic_oa_link'], data['researcher_oa_link'], data['institution_oa_link'])
        data['work_count'] = extra_metadata['work_count']
        data['cited_by_count'] = extra_metadata['cited_by_count']
        results = {"metadata": data, "graph": graph, "list": work_list}
        app.logger.info(f"Successfully retrieved SPARQL results for researcher: {researcher}, institution: {institution}, and topic: {topic}")
        return results

    app.logger.debug("Processing database results for institution, researcher, and topic")
    metadata = {}

    metadata['homepage'] = data['institution_metadata']['url']
    metadata['institution_oa_link'] = data['institution_metadata']['openalex_url']
    metadata['ror'] = data['institution_metadata']['ror']
    metadata['institution_name'] = institution

    metadata['orcid'] = '' if data['author_metadata']['orcid'] is None else data['author_metadata']['orcid']
    metadata['researcher_name'] = researcher
    metadata['researcher_oa_link'] = data['author_metadata']['openalex_url']
    metadata['current_institution'], metadata['institution_url'] = determine_last_known_institution(app, data['author_metadata']['last_known_institution'], metadata['researcher_oa_link'])

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

    app.logger.debug("Building graph structure")

    total_topics = len(data['data'])
    start = (page - 1) * per_page
    end = start + per_page

    list = construct_list(app, data['data'], 'work_name', 'cited_by_count', start, end)
    graph = construct_simple_graph(app, list, researcher, 'AUTHOR', 'WORK', metadata['cited_by_count'], 10, 'Authored')
    graph['nodes'].append({ 'id': institution, 'label': institution, 'type': 'INSTITUTION' })
    graph['nodes'].append({ 'id': topic, 'label': topic, 'type': 'TOPIC' })
    graph['edges'].append({ 'id': f"""{researcher}-{institution}""", 'start': researcher, 'end': institution, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
    graph['edges'].append({ 'id': f"""{researcher}-{topic}""", 'start': researcher, 'end': topic, "label": "researches", "start_type": "AUTHOR", "end_type": "SUBFIELD"})
    
    app.logger.info(f"Successfully built result for researcher: {researcher}, institution: {institution}, and topic: {topic}")

    return {"metadata": metadata, 
            "metadata_pagination": {
            "total_pages": (total_topics + per_page - 1) // per_page,
            "current_page": page,
            "total_topics": total_topics,
        }, "graph": graph, "list": list}

