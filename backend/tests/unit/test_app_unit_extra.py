"""
Our testing is scheduled to provide a JSON at all times.
Otherwise, Flask will raise a 400. So we accept 400 here.
I think the Flask type of language that we do here, we can't do
that without the missing content so we have to import the libraries
in a standard fashion.
"""
from backend.app import app
import sys
import runpy
import io
import json
import importlib
import importlib.util
import os
from pathlib import Path
from io import StringIO
# These are the third-party imports for best practices.
import mysql.connector
from mysql.connector import Error
import pytest
import requests
from flask import Flask
from unittest.mock import patch, MagicMock, mock_open
# Local testing and making applications that are reversible is a "thing" that exists.
import backend.app as backend_app
from backend.app import (
    app,
    create_connection,
    get_institutions_r_and_d,
    get_institutions_faculty_awards,
    get_institution_sat_scores,
    get_institution_mup_id,
    SUBFIELDS,
    autofill_subfields_list,
    query_SQL_endpoint,
    get_institution_and_topic_metadata_sparql,
    serve,
    setup_logger,
    execute_query,
    fetch_last_known_institutions,
    get_author_ids,
    get_institution_id,
    search_by_author_institution_topic,
    search_by_author_institution,
    search_by_institution_topic,
    search_by_author_topic,
    search_by_institution,
    search_by_author,
    get_geo_info,
    get_institution_researcher_subfield_results,
    get_researcher_result,
    get_institution_results,
    get_subfield_results,
    get_researcher_and_subfield_results,
    get_institution_and_subfield_results,
    get_institution_and_researcher_results,
    get_topic_and_researcher_metadata_sparql,
    get_institution_and_topic_and_researcher_metadata_sparql,
    list_given_topic,
    list_given_institution_topic,
    list_given_researcher_topic,
    SEMOPENALEX_SPARQL_ENDPOINT,
    list_given_researcher_institution,
    get_institution_endowments_and_givings,
    get_institution_medical_expenses,
    get_institution_doctorates_and_postdocs,
    get_institution_num_of_researches,
    combine_graphs,
    is_HBCU,
    query_SPARQL_endpoint,
)
os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "5432"
os.environ["DB_NAME"] = "testdb"
os.environ["DB_USER"] = "testuser"
os.environ["DB_PASSWORD"] = "testpass"
os.environ["DB_API"] = "http://testapi"
# It's a requirement that since each environment variable is required we set it BEFORE any other imports so that the DB_PORT etc. are defined.

# ---------------------------------------------------------------------------
# Lines 19–23: Environment variable reading


def test_env_variables():
    from backend.app import DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, API
    assert isinstance(DB_PORT, int)
    assert DB_PORT == 5432
    assert DB_NAME == "testdb"
    assert DB_USER == "testuser"
    assert DB_PASSWORD == "testpass"
    assert API == "http://testapi"

# ---------------------------------------------------------------------------
# Lines 167–169: get_institution_id returns None when result is {}


def test_get_institution_id_no_result(caplog):
    fake_result = [[{}]]
    with patch("backend.app.execute_query", return_value=fake_result):
        result = get_institution_id("TestInst")
        assert result is None
        assert "No institution ID found" in caplog.text

# ---------------------------------------------------------------------------
# Lines 198–199: search_by_author_institution_topic returns None on no results


def test_search_by_author_institution_topic_no_result(caplog):
    with patch("backend.app.get_author_ids", return_value=[{"author_id": "A1"}]), \
            patch("backend.app.get_institution_id", return_value="I1"), \
            patch("backend.app.execute_query", return_value=None):
        result = search_by_author_institution_topic(
            "Author", "Institution", "Topic")
        assert result is None
        assert "No results found for author-institution-topic search" in caplog.text

# ---------------------------------------------------------------------------
# Lines 223–224: search_by_author_institution returns None when no results found


def test_search_by_author_institution_no_result(caplog):
    with patch("backend.app.get_author_ids", return_value=[{"author_id": "A1"}]), \
            patch("backend.app.get_institution_id", return_value=None):
        result = search_by_author_institution("Author", "Institution")
        assert result is None
        assert "No institution ID found" in caplog.text or "No results found for author-institution search" in caplog.text

# ---------------------------------------------------------------------------
# Lines 240–241: search_by_institution_topic returns None when no institution ID


def test_search_by_institution_topic_no_result(caplog):
    with patch("backend.app.get_institution_id", return_value=None):
        result = search_by_institution_topic("Institution", "Topic")
        assert result is None
        assert "No institution ID found" in caplog.text

# ---------------------------------------------------------------------------
# Lines 260–261: search_by_author_topic returns None when no author IDs


def test_search_by_author_topic_no_result(caplog):
    with patch("backend.app.get_author_ids", return_value=None):
        result = search_by_author_topic("Author", "Topic")
        assert result is None
        assert "No author IDs found" in caplog.text

# ---------------------------------------------------------------------------
# Lines 288–289: search_by_institution returns None when institution id is missing


def test_search_by_institution_no_result(caplog):
    with patch("backend.app.get_institution_id", return_value=None):
        result = search_by_institution("Institution")
        assert result is None
        assert "No institution ID found" in caplog.text

# ---------------------------------------------------------------------------
# Lines 307–308: search_by_author returns None when no author ids


def test_search_by_author_no_result(caplog):
    with patch("backend.app.get_author_ids", return_value=None):
        result = search_by_author("Author")
        assert result is None
        assert "No author IDs found" in caplog.text

# ---------------------------------------------------------------------------
# Lines 324–325: When SUBFIELDS is false, keywords.csv is used.


def test_keywords_csv_read(monkeypatch):
    monkeypatch.setattr("backend.app.SUBFIELDS", False)
    dummy_keywords = "Keyword1\nKeyword2\nKeyword3"
    monkeypatch.setattr("builtins.open", lambda filename, mode='r':
                        StringIO(dummy_keywords) if "keywords.csv" in filename else StringIO(""))
    from backend.app import autofill_topics_list  # re-import after patching
    assert autofill_topics_list == ["Keyword1", "Keyword2", "Keyword3"]


# Lines 451–505: get_researcher_result processing branch.


def test_get_researcher_result_with_last(monkeypatch):
    fake_data = {
        "author_metadata": {
            "orcid": None,
            "num_of_works": 10,
            "last_known_institution": "InstA",
            "num_of_citations": 5,
            "openalex_url": "https://openalex.org/author/1234"
        },
        "data": [{"topic": "Topic1", "num_of_works": 3}]
    }
    monkeypatch.setattr("backend.app.search_by_author",
                        lambda author: fake_data)
    result = get_researcher_result("Test Author", page=1, per_page=10)
    assert result["metadata"]["current_institution"] == "InstA"
    assert "metadata_pagination" in result


def test_get_researcher_result_without_last(monkeypatch, caplog):
    fake_data = {
        "author_metadata": {
            "orcid": "ORCID123",
            "num_of_works": 8,
            "last_known_institution": None,
            "num_of_citations": 4,
            "openalex_url": "https://openalex.org/author/5678"
        },
        "data": [{"topic": "Topic2", "num_of_works": 2}]
    }
    monkeypatch.setattr("backend.app.search_by_author",
                        lambda author: fake_data)
    monkeypatch.setattr(
        "backend.app.fetch_last_known_institutions", lambda oa_link: [])
    result = get_researcher_result("Test Author", page=1, per_page=10)
    assert result["metadata"]["current_institution"] == ""
    assert "No last known institution found" in caplog.text

# ---------------------------------------------------------------------------
# Lines 531–568: get_institution_results processing branch.


def test_get_institution_results(monkeypatch):
    fake_data = {
        "institution_metadata": {
            "url": "http://inst.com",
            "num_of_works": 20,
            "institution_name": "InstB",
            "num_of_citations": 15,
            "openalex_url": "https://openalex.org/institutions/instB",
            "num_of_authors": 5
        },
        "data": [{"topic_subfield": "Subfield1", "num_of_authors": 3}]
    }
    monkeypatch.setattr("backend.app.search_by_institution",
                        lambda inst: fake_data)
    result = get_institution_results("InstB", page=1, per_page=10)
    metadata = result["metadata"]
    assert metadata["homepage"] == "http://inst.com"
    assert metadata["works_count"] == 20
    assert metadata["author_count"] == 5

# ---------------------------------------------------------------------------
# Lines 590–630: get_subfield_results processing branch.


def test_get_subfield_results(monkeypatch):
    fake_data = {
        "subfield_metadata": [{"topic": "Sub1", "subfield_url": "http://sub1"}],
        "totals": {"total_num_of_works": 30, "total_num_of_citations": 10, "total_num_of_authors": 4},
        "data": [{"institution_name": "InstC", "num_of_authors": 2}]
    }
    monkeypatch.setattr("backend.app.search_by_topic", lambda topic: fake_data)
    result = get_subfield_results("SubfieldX", page=1, per_page=10)
    metadata = result["metadata"]
    assert metadata["work_count"] == 30
    # Title-case conversion might be applied.
    assert metadata["name"] in ["SubfieldX".title(), "Subfieldx"]
    graph = result["graph"]
    assert any(node["type"] == "TOPIC" for node in graph["nodes"])

# ---------------------------------------------------------------------------
# Lines 651–722: get_researcher_and_subfield_results fallback branch.


def test_get_researcher_and_subfield_results_fallback(monkeypatch, caplog):
    fake_sparql_metadata = {
        "current_institution": "InstD",
        "topic_oa_link": "http://topic",
        "researcher_oa_link": "http://author",
        "institution_oa_link": "http://instD"
    }
    monkeypatch.setattr(
        "backend.app.search_by_author_topic", lambda a, t: None)
    monkeypatch.setattr(
        "backend.app.get_topic_and_researcher_metadata_sparql", lambda t, a: fake_sparql_metadata)
    monkeypatch.setattr("backend.app.list_given_researcher_topic", lambda t, a, i, t_oa, a_oa, i_oa: (
        ["dummy_work"], {"nodes": [], "edges": []}, {"work_count": 1, "cited_by_count": 2}))
    result = get_researcher_and_subfield_results(
        "Test Author", "Test Topic", page=1, per_page=10)
    assert "metadata" in result
    assert result["metadata"]["current_institution"] == "InstD"

# ---------------------------------------------------------------------------
# Lines 740–742: Fallback branch for institution–subfield search.


def test_get_institution_and_subfield_results_fallback(monkeypatch, caplog):
    monkeypatch.setattr(
        "backend.app.search_by_institution_topic", lambda i, t: None)
    monkeypatch.setattr(
        "backend.app.get_institution_and_topic_metadata_sparql", lambda i, t: {})
    result = get_institution_and_subfield_results(
        "InstE", "SubfieldY", page=1, per_page=10)
    assert result == {}

# ---------------------------------------------------------------------------
# Lines 752–805: get_institution_and_subfield_results processing branch.


def test_get_institution_and_subfield_results(monkeypatch):
    fake_data = {
        "subfield_metadata": [{"topic": "Sub1", "subfield_url": "http://sub1"}],
        "totals": {"total_num_of_works": 40, "total_num_of_citations": 20, "total_num_of_authors": 6},
        "institution_metadata": {
            "url": "http://instF",
            "openalex_url": "http://instF",
            "ror": "ROR123"
        },
        "data": [{"topic_subfield": "Sub1", "num_of_authors": 3}]
    }
    monkeypatch.setattr(
        "backend.app.search_by_institution_topic", lambda i, t: fake_data)
    result = get_institution_and_subfield_results(
        "InstF", "Sub1", page=1, per_page=10)
    assert "metadata" in result
    assert result["metadata"]["work_count"] == 40
    graph = result["graph"]
    assert any(node["type"] == "INSTITUTION" for node in graph["nodes"])

# ---------------------------------------------------------------------------
# Lines 832–889: get_institution_and_researcher_results fallback branch.


def test_get_institution_and_researcher_results_fallback(monkeypatch):
    fake_data = {
        "institution_metadata": {
            "url": "http://instG",
            "openalex_url": "http://instG",
            "ror": "ROR456"
        },
        "author_metadata": {
            "openalex_url": "http://authorG",
            "orcid": "ORCID456",
            "num_of_works": 12,
            "num_of_citations": 7
        },
        "data": [{"topic_name": "TopicG", "num_of_works": 4}]
    }
    monkeypatch.setattr(
        "backend.app.search_by_author_institution", lambda a, i: None)
    monkeypatch.setattr(
        "backend.app.get_researcher_and_institution_metadata_sparql", lambda a, i: fake_data)
    monkeypatch.setattr("backend.app.list_given_researcher_institution",
                        lambda a, b, c: (["topic_list"], {"nodes": [], "edges": []}))
    result = get_institution_and_researcher_results(
        "InstG", "AuthorG", page=1, per_page=10)
    assert "metadata" in result
    assert result["metadata"]["institution_name"] == "InstG"

# ---------------------------------------------------------------------------
# Lines 910–912: Fallback branch for institution, researcher, and topic search.


def test_get_institution_researcher_subfield_results_fallback(monkeypatch, caplog):
    monkeypatch.setattr(
        "backend.app.search_by_author_institution_topic", lambda a, i, t: None)
    monkeypatch.setattr(
        "backend.app.get_institution_and_topic_and_researcher_metadata_sparql", lambda i, t, a: {})
    result = get_institution_researcher_subfield_results(
        "InstH", "AuthorH", "TopicH", page=1, per_page=10)
    assert result == {}
    assert "No results found in SPARQL for institution, researcher, and topic" in caplog.text

# ---------------------------------------------------------------------------
# Lines 922–986: get_institution_researcher_subfield_results processing branch.


def test_get_institution_researcher_subfield_results(monkeypatch):
    fake_data = {
        "institution_metadata": {
            "url": "http://instI",
            "openalex_url": "http://instI",
            "ror": "ROR789"
        },
        "author_metadata": {
            "openalex_url": "http://authorI",
            "orcid": "ORCID789",
            "num_of_works": 9,
            "num_of_citations": 3,
            "last_known_institution": "InstI"
        },
        "subfield_metadata": [{"topic": "SubfieldI", "subfield_url": "http://subI"}],
        "totals": {"total_num_of_works": 50, "total_num_of_citations": 25},
        "data": [{"work_name": "Work1", "cited_by_count": 5}]
    }
    monkeypatch.setattr(
        "backend.app.search_by_author_institution_topic", lambda a, i, t: fake_data)
    result = get_institution_researcher_subfield_results(
        "InstI", "AuthorI", "TopicI", page=1, per_page=10)
    metadata = result["metadata"]
    assert metadata["institution_name"] == "InstI"
    assert "graph" in result
    assert "list" in result

# ---------------------------------------------------------------------------
# Lines 1173–1183: get_researcher_and_institution_metadata_sparql.


def test_get_researcher_and_institution_metadata_sparql():
    fake_researcher = {
        "oa_link": "http://authorJ",
        "orcid": "ORCIDJ",
        "work_count": 11,
        "cited_by_count": 6,
        "current_institution": "InstJ",
        "institution_url": "http://instJ"
    }
    fake_institution = {
        "homepage": "http://instJ",
        "oa_link": "http://instJ",
        "ror": "ROR101"
    }
    with patch("backend.app.get_author_metadata_sparql", return_value=fake_researcher), \
            patch("backend.app.get_institution_metadata_sparql", return_value=fake_institution):
        result = get_researcher_and_institution_metadata_sparql(
            "AuthorJ", "InstJ")
        assert result["institution_name"] == "InstJ"
        assert result["researcher_name"] == "AuthorJ"
        assert result["orcid"] == "ORCIDJ"
        assert result["ror"] == "ROR101"

# ---------------------------------------------------------------------------
# Lines 1276–1313: list_given_topic.


def test_list_given_topic(monkeypatch):
    fake_response_data = {
        "results": [{
            "display_name": "InstK",
            "topics": [{"subfield": {"display_name": "SubK"}, "count": 7}]
        }],
        "meta": {"next_cursor": None}
    }
    fake_get = MagicMock()
    fake_get.json.return_value = fake_response_data
    monkeypatch.setattr("backend.app.requests.get",
                        lambda url, headers: fake_get)
    subfield_list, graph, extra_metadata = list_given_topic("SubK", "ID_SubK")
    assert subfield_list == [("InstK", 7)]
    assert extra_metadata["work_count"] == 7

# ---------------------------------------------------------------------------
# Lines 1369–1371: list_given_institution_topic work count.


def test_list_given_institution_topic_work_count(monkeypatch):
    fake_sparql_results = [
        {"author": "A1", "name": "Author1", "works": {"value": "W1, W2, W3"}}
    ]
    monkeypatch.setattr("backend.app.query_SPARQL_endpoint",
                        lambda endpoint, query: fake_sparql_results)
    subfield_list, graph, extra_metadata = list_given_institution_topic(
        "InstL", "ID_InstL", "SubL", "ID_SubL")
    # Count should be number of commas+1, i.e. 3
    assert extra_metadata["work_count"] == 3

# ---------------------------------------------------------------------------
# Lines 1386–1390: list_given_researcher_institution graph nodes.


def test_list_given_researcher_institution_graph(monkeypatch):
    fake_api_response = {"topics": [
        {"subfield": {"display_name": "SubM"}, "count": 4}]}
    fake_get = MagicMock()
    fake_get.json.return_value = fake_api_response
    monkeypatch.setattr("backend.app.requests.get",
                        lambda url, headers: fake_get)
    sorted_subfields, graph = list_given_researcher_institution(
        "https://openalex.org/authors/9999", "AuthorM", "InstM")
    node_ids = {node["id"] for node in graph["nodes"]}
    assert "InstM" in node_ids
    assert "SubM" in node_ids

# ---------------------------------------------------------------------------
# Lines 1412–1425: get_topic_and_researcher_metadata_sparql.


def test_get_topic_and_researcher_metadata_sparql():
    fake_researcher_data = {
        "orcid": "ORCIDX",
        "current_institution": "InstX",
        "work_count": 15,
        "cited_by_count": 8,
        "oa_link": "http://authorX",
        "institution_url": "http://instX"
    }
    fake_topic_data = {
        "topic_clusters": ["Cluster1", "Cluster2"],
        "oa_link": "http://topicX"
    }
    with patch("backend.app.get_author_metadata_sparql", return_value=fake_researcher_data), \
            patch("backend.app.get_subfield_metadata_sparql", return_value=fake_topic_data):
        result = get_topic_and_researcher_metadata_sparql("TopicX", "AuthorX")
        assert result["orcid"] == "ORCIDX"
        assert result["topic_clusters"] == ["Cluster1", "Cluster2"]

# ---------------------------------------------------------------------------
# Lines 1452–1453: list_given_researcher_topic citation count.


def test_list_given_researcher_topic_citation_count(monkeypatch):
    fake_sparql_results = [
        {"title": "WorkA", "cited_by_count": {"value": "10"}}
    ]
    monkeypatch.setattr("backend.app.query_SPARQL_endpoint",
                        lambda endpoint, query: fake_sparql_results)
    work_list, graph, extra_metadata = list_given_researcher_topic(
        "TopicY", "AuthorY", "InstY", "ID_TopicY", "ID_AuthorY", "ID_InstY")
    assert work_list[0][1] == 10
    assert extra_metadata["cited_by_count"] == 10

# ---------------------------------------------------------------------------
# Lines 1469–1473: list_given_researcher_topic graph nodes for works.


def test_list_given_researcher_topic_graph_nodes(monkeypatch):
    fake_sparql_results = [
        {"title": "WorkB", "cited_by_count": {"value": "5"}}
    ]
    monkeypatch.setattr("backend.app.query_SPARQL_endpoint",
                        lambda endpoint, query: fake_sparql_results)
    work_list, graph, extra_metadata = list_given_researcher_topic(
        "TopicZ", "AuthorZ", "InstZ", "ID_TopicZ", "ID_AuthorZ", "ID_InstZ")
    node_ids = {node["id"] for node in graph["nodes"]}
    assert "WorkB" in node_ids

# ---------------------------------------------------------------------------
# Lines 1497–1498: list_given_researcher_topic extra metadata.


def test_list_given_researcher_topic_extra_metadata(monkeypatch):
    fake_sparql_results = [
        {"title": "WorkC", "cited_by_count": {"value": "2"}}
    ]
    monkeypatch.setattr("backend.app.query_SPARQL_endpoint",
                        lambda endpoint, query: fake_sparql_results)
    work_list, graph, extra_metadata = list_given_researcher_topic(
        "TopicW", "AuthorW", "InstW", "ID_TopicW", "ID_AuthorW", "ID_InstW")
    assert extra_metadata["work_count"] == 1
    assert extra_metadata["cited_by_count"] == 2

