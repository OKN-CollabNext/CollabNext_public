// This file establishes the foundational data blueprints for our research collaboration tool.
// Defining clear interfaces is a crucial first step, ensuring that all components
// communicate effectively and handle data with consistency and integrity.
export type SearchType =
  | "topic"
  | "researcher"
  | "institution"
  | "topic-researcher"
  | "researcher-institution"
  | "topic-institution"
  | "all-three-search";

// The ResearchDataInterface serves as the core structure for representing
// the rich, interconnected information our platform manages. Each field is a testament
// to the depth of data we aim to make accessible and understandable.
export interface ResearchDataInterface {
  cited_count: string;
  works_count: string;
  institution_name: string;
  ror_link: string;
  author_count: string;
  institution_url: string;
  open_alex_link: string;
  graph?: { nodes: any[]; edges: any[] }; // Represents the network of connections, a visual pathway to discovery.
  is_hbcu: boolean;
  topics: string[][]; // A collection of topics, each a thread in the larger tapestry of research.
  coordinates: string[][]; // Geospatial data, anchoring research to physical locations.
  works: string[][];
  organizations: string[][];
  authors: string[][];
  topic_name: string;
  topic_clusters: string[]; // Clusters that group related topics, revealing broader themes.
  researcher_name: string;
  orcid_link: string; // Linking to ORCID ensures researcher identity and clear attribution.
  researcher_open_alex_link: string;
  topic_open_alex_link: string;
  search?: SearchType; // The type of search performed, guiding how results are interpreted.

  // Indicates if the search results encompass multiple primary institutions,
  // reflecting a broader, more collaborative inquiry.
  has_multiple_institutions?: boolean;
  // Holds metadata for all institutions when a multi-institution search is performed.
  // The key is typically the institution's name or identifier, allowing for a
  // structured and accessible collection of diverse institutional data.
  all_institution_metadata?: {
    [key: string]: ResearchDataInterface; // Each entry provides a comprehensive snapshot of an institution.
  };
}