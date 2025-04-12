export type SearchType =
  | "topic"
  | "researcher"
  | "institution"
  | "topic-researcher"
  | "researcher-institution"
  | "topic-institution"
  | "all-three-search";

export interface ResearchDataInterface {
  cited_count: string;
  works_count: string;
  institution_name: string;
  ror_link: string;
  author_count: string;
  institution_url: string;
  open_alex_link: string;
  graph?: { nodes: any[]; edges: any[] };
  is_hbcu: boolean;
  topics: string[][];
  coordinates: string[][];
  works: string[][];
  organizations: string[][];
  authors: string[][];
  topic_name: string;
  topic_clusters: string[];
  researcher_name: string;
  orcid_link: string;
  researcher_open_alex_link: string;
  topic_open_alex_link: string;
  search?: SearchType;
}