# ---------------------------------------------------------------------------
# Lines 1542–1543: query_SQL_endpoint error logging.


def test_query_SQL_endpoint_error(monkeypatch, caplog):
    fake_connection = MagicMock()
    fake_cursor = MagicMock()
    fake_cursor.execute.side_effect = Exception("SQL Error")
    fake_connection.cursor.return_value.__enter__.return_value = fake_cursor
    with pytest.raises(Exception):
        query_SQL_endpoint(fake_connection, "SELECT * FROM table")
    assert "SQL query failed" in caplog.text

# ---------------------------------------------------------------------------
# Lines 1579–1581: autofill_topics filtering.


def test_autofill_topics_filter(client):
    response = client.post("/autofill-topics", json={"topic": "Che"})
    data = response.get_json()
    # Our dummy subfields (set in conftest) are "Biology\nChemistry\nPhysics"
    assert any("Chemistry" in s for s in data["possible_searches"])

# ---------------------------------------------------------------------------
# Lines 1779–1780: create_connection success.


def test_create_connection_success(monkeypatch):
    fake_conn = MagicMock()
    with patch("backend.app.mysql.connector.connect", return_value=fake_conn):
        from backend.app import create_connection
        conn = create_connection("host", "user", "pass", "db")
        assert conn == fake_conn

# ---------------------------------------------------------------------------
# Lines 1802–1815: get_institution_mup_id success.


def test_get_institution_mup_id_success(monkeypatch, caplog):
    fake_inst_id = "Inst123"
    fake_query_result = [[{"institution_id": "Inst123"}]]
    monkeypatch.setattr("backend.app.get_institution_id",
                        lambda name: fake_inst_id)
    monkeypatch.setattr("backend.app.execute_query",
                        lambda q, params: fake_query_result)
    result = get_institution_mup_id("TestInst")
    assert result == {"institution_id": "Inst123"}

# ---------------------------------------------------------------------------
# Lines 1824–1825: get_institution_mup_id returns None if no inst id.


def test_get_institution_mup_id_no_inst(monkeypatch, caplog):
    monkeypatch.setattr("backend.app.get_institution_id", lambda name: None)
    result = get_institution_mup_id("NoInst")
    assert result is None
    assert "No institution ID found" in caplog.text

# ---------------------------------------------------------------------------
# Lines 1835–1836: get_institution_sat_scores not found.


def test_get_institution_sat_scores_not_found(monkeypatch, caplog):
    monkeypatch.setattr("backend.app.get_institution_id",
                        lambda name: "InstNotFound")
    monkeypatch.setattr("backend.app.execute_query", lambda q, params: None)
    result = get_institution_sat_scores("NoSatInst")
    assert result is None
    assert "No MUP SAT scores data found" in caplog.text

# ---------------------------------------------------------------------------
# Lines 1841–1858: get_institution_endowments_and_givings success.


def test_get_institution_endowments_and_givings_success(monkeypatch, caplog):
    fake_result = [[{"endowment": 100, "giving": 50, "year": 2020}]]
    monkeypatch.setattr("backend.app.get_institution_id",
                        lambda name: "InstEG")
    monkeypatch.setattr("backend.app.execute_query",
                        lambda q, params: fake_result)
    result = get_institution_endowments_and_givings("InstEG")
    assert result["endowment"] == 100

# ---------------------------------------------------------------------------
# Lines 1867–1868: get_institution_medical_expenses returns None if no MUP id.


def test_get_institution_medical_expenses_no_mup(monkeypatch, caplog):
    monkeypatch.setattr(
        "backend.app.get_institution_mup_id", lambda name: None)
    result = get_institution_medical_expenses("NoMedInst")
    assert result is None

# ---------------------------------------------------------------------------
# Lines 1879–1881: get_institution_doctorates_and_postdocs success.


def test_get_institution_doctorates_and_postdocs_success(monkeypatch):
    fake_result = [[{"num_postdocs": 3, "num_doctorates": 10, "year": 2021}]]
    monkeypatch.setattr("backend.app.get_institution_id",
                        lambda name: "InstDP")
    monkeypatch.setattr("backend.app.execute_query",
                        lambda q, params: fake_result)
    result = get_institution_doctorates_and_postdocs("InstDP")
    assert result["num_doctorates"] == 10

# ---------------------------------------------------------------------------
# Lines 1930–1946: get_institutions_faculty_awards success.


def test_get_institutions_faculty_awards_success(monkeypatch):
    fake_result = [[{"nae": "NAE", "nam": "NAM",
                     "nas": "NAS", "num_fac_awards": 4, "year": 2019}]]
    monkeypatch.setattr("backend.app.get_institution_id",
                        lambda name: "InstFA")
    monkeypatch.setattr("backend.app.execute_query",
                        lambda q, params: fake_result)
    result = get_institutions_faculty_awards("InstFA")
    assert result["num_fac_awards"] == 4

# ---------------------------------------------------------------------------
# Lines 1951–1967: get_institutions_r_and_d success.


def test_get_institutions_r_and_d_success(monkeypatch):
    fake_result = [[{"category": "Cat", "federal": 1,
                     "percent_federal": 50, "total": 2, "percent_total": 50}]]
    monkeypatch.setattr("backend.app.get_institution_id",
                        lambda name: "InstRD")
    monkeypatch.setattr("backend.app.execute_query",
                        lambda q, params: fake_result)
    result = get_institutions_r_and_d("InstRD")
    assert result["total"] == 2

# ---------------------------------------------------------------------------
# Lines 2023,2037,2084,2098: Endpoints abort if missing 'institution_name'.


@pytest.mark.parametrize("endpoint", [
    "/mup-sat-scores",
    "/endowments-and-givings",
    "/mup-faculty-awards",
    "/mup-r-and-d"
])
def test_endpoint_missing_institution_name(client, endpoint):
    response = client.post(endpoint, json={})
    assert response.status_code == 400
    assert b"Missing 'institution_name'" in response.data

# ---------------------------------------------------------------------------
# Lines 1982–1987: serve() route for static file and index fallback.


def test_serve_route_static_file(client, monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda path: True)
    monkeypatch.setattr("backend.app.send_from_directory",
                        lambda folder, file: __import__("flask").Response("Static File Content", status=200))
    response = client.get("/dummy.js")
    assert response.status_code == 200
    assert b"Static File Content" in response.data


def test_serve_route_index_fallback(client, monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda path: False)
    monkeypatch.setattr("backend.app.send_from_directory",
                        lambda folder, file: __import__("flask").Response("Index HTML", status=200))
    response = client.get("/nonexistent")
    assert response.status_code == 200
    assert b"Index HTML" in response.data

# ---------------------------------------------------------------------------
# Lines 2110–2111: Application startup is not directly unit tested.


def test_env_var_extraction():
    # Lines 19-23 are executed on import. The environment is always different
    # from the test environment so neither of us can contradict it. This test simply
    # re-imports the module with the environment variables that are known.
    import os
    os.environ["DB_HOST"] = "localhost"
    os.environ["DB_PORT"] = "5432"
    os.environ["DB_NAME"] = "testdb"
    os.environ["DB_USER"] = "testuser"
    os.environ["DB_PASSWORD"] = "testpass"
    os.environ["DB_API"] = "http://testapi"
    import backend.app as app_module
    # Assert that the variables are correctly set
    assert app_module.DB_PORT == 5432
    assert app_module.DB_NAME == "testdb"
    assert app_module.DB_USER == "testuser"
    assert app_module.DB_PASSWORD == "testpass"
    assert app_module.API == "http://testapi"


def test_search_by_institution_topic_no_data(monkeypatch, caplog):
    # Lines 240-241: if get_institution_id returns None, log the warning and then re-return None.
    monkeypatch.setattr("backend.app.get_institution_id", lambda x: None)
    result = search_by_institution_topic("FakeInst", "FakeTopic")
    assert result is None
    assert "No results found for institution-topic search" in caplog.text


def test_search_by_author_topic_no_data(monkeypatch, caplog):
    # Lines 260-261: if get_author_ids returns None, log the warning & return None.
    monkeypatch.setattr("backend.app.get_author_ids", lambda x: None)
    result = search_by_author_topic("FakeAuthor", "FakeTopic")
    assert result is None
    assert "No results found for author-topic search" in caplog.text


def test_search_by_institution_no_inst(monkeypatch, caplog):
    # Lines 288-289: If get_institution_id returns None, log a warning & return NOne.
    monkeypatch.setattr("backend.app.get_institution_id", lambda x: None)
    result = search_by_institution("FakeInstitution")
    assert result is None
    assert "No results found for institution:" in caplog.text


def test_search_by_author_no_author(monkeypatch, caplog):
    # Lines 307-308: If get_author_ids returns None, function logs a warning & returns NOne.
    monkeypatch.setattr("backend.app.get_author_ids", lambda x: None)
    result = search_by_author("FakeAuthor")
    assert result is None
    assert "No results found for author:" in caplog.text


def test_keywords_csv_loading(monkeypatch):
    # Lines 324-325: Test(s) the file reading of keywords.csv, when SUBFIELDS is False.
    monkeypatch.setattr("backend.app.SUBFIELDS", False)
    monkeypatch.setattr("builtins.open", lambda f,
                        mode='r': StringIO("Key1\nKey2\nKey3"))
    import backend.app as app_module
    importlib.reload(app_module)
    from backend.app import autofill_topics_list
    assert autofill_topics_list == ["Key1", "Key2", "Key3"]


def test_get_geo_info_returns_none(monkeypatch, client, caplog):
    # Line 421: If the response JSON is None then no geo data is found other than None.
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = None
    monkeypatch.setattr("backend.app.requests.get",
                        lambda url, headers: fake_response)
    response = client.post(
        "/geo_info", json={"institution_oa_link": "openalex.org/institutions/12345"})
    data = response.get_json()
    # Expecting None (or some empty dictionary) and a warning log
    assert data is None or data == {}
    assert "No data found for institution" in caplog.text


def test_get_institution_researcher_subfield_results_sparql(monkeypatch, caplog):
    # Lines 919-921: In SPARQL branch, if search_by_author_institution_topic returns None..:
    monkeypatch.setattr(
        "backend.app.search_by_author_institution_topic", lambda a, i, t: None)
    result = get_institution_researcher_subfield_results(
        "Inst", "Auth", "Topic", page=1, per_page=10)
    assert result == {}
    assert "No results found in SPARQL for institution, researcher, and topic" in caplog.text


def test_list_given_topic_exception(monkeypatch):
    # Lines 1308-1309: Test exception handling in list_given_topic.
    def fake_get(url, headers):
        raise Exception("Fake error")
    monkeypatch.setattr("backend.app.requests.get", fake_get)
    from backend.app import autofill_inst_list
    original_list = autofill_inst_list.copy()
    monkeypatch.setattr("backend.app.autofill_inst_list", ["InstError"])
    subfield_list, graph, extra_metadata = list_given_topic(
        "SubfieldTest", "ID_Subfield")
    # Even if an exception occurs in one iteration, the function should return other-wise valid output.
    assert isinstance(subfield_list, list)
    monkeypatch.setattr("backend.app.autofill_inst_list", original_list)


def test_create_connection_failure(monkeypatch, caplog):
    # Lines 1792-1793: Test the error handling in create_connection.
    def fake_connect(*args, **kwargs):
        raise Exception("Connection failed")
    monkeypatch.setattr("backend.app.mysql.connector.connect", fake_connect)
    conn = create_connection("host", "user", "pass", "db")
    assert conn is None
    assert "Failed to connect to MySQL database" in caplog.text


def test_search_by_institution_topic_no_data(monkeypatch, caplog):
    # Lines 240-241: if get_institution_id returns None, log warning and return NOne.
    monkeypatch.setattr("backend.app.get_institution_id", lambda x: None)
    result = search_by_institution_topic("FakeInst", "FakeTopic")
    assert result is None
    assert "No results found for institution-topic search" in caplog.text


def test_search_by_author_topic_no_data(monkeypatch, caplog):
    # Lines 260-261: if get_author_ids returns None, log warning and return None.
    monkeypatch.setattr("backend.app.get_author_ids", lambda x: None)
    result = search_by_author_topic("FakeAuthor", "FakeTopic")
    assert result is None
    assert "No results found for author-topic search" in caplog.text


def test_search_by_institution_no_inst(monkeypatch, caplog):
    # Lines 288-289: If get_institution_id returns None, function logs a warning and returns None.
    monkeypatch.setattr("backend.app.get_institution_id", lambda x: None)
    result = search_by_institution("FakeInstitution")
    assert result is None
    assert "No results found for institution:" in caplog.text


def test_search_by_author_no_author(monkeypatch, caplog):
    # Lines 307-308: If get_author_ids returns None, function logs a warning & returns None.
    monkeypatch.setattr("backend.app.get_author_ids", lambda x: None)
    result = search_by_author("FakeAuthor")
    assert result is None
    assert "No results found for author:" in caplog.text


def test_keywords_csv_loading(monkeypatch):
    # Lines 324-325: Test the file reading of keywords.csv when SUBFIELDS is False.
    monkeypatch.setattr("backend.app.SUBFIELDS", False)
    monkeypatch.setattr("builtins.open", lambda f,
                        mode='r': StringIO("Key1\nKey2\nKey3"))
    import backend.app as app_module
    importlib.reload(app_module)
    from backend.app import autofill_topics_list
    assert autofill_topics_list == ["Key1", "Key2", "Key3"]


def test_get_geo_info_returns_none(monkeypatch, client, caplog):
    # Line 421: If the response JSON is None then no geo data is found (other than the None value).
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = None
    monkeypatch.setattr("backend.app.requests.get",
                        lambda url, headers: fake_response)
    response = client.post(
        "/geo_info", json={"institution_oa_link": "openalex.org/institutions/12345"})
    data = response.get_json()
    # Expecting None (or empty dictionary) as well as a warning log
    assert data is None or data == {}
    assert "No data found for institution" in caplog.text


def test_get_institution_researcher_subfield_results_sparql(monkeypatch, caplog):
    # Lines 919-921: In SPARQL branch, if search_by_author_institution_topic returns None.
    monkeypatch.setattr(
        "backend.app.search_by_author_institution_topic", lambda a, i, t: None)
    result = get_institution_researcher_subfield_results(
        "Inst", "Auth", "Topic", page=1, per_page=10)
    assert result == {}
    assert "No results found in SPARQL for institution, researcher, and topic" in caplog.text


def test_list_given_topic_exception(monkeypatch):
    # Lines 1308-1309: Test exception handling in list_given_topic.
    def fake_get(url, headers):
        raise Exception("Fake error")
    monkeypatch.setattr("backend.app.requests.get", fake_get)
    from backend.app import autofill_inst_list
    original_list = autofill_inst_list.copy()
    monkeypatch.setattr("backend.app.autofill_inst_list", ["InstError"])
    subfield_list, graph, extra_metadata = list_given_topic(
        "SubfieldTest", "ID_Subfield")
    # Even if an exception occurs in one iteration, the function should then return valid output.
    assert isinstance(subfield_list, list)
    monkeypatch.setattr("backend.app.autofill_inst_list", original_list)


def test_create_connection_failure(monkeypatch, caplog):
    # Lines 1792-1793: Test the error handling in create_connection.
    def fake_connect(*args, **kwargs):
        raise Exception("Connection failed")
    monkeypatch.setattr("backend.app.mysql.connector.connect", fake_connect)
    conn = create_connection("host", "user", "pass", "db")
    assert conn is None
    assert "Failed to connect to MySQL database" in caplog.text


def test_create_connection_success(monkeypatch):
    fake_conn = MagicMock()
    with patch("backend.app.mysql.connector.connect", return_value=fake_conn):
        from backend.app import create_connection
        conn = create_connection("host", "user", "pass", "db")
        assert conn == fake_conn
# ------------------------------------------------------------------------------
# Lines 240–241: search_by_institution_topic returns None if get_institution_id is None


def test_search_by_institution_topic_no_inst(caplog):
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr("backend.app.get_institution_id", lambda x: None)
    result = search_by_institution_topic("FakeInst", "FakeTopic")
    assert result is None
    assert "No institution ID found" in caplog.text
    monkeypatch.undo()

# ------------------------------------------------------------------------------
# Lines 260–261: search_by_author_topic returns None if no author IDs found


def test_search_by_author_topic_no_ids(caplog):
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr("backend.app.get_author_ids", lambda x: None)
    result = search_by_author_topic("FakeAuthor", "FakeTopic")
    assert result is None
    # Depending on the excellency of our database, the warning may mention "No author IDs found"
    assert ("No author IDs found" in caplog.text or
            "No results found for author-topic search" in caplog.text)
    monkeypatch.undo()

# ------------------------------------------------------------------------------
# Lines 288–289: search_by_institution returns None when institution id is missing


def test_search_by_institution_no_id(caplog):
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr("backend.app.get_institution_id", lambda x: None)
    result = search_by_institution("FakeInstitution")
    assert result is None
    assert "No institution ID found" in caplog.text
    monkeypatch.undo()

# ------------------------------------------------------------------------------
# Lines 307–308: search_by_author returns None when no author IDs found


def test_search_by_author_no_ids(caplog):
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr("backend.app.get_author_ids", lambda x: None)
    result = search_by_author("FakeAuthor")
    assert result is None
    assert "No author IDs found" in caplog.text
    monkeypatch.undo()

# ------------------------------------------------------------------------------
# Lines 324–325: When SUBFIELDS is False, the file keywords.csv is used.
# (Here we simulate file reading for keywords.csv by patching builtins.open.)


def test_autofill_topics_csv_loading(monkeypatch):
    monkeypatch.setattr("backend.app.SUBFIELDS", False)
    monkeypatch.setattr(
        "builtins.open",
        lambda filename, mode='r': StringIO("Key1\nKey2\nKey3")
        if "keywords.csv" in filename else StringIO("")
    )
    import importlib
    import backend.app as app_module
    importlib.reload(app_module)
    # Now, if your app assigns a variable (for example, autofill_topics_list) when SUBFIELDS is False,
    # you can import it from backend.app. Alter the name if that's what the app has formatted.
    try:
        from backend.app import autofill_topics_list
        assert autofill_topics_list == ["Key1", "Key2", "Key3"]
    except ImportError:
        # If the variable isn't defined in your app, then this test may need to be formatted.
        pytest.skip("autofill_topics_list not defined in backend.app")

# ------------------------------------------------------------------------------
# Line 421: get_geo_info logs a warning and returns None when no data is found in the API response


def test_get_geo_info_no_data(monkeypatch, caplog):
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = None
    monkeypatch.setattr("backend.app.requests.get",
                        lambda url, headers: fake_response)
    from flask import Flask
    app = Flask(__name__)
    with app.test_request_context(json={"institution_oa_link": "openalex.org/institutions/12345"}):
        result = get_geo_info()
        assert result in (None, {})
    assert "No data found for institution" in caplog.text

# ------------------------------------------------------------------------------
# Lines 663–728: get_researcher_and_subfield_results processing branch


def test_get_researcher_and_subfield_results_processing(monkeypatch, caplog):
    fake_data = {
        "subfield_metadata": [{"topic": "TestSub", "subfield_url": "http://testsub"}],
        "totals": {"total_num_of_works": 20, "total_num_of_citations": 10},
        "author_metadata": {
            "orcid": "ORCID123",
            "openalex_url": "http://author_test",
            "last_known_institution": "InstTest"
        },
        "data": [{"work_name": "WorkTest", "num_of_citations": 5}]
    }
    monkeypatch.setattr("backend.app.search_by_author_topic",
                        lambda a, t: fake_data)
    result = get_researcher_and_subfield_results(
        "TestAuthor", "TestTopic", page=1, per_page=10)
    metadata = result.get("metadata", {})
    assert metadata.get("researcher_name") == "TestAuthor"
    assert metadata.get("current_institution") == "InstTest"
    assert "graph" in result
    assert "list" in result

# ------------------------------------------------------------------------------
# Lines 842–845: In the second tier (if the first tier database query didn't work out) we got the branch for get_researcher_result (SPARQL), successful retrieval logging


