## Base URL
If you are running the server locally:
```
http://localhost:5000
```
(Adjust the port as necessary)

## Endpoints

### 1. **`GET /<path>` and `GET /`**

Serves the React frontend (the compiled `index.html`).  

**Usage**: Not typically accessed manually; used to load the React SPA (single page app).

---

### 2. **`POST /initial-search`**

Initiates a search given various parameters: `organization`, `researcher`, `type`, and `topic`.

<details>
<summary>Example Request</summary>

POST /initial-search HTTP/1.1
Host: https://collabnext.io
Content-Type: application/json

{
  "organization": "Chicago State University",
  "researcher": "John Doe",
  "type": "HBCU",
  "topic": "Machine Learning"
}
</details>

<details>
<summary>Example Response</summary>

{
  "metadata": {
    "institution_name": "Georgia Institute of Technology",
    "topic_name": "Machine Learning",
    "researcher_name": "John Doe",
    "work_count": 25,
    "cited_by_count": 290,
    ...
  },
  "graph": {
    "nodes": [...],
    "edges": [...]
  },
  "list": [
    ["Paper Title #1", 50],
    ["Paper Title #2", 38]
  ]
}
</details>

**Notes**:  
- **Return Value**:  
  - **metadata**: Basic info about the institution, researcher, and/or topic.  
  - **graph**: A node-edge representation of the results (for visualization).  
  - **list**: A simpler list view of data (e.g., top subfields or works).

---

### 3. **`POST /get-default-graph`**

Returns a default graph with curated nodes and edges (used for initial display).

<details>
<summary>Example Request</summary>

POST /get-default-graph HTTP/1.1
Host: https://collabnext.io
Content-Type: application/json

{}
</details>

<details>
<summary>Example Response</summary>

{
  "graph": {
    "nodes": [
      { "id": "Harvard", "label": "Harvard University", "type": "INSTITUTION" },
      ...
    ],
    "edges": [
      { "start": "Harvard", "end": "Artificial Intelligence", ... },
      ...
    ]
  }
}
</details>

---

### 4. **`POST /get-topic-space-default-graph`**

Returns a default graph of high-level topics (domains in OpenAlex).

<details>
<summary>Example Request</summary>

POST /get-topic-space-default-graph HTTP/1.1
Host: https://collabnext.io
Content-Type: application/json

{}
</details>

<details>
<summary>Example Response</summary>

{
  "graph": {
    "nodes": [
      { "id": 1, "label": "Physical Sciences", "type": "DOMAIN" },
      { "id": 2, "label": "Life Sciences", "type": "DOMAIN" },
      ...
    ],
    "edges": []
  }
}
</details>

---

### 5. **`POST /search-topic-space`**

Given a **topic** string, returns a subgraph from `topic_default.json`, representing related topics, fields, and domains.

<details>
<summary>Example Request</summary>

POST /search-topic-space HTTP/1.1
Host: https://collabnext.io
Content-Type: application/json

{
  "topic": "Quantum Mechanics"
}
</details>

<details>
<summary>Example Response</summary>

{
  "graph": {
    "nodes": [
      { "id": "QMech", "label": "Quantum Mechanics", "type": "TOPIC", "keywords": "...", "wikipedia_url": "..." },
      { "id": 200, "label": "Physics", "type": "SUBFIELD" },
      ...
    ],
    "edges": [
      { "start": "QMech", "end": 200, "label": "hasSubfield" },
      ...
    ]
  }
}
</details>

---

### 6. **`POST /autofill-institutions`**

Given an institution substring, returns a list of matching institution names (for autocomplete in the UI).

<details>
<summary>Example Request</summary>

POST /autofill-institutions HTTP/1.1
Host: https://collabnext.io
Content-Type: application/json

{
  "institution": "Ch"
}
</details>

<details>
<summary>Example Response</summary>

{
  "possible_searches": [
    "Chicago State University",
    "Chatham University"
  ]
}
</details>

---

### 7. **`POST /autofill-topics`**

Given a topic substring, returns a list of matching topics or subfields (for autocomplete).

<details>
<summary>Example Request</summmary>

POST /autofill-topics HTTP/1.1
Host: https://collabnext.io
Content-Type: application/json

{
  "topic": "Machine"
}
</details>

<details>
<summary>Example Response</summary>

{
  "possible_searches": [
    "Machine Learning",
    "Machine Vision"
  ]
}
</details>

---

## **Error Handling**

- For most API calls, if an internal server error occurs, the endpoint returns an HTTP `500` status code, typically with a JSON payload containing an `"error"` key.

- If data is missing or parameters are invalid, some endpoints may return a partial result, empty result, or an error message.

## **Contact / Support**

- **Slack Channel**: `#backend-team`  

- **Issue Tracker**: [CollabNext GitHub Issues](https://github.com/OKN-CollabNext/CollabNext_public/issues)
