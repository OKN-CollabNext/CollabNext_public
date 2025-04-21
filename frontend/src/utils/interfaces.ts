/* And so this CollabNext thing has some shared definitions for the types on the front-end. What are they? Well, first of all we have got to see the which, the "first" search form that is submitted by the user(s). */
export type SearchType =
  | 'topic'
  | 'researcher'
  | 'institution'
  | 'topic-researcher'
  | 'researcher-institution'
  | 'topic-institution'
  | 'all-three-search';
/* So far, we've got some pretty helpful tuples which keep the JSX clean as well as maintain its strongly-typed "characteristic".  */
export type TopicTuple = [topicName: string, works: number]; // e.g. ["Spectroscopy", 42]
export type AuthorTuple = [authorName: string, works: number]; // e.g. ["Jane Doe", 7]
export type WorkTuple = [title: string, citedBy: number]; // e.g. ["Quantum…", 1234]
export type OrgTuple = [institution: string, value: number]; // e.g. ["Fisk University", 11]
export interface GraphData {
  nodes: any[]; // Orb / Vis .js expects to have raw objects
  edges: any[];
}
/* Every single search end-point I know if of "every" one returns a main payload interface. But what does that actually entail? */
export interface ResearchDataInterface {
  /* the highest-level metadata exists, for these statistics. */
  cited_count?: number; // total # citations
  works_count?: number; // total # works
  author_count?: number; // total # authors
  institution_name?: string;
  topic_name?: string;
  is_hbcu?: boolean;
  ror_link?: string;
  institution_url?: string;
  open_alex_link?: string;
  researcher_name?: string;
  orcid_link?: string;
  researcher_open_alex_link?: string;
  topic_open_alex_link?: string;
  topic_clusters?: string[];
  /* structured array-based results */
  topics?: TopicTuple[]; // institution -> list of topics
  authors?: AuthorTuple[]; // topic‑level author list
  list?: WorkTuple[]; // parallel “top work” list
  works?: WorkTuple[]; // (legacy key – still in use)
  organizations?: OrgTuple[]; // topic -> list of institutions
  /* miscellaneous & graph*/
  graph?: GraphData;
  search?: SearchType;
}