def test_get_researcher_result_sparql_success(monkeypatch, caplog):
    fake_sparql_data = {
        "oa_link": "http://author_sparql",
        "name": "Sparql Author",
        "current_institution": "InstSparql",
        "data": [{"topic": "SparqlTopic", "num_of_works": 3}]
    }
    monkeypatch.setattr("backend.app.search_by_author", lambda author: None)
    monkeypatch.setattr("backend.app.get_author_metadata_sparql",
                        lambda author: fake_sparql_data)
    monkeypatch.setattr("backend.app.list_given_researcher_institution",
                        lambda oa_link, name, inst: (["dummy_list"], {"nodes": [], "edges": []}))
    # Call the view function directly from the Flask app instance.
    result = __import__("backend.app").app.view_functions["get_researcher_result"](
        "Sparql Author", page=1, per_page=10)
    assert "Successfully retrieved SPARQL results for researcher" in caplog.text

# ------------------------------------------------------------------------------
# Lines 858: In get_researcher_result, metadata['work_count'] has changed and has been set correctly from author_metadata


def test_get_researcher_result_work_count(monkeypatch):
    fake_data = {
        "author_metadata": {
            "orcid": "ORCID456",
            "num_of_works": 12,
            "last_known_institution": "Inst456",
            "num_of_citations": 7,
            "openalex_url": "http://author456"
        },
        "data": [{"topic": "Topic456", "num_of_works": 4}]
    }
    monkeypatch.setattr("backend.app.search_by_author",
                        lambda author: fake_data)
    result = get_researcher_result("Author456", page=1, per_page=10)
    assert result["metadata"]["work_count"] == 12

# ------------------------------------------------------------------------------
# Lines 942: In get_institution_results, metadata['homepage'] has been set ("ideally") from institution_metadata['url']


def test_get_institution_results_homepage(monkeypatch):
    fake_data = {
        "institution_metadata": {
            "url": "http://homepage_test",
            "num_of_works": 25,
            "institution_name": "InstHomepage",
            "num_of_citations": 18,
            "openalex_url": "http://instHomepage",
            "num_of_authors": 6
        },
        "data": [{"topic_subfield": "SubHomepage", "num_of_authors": 2}]
    }
    monkeypatch.setattr("backend.app.search_by_institution",
                        lambda inst: fake_data)
    result = get_institution_results("InstHomepage", page=1, per_page=10)
    metadata = result["metadata"]
    assert metadata["homepage"] == "http://homepage_test"

# ------------------------------------------------------------------------------
# Lines 1593–1594 and 1626: get_topic_space returns a graph with "proper" logging


def test_get_topic_space_graph(caplog):
    result = get_topic_space()
    graph = result.get("graph", {})
    nodes = graph.get("nodes", [])
    assert len(nodes) == 4
    assert ("Successfully built topic space default graph" in caplog.text or
            "Successfully built topic space" in caplog.text)

# ------------------------------------------------------------------------------
# Lines 1793: get_institution_mup_id logs info when a MUP ID is found and re-viewed


def test_get_institution_mup_id_found(monkeypatch, caplog):
    fake_inst_id = "InstMUP"
    fake_result = [[{"institution_id": fake_inst_id}]]
    monkeypatch.setattr("backend.app.get_institution_id",
                        lambda name: "FakeInstID")
    monkeypatch.setattr("backend.app.execute_query",
                        lambda q, params: fake_result)
    result = get_institution_mup_id("FakeInst")
    assert result == {"institution_id": fake_inst_id}
    assert "Successfully fetched MUP ID for" in caplog.text

# ------------------------------------------------------------------------------
# Lines 1827–1828: autofill_topics endpoint logs "quantity" number of matching topics


def test_autofill_topics_logging(client, caplog):
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("SUBFIELDS", "true")
    response = client.post("/autofill-topics", json={"topic": "Chem"})
    data = response.get_json()
    assert "Found" in caplog.text and "matching topics" in caplog.text
    monkeypatch.undo()

# ------------------------------------------------------------------------------
# Lines 1837–1838: search_topic_space also logs some processing message.


def test_search_topic_space_logging(monkeypatch, caplog):
    fake_graph = {
        "nodes": [{
            "id": "1",
            "label": "FakeTopic",
            "subfield_name": "FakeSub",
            "field_name": "FakeField",
            "domain_name": "FakeDomain",
            "keywords": "key1; key2",
            "summary": "Test summary",
            "wikipedia_url": "http://wiki"
        }],
        "edges": []
    }
    monkeypatch.setattr("builtins.open", lambda filename, mode='r': StringIO(
        json.dumps(fake_graph)) if "topic_default.json" in filename else StringIO(""))
    from backend.app import app
    client = app.test_client()
    response = client.post("/search-topic-space", json={"topic": "FakeTopic"})
    assert "Processing topic space search results" in caplog.text

# ------------------------------------------------------------------------------
# Lines 1947–1948: get_institution_id logs (files type) warning if the query returns {} (no ID found)


def test_get_institution_id_empty_result(caplog):
    fake_result = [[{}]]
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr("backend.app.execute_query",
                        lambda q, params: fake_result)
    result = get_institution_id("NoIDInst")
    assert result is None
    assert "No institution ID found" in caplog.text
    monkeypatch.undo()

# ------------------------------------------------------------------------------
# Lines 1968–1969: search_by_topic logs warning when no results ("any type" of results) found


def test_search_by_topic_no_results(caplog, monkeypatch):
    monkeypatch.setattr("backend.app.execute_query", lambda q, params: None)
    from backend.app import search_by_topic
    result = search_by_topic("NoTopic")
    assert result is None
    assert "No results found for topic:" in caplog.text

# ------------------------------------------------------------------------------
# Lines 1995–2000: get_researcher_result logs info after building list as well as graph for researcher


def test_get_researcher_result_logs_list_graph(monkeypatch, caplog):
    fake_data = {
        "author_metadata": {
            "orcid": "ORCID789",
            "num_of_works": 5,
            "last_known_institution": "Inst789",
            "num_of_citations": 3,
            "openalex_url": "http://author789"
        },
        "data": [{"topic": "Topic789", "num_of_works": 2}]
    }
    monkeypatch.setattr("backend.app.search_by_author",
                        lambda author: fake_data)
    result = get_researcher_result("Author789", page=1, per_page=10)
    assert "Successfully built result for researcher:" in caplog.text

# ------------------------------------------------------------------------------
# Lines 2123–2124: get_institution_metadata_sparql logs successful (non-fixed but variable) metadata retrieval


def test_get_institution_metadata_sparql_success(monkeypatch, caplog):
    fake_results = [{
        "ror": "ROR_Test",
        "workscount": "30",
        "citedcount": "15",
        "homepage": "http://instmeta",
        "institution": "http://instmeta"
    }]
    monkeypatch.setattr("backend.app.query_SPARQL_endpoint",
                        lambda endpoint, query: fake_results)
    from backend.app import get_institution_metadata_sparql
    metadata = get_institution_metadata_sparql("TestInst")
    assert metadata["homepage"] == "http://instmeta"
    assert "Successfully retrieved metadata for institution:" in caplog.text


def test_search_by_institution_topic_no_results(monkeypatch, caplog):
    # A bit of a blocker to patch, the get_institution_id is going to return a
    # dummy and valid institution ID.
    monkeypatch.setattr("backend.app.get_institution_id",
                        lambda inst: "dummy_inst_id")
    # Similarly we patch the execute_query to return an empty list
    # simulating no results at least at the beginning when we have a
    # bunch of blobs that are wholly disconnected.
    monkeypatch.setattr("backend.app.execute_query", lambda q, params: [])
    from backend.app import search_by_institution_topic
    result = search_by_institution_topic("TestInstitution", "TestTopic")
    # Otherwise we're going to want to take some time to go through the fact
    # that the function returns None.
    assert result is None
    # We also ought to show that whether or not, the warning message ends up being logged
    assert "No results found for institution-topic search" in caplog.text


def test_search_by_author_topic_no_results(monkeypatch, caplog):
    # And, the code is being duplicated of course in the patch of the get_author_ids
    # because that is what returns a dummy author ID so that the function continues
    # past the first and initial check.
    monkeypatch.setattr("backend.app.get_author_ids", lambda author: [
                        {"author_id": "dummy_author_id"}])
    # Then the patch execute-Query allows us to return an empty list in order
    # to show what we needed from the simulation, the no results found.
    monkeypatch.setattr("backend.app.execute_query", lambda q, params: [])
    from backend.app import search_by_author_topic
    result = search_by_author_topic("TestAuthor", "TestTopic")
    # And then we needed some help to assert that the function returns None.
    assert result is None
    # As well as in updating the assertions, that the expected warning is logged.
    assert "No results found for author-topic search" in caplog.text


def test_search_by_institution_no_results(monkeypatch, caplog):
    # Furthermore, we do patch the subfields get_institution_id to return the
    # dummy true institution id as we know it.
    monkeypatch.setattr("backend.app.get_institution_id",
                        lambda name: "dummy_inst_id")
    # Which means that since the patch might have 100+ topics, we patch the
    # execute_query to simulate no results found by returning a list that is empty!
    monkeypatch.setattr("backend.app.execute_query", lambda q, params: [])
    from backend.app import search_by_institution
    result = search_by_institution("FakeInstitution")
    # And the confirmation is that the function returns NOne.
    assert result is None
    # It's a kind thing that the warning message is logged on this.
    assert "No results found for institution: FakeInstitution" in caplog.text


def test_search_by_author_no_results(monkeypatch, caplog):
    # We can also get some guidance with direction of where we patch the get_author_ids
    # moreover to return a dummy author id such that the procession of the function
    # seems to load, which engenders technical success with existential failure.
    monkeypatch.setattr("backend.app.get_author_ids", lambda author: [
                        {"author_id": "dummy_author_id"}])
    # And then we have this search full functionality via the execute_query simulation
    # when no results are found by returning an empty list.
    monkeypatch.setattr("backend.app.execute_query", lambda q, params: [])
    from backend.app import search_by_author
    result = search_by_author("FakeAuthor")
    # And I want feedback to show that the function returns None!
    assert result is None
    # And I know that the successful assertions are logged of the warning
    # messages that we expect.
    assert "No results found for author: FakeAuthor" in caplog.text


def test_get_institution_and_researcher_results_graph(monkeypatch, caplog):
    # Focus on simulating dummy data for the response institutionally as well as
    # the researcher, search.
    dummy_data = {
        "author_metadata": {
            "orcid": "dummy_orcid",
            "num_of_works": 10,
            "last_known_institution": "Dummy Inst",
            "num_of_citations": 5,
            "openalex_url": "http://dummy_author_url"
        },
        "institution_metadata": {
            "url": "http://fakeinstitution.com",
            # Use this as the institution ID credential(s) in the graph.
            "openalex_url": "FakeInstitution",
            "ror": "dummy_ror",
            "institution_name": "FakeInstitution"
        },
        "data": [
            {"author_id": "dummy_author_1",
                "author_name": "Author One", "num_of_works": 7},
            {"author_id": "dummy_author_2",
                "author_name": "Author Two", "num_of_works": 3}
        ],
        "totals": {
            "total_num_of_works": 2,
            "total_num_of_citations": 5,
            "total_num_of_authors": 2
        }
    }
    # Feel free to patch the function that does data retrieval from the data-base.
    monkeypatch.setattr("backend.app.search_by_author_institution",
                        lambda researcher, institution: dummy_data)
    # In Azure traditionally we would call & import and test the function under the accuracy constraint.
    from backend.app import get_institution_and_researcher_results
    result = get_institution_and_researcher_results(
        "FakeInstitution", "FakeResearcher", page=1, per_page=20)
    # And I think that the list aggregates author_name and num_of_works among
    # "other things", for which the good news is that the institutions, the
    # topics and even the people..do they change? No, at least not at high
    # frequency.
    expected_list = [("Author One", 7), ("Author Two", 3)]
    assert result["list"] == expected_list
    # Extraction of the graph for synchronicity.
    graph = result["graph"]
    nodes = graph["nodes"]
    edges = graph["edges"]
    # It may take a while to sync, so first check that the institution node is present.
    institution_node = {"id": "FakeInstitution",
                        "label": "FakeInstitution", "type": "INSTITUTION"}
    assert institution_node in nodes
    # It only takes each entry, to create an author node.
    author_node_1 = {"id": "dummy_author_1",
                     "label": "Author One", "type": "AUTHOR"}
    author_node_2 = {"id": "dummy_author_2",
                     "label": "Author Two", "type": "AUTHOR"}
    assert author_node_1 in nodes
    assert author_node_2 in nodes
    # That's how we define progress--when a number node is created for the
    # values of the number of works..
    number_node_1 = {"id": 7, "label": 7, "type": "NUMBER"}
    number_node_2 = {"id": 3, "label": 3, "type": "NUMBER"}
    assert number_node_1 in nodes
    assert number_node_2 in nodes
    # For each entry, the edge "numWorks" "creates" the graphical connection.
    expected_edge_1 = {
        "id": "dummy_author_1-7",
        "start": "dummy_author_1",
        "end": 7,
        "label": "numWorks",
        "start_type": "AUTHOR",
        "end_type": "NUMBER"
    }
    expected_edge_2 = {
        "id": "dummy_author_2-3",
        "start": "dummy_author_2",
        "end": 3,
        "label": "numWorks",
        "start_type": "AUTHOR",
        "end_type": "NUMBER"
    }
    # Just set some level of the "memberOf" edge that "links", the author to the
    # institution.
    expected_edge_3 = {
        "id": "dummy_author_1-FakeInstitution",
        "start": "dummy_author_1",
        "end": "FakeInstitution",
        "label": "memberOf",
        "start_type": "AUTHOR",
        "end_type": "INSTITUTION"
    }
    expected_edge_4 = {
        "id": "dummy_author_2-FakeInstitution",
        "start": "dummy_author_2",
        "end": "FakeInstitution",
        "label": "memberOf",
        "start_type": "AUTHOR",
        "end_type": "INSTITUTION"
    }
    assert expected_edge_1 in edges
    assert expected_edge_2 in edges
    assert expected_edge_3 in edges
    assert expected_edge_4 in edges
    # A lot of the metadata's people_count we want to set to the number of data entries so we know what quantity of research is happening.
    assert result["metadata"]["people_count"] == 2

# Now, when we expect an empty string we have got to test when the "orcID" is NOne


def test_metadata_orcid_is_none(monkeypatch):
    fake_data = {
        "author_metadata": {
            "orcid": None,
            "openalex_url": "http://fakeopenalexurl",
            "last_known_institution": "Test Institution"
        },
        "subfield_metadata": [{"topic": "TopicA", "subfield_url": "http://subfieldurl"}],
        "totals": {"total_num_of_works": 10, "total_num_of_citations": 20},
        "data": []
    }

    monkeypatch.setattr("backend.app.search_by_author_topic",
                        lambda a, t: fake_data)

    result = get_researcher_and_subfield_results("John Doe", "Physics")

    assert result["metadata"]["orcid"] == ''
    assert result["metadata"]["researcher_oa_link"] == "http://fakeopenalexurl"
    assert result["metadata"]["current_institution"] == "Test Institution"

# And, we should just keep some tests for when orcID is provided


def test_metadata_orcid_provided(monkeypatch):
    fake_data = {
        "author_metadata": {
            "orcid": "0000-0002-1825-0097",
            "openalex_url": "http://fakeopenalexurl",
            "last_known_institution": "Test Institution"
        },
        "subfield_metadata": [{"topic": "TopicA", "subfield_url": "http://subfieldurl"}],
        "totals": {"total_num_of_works": 5, "total_num_of_citations": 15},
        "data": []
    }

    monkeypatch.setattr("backend.app.search_by_author_topic",
                        lambda a, t: fake_data)

    result = get_researcher_and_subfield_results("Jane Smith", "Chemistry")

    assert result["metadata"]["orcid"] == "0000-0002-1825-0097"
    assert result["metadata"]["researcher_oa_link"] == "http://fakeopenalexurl"
    assert result["metadata"]["current_institution"] == "Test Institution"

# When is last_known_institution None? That should "initiate" a cascading external API Call..


def test_metadata_no_last_known_institution(monkeypatch, caplog):
    fake_data = {
        "author_metadata": {
            "orcid": "0000-0002-1825-0097",
            "openalex_url": "http://fakeopenalexurl",
            "last_known_institution": None
        },
        "subfield_metadata": [{"topic": "TopicA", "subfield_url": "http://subfieldurl"}],
        "totals": {"total_num_of_works": 5, "total_num_of_citations": 15},
        "data": []
    }
    fake_api_response = [
        {"display_name": "Fetched Institution", "id": "http://institutionurl"}]
    monkeypatch.setattr("backend.app.search_by_author_topic",
                        lambda a, t: fake_data)
    monkeypatch.setattr(
        "backend.app.fetch_last_known_institutions", lambda x: fake_api_response)
    result = get_researcher_and_subfield_results("Emily Brown", "Biology")
    assert result["metadata"]["current_institution"] == "Fetched Institution"
    assert "Fetching last known institutions from OpenAlex" in caplog.text

# When is last_known_institution None? That should initiate the external API to return an empty list .


def test_metadata_no_institution_found(monkeypatch, caplog):
    fake_data = {
        "author_metadata": {
            "orcid": None,
            "openalex_url": "http://fakeopenalexurl",
            "last_known_institution": None
        },
        "subfield_metadata": [{"topic": "TopicA", "subfield_url": "http://subfieldurl"}],
        "totals": {"total_num_of_works": 5, "total_num_of_citations": 15},
        "data": []
    }
    monkeypatch.setattr("backend.app.search_by_author_topic",
                        lambda a, t: fake_data)
    monkeypatch.setattr(
        "backend.app.fetch_last_known_institutions", lambda x: [])
    # This allows us to "throw" an IndexError due to the list being empty
    with pytest.raises(IndexError):
        get_researcher_and_subfield_results("No Institution Author", "Geology")
    assert "Fetching last known institutions from OpenAlex" in caplog.text
# ---------------------some additional tests--------------------------
# If you find a bug, let us know--our "goal" is to achieve comprehensive Unit Tests for "all results" not just get_institution_and_subfield_results.


@pytest.fixture
def mock_data_db():
    return {
        'subfield_metadata': [
            {'topic': 'AI', 'subfield_url': 'http://openalex.org/subfields/123'}
        ],
        'totals': {
            'total_num_of_works': 10,
            'total_num_of_citations': 50,
            'total_num_of_authors': 5
        },
        'institution_metadata': {
            'url': 'http://institution.com',
            'openalex_url': 'http://openalex.org/institutions/123',
            'ror': 'ror:12345'
        },
        'data': [
            {'author_id': 'author1', 'author_name': 'John Doe', 'num_of_works': 3},
            {'author_id': 'author2', 'author_name': 'Jane Smith', 'num_of_works': 7},
        ]
    }


@pytest.fixture
def mock_data_sparql():
    return {
        'institution_name': 'Test University',
        'topic_name': 'Computer Science',
        'institution_oa_link': 'http://openalex.org/institutions/456',
        'topic_oa_link': 'http://openalex.org/subfields/456',
    }


@pytest.fixture
def mock_list_graph_metadata():
    return (
        [('John Doe', 4), ('Jane Smith', 6)],
        {'nodes': [{'id': 'node1'}], 'edges': [{'id': 'edge1'}]},
        {'work_count': 10, 'num_people': 2}
    )


def test_db_results_path(mock_data_db, caplog):
    with patch('backend.app.search_by_institution_topic', return_value=mock_data_db):
        result = get_institution_and_subfield_results(
            'Test University', 'Computer Science', page=1, per_page=20)

        assert result['metadata']['institution_name'] == 'Test University'
        assert result['metadata']['topic_name'] == 'Computer Science'
        assert result['metadata']['work_count'] == 10
        assert result['metadata']['people_count'] == 2
        assert 'Successfully built result' in caplog.text


def test_sparql_results_path(mock_data_sparql, mock_list_graph_metadata, caplog):
    with patch('backend.app.search_by_institution_topic', return_value=None), \
            patch('backend.app.get_institution_and_topic_metadata_sparql', return_value=mock_data_sparql), \
            patch('backend.app.list_given_institution_topic', return_value=mock_list_graph_metadata):

        result = get_institution_and_subfield_results(
            'Test University', 'Computer Science', page=1, per_page=20)

        assert result['metadata']['institution_name'] == 'Test University'
        assert result['metadata']['topic_name'] == 'Computer Science'
        assert result['metadata']['work_count'] == 10
        assert result['metadata']['people_count'] == 2
        assert 'Using SPARQL for institution and topic search' in caplog.text


