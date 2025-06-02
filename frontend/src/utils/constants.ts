/* ------------------------------------------------------------------ */
/*  Global constants & shared helpers                                 */
/* ------------------------------------------------------------------ */

export const baseUrl =
  process.env.REACT_APP_BASE_URL || "http://localhost:5000";

/* ---------------- Cytoscape styling ------------------------------- */

export const styleSheet = [
  {
    selector: "node",
    style: {
      width: 30,
      height: 30,
      label: "data(label)",
      "overlay-padding": "6px",
      "text-outline-color": "#4a56a6",
      "text-outline-width": "2px",
      color: "white",
      fontSize: 20,
    },
  },
  {
    selector: "node:selected",
    style: {
      "border-width": "6px",
      "border-color": "#AAD8FF",
      "border-opacity": "0.5",
      "background-color": "#77828C",
      width: 50,
      height: 50,
      "text-outline-color": "#77828C",
      "text-outline-width": 8,
    },
  },
  { selector: "node[type='device']", style: { shape: "rectangle" } },
  { selector: "node[type='institution']", style: { backgroundColor: "#4a56a6" } },
  { selector: "node[type='topic']", style: { backgroundColor: "blue" } },
  { selector: "node[type='researcher']", style: { backgroundColor: "green" } },
  {
    selector: "edge",
    style: {
      width: 3,
      "line-color": "#AAD8FF",
      "target-arrow-color": "#6774cb",
      "target-arrow-shape": "triangle",
      "curve-style": "bezier",
    },
  },
];

/* ---------------- Cytoscape layout -------------------------------- */

export const layout = {
  name: "breadthfirst",
  fit: true,
  directed: true,
  padding: 50,
  animate: true,
  animationDuration: 1000,
  avoidOverlap: true,
  nodeDimensionsIncludeLabels: false,
};

/* ---------------- Initial empty-state object ----------------------- */

export const initialValue = {
  cited_count: "",
  works_count: "",
  institution_name: "",
  ror_link: "",
  author_count: "",
  institution_url: "",
  open_alex_link: "",
  is_hbcu: false,
  topics: [],
  works: [],
  organizations: [],
  authors: [],
  topic_name: "",
  topic_clusters: [],
  researcher_name: "",
  orcid_link: "",
  researcher_open_alex_link: "",
  topic_open_alex_link: "",
  coordinates: [],
};

/* ---------------- Helper for auto-fill inputs ---------------------- */

export const handleAutofill = (
  text: string,
  topic: boolean,
  setSuggestedTopics: React.Dispatch<React.SetStateAction<never[]>>,
  setSuggestedInstitutions: React.Dispatch<React.SetStateAction<never[]>>
) => {
  fetch(
    !topic ? `${baseUrl}/autofill-institutions` : `${baseUrl}/autofill-topics`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        topic ? { topic: text } : { institution: text }
      ),
    }
  )
    .then((res) => res.json())
    .then((data) => {
      if (topic) {
        setSuggestedTopics(data?.possible_searches);
      } else {
        setSuggestedInstitutions(data?.possible_searches);
      }
    })
    .catch(() => {
      if (topic) setSuggestedTopics([]);
      else setSuggestedInstitutions([]);
    });
};

/* ---------------- NEW: shared institution-type list ---------------- */

/**
 * Centralised list so every page can import the same source of truth:
 *    import { institutionTypes } from "../utils/constants";
 */
export const institutionTypes: string[] = [
  "HBCU",
  "AANAPISI",
  "ANNH",
  "Carnegie R1",
  "Carnegie R2",
  "Emerging",
  "HSI",
  "MSI",
  "NASNTI",
  "PBI",
  "TCU",
];
