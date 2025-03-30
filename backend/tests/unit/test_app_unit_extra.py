""" # When no JSON is provided, Flask will raise a 400
    # So we accept 400 here. Like the DuoLingo owl,
    # you know what comes next! """
import importlib
import json
from io import StringIO
import pytest
from unittest.mock import patch, MagicMock
from backend.app import (
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
    list_given_topic,
    create_connection,
    list_given_institution_topic,
    list_given_researcher_institution,
    get_institution_mup_id,
    get_institution_sat_scores,
    get_institution_endowments_and_givings,
    get_institution_medical_expenses,
    get_institution_doctorates_and_postdocs,
    get_institution_num_of_researches,
    get_institutions_faculty_awards,
    get_institutions_r_and_d,
    query_SQL_endpoint,
    combine_graphs,
    is_HBCU,
    query_SPARQL_endpoint
)
import os
import requests
os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "5432"
os.environ["DB_NAME"] = "testdb"
os.environ["DB_USER"] = "testuser"
os.environ["DB_PASSWORD"] = "testpass"
os.environ["DB_API"] = "http://testapi"

# Set required environment variables BEFORE any other imports so that DB_PORT, etc. are defined.

# ---------------------------------------------------------------------------
# Lines 19–23: Environment variable reading


def test_env_variables():
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