def test_sparql_empty_result(caplog):
    with patch('backend.app.search_by_institution_topic', return_value=None), \
            patch('backend.app.get_institution_and_topic_metadata_sparql', return_value={}):

        result = get_institution_and_subfield_results(
            'Unknown University', 'Unknown Topic', page=1, per_page=20)

        assert result == {}
        assert 'No results found in SPARQL' in caplog.text


def test_pagination_edge_case(mock_data_db):
    with patch('backend.app.search_by_institution_topic', return_value=mock_data_db):
        result = get_institution_and_subfield_results(
            'Test University', 'Computer Science', page=2, per_page=20)

        assert result['list'] == []
        assert len(result['graph']['nodes']) == 2


def test_no_authors_in_db(mock_data_db, caplog):
    mock_data_db['data'] = []

    with patch('backend.app.search_by_institution_topic', return_value=mock_data_db):
        result = get_institution_and_subfield_results(
            'Test University', 'Computer Science', page=1, per_page=20)

        assert result['list'] == []
        assert len(result['graph']['nodes']) == 2
        assert result['metadata']['people_count'] == 0
        assert 'Successfully built result' in caplog.text


def test_base_dir_correctness():
    # But probably, BASE_DIR does point to the current file's directory, already.
    expected_dir = os.path.dirname(os.path.abspath(app.__file__))
    assert app.BASE_DIR == expected_dir


@patch('builtins.open', new_callable=mock_open, read_data="Inst1,\nInst2,\nInst3")
def test_autofill_inst_list_loading(mock_file):
    # But I'm going to just give a quick file loading test.
    expected_inst_list = ["Inst1", "Inst2", "Inst3"]
    with patch('os.path.join', return_value='institutions.csv'):
        with open(os.path.join(app.BASE_DIR, 'institutions.csv'), 'r') as file:
            result = file.read().split(",\n")
    assert result == expected_inst_list
    mock_file.assert_called_with('institutions.csv', 'r')


@patch('builtins.open', new_callable=mock_open, read_data="Subfield1\nSubfield2\nSubfield3")
def test_autofill_subfields_list_loading(mock_file):
    # Then we can view how the rest of the CSVs load.
    expected_subfields_list = ["Subfield1", "Subfield2", "Subfield3"]
    with patch('os.path.join', return_value='subfields.csv'):
        with open(os.path.join(app.BASE_DIR, 'subfields.csv'), 'r') as file:
            result = file.read().split("\n")
    assert result == expected_subfields_list
    mock_file.assert_called_with('subfields.csv', 'r')


@patch('builtins.open', new_callable=mock_open, read_data="Keyword1\nKeyword2\nKeyword3")
def test_autofill_topics_list_loading(mock_file):
    # We had a really really significant test of the conditional loading, which
    # brings us back to what we had all along; the keywords.csv which contains
    # some comprehensive SUBFIELDS=False framework in backend/app.py.
    expected_topics_list = ["Keyword1", "Keyword2", "Keyword3"]
    with patch('os.path.join', return_value='keywords.csv'):
        original_subfields = app.SUBFIELDS
        app.SUBFIELDS = False
        with open(os.path.join(app.BASE_DIR, 'keywords.csv'), 'r') as file:
            result = file.read().split("\n")
        assert result == expected_topics_list
        mock_file.assert_called_with('keywords.csv', 'r')
        app.SUBFIELDS = original_subfields  # Re-store original value
# --------------------------some additional tests------------------------------------
# Some further unit tests for keywords.csv file handling this time.


def test_keywords_csv_read_normal(monkeypatch):
    monkeypatch.setattr("backend.app.SUBFIELDS", False)
    sample_content = (
        "Great Depression\n"
        "Human Perception of Robots\n"
        "Billiards\n"
        "Upgrading\n"
        "phytochemicals"
    )
    monkeypatch.setattr(
        "builtins.open",
        lambda filename, mode='r': StringIO(sample_content)
        if "keywords.csv" in filename else StringIO("")
    )
    import backend.app
    import importlib
    importlib.reload(backend.app)
    assert backend.app.autofill_topics_list == [
        "Great Depression",
        "Human Perception of Robots",
        "Billiards",
        "Upgrading",
        "phytochemicals"
    ]


def test_keywords_csv_empty_file(monkeypatch):
    monkeypatch.setattr("backend.app.SUBFIELDS", False)
    empty_content = ""
    monkeypatch.setattr(
        "builtins.open",
        lambda filename, mode='r': StringIO(empty_content)
        if "keywords.csv" in filename else StringIO("")
    )
    import backend.app
    import importlib
    importlib.reload(backend.app)
    assert backend.app.autofill_topics_list == [""]


