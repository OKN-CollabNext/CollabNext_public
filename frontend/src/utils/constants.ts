export const baseUrl =
  process.env.REACT_APP_BASE_URL || 'http://localhost:5000';

export const styleSheet = [
  {
    selector: 'node',
    style: {
      // backgroundColor: '#4a56a6',
      width: 30,
      height: 30,
      label: 'data(label)',

      // "width": "mapData(score, 0, 0.006769776522008331, 20, 60)",
      // "height": "mapData(score, 0, 0.006769776522008331, 20, 60)",
      // "text-valign": "center",
      // "text-halign": "center",
      'overlay-padding': '6px',
      // 'z-index': '10',
      //text props
      'text-outline-color': '#4a56a6',
      'text-outline-width': '2px',
      color: 'white',
      fontSize: 20,
    },
  },
  {
    selector: 'node:selected',
    style: {
      'border-width': '6px',
      'border-color': '#AAD8FF',
      'border-opacity': '0.5',
      'background-color': '#77828C',
      width: 50,
      height: 50,
      //text props
      'text-outline-color': '#77828C',
      'text-outline-width': 8,
    },
  },
  {
    selector: "node[type='device']",
    style: {
      shape: 'rectangle',
    },
  },
  {
    selector: "node[type='institution']",
    style: {
      backgroundColor: '#4a56a6',
    },
  },
  {
    selector: "node[type='topic']",
    style: {
      backgroundColor: 'blue',
    },
  },
  {
    selector: "node[type='researcher']",
    style: {
      backgroundColor: 'green',
    },
  },
  {
    selector: 'edge',
    style: {
      width: 3,
      // "line-color": "#6774cb",
      'line-color': '#AAD8FF',
      'target-arrow-color': '#6774cb',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
    },
  },
];

export const layout = {
  name: 'breadthfirst',
  fit: true,
  // circle: true,
  directed: true,
  padding: 50,
  // spacingFactor: 1.5,
  animate: true,
  animationDuration: 1000,
  avoidOverlap: true,
  nodeDimensionsIncludeLabels: false,
};

export const initialValue = {
  cited_count: '',
  works_count: '',
  institution_name: '',
  ror_link: '',
  author_count: '',
  institution_url: '',
  open_alex_link: '',
  is_hbcu: false,
  topics: [],
  works: [],
  organizations: [],
  authors: [],
  topic_name: '',
  topic_clusters: [],
  researcher_name: '',
  orcid_link: '',
  researcher_open_alex_link: '',
  topic_open_alex_link: '',
};

export const handleAutofill = (
  text: string,
  topic: boolean,
  setSuggestedTopics: React.Dispatch<React.SetStateAction<never[]>>,
  setSuggestedInstitutions: React.Dispatch<React.SetStateAction<never[]>>,
) => {
  fetch(
    !topic ? `${baseUrl}/autofill-institutions` : `${baseUrl}/autofill-topics`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(
        topic
          ? {
              topic: text,
            }
          : {
              institution: text,
            },
      ),
    },
  )
    .then((res) => res.json())
    .then((data) => {
      console.log(data);
      if (topic) {
        setSuggestedTopics(data?.possible_searches);
      } else {
        setSuggestedInstitutions(data?.possible_searches);
      }
      // setIsLoading(false);
    })
    .catch((error) => {
      // setIsLoading(false);
      if (topic) {
        setSuggestedTopics([]);
      } else {
        setSuggestedInstitutions([]);
      }
      console.log(error);
    });
};

export const handleTopicSpaceAutofill = (
  text: string,
  setSuggestedTopics: React.Dispatch<React.SetStateAction<never[]>>,
) => {
  fetch(
    `${baseUrl}/autofill-topic-space`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(
        {
          topic: text,
        }
      ),
    },
  )
    .then((res) => res.json())
    .then((data) => {
      console.log(data);
      setSuggestedTopics(data?.possible_searches);
    })
    .catch((error) => {
      setSuggestedTopics([]);
      console.log(error);
    });
};