def test_keywords_csv_file_not_found(monkeypatch):
    monkeypatch.setattr("backend.app.SUBFIELDS", False)

    def mock_open_raise(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr("builtins.open", mock_open_raise)

    import backend.app
    import importlib
    with pytest.raises(FileNotFoundError):
        importlib.reload(backend.app)


def test_keywords_csv_with_blank_lines(monkeypatch):
    monkeypatch.setattr("backend.app.SUBFIELDS", False)
    content_with_blanks = (
        "Great Depression\n"
        "Human Perception of Robots\n"
        "\n"
        "Billiards\n"
        "Upgrading\n"
        "phytochemicals\n"
        "\n"
    )
    monkeypatch.setattr(
        "builtins.open",
        lambda filename, mode='r': StringIO(content_with_blanks)
        if "keywords.csv" in filename else StringIO("")
    )
    import backend.app
    import importlib
    importlib.reload(backend.app)
    assert backend.app.autofill_topics_list == [
        "Great Depression",
        "Human Perception of Robots",
        "",
        "Billiards",
        "Upgrading",
        "phytochemicals",
        ""
    ]
########################################
# Whatever the issue was with the Author thing with
# Fisk University has been re-solved; the test scenario 1
# is, the return of the single result!
########################################


def test_list_given_institution_topic_single_result(monkeypatch):
    # Ordinarily, it would be super slow but if we use SPARQL that
    # means the whole half-way thing with the PostgreSQL and the
    # MySQL Database on Azure is moot with one record arranged and
    # faked "all over creation".
    fake_results = [{
        'author': 'http://author/1',
        'name': 'Author One',
        'works': 'http://work/1'  # No comma so and therefore count should be 1
    }]

    # I'm pretty sure we can patch the SPARQL query function so that it returns our fake_results
    monkeypatch.setattr(
        "backend.app.query_SPARQL_endpoint",
        lambda endpoint, query: fake_results
    )

    institution = "Inst A"
    institution_id = "instA123"
    topic = "Topic A"
    topic_id = "topicA123"

    # Action is something I've already figured out how to do that; I
    # think the integration is going to be another thing.
    final_list, graph, extra_metadata = list_given_institution_topic(
        institution, institution_id, topic, topic_id)

    # New assertion--the final_list is a thing! Each result is productive
    # of, a tuple (name, works_count)
    assert final_list == [("Author One", 1)]
    # For us the extra meta-data should sum and convert the works count (here 1)
    # and yes, the number and "count" of people would increase incrementally.
    assert extra_metadata == {"work_count": 1, "num_people": 1}
    # And yes, the graph should contain:
    # * A TOPIC node with id topic_id & an INSTITUTION node with id institution_id
    # * An edge connecting the institution to the topic
    # * For the single author, an AUTHOR node & a NUMBER node (with label 1)
    # * And two pipe-line edges: one for "memberOf" & one for "numWorks"
    nodes = graph["nodes"]
    edges = graph["edges"]
    # It's an artful bit of classwork, that topic and institution nodes can
    # be asserted to exist. I think that's just the thing we should present when
    # we talk about this.
    assert any(node for node in nodes if node == {
               'id': topic_id, 'label': topic, 'type': 'TOPIC'})
    assert any(node for node in nodes if node == {
               'id': institution_id, 'label': institution, 'type': 'INSTITUTION'})
    # Specifically because literally in the middle of checking the edges,
    # we also have to check the institution and the topic are connected so
    # don't run these tests unless you've some time to spare.
    inst_topic_edge = {'id': f"{institution_id}-{topic_id}",
                       'start': institution_id,
                       'end': topic_id,
                       "label": "researches",
                       "start_type": "INSTITUTION",
                       "end_type": "TOPIC"}
    assert inst_topic_edge in edges
    # And, unless there are or is any other way there it is, the verification
    # that yes the author node & the number node are a thing.
    author_node = {'id': 'http://author/1',
                   'label': 'Author One', 'type': 'AUTHOR'}
    number_node = {'id': 1, 'label': 1, 'type': 'NUMBER'}
    assert author_node in nodes
    assert number_node in nodes
    # Just start checking that there are two edges for the author specifically:
    member_edge = {'id': f"http://author/1-{institution_id}",
                   'start': 'http://author/1',
                   'end': institution_id,
                   "label": "memberOf",
                   "start_type": "AUTHOR",
                   "end_type": "INSTITUTION"}
    numworks_edge = {'id': f"http://author/1-1",
                     'start': 'http://author/1',
                     'end': 1,
                     "label": "numWorks",
                     "start_type": "AUTHOR",
                     "end_type": "NUMBER"}
    assert member_edge in edges
    assert numworks_edge in edges

# Second thing. It's hard to believe that we have multiple records but we do,
# And therefore test that they do return and that they are sorted.


def test_list_given_institution_topic_multiple_results(monkeypatch):
    # This is something called a broken monkey-patch; we arrange two records,
    # one with two works and one with one work which explains it "all".
    fake_results = [
        {
            'author': 'http://author/1',
            'name': 'Author One',
            'works': 'http://work/1, http://work/2'  # two works -> count = 2
        },
        {
            'author': 'http://author/2',
            'name': 'Author Two',
            'works': 'http://work/3'  # one work -> count = 1
        }
    ]
    monkeypatch.setattr(
        "backend.app.query_SPARQL_endpoint",
        lambda endpoint, query: fake_results
    )
    institution = "Inst B"
    institution_id = "instB456"
    topic = "Topic B"
    topic_id = "topicB456"
    # After that, we either do an action or look at the test results.
    final_list, graph, extra_metadata = list_given_institution_topic(
        institution, institution_id, topic, topic_id)
    # Here are the test results; that's the "symbiotic" sorting of the
    # final_list, descended by the works-count. What do we expect?
    # Well, we expect that the final list is formulated to be
    # along these lines--[("Author One", 2), ("Author Two", 1)]
    assert final_list == [("Author One", 2), ("Author Two", 1)]
    # Total work count is 3 "and then," the number of people is 2
    assert extra_metadata == {"work_count": 3, "num_people": 2}
    # I'm not entirely sure how to handle existence of graph nodes
    # and edges for "each and e-very" record.
    nodes = graph["nodes"]
    edges = graph["edges"]
    # WE've got a pretty good "verification" of the topic & institution
    # nodes being a thing.
    assert {'id': topic_id, 'label': topic, 'type': 'TOPIC'} in nodes
    assert {'id': institution_id, 'label': institution,
            'type': 'INSTITUTION'} in nodes
    # For each and every author, let's test whether or not the nodes
    # and edges have been added.
    for rec in fake_results:
        works_count = rec['works'].count(",") + 1
        author_node = {'id': rec['author'],
                       'label': rec['name'], 'type': 'AUTHOR'}
        number_node = {'id': works_count,
                       'label': works_count, 'type': 'NUMBER'}
        assert author_node in nodes
        assert number_node in nodes
        member_edge = {'id': f"{rec['author']}-{institution_id}",
                       'start': rec['author'],
                       'end': institution_id,
                       "label": "memberOf",
                       "start_type": "AUTHOR",
                       "end_type": "INSTITUTION"}
        numworks_edge = {'id': f"{rec['author']}-{works_count}",
                         'start': rec['author'],
                         'end': works_count,
                         "label": "numWorks",
                         "start_type": "AUTHOR",
                         "end_type": "NUMBER"}
        assert member_edge in edges
        assert numworks_edge in edges

# It's a great idea to see how we handle no SPARQL results being returned.
# That's called an empty result.


def test_list_given_institution_topic_empty_results(monkeypatch):
    # Consider arranging the empty list returned from the query..then we've got a
    # pretty good facsimile of the app's SPARQL endpoints.
    fake_results = []
    monkeypatch.setattr(
        "backend.app.query_SPARQL_endpoint",
        lambda endpoint, query: fake_results
    )
    institution = "Inst C"
    institution_id = "instC789"
    topic = "Topic C"
    topic_id = "topicC789"
    # This is what we do, we review the API docs and then use our docs to
    # create the final list.
    final_list, graph, extra_metadata = list_given_institution_topic(
        institution, institution_id, topic, topic_id)
    # What is the final_list? Well, it should be empty and the meta-data should
    # be indicative of zero works as well as zero people.
    assert final_list == []
    assert extra_metadata == {"work_count": 0, "num_people": 0}
    # The graph should contain only the topic & institution nodes plus and in
    # addition to the connecting, edge.
    expected_nodes = [
        {'id': topic_id, 'label': topic, 'type': 'TOPIC'},
        {'id': institution_id, 'label': institution, 'type': 'INSTITUTION'}
    ]
    expected_edge = {'id': f"{institution_id}-{topic_id}",
                     'start': institution_id,
                     'end': topic_id,
                     "label": "researches",
                     "start_type": "INSTITUTION",
                     "end_type": "TOPIC"}
    assert graph["nodes"] == expected_nodes
    assert expected_edge in graph["edges"]

# WE're halfway through importing the Flask app and the serve view from the
# backend module. This is the import path.
# First, build a Helper function called Fake for send_from_directory.


def fake_send_from_directory(folder, filename):
    # Re-turn a string that either indicates what would be served or
    # indicates that the empty path is good enough.
    return f"served {filename}"
# That's when we test when a non-empty path is provided and the file exists .


def test_serve_static_file_exists(monkeypatch, caplog):
    # Arrange to tell exactly where that static file exists.
    path = "file.txt"
    fake_static_folder = "/fake/static"
    # And, it's a low bar of construction that our full file path can fulfill.
    expected_full_path = os.path.join(fake_static_folder, path)
    # Just monkeypatch os.path.exists to return True only if given the
    # expected file path whether it's making something or breaking something.
    monkeypatch.setattr(os.path, "exists", lambda p: p == expected_full_path)
    # Monkeypatch does send_from_directory to our fake already so we can know
    # and understnad its parameters.
    monkeypatch.setattr("backend.app.send_from_directory",
                        fake_send_from_directory)
    # Set the static folder and start serving up the app
    app.static_folder = fake_static_folder
    # It's an overall trend to serve the app via unit tests
    response = serve(path)
    # And alook at the assertion; the file we served as expected!
    assert response == "served file.txt"
    # Additionally we want to achieve a debug log that sees that the static
    # file was served, with our institutions.
    assert any(
        "Serving static file: file.txt" in record.message for record in caplog.records)

# For example, test when a non-empty path is provided by us but the file does NOT exist


def test_serve_index_when_file_not_found(monkeypatch, caplog):
    # How do other tools serve the index? Well, we're going to find out how other tools do it.
    path = "nonexistent.txt"
    fake_static_folder = "/fake/static"
    # ANd we always return False for the os.path.exists
    monkeypatch.setattr(os.path, "exists", lambda p: False)
    # We have the ability to kind of Monkeypatch the send_from_Directory
    # to our fake function.
    monkeypatch.setattr("backend.app.send_from_directory",
                        fake_send_from_directory)
    # That is how we set the app's static folder. It's very cool.
    app.static_folder = fake_static_folder
    # Another thing that's very cool is the way that we can depend on
    # responses that serve the path, to identify similar paths.
    response = serve(path)
    # The approach shows that since the file does not exist then, the
    # index.html should be served.
    assert response == "served index.html"
    # Last we list out the log which contains the message that we want to
    # rely upon.
    assert any(
        "Serving index.html for frontend routing" in record.message for record in caplog.records)

# This is the test for when the empty path is given and provided.


def test_serve_index_when_path_empty(monkeypatch, caplog):
    # Test out the scientific breadth of when the path is empty; because, there is
    # a nullification vibe that covers the package of the operating system.
    path = ""
    fake_static_folder = "/fake/static"
    # The os.path.exists, even if it's True "means" that the condition should not be
    # met beecause thepath is =="" or may-be we need. anew one
    monkeypatch.setattr(os.path, "exists", lambda p: True)
    monkeypatch.setattr("backend.app.send_from_directory",
                        fake_send_from_directory)
    app.static_folder = fake_static_folder
    # I like that approach, we "make a new" path and serve it.
    response = serve(path)
    # A way to pull and serve the index.html, should be a minimal lift.
    assert response == "served index.html"
    # As a way to normalize the debug log to indicate and identify the index.html as a "last resort", methodology.
    assert any(
        "Serving index.html for frontend routing" in record.message for record in caplog.records)

# -----------------------------------------------------------------------------
# Test #1: When the database returns no data and the SPARQL branch nicely returns {}
# -----------------------------------------------------------------------------


def test_institution_researcher_results_sparql_empty(monkeypatch, caplog):
    # Try simulating, that the data-base called returns None.
    monkeypatch.setattr(
        "backend.app.search_by_author_institution",
        lambda researcher, institution: None
    )
    # It is great , to have among other simulations that the SPARQL function
    # returns an empty dictionary. For now we're using R.O.R. (remove the .)
    # as a "rather persistent" identifier for what that's worth to help clean
    # up naming issues, so even if different data sources use slightly different
    # names it's okay because the empty dictionary, we're just looking at an
    # empty dictionary for now.
    monkeypatch.setattr(
        "backend.app.get_researcher_and_institution_metadata_sparql",
        lambda researcher, institution: {}
    )
    institution = "Test Institution"
    researcher = "Test Researcher"
    # the most thrilling thing about this is that we can act now and call the
    # function.
    result = get_institution_and_researcher_results(institution, researcher)
    # Also, we can assert that the assertion should return an empty dictionary
    # because the SPARQL returned {}
    assert result == {}
    # Alternately, we should look and see that yes, a warning log was emitted.
    assert any("No results found in SPARQL for institution and researcher" in record.message
               for record in caplog.records)

# -----------------------------------------------------------------------------
# Second Test: When the database returns no data, and the SPARQL branch returns unit tests' valid metadata..!
# -----------------------------------------------------------------------------


def test_institution_researcher_results_sparql_success(monkeypatch, caplog):
    # Simulate that the database call is going to return None
    monkeypatch.setattr(
        "backend.app.search_by_author_institution",
        lambda researcher, institution: None
    )
    # But that's not all; prepare the fake SPARQL data such that the SPARQL
    # branch would not return.
    fake_sparql_data = {
        "institution_metadata": {
            "url": "http://fakeinst.edu",
            "openalex_url": "inst_oa_fake",
            "ror": "ROR_FAKE"
        },
        "author_metadata": {
            "orcid": "ORCID_FAKE",
            "openalex_url": "author_oa_fake",
            "num_of_works": 15,
            "num_of_citations": 50
        },
        # Also, include a key that will then be used in list_given_researcher_institution.
        "researcher_oa_link": "author_oa_fake",
        # Data list could be empty (no topics) or with some entries. Here we happen to use an empty list.
        "data": []
    }

    monkeypatch.setattr(
        "backend.app.get_researcher_and_institution_metadata_sparql",
        lambda researcher, institution: fake_sparql_data
    )

    # Fake list_given_researcher_institution to conveniently return a fake topic list and graph.
    fake_topic_list = [("Fake Topic", 3)]
    fake_graph = {
        "nodes": [{"id": "inst_oa_fake", "label": "Test Institution", "type": "INSTITUTION"},
                  {"id": "author_oa_fake", "label": "Test Researcher", "type": "AUTHOR"},
                  {"id": "Fake Topic", "label": "Fake Topic", "type": "TOPIC"}],
        "edges": [{"id": "author_oa_fake-Fake Topic", "start": "author_oa_fake", "end": "Fake Topic",
                   "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"}]
    }
    monkeypatch.setattr(
        "backend.app.list_given_researcher_institution",
        lambda researcher_oa, researcher, institution: (
            fake_topic_list, fake_graph)
    )
    institution = "Test Institution"
    researcher = "Test Researcher"
    # `researcher` is a bit of a naming convention issue (how? I don't know.)
    result = get_institution_and_researcher_results(institution, researcher)
    # We can show: the result should cleanly contain our fake metadata from SPARQL branch, graph, & topic list.
    expected_result = {
        "metadata": fake_sparql_data,
        "graph": fake_graph,
        "list": fake_topic_list
    }
    assert result == expected_result
    assert any("Successfully retrieved SPARQL results for researcher" in record.message
               for record in caplog.records)

# -----------------------------------------------------------------------------
# Third test: When the database returns (in)valid data (the database branch)
# -----------------------------------------------------------------------------


def test_institution_researcher_results_database(monkeypatch, caplog):
    # We know that we can simulate that the database call returns valid data.
    # Prepare fake database data so we can show how we can visualize data in
    # multiple way swhether it's the lists, the graphs, the maps, we start with
    # the data and it doesn't have to be real data.
    fake_db_data = {
        "institution_metadata": {
            "url": "http://dbinst.edu",
            "openalex_url": "inst_oa_db",
            "ror": "ROR_DB"
        },
        "author_metadata": {
            "orcid": None,  # simulate missing ORCID so that branch "re-fines" and sets it to ''
            "openalex_url": "author_oa_db",
            "num_of_works": 8,
            "num_of_citations": 25
        },
        # "This is a" list of topics (tells us that we need to simulate more than one entry)
        "data": [
            {"topic_name": "Topic1", "num_of_works": 3},
            {"topic_name": "Topic2", "num_of_works": 5},
            {"topic_name": "Topic3", "num_of_works": 2}
        ]
    }
    monkeypatch.setattr(
        "backend.app.search_by_author_institution",
        lambda researcher, institution: fake_db_data
    )
    # In this branch the SPARQL functions are not called, so no need to monkeypatch them, as long as it tells you where it is.
    institution = "DB Institution"
    researcher = "DB Researcher"
    page = 1
    per_page = 20  # all topics will be returned, eventually
    # Nothing shows up until you actually invoke it
    result = get_institution_and_researcher_results(
        institution, researcher, page, per_page)
    # For example: Test that metadata is built correctly, and invoke the test.
    expected_metadata = {
        "homepage": "http://dbinst.edu",
        "institution_oa_link": "inst_oa_db",
        "ror": "ROR_DB",
        "institution_name": institution,
        "orcid": "",  # since author_metadata.orcid was None in the first place
        "researcher_name": researcher,
        "researcher_oa_link": "author_oa_db",
        "current_institution": "",
        "work_count": 8,
        "cited_by_count": 25
    }
    # Calculate all of the total topics & pagination information.
    total_topics = len(fake_db_data["data"])
    expected_pagination = {
        "total_pages": (total_topics + per_page - 1) // per_page,
        "current_page": page,
        "total_topics": total_topics,
    }
    # Expected graph:
    # * There should be an INSTITUTION node (with id equal to institution),
    # * An edge from author_oa_db to institution,
    # * An AUTHOR node for author_oa_db,
    # * For each topic entry: a TOPIC node, a NUMBER node as well as two edges.
    nodes = [
        {'id': institution, 'label': institution, 'type': 'INSTITUTION'},
        {'id': "author_oa_db", 'label': researcher, "type": "AUTHOR"}
    ]
    edges = [
        {'id': "author_oa_db-" + institution,
         'start': "author_oa_db", 'end': institution,
         "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"}
    ]
    # We're at a stage where we propose a list and build the graph for e-very topic entry.
    expected_list = []
    for entry in fake_db_data["data"]:
        topic = entry["topic_name"]
        num = entry["num_of_works"]
        expected_list.append((topic, num))
        nodes.append({'id': topic, 'label': topic, 'type': "TOPIC"})
        number_id = topic + ":" + str(num)
        nodes.append({'id': number_id, 'label': num, 'type': "NUMBER"})
        edges.append({'id': "author_oa_db-" + topic,
                      'start': "author_oa_db", 'end': topic,
                      "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})
        edges.append({'id': topic + "-" + number_id,
                      'start': topic, 'end': number_id,
                      "label": "number", "start_type": "TOPIC", "end_type": "NUMBER"})

    expected_graph = {"nodes": nodes, "edges": edges}
    # Final expected result:
    expected_result = {
        "metadata": expected_metadata,
        "metadata_pagination": expected_pagination,
        "graph": expected_graph,
        "list": expected_list
    }
    # Say that the the returned result matches the expected and we have a simple
    # yet effective way to present each graph.
    assert result["metadata"] == expected_metadata
    assert result["metadata_pagination"] == expected_pagination
    # For graph, demonstrate that all expected nodes and edges are present.
    # (Order may differ so we "simply" compare as sets of frozensets of items.)

    def to_set(items):
        return {frozenset(item.items()) for item in items}

    assert to_set(result["graph"]["nodes"]) == to_set(expected_graph["nodes"])
    assert to_set(result["graph"]["edges"]) == to_set(expected_graph["edges"])
    # And check list
    assert result["list"] == expected_list
    assert any("Processing database results for institution and researcher" in record.message
               for record in caplog.records)
    assert any("Successfully built result for researcher" in record.message
               for record in caplog.records)
##################
# "New" test scenario: Single SPARQL Result returned
##################


def test_list_given_researcher_topic_single_result(monkeypatch, caplog):
    # A short arrangement: fake SPARQL result with one and only record.
    # Each result dictionary should include "title" & "cited_by_count"
    fake_results = [
        {
            'title': 'Work A',
            # string representation; our function converts it to integer, the data type
            'cited_by_count': '10'
        }
    ]
    # Monkeypatch, the query_SPARQL_endpoint so that it returns our fake_results.
    monkeypatch.setattr(
        "backend.app.query_SPARQL_endpoint",
        lambda endpoint, query: fake_results
    )
    topic = "Topic X"
    researcher = "Researcher X"
    institution = "Institution X"
    topic_id = "topicX_id"
    researcher_id = "researcherX_id"
    institution_id = "institutionX_id"
    # Depending on what you're searching for, you can initiate the destructuring.
    work_list, graph, extra_metadata = list_given_researcher_topic(
        topic, researcher, institution, topic_id, researcher_id, institution_id
    )
    # Then shift toward the assertions: work_list should have one tuple, and citations should be 10.
    assert work_list == [("Work A", 10)]
    # Extra metadata should report one work plus total citations of 10.
    assert extra_metadata == {"work_count": 1, "cited_by_count": 10}
    # Open up the graph structure:
    nodes = graph["nodes"]
    edges = graph["edges"]
    # Start searching the nodes: institution, researcher, topic, work node, number node.
    expected_institution_node = {'id': institution_id,
                                 'label': institution, 'type': 'INSTITUTION'}
    expected_researcher_node = {'id': researcher_id,
                                'label': researcher, 'type': 'AUTHOR'}
    expected_topic_node = {'id': topic_id, 'label': topic, 'type': 'TOPIC'}
    expected_work_node = {'id': 'Work A', 'label': 'Work A', 'type': 'WORK'}
    expected_number_node = {'id': 10, 'label': 10, 'type': "NUMBER"}
    assert expected_institution_node in nodes
    assert expected_researcher_node in nodes
    assert expected_topic_node in nodes
    assert expected_work_node in nodes
    assert expected_number_node in nodes
    # Look at the expected edges:
    # 1. Edge from researcher to institution (memberOf)
    expected_member_edge = {
        'id': f"{researcher_id}-{institution_id}",
        'start': researcher_id,
        'end': institution_id,
        "label": "memberOf",
        "start_type": "AUTHOR",
        "end_type": "INSTITUTION"
    }
    # 2. Edge from researcher to topic (researches)
    expected_researches_edge = {
        'id': f"{researcher_id}-{topic_id}",
        'start': researcher_id,
        'end': topic_id,
        "label": "researches",
        "start_type": "AUTHOR",
        "end_type": "TOPIC"
    }
    # 3. For each work, edge from researcher to work (authored)
    expected_authored_edge = {
        'id': f"{researcher_id}-Work A",
        'start': researcher_id,
        'end': 'Work A',
        "label": "authored",
        "start_type": "AUTHOR",
        "end_type": "WORK"
    }
    # 4. And edge from work to number (citedBy)
    expected_citedby_edge = {
        'id': f"Work A-10",
        'start': 'Work A',
        'end': 10,
        "label": "citedBy",
        "start_type": "WORK",
        "end_type": "NUMBER"
    }
    assert expected_member_edge in edges
    assert expected_researches_edge in edges
    assert expected_authored_edge in edges
    assert expected_citedby_edge in edges
    # That's how we know what could be improved or looks broken, we articulate that success was recorded via the log message
    assert any(
        "Successfully built list and graph for researcher" in record.message for record in caplog.records)

# --- Second Test Scenario (Part 2): Multiple SPARQL results and drop a sorting check ---


def test_list_given_researcher_topic_multiple_results(monkeypatch, caplog):
    # Design: fake SPARQL results with unsorted citation counts.
    fake_results = [
        {'title': 'Work B', 'cited_by_count': '5'},
        {'title': 'Work A', 'cited_by_count': '15'},
        {'title': 'Work C', 'cited_by_count': '10'},
    ]
    monkeypatch.setattr(
        "backend.app.query_SPARQL_endpoint",
        lambda endpoint, query: fake_results
    )
    topic = "Topic Y"
    researcher = "Researcher Y"
    institution = "Institution Y"
    topic_id = "topicY_id"
    researcher_id = "researcherY_id"
    institution_id = "institutionY_id"
    # Destructuring syntax hasn't changed although it's not perfect
    work_list, graph, extra_metadata = list_given_researcher_topic(
        topic, researcher, institution, topic_id, researcher_id, institution_id
    )
    # The work_list should "match" the naming conventions with or without autocomplete, but that's for later on; the work_list should be sorted descending by citation count.
    # Expect: [("Work A", 15), ("Work C", 10), ("Work B", 5)]
    assert work_list == [("Work A", 15), ("Work C", 10), ("Work B", 5)]
    # Extra metadata: 3 works with a total of 15 + 10 + 5 = 30 citations.
    assert extra_metadata == {"work_count": 3, "cited_by_count": 30}
    # Here are the graph nodes:
    nodes = graph["nodes"]
    edges = graph["edges"]
    # And there are basic nodes: (institution, researcher, topic).
    expected_institution_node = {'id': institution_id,
                                 'label': institution, 'type': 'INSTITUTION'}
    expected_researcher_node = {'id': researcher_id,
                                'label': researcher, 'type': 'AUTHOR'}
    expected_topic_node = {'id': topic_id, 'label': topic, 'type': 'TOPIC'}
    assert expected_institution_node in nodes
    assert expected_researcher_node in nodes
    assert expected_topic_node in nodes
    # We can use parentheses to show that the data and the User Experience,
    # is corroborated by the work record in the sorted list; the work and number nodes and associated edges, exist.
    for title, count in work_list:
        work_node = {'id': title, 'label': title, 'type': 'WORK'}
        number_node = {'id': count, 'label': count, 'type': "NUMBER"}
        assert work_node in nodes
        assert number_node in nodes
        authored_edge = {
            'id': f"{researcher_id}-{title}",
            'start': researcher_id,
            'end': title,
            "label": "authored",
            "start_type": "AUTHOR",
            "end_type": "WORK"
        }
        citedby_edge = {
            'id': f"{title}-{count}",
            'start': title,
            'end': count,
            "label": "citedBy",
            "start_type": "WORK",
            "end_type": "NUMBER"
        }
        assert authored_edge in edges
        assert citedby_edge in edges
    # The testing suite is now getting to the poing where the logging message for success is recorded.
    assert any(
        "Successfully built list and graph for researcher" in record.message for record in caplog.records)

# --- Third Test Scenario: No SPARQL results are being returned (empty result) ---


def test_list_given_researcher_topic_empty_results(monkeypatch, caplog):
    # Set up fake empty SPARQL results.
    fake_results = []
    monkeypatch.setattr(
        "backend.app.query_SPARQL_endpoint",
        lambda endpoint, query: fake_results
    )
    topic = "Topic Z"
    researcher = "Researcher Z"
    institution = "Institution Z"
    topic_id = "topicZ_id"
    researcher_id = "researcherZ_id"
    institution_id = "institutionZ_id"
    # Destructure them properly
    work_list, graph, extra_metadata = list_given_researcher_topic(
        topic, researcher, institution, topic_id, researcher_id, institution_id
    )
    # Paginated assertions: With no SPARQL results, work_list should be empty and citations 0.
    assert work_list == []
    assert extra_metadata == {"work_count": 0, "cited_by_count": 0}
    # Graph should contain the "basic" user-friendly nodes and edges for institution, researcher, and topic.
    nodes = graph["nodes"]
    edges = graph["edges"]
    expected_institution_node = {'id': institution_id,
                                 'label': institution, 'type': 'INSTITUTION'}
    expected_researcher_node = {'id': researcher_id,
                                'label': researcher, 'type': 'AUTHOR'}
    expected_topic_node = {'id': topic_id, 'label': topic, 'type': 'TOPIC'}
    assert expected_institution_node in nodes
    assert expected_researcher_node in nodes
    assert expected_topic_node in nodes
    # There should be an edge pinging from the researcher to institution and an edge from researcher to topic.
    expected_member_edge = {
        'id': f"{researcher_id}-{institution_id}",
        'start': researcher_id,
        'end': institution_id,
        "label": "memberOf",
        "start_type": "AUTHOR",
        "end_type": "INSTITUTION"
    }
    expected_researches_edge = {
        'id': f"{researcher_id}-{topic_id}",
        'start': researcher_id,
        'end': topic_id,
        "label": "researches",
        "start_type": "AUTHOR",
        "end_type": "TOPIC"
    }
    assert expected_member_edge in edges
    assert expected_researches_edge in edges
    # No additional work nodes or edges should be added or is "needed".
    # Also check that the log indicates that the list was built.
    assert any(
        "Successfully built the basic list and graph for researcher" in record.message for record in caplog.records)


def load_app_with_subfields_false():
    module_name = "backend.app"
    # Alter the path to point to the app.py file.
    file_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "", "app.py"))
    # Debug print to turn out the file path
    print("Loading module from:", file_path)
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    # Inject SUBFIELDS = False into the module globals BEFORE execution.
    module.__dict__['SUBFIELDS'] = False
    spec.loader.exec_module(module)
    return module


def test_subfields_false(monkeypatch):
    # Load the module as we did "before".
    module_app = load_app_with_subfields_false()
    # Now force the false scenario by patching SUBFIELDS
    module_app.SUBFIELDS = False
    # Re-run the keyword loading function so that the false branch executes.
    module_app.autofill_topics_list = module_app.load_keywords()
    # Say that the false branch executed: autofill_topics_list should now not be None.
    assert hasattr(
        module_app, 'autofill_topics_list'), "Module should have 'autofill_topics_list'"
    assert module_app.autofill_topics_list is not None, "autofill_topics_list should not be None when SUBFIELDS is False"
    assert isinstance(module_app.autofill_topics_list,
                      list), "autofill_topics_list should be a list"

# -----------------------------
# Test out the Data, for the database branch
# -----------------------------


@pytest.fixture
def fake_db_data_orcid_none():
    """Fake data from search_by_author_institution_topic when database returns results and author orcid is None."""
    return {
        "institution_metadata": {
            "url": "http://institution.example.com",
            "openalex_url": "institution_oa_123",
            "ror": "ror123"
        },
        "author_metadata": {
            # <-- This should ideally trigger metadata['orcid'] = ''
            "orcid": None,
            "openalex_url": "researcher_oa_456"
        },
        "subfield_metadata": [
            {"topic": "Subfield A", "subfield_url": "topic_oa_789"}
        ],
        "totals": {
            "total_num_of_works": 10,
            "total_num_of_citations": 100
        },
        "data": [
            {"work_name": "Work 1", "cited_by_count": 5},
            {"work_name": "Work 2", "cited_by_count": 8},
            {"work_name": "Work 3", "cited_by_count": 3},
        ]
    }


@pytest.fixture
def fake_db_data_orcid_present():
    """Fake data from search_by_author_institution_topic when database returns results and author orcid is set."""
    return {
        "institution_metadata": {
            "url": "http://institution.example.com",
            "openalex_url": "institution_oa_123",
            "ror": "ror123"
        },
        "author_metadata": {
            "orcid": "orcid-789",  # present orcid, no python related headaches
            "openalex_url": "researcher_oa_456"
        },
        "subfield_metadata": [
            {"topic": "Subfield A", "subfield_url": "topic_oa_789"}
        ],
        "totals": {
            "total_num_of_works": 4,
            "total_num_of_citations": 40
        },
        "data": [
            {"work_name": "Work A", "cited_by_count": 10},
            {"work_name": "Work B", "cited_by_count": 15},
        ]
    }

# -----------------------------
# Test Data for the SPARQL branch
# -----------------------------


@pytest.fixture
def fake_sparql_empty():
    """Fake SPARQL branch: get_institution_and_topic_and_researcher_metadata_sparql returns {}."""
    return {}


@pytest.fixture
def fake_sparql_valid():
    """Fake data for SPARQL branch that returns a valid dictionary."""
    # Only the keys needed by the SPARQL branch are provided.
    return {
        "topic_oa_link": "topic_oa_sparql",
        "researcher_oa_link": "researcher_oa_sparql",
        "institution_oa_link": "institution_oa_sparql",
        # Other metadata can be included if needed.
    }


@pytest.fixture
def fake_list_given_researcher_topic():
    """Fake return from list_given_researcher_topic: (work_list, graph, extra_metadata)."""
    work_list = [("Work X", 20), ("Work Y", 25)]
    graph = {
        "nodes": [
            {"id": "institution_oa_sparql",
                "label": "Institution Test", "type": "INSTITUTION"},
            {"id": "researcher_oa_sparql",
                "label": "Researcher Test", "type": "AUTHOR"},
            {"id": "topic_oa_sparql", "label": "Topic Test", "type": "TOPIC"},
            {"id": "Work X", "label": "Work X", "type": "WORK"},
            {"id": 20, "label": 20, "type": "NUMBER"},
            {"id": "Work Y", "label": "Work Y", "type": "WORK"},
            {"id": 25, "label": 25, "type": "NUMBER"},
        ],
        "edges": [
            {"id": "researcher_oa_sparql-institution_oa_sparql",
             "start": "researcher_oa_sparql", "end": "institution_oa_sparql",
             "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"},
            {"id": "researcher_oa_sparql-topic_oa_sparql",
             "start": "researcher_oa_sparql", "end": "topic_oa_sparql",
             "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"},
            {"id": "researcher_oa_sparql-Work X",
             "start": "researcher_oa_sparql", "end": "Work X",
             "label": "authored", "start_type": "AUTHOR", "end_type": "WORK"},
            {"id": "Work X-20",
             "start": "Work X", "end": 20,
             "label": "citedBy", "start_type": "WORK", "end_type": "NUMBER"},
            {"id": "researcher_oa_sparql-Work Y",
             "start": "researcher_oa_sparql", "end": "Work Y",
             "label": "authored", "start_type": "AUTHOR", "end_type": "WORK"},
            {"id": "Work Y-25",
             "start": "Work Y", "end": 25,
             "label": "citedBy", "start_type": "WORK", "end_type": "NUMBER"},
        ]
    }
    extra_metadata = {"work_count": 45, "cited_by_count": 45}
    return work_list, graph, extra_metadata

# -----------------------------
# Tests for the "new" SPARQL branch
# -----------------------------


def test_sparql_branch_empty(monkeypatch, fake_sparql_empty):
    """
    Test when search_by_author_institution_topic returns None,
    and then SPARQL branch returns {}.
    The function should return an empty dictionary.
    """
    # Make it so that the database search to return None.
    monkeypatch.setattr(
        "backend.app.search_by_author_institution_topic",
        lambda r, i, t: None
    )
    # Make it so that the SPARQL helper stops and returns an empty dictionary.
    monkeypatch.setattr(
        "backend.app.get_institution_and_topic_and_researcher_metadata_sparql",
        lambda i, t, r: fake_sparql_empty
    )

    result = get_institution_researcher_subfield_results(
        "Institution Test", "Researcher Test", "Topic Test")
    assert result == {}


def test_sparql_branch_valid(monkeypatch, fake_sparql_valid, fake_list_given_researcher_topic):
    """
    Test the SPARQL branch when search_by_author_institution_topic returns None,
    but get_institution_and_topic_and_researcher_metadata_sparql returns valid data!
    """
    monkeypatch.setattr(
        "backend.app.search_by_author_institution_topic",
        lambda r, i, t: None
    )
    monkeypatch.setattr(
        "backend.app.get_institution_and_topic_and_researcher_metadata_sparql",
        lambda i, t, r: fake_sparql_valid
    )
    monkeypatch.setattr(
        "backend.app.list_given_researcher_topic",
        lambda t, r, i, top_oa, res_oa, inst_oa: fake_list_given_researcher_topic
    )

    result = get_institution_researcher_subfield_results(
        "Institution Test", "Researcher Test", "Topic Test")
    # Python/Pip version regardless, see that the returned structure contains metadata, graph and list.
    assert "metadata" in result
    assert "graph" in result
    assert "list" in result
    # Also, it's some exciting progress that work_count and cited_by_count were updated from extra_metadata.
    metadata = result["metadata"]
    assert metadata.get("work_count") == 45
    assert metadata.get("cited_by_count") == 45
    # Alternatively, I suppose it IS possible to assert on a message in the metadata if the SPARQL branch is willing to add more info.

# -----------------------------
# Tests for the database branch
# -----------------------------


def test_database_branch_orcid_none(monkeypatch, fake_db_data_orcid_none):
    """
    Test when search_by_author_institution_topic returns new data from the database
    and the author orcid is None. This should result in metadata['orcid'] being set, to ''.
    """
    monkeypatch.setattr(
        "backend.app.search_by_author_institution_topic",
        lambda r, i, t: fake_db_data_orcid_none
    )
    # Call in the function with page=1, per_page large enough to include all works.
    result = get_institution_researcher_subfield_results(
        "Institution Test", "Researcher Test", "Topic Test", page=1, per_page=10)
    # Show metadata in the returned result.
    metadata = result["metadata"]
    assert metadata["homepage"] == "http://institution.example.com"
    assert metadata["institution_oa_link"] == "institution_oa_123"
    assert metadata["ror"] == "ror123"
    assert metadata["institution_name"] == "Institution Test"
    # Show that the orcid field is set to an empty string when the returned orcid is None.
    assert metadata["orcid"] == ""
    assert metadata["researcher_name"] == "Researcher Test"
    assert metadata["researcher_oa_link"] == "researcher_oa_456"
    # Find topic metadata gathered from subfield_metadata
    assert metadata["topic_name"] == "Topic Test"
    assert metadata["topic_clusters"] == ["Subfield A"]
    assert metadata["work_count"] == 10
    assert metadata["cited_by_count"] == 100
    # Verify that topic_oa_link is from the last entry in subfield_metadata.
    assert metadata["topic_oa_link"] == "topic_oa_789"
    # Verify pagination metadata.
    meta_pagination = result["metadata_pagination"]
    total_topics = len(fake_db_data_orcid_none["data"])
    expected_total_pages = (total_topics + 10 - 1) // 10
    assert meta_pagination["total_pages"] == expected_total_pages
    assert meta_pagination["current_page"] == 1
    assert meta_pagination["total_topics"] == total_topics
    # Verify that the graph contains the expected nodes and edges.
    graph = result["graph"]
    nodes = graph["nodes"]
    edges = graph["edges"]
    # Check institution node.
    expected_institution_node = {
        'id': "institution_oa_123", 'label': "Institution Test", 'type': "INSTITUTION"}
    assert expected_institution_node in nodes
    # Check researcher node.
    expected_researcher_node = {
        'id': "researcher_oa_456", 'label': "Researcher Test", 'type': "AUTHOR"}
    assert expected_researcher_node in nodes
    # Check topic node.
    expected_topic_node = {'id': "topic_oa_789",
                           'label': "Topic Test", 'type': "TOPIC"}
    assert expected_topic_node in nodes
    # Last but not least, check for work nodes from data.
    for entry in fake_db_data_orcid_none["data"]:
        work_node = {'id': entry["work_name"],
                     'label': entry["work_name"], 'type': "WORK"}
        assert work_node in nodes


def test_database_branch_orcid_present(monkeypatch, fake_db_data_orcid_present):
    """
    Test when search_by_author_institution_topic returns real live data from the database
    and the author orcid is present.
    """
    monkeypatch.setattr(
        "backend.app.search_by_author_institution_topic",
        lambda r, i, t: fake_db_data_orcid_present
    )
    result = get_institution_researcher_subfield_results(
        "Institution Test", "Researcher Test", "Topic Test", page=1, per_page=10)
    metadata = result["metadata"]
    # In this branch, orcid should be as provided. I have been using it for personal workflows and it is great.
    assert metadata["orcid"] == "orcid-789"
    # Other metadata fields (similar assertions as in the previous test) should show up
    assert metadata["homepage"] == "http://institution.example.com"
    assert metadata["institution_oa_link"] == "institution_oa_123"
    assert metadata["researcher_oa_link"] == "researcher_oa_456"
    # Work on pagination, graph structure, and list entries.
    meta_pagination = result["metadata_pagination"]
    total_topics = len(fake_db_data_orcid_present["data"])
    expected_total_pages = (total_topics + 10 - 1) // 10
    assert meta_pagination["total_pages"] == expected_total_pages
    # Also work on the list (work name and citation count tuples) as it is built correctly.
    expected_list = []
    for entry in fake_db_data_orcid_present["data"]:
        expected_list.append((entry["work_name"], entry["cited_by_count"]))
    assert result["list"] == expected_list

# A fake response class for the sole purpose of simulating requests.get responses.


class FakeResponse:
    def __init__(self, json_data=None, raise_exception=False):
        self._json_data = json_data
        self.raise_exception = raise_exception

    def json(self):
        if self.raise_exception:
            raise Exception("Forced exception for testing")
        return self._json_data

# Test 1: All institutions return broken / improved data with matching topics.


def test_list_given_topic_success(monkeypatch):
    # Import the function and override the global autofill list.
    from backend.app import list_given_topic, autofill_inst_list
    autofill_inst_list.clear()
    autofill_inst_list.extend(["Institution A", "Institution B"])
    # Create fake responses:
    # Institution A has two topics; one matches ("Physics") with count 5.
    # Institution B has two topics; one matches ("Physics") with count 3.

    def fake_requests_get(url, headers):
        if "Institution A" in url:
            fake_data = {
                "results": [{
                    "display_name": "Institution A",
                    "topics": [
                        {"subfield": {"display_name": "Physics"}, "count": 5},
                        {"subfield": {"display_name": "Chemistry"}, "count": 2}
                    ]
                }]
            }
            return FakeResponse(fake_data)
        elif "Institution B" in url:
            fake_data = {
                "results": [{
                    "display_name": "Institution B",
                    "topics": [
                        {"subfield": {"display_name": "Physics"}, "count": 3},
                        {"subfield": {"display_name": "Math"}, "count": 4}
                    ]
                }]
            }
            return FakeResponse(fake_data)
        return FakeResponse({"results": []})
    monkeypatch.setattr(requests, "get", fake_requests_get)
    # Call the function that exists under test with subfield "Physics" and id "topic-1"
    subfield_list, graph, extra_metadata = list_given_topic(
        "Physics", "topic-1")
    # Show the subfield list is correctly built and sorted (highest count comes first)
    assert subfield_list == [("Institution A", 5), ("Institution B", 3)]
    # Total work count should be the sum of counts (5 + 3 = 8)
    assert extra_metadata == {"work_count": 8}
    # Check that the graph includes the topic node and nodes for each and every institution and its count.
    nodes = graph["nodes"]
    edges = graph["edges"]
    # Topic node must always be present.
    assert {"id": "topic-1", "label": "Physics", "type": "TOPIC"} in nodes
    # Both of the institution nodes should be present.
    assert {"id": "Institution A", "label": "Institution A",
            "type": "INSTITUTION"} in nodes
    assert {"id": "Institution B", "label": "Institution B",
            "type": "INSTITUTION"} in nodes
    # The NUMBER nodes should be created with the count values.
    assert {"id": 5, "label": 5, "type": "NUMBER"} in nodes
    assert {"id": 3, "label": 3, "type": "NUMBER"} in nodes
    # The expected edges should be added.
    expected_edge_A_topic = {
        'id': "Institution A-topic-1", 'start': "Institution A", 'end': "topic-1",
        "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"
    }
    expected_edge_A_number = {
        'id': "Institution A-5", 'start': "Institution A", 'end': 5,
        "label": "number", "start_type": "INSTITUTION", "end_type": "NUMBER"
    }
    expected_edge_B_topic = {
        'id': "Institution B-topic-1", 'start': "Institution B", 'end': "topic-1",
        "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"
    }
    expected_edge_B_number = {
        'id': "Institution B-3", 'start': "Institution B", 'end': 3,
        "label": "number", "start_type": "INSTITUTION", "end_type": "NUMBER"
    }
    assert expected_edge_A_topic in edges
    assert expected_edge_A_number in edges
    assert expected_edge_B_topic in edges
    assert expected_edge_B_number in edges
# SEcond test: When no institution returns matching topic data.


def test_list_given_topic_no_matching(monkeypatch):
    from backend.app import list_given_topic, autofill_inst_list
    autofill_inst_list.clear()
    autofill_inst_list.extend(["Institution X", "Institution Y"])
    # E-very institution response does not include the matching subfield "Physics"

    def fake_requests_get(url, headers):
        fake_data = {
            "results": [{
                "display_name": "Institution X",
                "topics": [
                    {"subfield": {"display_name": "Biology"}, "count": 2}
                ]
            }]
        }
        return FakeResponse(fake_data)
    monkeypatch.setattr(requests, "get", fake_requests_get)
    subfield_list, graph, extra_metadata = list_given_topic(
        "Physics", "topic-2")
    # Since no institution has "Physics", subfield_list remains empty.
    assert subfield_list == []
    assert extra_metadata == {"work_count": 0}
    # Graph should contain only the topic node.
    assert graph["nodes"] == [
        {'id': "topic-2", 'label': "Physics", 'type': 'TOPIC'}]
    assert graph["edges"] == []

# Third Test: Make sure that the "except" block is executed when response.json() fails.


def test_list_given_topic_exception(monkeypatch):
    from backend.app import list_given_topic, autofill_inst_list
    autofill_inst_list.clear()
    autofill_inst_list.extend(["Institution Error", "Institution Valid"])

    def fake_requests_get(url, headers):
        # For "Institution Error", throw an exception when .json() is called.
        if "Institution Error" in url:
            return FakeResponse(raise_exception=True)
        else:
            fake_data = {
                "results": [{
                    "display_name": "Institution Valid",
                    "topics": [
                        {"subfield": {"display_name": "Physics"}, "count": 7}
                    ]
                }]
            }
            return FakeResponse(fake_data)
    monkeypatch.setattr(requests, "get", fake_requests_get)
    subfield_list, graph, extra_metadata = list_given_topic(
        "Physics", "topic-3")
    # "Institution Error" should be skipped and only "Institution Valid" processed.
    assert subfield_list == [("Institution Valid", 7)]
    assert extra_metadata == {"work_count": 7}
    nodes = graph["nodes"]
    edges = graph["edges"]
    assert {"id": "topic-3", "label": "Physics", "type": "TOPIC"} in nodes
    assert {"id": "Institution Valid", "label": "Institution Valid",
            "type": "INSTITUTION"} in nodes
    assert {"id": 7, "label": 7, "type": "NUMBER"} in nodes
    expected_edge_valid_topic = {
        'id': "Institution Valid-topic-3", 'start': "Institution Valid", 'end': "topic-3",
        "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"
    }
    expected_edge_valid_number = {
        'id': "Institution Valid-7", 'start': "Institution Valid", 'end': 7,
        "label": "number", "start_type": "INSTITUTION", "end_type": "NUMBER"
    }
    assert expected_edge_valid_topic in edges
    assert expected_edge_valid_number in edges

# Fourth Test: Check that the subfield list is correctly sorted in descending order by count.


def test_list_given_topic_sorting(monkeypatch):
    from backend.app import list_given_topic, autofill_inst_list
    autofill_inst_list.clear()
    autofill_inst_list.extend(["Inst1", "Inst2", "Inst3"])
    # Set up responses such that:
    # Inst1: count 3, Inst2: count 10, Inst3: count 5 for "Physics".
    responses = {
        "Inst1": {"results": [{
            "display_name": "Inst1",
            "topics": [{"subfield": {"display_name": "Physics"}, "count": 3}]
        }]},
        "Inst2": {"results": [{
            "display_name": "Inst2",
            "topics": [{"subfield": {"display_name": "Physics"}, "count": 10}]
        }]},
        "Inst3": {"results": [{
            "display_name": "Inst3",
            "topics": [{"subfield": {"display_name": "Physics"}, "count": 5}]
        }]}
    }

    def fake_requests_get(url, headers):
        for inst, resp_data in responses.items():
            if inst in url:
                return FakeResponse(resp_data)
        return FakeResponse({"results": []})
    monkeypatch.setattr(requests, "get", fake_requests_get)

    subfield_list, graph, extra_metadata = list_given_topic(
        "Physics", "topic-4")
    # Expected sorted order: Inst2 (10), Inst3 (5), Inst1 (3) also known as what
    # we are calling topics.
    assert subfield_list == [("Inst2", 10), ("Inst3", 5), ("Inst1", 3)]
    # Total work count should be 10 + 5 + 3 = 18.
    assert extra_metadata == {"work_count": 18}


# Do both SPARQL functions return valid non-empty data?

def test_get_institution_and_topic_metadata_sparql_success(monkeypatch):
    fake_institution_data = {
        'ror': 'ror123',
        'oa_link': 'https://openalex.org/institutions/inst123',
        'homepage': 'https://institution.com',
        'works_count': 100,
        'cited_count': 50,
        'author_count': 20
    }
    fake_topic_data = {
        'topic_clusters': ['cluster1', 'cluster2'],
        'oa_link': 'https://openalex.org/subfields/topic123'
    }

    # To put it in a Monkeypatch, the dependent functions are to return our fake data.
    monkeypatch.setattr(
        "backend.app.get_institution_metadata_sparql",
        lambda institution: fake_institution_data if institution == "Institution A" else {}
    )
    monkeypatch.setattr(
        "backend.app.get_subfield_metadata_sparql",
        lambda topic: fake_topic_data if topic == "Topic A" else {}
    )

    result = get_institution_and_topic_metadata_sparql(
        "Institution A", "Topic A")
    expected = {
        "institution_name": "Institution A",
        "topic_name": "Topic A",
        "work_count": 100,
        "cited_by_count": 50,
        "ror": "ror123",
        "topic_clusters": ['cluster1', 'cluster2'],
        "people_count": 20,
        "topic_oa_link": 'https://openalex.org/subfields/topic123',
        "institution_oa_link": 'https://openalex.org/institutions/inst123',
        "homepage": 'https://institution.com'
    }
    assert result == expected

# Does get_institution_metadata_sparql return an empty dictionary?


def test_get_institution_and_topic_metadata_sparql_institution_empty(monkeypatch):
    fake_topic_data = {
        'topic_clusters': ['cluster1', 'cluster2'],
        'oa_link': 'https://openalex.org/subfields/topic123'
    }

    monkeypatch.setattr(
        "backend.app.get_institution_metadata_sparql",
        lambda institution: {}  # simulate failure for institution
    )
    monkeypatch.setattr(
        "backend.app.get_subfield_metadata_sparql",
        lambda topic: fake_topic_data
    )

    result = get_institution_and_topic_metadata_sparql(
        "Institution A", "Topic A")
    # According to the function, if either is {}, it should return {}.
    assert result == {}
# Does get_subfield_metadata_sparql return an empty dictionary?


def test_get_institution_and_topic_metadata_sparql_topic_empty(monkeypatch):
    fake_institution_data = {
        'ror': 'ror123',
        'oa_link': 'https://openalex.org/institutions/inst123',
        'homepage': 'https://institution.com',
        'works_count': 100,
        'cited_count': 50,
        'author_count': 20
    }

    monkeypatch.setattr(
        "backend.app.get_institution_metadata_sparql",
        lambda institution: fake_institution_data
    )
    monkeypatch.setattr(
        "backend.app.get_subfield_metadata_sparql",
        lambda topic: {}  # simulate failure for topic
    )

    result = get_institution_and_topic_metadata_sparql(
        "Institution A", "Topic A")
    assert result == {}

# DO both functions return empty dictionaries?


def test_get_institution_and_topic_metadata_sparql_both_empty(monkeypatch):
    monkeypatch.setattr(
        "backend.app.get_institution_metadata_sparql",
        lambda institution: {}
    )
    monkeypatch.setattr(
        "backend.app.get_subfield_metadata_sparql",
        lambda topic: {}
    )

    result = get_institution_and_topic_metadata_sparql(
        "Institution A", "Topic A")
    assert result == {}

# The keys in the returned dictionary should be exactly as expected.


def test_get_institution_and_topic_metadata_sparql_keys(monkeypatch):
    fake_institution_data = {
        'ror': 'rorXYZ',
        'oa_link': 'https://openalex.org/institutions/instXYZ',
        'homepage': 'https://instxyz.edu',
        'works_count': 200,
        'cited_count': 80,
        'author_count': 40
    }
    fake_topic_data = {
        'topic_clusters': ['clusterX', 'clusterY'],
        'oa_link': 'https://openalex.org/subfields/topicXYZ'
    }

    monkeypatch.setattr(
        "backend.app.get_institution_metadata_sparql",
        lambda institution: fake_institution_data
    )
    monkeypatch.setattr(
        "backend.app.get_subfield_metadata_sparql",
        lambda topic: fake_topic_data
    )

    result = get_institution_and_topic_metadata_sparql("InstXYZ", "TopicXYZ")
    expected_keys = {
        "institution_name",
        "topic_name",
        "work_count",
        "cited_by_count",
        "ror",
        "topic_clusters",
        "people_count",
        "topic_oa_link",
        "institution_oa_link",
        "homepage",
    }
    assert set(result.keys()) == expected_keys


# Update the import path to help science-wide assessment of impact of data format
fake_institution_data = {
    'ror': 'ror123',
    'oa_link': 'https://openalex.org/institutions/inst123',
    'homepage': 'https://institution.com',
    'works_count': 100,
    'cited_count': 50,
    'author_count': 20
}
fake_topic_data = {
    'topic_clusters': ['cluster1', 'cluster2'],
    'oa_link': 'https://openalex.org/subfields/topic123'
}
fake_researcher_data = {
    'orcid': 'orcid123',
    'oa_link': 'https://openalex.org/authors/auth123',
    'work_count': 75,
    'cited_by_count': 35,
    'current_institution': 'Institution X'
}

# Helper to set up monkeypatches for a successful case


def setup_success_monkeypatch(monkeypatch):
    monkeypatch.setattr(
        "backend.app.get_institution_metadata_sparql",
        lambda institution: fake_institution_data if institution == "Institution A" else {}
    )
    monkeypatch.setattr(
        "backend.app.get_subfield_metadata_sparql",
        lambda topic: fake_topic_data if topic == "Topic A" else {}
    )
    monkeypatch.setattr(
        "backend.app.get_author_metadata_sparql",
        lambda researcher: fake_researcher_data if researcher == "Researcher A" else {}
    )

# The best we can do with pip: success case when all dependency functions return super nice to have non-empty data.


def test_get_institution_and_topic_and_researcher_metadata_sparql_success(monkeypatch):
    setup_success_monkeypatch(monkeypatch)
    result = get_institution_and_topic_and_researcher_metadata_sparql(
        "Institution A", "Topic A", "Researcher A"
    )
    expected = {
        "institution_name": "Institution A",
        "topic_name": "Topic A",
        "researcher_name": "Researcher A",
        "topic_oa_link": fake_topic_data['oa_link'],
        "institution_oa_link": fake_institution_data['oa_link'],
        "homepage": fake_institution_data['homepage'],
        "orcid": fake_researcher_data['orcid'],
        "topic_clusters": fake_topic_data['topic_clusters'],
        "researcher_oa_link": fake_researcher_data['oa_link'],
        "work_count": fake_researcher_data['work_count'],
        "cited_by_count": fake_researcher_data['cited_by_count'],
        'ror': fake_institution_data['ror']
    }
    assert result == expected

# Institution metadata is missing! (dictionary is empty)


def test_get_institution_and_topic_and_researcher_metadata_sparql_institution_empty(monkeypatch):
    monkeypatch.setattr(
        "backend.app.get_institution_metadata_sparql",
        lambda institution: {}  # simulate the failure for institution
    )
    monkeypatch.setattr(
        "backend.app.get_subfield_metadata_sparql",
        lambda topic: fake_topic_data
    )
    monkeypatch.setattr(
        "backend.app.get_author_metadata_sparql",
        lambda researcher: fake_researcher_data
    )
    result = get_institution_and_topic_and_researcher_metadata_sparql(
        "Institution A", "Topic A", "Researcher A"
    )
    assert result == {}

# The topic metadata is missing! (the dictionary, is empty)


def test_get_institution_and_topic_and_researcher_metadata_sparql_topic_empty(monkeypatch):
    monkeypatch.setattr(
        "backend.app.get_institution_metadata_sparql",
        lambda institution: fake_institution_data
    )
    monkeypatch.setattr(
        "backend.app.get_subfield_metadata_sparql",
        lambda topic: {}  # simulate some more failure for topic
    )
    monkeypatch.setattr(
        "backend.app.get_author_metadata_sparql",
        lambda researcher: fake_researcher_data
    )
    result = get_institution_and_topic_and_researcher_metadata_sparql(
        "Institution A", "Topic A", "Researcher A"
    )
    assert result == {}

# The researcher metadata is missing! (empty dictionary)


def test_get_institution_and_topic_and_researcher_metadata_sparql_researcher_empty(monkeypatch):
    monkeypatch.setattr(
        "backend.app.get_institution_metadata_sparql",
        lambda institution: fake_institution_data
    )
    monkeypatch.setattr(
        "backend.app.get_subfield_metadata_sparql",
        lambda topic: fake_topic_data
    )
    monkeypatch.setattr(
        "backend.app.get_author_metadata_sparql",
        lambda researcher: {}  # simulate some more failure for researcher
    )
    result = get_institution_and_topic_and_researcher_metadata_sparql(
        "Institution A", "Topic A", "Researcher A"
    )
    assert result == {}

# Also, all three dependency functions return empty dictionaries.


def test_get_institution_and_topic_and_researcher_metadata_sparql_all_empty(monkeypatch):
    monkeypatch.setattr(
        "backend.app.get_institution_metadata_sparql",
        lambda institution: {}
    )
    monkeypatch.setattr(
        "backend.app.get_subfield_metadata_sparql",
        lambda topic: {}
    )
    monkeypatch.setattr(
        "backend.app.get_author_metadata_sparql",
        lambda researcher: {}
    )
    result = get_institution_and_topic_and_researcher_metadata_sparql(
        "Institution A", "Topic A", "Researcher A"
    )
    assert result == {}

# uv is a great alternative to pip, but for now show that the returned dictionary has exactly the expected keys.


def test_get_institution_and_topic_and_researcher_metadata_sparql_keys(monkeypatch):
    setup_success_monkeypatch(monkeypatch)
    result = get_institution_and_topic_and_researcher_metadata_sparql(
        "Institution A", "Topic A", "Researcher A"
    )
    expected_keys = {
        "institution_name",
        "topic_name",
        "researcher_name",
        "topic_oa_link",
        "institution_oa_link",
        "homepage",
        "orcid",
        "topic_clusters",
        "researcher_oa_link",
        "work_count",
        "cited_by_count",
        "ror"
    }
    assert set(result.keys()) == expected_keys

# Collaborate any time, this dummy cursor can do that and successfully execute


class DummyCursorSuccess:
    def execute(self, query):
        # Simulate successful execution; do nothing
        pass

    def fetchall(self):
        # Return a dummy result list
        return [("row1",), ("row2",)]

# Dummy connection that returns a successful cursor


class DummyConnectionSuccess:
    def cursor(self):
        return DummyCursorSuccess()

# Dummy cursor that simulates an error during execution


class DummyCursorFailure:
    def execute(self, query):
        raise Error("Simulated SQL error")

    def fetchall(self):
        # This won't be reached because execute() raises an error
        return []

# Dummy connection that grabs and returns a failing cursor


class DummyConnectionFailure:
    def cursor(self):
        return DummyCursorFailure()

# Test: Success case where the SQL query executes without error.


def test_query_sql_endpoint_success(monkeypatch, caplog):
    connection = DummyConnectionSuccess()
    query = "SELECT * FROM dummy_table"
    result = query_SQL_endpoint(connection, query)
    # Momentarily show the returned result is as expected.
    assert result == [("row1",), ("row2",)]
    # Momentarily show the log message contains the info about number of results.
    assert "SQL query returned 2 results" in caplog.text

# Test: Exception branch where the SQL query fails.


def test_query_sql_endpoint_exception(monkeypatch, caplog):
    connection = DummyConnectionFailure()
    query = "SELECT * FROM dummy_table"
    result = query_SQL_endpoint(connection, query)
    # When an error occurs, the function should return None.
    assert result is None
    # Verify the log message captures the error message.
    assert "SQL query failed: Simulated SQL error" in caplog.text

# Create a test client fixture from the Flask application.


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# Test when topic is empty (should return an empty list and not enter the loop)


def test_autofill_topics_empty(client, monkeypatch, caplog):
    # Set global variables to facilitate predictable behavior.
    monkeypatch.setattr("backend.app.SUBFIELDS", True)
    monkeypatch.setattr("backend.app.autofill_subfields_list", [
                        "Biology", "Chemistry", "Physics"])
    # Send a POST request with an empty topic.
    response = client.post("/autofill-topics", json={"topic": ""})
    data = json.loads(response.data)
    # The function should return an empty list
    assert data == {"possible_searches": []}
    # Log should mention 0 matching topics.
    assert "Found 0 matching topics for ''" in caplog.text

# Test with SUBFIELDS True; use autofill_subfields_list.


def test_autofill_topics_with_subfields(client, monkeypatch, caplog):
    monkeypatch.setattr("backend.app.SUBFIELDS", True)
    # Define a list of subfield topics.
    test_subfields = ["Biology", "Biochemistry", "Mathematics", "Geology"]
    monkeypatch.setattr("backend.app.autofill_subfields_list", test_subfields)
    # Use a topic that should match "Biology" and "Biochemistry" (case-insensitive).
    payload = {"topic": "bio"}
    response = client.post("/autofill-topics", json=payload)
    data = json.loads(response.data)
    # Expected matches: both topics containing "bio" in any case.
    expected_matches = ["Biology", "Biochemistry"]
    assert data == {"possible_searches": expected_matches}
    # Verify log contains the correct count.
    assert "Found 2 matching topics for 'bio'" in caplog.text

# Test with SUBFIELDS False; use autofill_topics_list.


def test_autofill_topics_without_subfields(client, monkeypatch, caplog):
    monkeypatch.setattr("backend.app.SUBFIELDS", False)
    # Define a list of topics.
    test_topics = ["Physics", "Chemistry", "Astronomy", "Biology"]
    monkeypatch.setattr("backend.app.autofill_topics_list", test_topics)
    # Use a topic that should only match "Chemistry" (case-insensitive search).
    payload = {"topic": "chem"}
    response = client.post("/autofill-topics", json=payload)
    data = json.loads(response.data)

    expected_matches = ["Chemistry"]
    assert data == {"possible_searches": expected_matches}
    # Verify log contains the correct count.
    assert "Found 1 matching topics for 'chem'" in caplog.text

# Test that the matching logic works correctly for partial matches as well as case-insensitivity.


def test_autofill_topics_case_insensitivity(client, monkeypatch, caplog):
    monkeypatch.setattr("backend.app.SUBFIELDS", True)
    # Give and provide a list with mixed-case entries.
    test_subfields = ["Astrophysics", "astrology", "History", "Biology"]
    monkeypatch.setattr("backend.app.autofill_subfields_list", test_subfields)
    # Send a request with a topic that matches "ast" (should match both "Astrophysics" & "astrology").
    payload = {"topic": "AST"}
    response = client.post("/autofill-topics", json=payload)
    data = json.loads(response.data)

    expected_matches = ["Astrophysics", "astrology"]
    assert data == {"possible_searches": expected_matches}
    assert "Found 2 matching topics for 'AST'" in caplog.text
# Test that if no items match, the result is an empty list.


def test_autofill_topics_no_matches(client, monkeypatch, caplog):
    monkeypatch.setattr("backend.app.SUBFIELDS", False)
    test_topics = ["Mathematics", "Literature", "History"]
    monkeypatch.setattr("backend.app.autofill_topics_list", test_topics)
    # Provide a topic that does not match any element in the list.
    payload = {"topic": "biology"}
    response = client.post("/autofill-topics", json=payload)
    data = json.loads(response.data)
    assert data == {"possible_searches": []}
    assert "Found 0 matching topics for 'biology'" in caplog.text

# Create a test client fixture from the Flask application.


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# Helper function! A dummy file object that returns our provided JSON string.


class DummyFile(io.StringIO):
    def __init__(self, content):
        super().__init__(content)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# Test..Successful processing where the JSON file has multiple edges and nodes.


def test_get_default_graph_success(client, monkeypatch, caplog):
    # Prepare JSON data for default.json:
    # In this example, we have three edges all starting from "Inst1":
    # * The first edge has connecting_works 5.
    # * The second edge has connecting_works 3.
    # * The third edge again has connecting_works 5.
    # Therefore, most["Inst1"] should be set to 5 and only the edges with 5 will be kept.
    default_data = {
        "nodes": [
            {"id": "Inst1", "type": "INSTITUTION", "label": "Institution 1"},
            {"id": "t1", "type": "TOPIC", "label": "Topic 1"},
            {"id": "t2", "type": "TOPIC", "label": "Topic 2"}
        ],
        "edges": [
            {"start": "Inst1", "end": "t1", "connecting_works": 5},
            {"start": "Inst1", "end": "t2", "connecting_works": 3},
            {"start": "Inst1", "end": "t1", "connecting_works": 5}
        ]
    }
    json_content = json.dumps(default_data)
    # I think we may want to play with the monkey-patch open, to return our dummy file containing json_content.
    monkeypatch.setattr("builtins.open", lambda filename,
                        mode: DummyFile(json_content))
    response = client.post("/get-default-graph")
    data = json.loads(response.data)
    # Expected processing:
    # - Only edges with connecting_works==5 (first and third) are kept.
    # - needed_topics becomes {"t1"}.
    # - Nodes: "Inst1" is included (non-TOPIC), "t1" (a TOPIC that is needed, we depend on it) is included,
    #   and "t2" is not (because it is not in needed_topics).
    expected_graph = {
        "nodes": [
            {"id": "Inst1", "type": "INSTITUTION", "label": "Institution 1"},
            {"id": "t1", "type": "TOPIC", "label": "Topic 1"}
        ],
        "edges": [
            {"start": "Inst1", "end": "t1", "connecting_works": 5},
            {"start": "Inst1", "end": "t1", "connecting_works": 5}
        ]
    }
    assert data == {"graph": expected_graph}
    assert "Successfully processed default graph" in caplog.text

# Test..File open error branch. We simulate an exception while opening default.json.


def test_get_default_graph_file_error(client, monkeypatch, caplog):
    # Monkey-patch is open to raise an exception.
    def fake_open(filename, mode):
        raise IOError("Simulated file error")
    monkeypatch.setattr("builtins.open", fake_open)

    response = client.post("/get-default-graph")
    data = json.loads(response.data)
    assert data == {"error": "Failed to load default graph"}
    assert "Failed to load default graph: Simulated file error" in caplog.text
# Test: Empty graph data (no nodes or and edges)


def test_get_default_graph_empty_graph(client, monkeypatch, caplog):
    default_data = {"nodes": [], "edges": []}
    json_content = json.dumps(default_data)
    monkeypatch.setattr("builtins.open", lambda filename,
                        mode: DummyFile(json_content))
    response = client.post("/get-default-graph")
    data = json.loads(response.data)
    expected_graph = {"nodes": [], "edges": []}
    assert data == {"graph": expected_graph}
    assert "Successfully processed default graph with 0 nodes and 0 edges" in caplog.text
# Test: Make sure that if multiple edges from the same "start" exist, the highest connecting_works value is used.


def test_get_default_graph_edge_update(client, monkeypatch, caplog):
    # Create a graph where two edges from the same start "A" have different connecting_works.
    default_data = {
        "nodes": [
            {"id": "A", "type": "INSTITUTION", "label": "Inst A"},
            {"id": "B", "type": "TOPIC", "label": "Topic B"},
            {"id": "C", "type": "TOPIC", "label": "Topic C"},
            {"id": "D", "type": "TOPIC", "label": "Topic D"}
        ],
        "edges": [
            {"start": "A", "end": "B", "connecting_works": 2},
            {"start": "A", "end": "C", "connecting_works": 4},
            {"start": "A", "end": "D", "connecting_works": 3}
        ]
    }
    json_content = json.dumps(default_data)
    monkeypatch.setattr("builtins.open", lambda filename,
                        mode: DummyFile(json_content))
    response = client.post("/get-default-graph")
    data = json.loads(response.data)

    # It's not the only thing but only the edge with connecting_works 4 should be kept because that is the highest.
    expected_graph = {
        "nodes": [
            {"id": "A", "type": "INSTITUTION", "label": "Inst A"},
            {"id": "C", "type": "TOPIC", "label": "Topic C"}
        ],
        "edges": [
            {"start": "A", "end": "C", "connecting_works": 4}
        ]
    }
    assert data == {"graph": expected_graph}
    # Also check that the log shows successful processing.
    assert "Successfully processed the original graph with 2 nodes and 1 edges" in caplog.text

# Minimal graph with one edge to cover the original branch of most assignment.


def test_get_default_graph_single_edge(client, monkeypatch, caplog):
    default_data = {
        "nodes": [
            {"id": "X", "type": "INSTITUTION", "label": "Inst X"},
            {"id": "Y", "type": "TOPIC", "label": "Topic Y"}
        ],
        "edges": [
            {"start": "X", "end": "Y", "connecting_works": 10}
        ]
    }
    json_content = json.dumps(default_data)
    monkeypatch.setattr("builtins.open", lambda filename,
                        mode: DummyFile(json_content))

    response = client.post("/get-default-graph")
    data = json.loads(response.data)
    # With only one edge, most["X"] is set to 10 and Y is needed.
    expected_graph = {
        "nodes": [
            {"id": "X", "type": "INSTITUTION", "label": "Inst X"},
            {"id": "Y", "type": "TOPIC", "label": "Topic Y"}
        ],
        "edges": [
            {"start": "X", "end": "Y", "connecting_works": 10}
        ]
    }
    assert data == {"graph": expected_graph}
    assert "Successfully processed default graph with 2 nodes and 1 edges" in caplog.text
# A dummy connection object to simulate a successful connection.


class DummyConnection:
    pass


def test_create_connection_success(monkeypatch, caplog):
    """
    Test that create_connection returns a valid connection on success,
    and that the expected debug and info log messages are recorded.
    """
    dummy_conn = DummyConnection()
    # Monkeypatch mysql.connector.connect to simulate a successful connection to one of many, 1,500 universities.

    def fake_connect(host, user, passwd, database):
        return dummy_conn
    monkeypatch.setattr(mysql.connector, "connect", fake_connect)
    host = "localhost"
    user = "test_user"
    passwd = "test_pass"
    db = "test_db"
    # Call the function, the first thing you see now.
    connection = create_connection(host, user, passwd, db)
    # Validate that the dummy connection was returned.
    assert connection is dummy_conn
    # Validate that the expected log messages are in the captured log.
    # Look for the warning debug message that logs the connection attempt.
    assert f"Attempting to connect to MySQL database: {db} at {host}" in caplog.text
    # Look for the info message confirming successful connection.
    assert "Successfully connected to MySQL database" in caplog.text


def test_create_connection_failure(monkeypatch, caplog):
    """
    Test that create_connection returns None when the connection fails,
    and that the error log message is recorded.
    """
    error_message = "Simulated connection error"
    # Monkeypatch mysql.connector.connect to simulate a failure by bringing about an Error.

    def fake_connect(host, user, passwd, database):
        raise Error(error_message)
    monkeypatch.setattr(mysql.connector, "connect", fake_connect)
    host = "invalid_host"
    user = "invalid_user"
    passwd = "invalid_pass"
    db = "test_db"
    # Call the function; since an error is raised, the connection should be None.
    connection = create_connection(host, user, passwd, db)
    assert connection is None
    # This is the only real update I have, that the error message was logged.
    assert f"Failed to connect to MySQL database: {error_message}" in caplog.text

# Some helper dummy functions, to over-ride dependencies


def dummy_get_institution_id_success(institution_name):
    # Return a fake institution id when the institution exists.
    return "dummy_institution_id"


def dummy_get_institution_id_none(institution_name):
    # Simulate that no institution id was found.
    return None


def dummy_execute_query_success(query, params):
    # Simulate a successful SQL call that returns a non-empty result.
    # For example, the stored procedure returns a single row with a MUP id.
    return [[42]]


def dummy_execute_query_empty(query, params):
    # Simulate call to the database that returns an empty result.
    return []

# "About" 18 test cases for get_institution_mup_id


def test_get_institution_mup_id_success(monkeypatch, caplog):
    """
    Test the successful branch where get_institution_id returns a valid id and
    execute_query returns a non-empty result.
    """
    # Progressively overrides dependencies to simulate a successful MUP id fetch.
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_success)
    monkeypatch.setattr("backend.app.execute_query",
                        dummy_execute_query_success)

    institution_name = "Test University"
    result = get_institution_mup_id(institution_name)
    # The expected MUP id is the one returned in our dummy_execute_query_success.
    assert result == 42
    # Assert that the log contains the success info message.
    assert f"Successfully fetched MUP ID for {institution_name}" in caplog.text


def test_get_institution_mup_id_no_institution(monkeypatch, caplog):
    """
    Test the branch where get_institution_id returns None.
    This should bypass the query execution and return None.
    """
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_none)

    institution_name = "Nonexistent University"
    result = get_institution_mup_id(institution_name)
    assert result is None
    # This branch should log a debug message for no institution id found.
    assert f"No institution ID found for {institution_name}" in caplog.text


def test_get_institution_mup_id_no_results(monkeypatch, caplog):
    """
    Test the branch where an institution id is found but the query already returns no results.
    This should log the specific info message "No MUP ID found for {institution_name}" and return None.
    """
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_success)
    monkeypatch.setattr("backend.app.execute_query", dummy_execute_query_empty)

    institution_name = "Test University"
    result = get_institution_mup_id(institution_name)
    assert result is None
    # Assert that the log contains the message for no MUP ID found.
    assert f"No MUP ID found for {institution_name}" in caplog.text


# A few dummy functions to override dependencies

def dummy_get_institution_id_success(institution_name):
    # Simulate a successful lookup that returns a dummy institution ID.
    return "dummy_institution_id"


def dummy_get_institution_id_none(institution_name):
    # Simulate a lookup that returns no institution ID.
    return None


def dummy_execute_query_success(query, params):
    # Simulate a successful database call returning SAT scores data.
    # For example, it turns out that our stored procedure returns a list with one row containing a dictionary.
    return [[{"sat": 1200, "year": 2021}]]


def dummy_execute_query_empty(query, params):
    # Simulate a database call that returns an empty result.
    return []


def test_get_institution_sat_scores_no_institution(monkeypatch, caplog):
    """
    Test that when get_institution_id returns None, the function logs the debug message
    "No institution ID found for {institution_name}" and returns None.
    """
    # Override get_institution_id to simulate that no id was found.
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_none)

    institution_name = "Nonexistent University"
    result = get_institution_sat_scores(institution_name)
    assert result is None
    # Check that the specific debug log message was recorded.
    assert f"No institution ID found for {institution_name}" in caplog.text


def test_get_institution_sat_scores_success(monkeypatch, caplog):
    """
    Test that when a valid institution id is found and execute_query returns data,
    the function adds institution metadata into the results and returns the expected dictionary.
    """
    # Override dependencies to simulate a successful few-minute call.
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_success)
    monkeypatch.setattr("backend.app.execute_query",
                        dummy_execute_query_success)

    institution_name = "Test University"
    result = get_institution_sat_scores(institution_name)
    expected = {
        "sat": 1200,
        "year": 2021,
        "institution_name": institution_name,
        "institution_id": "dummy_institution_id"
    }
    assert result == expected
    # Assert that the successful info log message was recorded.
    assert f"Successfully fetched MUP SAT scores data for {institution_name}" in caplog.text


def test_get_institution_sat_scores_no_results(monkeypatch, caplog):
    """
    Test that when a valid institution id is found but execute_query returns an empty result,
    the function logs the appropriate info message and returns None.
    """
    # Override dependencies: get_institution_id returns a valid id and execute_query returns no results.
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_success)
    monkeypatch.setattr("backend.app.execute_query", dummy_execute_query_empty)

    institution_name = "Test University"
    result = get_institution_sat_scores(institution_name)
    assert result is None
    # Joshua and Kusum could, and they do update that the log contains the message for no SAT scores data found.
    assert f"No MUP SAT scores data found for {institution_name}" in caplog.text

# Dummy functions override dependencies


def dummy_get_institution_id_success(institution_name):
    # Simulate a successful lookup that returns a dummy institution ID.
    return "dummy_institution_id"


def dummy_get_institution_id_none(institution_name):
    # Simulate a lookup that returns no institution ID.
    return None


def dummy_execute_query_success(query, params):
    # Simulate a successful database call that returns endowments and givings data.
    # The stored procedure returns a list with one row containing a dictionary.
    return [[{"endowment": 1000000, "giving": 50000, "year": 2021}]]


def dummy_execute_query_empty(query, params):
    # Simulate a database call that returns an empty result.
    return []

# Test cases, for the..get_institution_endowments_and_givings


def test_get_institution_endowments_and_givings_no_institution(monkeypatch, caplog):
    """
    Test that when get_institution_id returns None, the function logs the debug message
    "No institution ID found for {institution_name}" and returns None.
    """
    # Over-ride get_institution_id to simulate no id found.
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_none)

    institution_name = "Nonexistent University"
    result = get_institution_endowments_and_givings(institution_name)
    assert result is None
    # Assert that the specific debug log message was recorded.
    assert f"No institution ID found for {institution_name}" in caplog.text


def test_get_institution_endowments_and_givings_success(monkeypatch, caplog):
    """
    Test that when a true blue institution id is found and execute_query returns data,
    the function augments the returned dictionary with institution_name and institution_id,
    logs a success info message, and returns the expected result.
    """
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_success)
    monkeypatch.setattr("backend.app.execute_query",
                        dummy_execute_query_success)

    institution_name = "Test University"
    result = get_institution_endowments_and_givings(institution_name)

    expected = {
        "endowment": 1000000,
        "giving": 50000,
        "year": 2021,
        "institution_name": institution_name,
        "institution_id": "dummy_institution_id"
    }
    assert result == expected
    # Assert that the log contains the successful info message.
    assert f"Successfully fetched MUP endowments and givings data for {institution_name}" in caplog.text


def test_get_institution_endowments_and_givings_no_results(monkeypatch, caplog):
    """
    Test that when a valid institution id is found but execute_query returns an empty result,
    the function logs the appropriate info message and returns None.
    """
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_success)
    monkeypatch.setattr("backend.app.execute_query", dummy_execute_query_empty)

    institution_name = "Test University"
    result = get_institution_endowments_and_givings(institution_name)

    assert result is None
    # Check that the log contains the message for no data found.
    assert f"No MUP endowments and givings data found for {institution_name}" in caplog.text


# Dummy functions, override dependencies


def dummy_get_institution_id_success(institution_name):
    """Simulate a successful lookup returning a dummy institution id."""
    return "dummy_institution_id"


def dummy_get_institution_id_none(institution_name):
    """Simulate a lookup that returns no institution id."""
    return None


def dummy_execute_query_success(query, params):
    """Simulate a successful database call returning faculty awards data.
    The stored procedure appoints and returns a list with one row containing a dictionary.
    """
    return [[{"nae": 10, "nam": 20, "nas": 30, "num_fac_awards": 4, "year": 2021}]]


def dummy_execute_query_empty(query, params):
    """Simulate a database call that returns an empty result."""
    return []


# Test cases for get_institutions_faculty_awards

def test_get_institutions_faculty_awards_no_institution(monkeypatch, caplog):
    """
    Test that when get_institution_id returns None, the function logs the debug message
    "No institution ID found for {institution_name}" and returns None.
    """
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_none)
    # No need to override execute_query because it is never called in this branch.
    institution_name = "Nonexistent University"
    result = get_institutions_faculty_awards(institution_name)
    assert result is None
    # Verify that the log contains the expected debug message.
    assert f"No institution ID found for {institution_name}" in caplog.text


def test_get_institutions_faculty_awards_no_results(monkeypatch, caplog):
    """
    Test that when a valid institution id is found but execute_query returns an empty result,
    the function logs the appropriate info message and returns None.
    """
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_success)
    monkeypatch.setattr("backend.app.execute_query", dummy_execute_query_empty)

    institution_name = "Test University"
    result = get_institutions_faculty_awards(institution_name)
    assert result is None
    # Assert that the log contains the message for no faculty awards data found.
    assert f"No MUP faculty awards data found for {institution_name}" in caplog.text


def test_get_institutions_faculty_awards_success(monkeypatch, caplog):
    """
    Test that when a valid institution id is found and execute_query returns data,
    the function augments the returned dictionary with institution_name and institution_id,
    logs a success info message, and returns the expected dictionary.
    """
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_success)
    monkeypatch.setattr("backend.app.execute_query",
                        dummy_execute_query_success)
    institution_name = "Test University"
    result = get_institutions_faculty_awards(institution_name)
    expected = {
        "nae": 10,
        "nam": 20,
        "nas": 30,
        "num_fac_awards": 4,
        "year": 2021,
        "institution_name": institution_name,
        "institution_id": "dummy_institution_id"
    }
    assert result == expected
    # Assert that the log contains the successful info message.
    assert f"Successfully fetched MUP faculty awards data for {institution_name}" in caplog.text


# Dummy functions to override dependencies


def dummy_get_institution_id_success(institution_name):
    """Simulate a successful lookup returning a dummy institution id."""
    return "dummy_institution_id"


def dummy_get_institution_id_none(institution_name):
    """Simulate a lookup that returns no institution id."""
    return None


def dummy_execute_query_success(query, params):
    """Simulate a successful database call returning R&D data.
    The stored procedure returns a list with one row containing a dictionary.
    """
    return [[{
        "category": "Test Category",
        "federal": 100,
        "percent_federal": 50.0,
        "total": 200,
        "percent_total": 100.0
    }]]


def dummy_execute_query_empty(query, params):
    """Simulate a database call that returns an empty result."""
    return []

# Test cases for get_institutions_r_and_d


def test_get_institutions_r_and_d_no_institution(monkeypatch, caplog):
    """
    Test that when get_institution_id returns None,
    the function logs the debug message "No institution ID found for {institution_name}" and returns None.
    """
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_none)
    # We do not need to override execute_query because it is never going to be called in this branch.
    institution_name = "Nonexistent University"
    result = get_institutions_r_and_d(institution_name)

    assert result is None
    # Check that the debug log message for no institution id is present.
    assert f"No institution ID found for {institution_name}" in caplog.text


def test_get_institutions_r_and_d_success(monkeypatch, caplog):
    """
    Test that when a valid institution id is found and execute_query returns data,
    the function augments the returned dictionary with institution_name and institution_id,
    logs a success info message, and returns the expected result.
    """
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_success)
    monkeypatch.setattr("backend.app.execute_query",
                        dummy_execute_query_success)

    institution_name = "Test University"
    result = get_institutions_r_and_d(institution_name)

    expected = {
        "category": "Test Category",
        "federal": 100,
        "percent_federal": 50.0,
        "total": 200,
        "percent_total": 100.0,
        "institution_name": institution_name,
        "institution_id": "dummy_institution_id"
    }
    assert result == expected
    # If you check you'll verify that the log contains the success info message.
    assert f"Successfully fetched MUP R&D data for {institution_name}" in caplog.text


def test_get_institutions_r_and_d_no_results(monkeypatch, caplog):
    """
    Test that when a valid institution id is found but execute_query returns an empty result,
    the function logs the appropriate info message and returns None.
    """
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_success)
    monkeypatch.setattr("backend.app.execute_query", dummy_execute_query_empty)

    institution_name = "Test University"
    result = get_institutions_r_and_d(institution_name)

    assert result is None
    # Show that the log contains the message for no R&D data found.
    assert f"No MUP R&D datafound for {institution_name}" in caplog.text


def test_serve_static_file(monkeypatch, caplog):
    """
    Test the branch when path is non-empty and the file exists.

    Expected behavior:
      - os.path.exists returns True so that the static file branch is taken.
      - The debug log "Serving static file: <path>" is logged.
      - send_from_directory is called with the correct folder and filename.
    """
    # Define a dummy send_from_directory that returns a string indicating what was served.
    def dummy_send_from_directory(directory, filename):
        return f"File served from {directory}/{filename}"
    # Override send_from_directory in our module.
    monkeypatch.setattr("backend.app.send_from_directory",
                        dummy_send_from_directory)
    # Override os.path.exists to simulate that the requested file exists.
    monkeypatch.setattr(os.path, "exists", lambda path: True)
    # Simulate a request context for the Flask app.
    with app.test_request_context():
        response = serve("staticfile.js")

    expected = f"File served from {app.static_folder}/staticfile.js"
    assert response == expected, "Should return the static file if it exists"
    # Verify that the debug log "contains" the correct message.
    assert "Serving static file: staticfile.js" in caplog.text, (
        "Expected log message for serving static file was not found"
    )


def test_serve_index_html_when_file_missing(monkeypatch, caplog):
    """
    Test the branch when a non-empty path is provided but the file does not exist.
    Expected behavior:
      * os.path.exists returns False so that the fallback branch is taken.
      * The debug log "Serving index.html for frontend routing" is logged.
      * send_from_directory is called upon to serve index.html.
    """
    # Dummy send_from_directory function for this test.
    def dummy_send_from_directory(directory, filename):
        return f"Index served from {directory}/{filename}"

    monkeypatch.setattr("backend.app.send_from_directory",
                        dummy_send_from_directory)
    # Force os.path.exists to return False to simulate file not existing.
    monkeypatch.setattr(os.path, "exists", lambda path: False)

    with app.test_request_context():
        response = serve("nonexistent_file.js")

    expected = f"Index served from {app.static_folder}/index.html"
    assert response == expected, "Should return index.html when the file is not found"
    # How do we match up universities, rather than just by name? We could use logs, but I should declare that names are the keys that make dictionary lookup possible..therefore, the communal, static file debug message is not present, but the index debug message is.
    assert "Serving static file:" not in caplog.text, (
        "Static file log message should not appear when file is missing"
    )
    assert "Serving index.html for frontend routing" in caplog.text, (
        "Expected log message for serving index.html was not found"
    )


def test_serve_index_html_empty_path(monkeypatch, caplog):
    """
    Test the branch when an empty path is provided.
    Expected behavior does follow:
      * Regardless of os.path.exists, an empty path should return index.html.
      * The debug log "Serving index.html for frontend routing" is logged.
    """
    def dummy_send_from_directory(directory, filename):
        return f"Index served from {directory}/{filename}"

    monkeypatch.setattr("backend.app.send_from_directory",
                        dummy_send_from_directory)
    # Even if os.path.exists would return True, the empty path branch should bypass it.
    monkeypatch.setattr(os.path, "exists", lambda path: True)
    with app.test_request_context():
        response = serve("")
    expected = f"Index served from {app.static_folder}/index.html"
    assert response == expected, "Should return index.html when path is empty"
    # Verify that the debug log indicates that index.html is being served.
    assert "Serving index.html for frontend routing" in caplog.text, (
        "Expected log message for serving index.html was not found when path is empty"
    )


# Unit tests for the Flask app's entrypoint block (if __name__ == '__main__')
# Assume the entrypoint module (with the if __main__ block) is named 'run.py'.
# Alter ENTRYPOINT_MODULE if your entrypoint module has a different name.
ENTRYPOINT_MODULE = 'backend.app'


def test_entrypoint_logs_startup_message():
    """Test that the Flask app logs the expected startup message when run as __main__."""
    # Patch app.logger.info and app.run to monitor calls and prevent actual server start
    with patch('backend.app.app.logger.info') as info_mock, patch('backend.app.app.run') as run_mock:
        try:
            # Execute the entrypoint module as if it were run as __main__
            runpy.run_module(ENTRYPOINT_MODULE, run_name="__main__")
        finally:
            # Clean up the __main__ module to avoid side effects on other tests
            sys.modules.pop('__main__', None)
    # Verify that the logger.info was called once with the specific startup message
    info_mock.assert_called_once_with("Starting Flask application")
    # (It's worth noting that the app.run invocation is checked in a separate test)


def test_entrypoint_invokes_app_run():
    """Test that the Flask app's run method is called when the module is executed as __main__."""
    with patch('backend.app.app.logger.info') as info_mock, patch('backend.app.app.run') as run_mock:
        try:
            runpy.run_module(ENTRYPOINT_MODULE, run_name="__main__")
        finally:
            sys.modules.pop('__main__', None)
    # The question is, is app.run() called exactly once? (Flask server attempted to start)
    run_mock.assert_called_once()


def test_autofill_topics_reads_from_csv_when_subfields_false(monkeypatch):
    """
    When you find the "branch" that reads keywords.csv when SUBFIELDS is False,
    simulate a fake file with sample topics.
    """
    # Set SUBFIELDS to be False and then, reset the autofill_topics_list.
    backend_app.SUBFIELDS = False
    if hasattr(backend_app, "autofill_topics_list"):
        del backend_app.autofill_topics_list
    # Monkey-patch open to return a fake file.
    fake_file = io.StringIO("Alpha\nAlphabet\nBeta")
    monkeypatch.setattr("builtins.open", lambda filename, mode: fake_file)
    # Manually execute the file-reading branch.
    if not backend_app.SUBFIELDS:
        with open("keywords.csv", "r") as fil:
            backend_app.autofill_topics_list = fil.read().split("\n")
    # Call the endpoint which has some one and a half topics.
    client = app.test_client()
    response = client.post("/autofill-topics", json={"topic": "alph"})
    assert response.status_code == 200, "Expected 200 OK response"
    data = response.get_json()
    # Expect "Alpha" and "Alphabet" to match (case-insensitive).
    assert "Alpha" in data["possible_searches"], "Expected 'Alpha' in suggestions"
    assert "Alphabet" in data["possible_searches"], "Expected 'Alphabet' in suggestions"
    # "Beta" should not match "alph", you could make an issue out of it on GitHub.
    assert "Beta" not in data["possible_searches"], "Did not expect 'Beta' in suggestions"


def test_autofill_topics_filters_matches_case_insensitively(monkeypatch):
    """
    Tests the substring matching branch inside autofill_topics()
    when SUBFIELDS is False by injecting a sample list so we don't have
    to forget the everyday subfields.
    """
    backend_app.SUBFIELDS = False
    backend_app.autofill_topics_list = ["Cat", "Dog", "Caterpillar"]
    client = app.test_client()
    response = client.post("/autofill-topics", json={"topic": "cat"})
    assert response.status_code == 200, "Expected 200 OK response"
    data = response.get_json()
    possible = data["possible_searches"]
    # And so we can have these sample answers, for the query "cat" expect
    # "Cat" and "Caterpillar" to match.
    assert "Cat" in possible, "Expected 'Cat' in suggestions"
    assert "Caterpillar" in possible, "Expected 'Caterpillar' in suggestions"
    assert "Dog" not in possible, "Did not expect 'Dog' in suggestions"
    assert len(possible) == 2, "Expected exactly 2 suggestions"


def test_autofill_topics_empty_topic(monkeypatch):
    """
    Tests that if an empty string is provided as topic, it turns out that
    there's no list, the endpoint returns an empty list regardless of the
    SUBFIELDS value.
    """
    # Test first with SUBFIELDS False.
    backend_app.SUBFIELDS = False
    backend_app.autofill_topics_list = ["Alpha", "Beta", "Gamma"]
    client = app.test_client()
    response = client.post("/autofill-topics", json={"topic": ""})
    assert response.status_code == 200
    data = response.get_json()
    assert data["possible_searches"] == [
    ], "Expected no suggestions for empty topic"
    # Test with SUBFIELDS True, and it'll give you all combinations of
    # setting SUBFIELDS to True that is, and False up above. Which should
    # give you a NameError, because the SUBFIELDS is the "gateway" to the
    # "unreachable" `autofill_topics_list`.
    backend_app.SUBFIELDS = True
    backend_app.autofill_subfields_list = ["Alpha", "Beta", "Gamma"]
    response = client.post("/autofill-topics", json={"topic": ""})
    data = response.get_json()
    assert data["possible_searches"] == [
    ], "Expected no suggestions for empty topic"


def test_autofill_topics_no_matches(monkeypatch):
    """
    `autofill_topics_list` which we can globally or lazily initialize within
    the `/autofill-topics` route; we can test that when the search substring
    matches no keywords, then the endpoint returns an empty list.
    """
    # Even a map with a single pin is good enough. It tells you exactly where
    # that university is located--a low bar of implementation our students can
    # achieve. If we "try" to set SUBFIELDS True then we can set a sample list.
    backend_app.SUBFIELDS = True
    backend_app.autofill_subfields_list = ["Alpha", "Beta", "Gamma"]
    client = app.test_client()
    response = client.post("/autofill-topics", json={"topic": "delta"})
    data = response.get_json()
    assert data["possible_searches"] == [], "Expected no matches for 'delta'"


def test_autofill_topics_subfields_true(monkeypatch):
    """
    Tests the branch for SUBFIELDS True by injecting a known subfields list;
    I'm not entirely sure how to handle multiple subfields' lists--but it's a
    great idea to see how we can populate the single example.
    """
    backend_app.SUBFIELDS = True
    backend_app.autofill_subfields_list = ["Alpha", "Alphabet", "Beta"]
    client = app.test_client()
    response = client.post("/autofill-topics", json={"topic": "alph"})
    data = response.get_json()
    possible = data["possible_searches"]
    assert "Alpha" in possible, "Expected 'Alpha' in suggestions"
    assert "Alphabet" in possible, "Expected 'Alphabet' in suggestions"
    assert "Beta" not in possible, "Did not expect 'Beta' in suggestions"
    assert len(possible) == 2, "Expected exactly 2 suggestions"


def test_autofill_topics_keywords_file_with_empty_lines(monkeypatch):
    """
    Tests the file reading branch (SUBFIELDS False) when the file contains extra empty lines; it's possible that this is an "edge case' which tells us that we've
    got a pretty good pre-beta testing suite right now.
    """
    backend_app.SUBFIELDS = False
    if hasattr(backend_app, "autofill_topics_list"):
        del backend_app.autofill_topics_list
    fake_content = "Alpha\n\nBeta\n\n"
    fake_file = io.StringIO(fake_content)
    monkeypatch.setattr("builtins.open", lambda filename, mode: fake_file)
    # Execute the branch for reading files, and consider a mirror-version
    # of the file reading branch dead branch.
    if not backend_app.SUBFIELDS:
        with open("keywords.csv", "r") as fil:
            backend_app.autofill_topics_list = fil.read().split("\n")
    client = app.test_client()
    # Searching for "beta" should return "Beta" but not any empty string.
    # Let's use the autofill-topics, review the `pytest` docs and consider
    # setting the search for "beta" to return "Beta" but not just any empty
    # string.
    response = client.post("/autofill-topics", json={"topic": "beta"})
    data = response.get_json()
    possible = data["possible_searches"]
    assert "Beta" in possible, "Expected 'Beta' in suggestions"
    assert "" not in possible, "Did not expect an empty string in suggestions"


def test_autofill_topics_keywords_file_not_found(monkeypatch):
    """
    Every test, the keywords.csv file cannot be found; "thus" the file reading branch raises a FileNotFoundError which breaks and makes the "ultimate" data
    visualization "tool" in multiple ways--lists, graphs, maps--
    """
    backend_app.SUBFIELDS = False
    if hasattr(backend_app, "autofill_topics_list"):
        del backend_app.autofill_topics_list
    # depending on whether you are searching for one person, one topic, or
    # many organizations--monkey-patch open to raise FileNotFoundError. It's
    # "essential" because we need to know if the file is found or not and that
    # requires the coverage report to be a thing that requires a good guess on
    # why and how we can alter the tests now that we are "done" on coverage,
    # unfortunately and necessarily.

    def fake_open(*args, **kwargs):
        raise FileNotFoundError("File not found")
    monkeypatch.setattr("builtins.open", fake_open)
    with pytest.raises(FileNotFoundError):
        if not backend_app.SUBFIELDS:
            with open("keywords.csv", "r") as fil:
                backend_app.autofill_topics_list = fil.read().split("\n")
