import '../styles/Search.css';

import { useEffect, useState } from 'react';
import { Circles } from 'react-loader-spinner';
import { useSearchParams } from 'react-router-dom';

import { Box, Button } from '@chakra-ui/react';

import AllThreeMetadata from '../components/AllThreeMetadata';
// import CytoscapeComponent from 'react-cytoscapejs';
import GraphComponent from '../components/GraphComponent';
import InstitutionMetadata from '../components/InstitutionMetadata';
import InstitutionResearcherMetaData from '../components/InstitutionResearcherMetaData';
import ResearcherMetadata from '../components/ResearcherMetadata';
import TopicInstitutionMetadata from '../components/TopicInstitutionMetadata';
import TopicMetadata from '../components/TopicMetadata';
import TopicResearcherMetadata from '../components/TopicResearcherMetadata';
import { baseUrl, initialValue } from '../utils/constants';
import { ResearchDataInterface, SearchType } from '../utils/interfaces';

const Search = () => {
  let [searchParams] = useSearchParams();
  // const cyRef = React.useRef<cytoscape.Core | undefined>();
  const institution = searchParams.get('institution');
  const type = searchParams.get('type');
  const topic = searchParams.get('topic');
  const researcher = searchParams.get('researcher');
  const [isNetworkMap, setIsNetworkMap] = useState(false);
  const [universityName, setUniversityName] = useState(institution || '');
  const [topicType, setTopicType] = useState(topic || '');
  const [institutionType, setInstitutionType] = useState(type || 'Education');
  const [researcherType, setResearcherType] = useState(researcher || '');
  const [data, setData] = useState<ResearchDataInterface>(initialValue);
  const [isLoading, setIsLoading] = useState(false);

  // const toast = useToast();

  const handleToggle = () => {
    setIsNetworkMap(!isNetworkMap);
  };

  useEffect(() => {
    handleSearch();
  }, []);

  const sendSearchRequest = (search: SearchType) => {
    fetch(`${baseUrl}/initial-search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        organization: universityName,
        type: institutionType,
        topic: topicType,
        researcher: researcherType,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        console.log(data);
        const dataObj =
          search === 'institution'
            ? {
                institution_name: data?.metadata?.name,
                is_hbcu: data?.metadata?.hbcu,
                cited_count: data?.metadata?.cited_count,
                author_count: data?.metadata?.author_count,
                works_count: data?.metadata?.works_count,
                institution_url: data?.metadata?.homepage,
                open_alex_link: data?.metadata?.oa_link,
                ror_link: data?.metadata?.ror,
                graph: data?.graph,
                topics: data?.list,
                search,
              }
            : search === 'topic'
            ? {
                topic_name: data?.metadata?.name,
                topic_clusters: data?.metadata?.topic_clusters,
                graph: data?.graph,
                cited_count: data?.metadata?.cited_by_count,
                author_count: data?.metadata?.researchers,
                works_count: data?.metadata?.work_count,
                open_alex_link: data?.metadata?.oa_link,
                organizations: data?.list,
                search,
              }
            : search === 'researcher'
            ? {
                institution_name: data?.metadata?.current_institution,
                researcher_name: data?.metadata?.name,
                orcid_link: data?.metadata?.orcid,
                cited_count: data?.metadata?.cited_by_count,
                works_count: data?.metadata?.work_count,
                graph: data?.graph,
                open_alex_link: data?.metadata?.oa_link,
                topics: data?.list,
                institution_url: data?.metadata?.institution_url,
                search,
              }
            : search === 'researcher-institution'
            ? {
                graph: data?.graph,
                topics: data?.list,
                institution_url: data?.metadata?.homepage,
                institution_name: data?.metadata?.institution_name,
                researcher_name: data?.metadata?.researcher_name,
                orcid_link: data?.metadata?.orcid,
                works_count: data?.metadata?.work_count,
                cited_count: data?.metadata?.cited_by_count,
                ror_link: data?.metadata?.ror,
                open_alex_link: data?.metadata?.institution_oa_link,
                researcher_open_alex_link: data?.metadata?.researcher_oa_link,
                search,
              }
            : search === 'topic-researcher'
            ? {
                graph: data?.graph,
                works: data?.list,
                institution_name: data?.metadata?.current_institution,
                topic_name: data?.metadata?.topic_name,
                researcher_name: data?.metadata?.researcher_name,
                orcid_link: data?.metadata?.orcid,
                works_count: data?.metadata?.work_count,
                cited_count: data?.metadata?.cited_by_count,
                open_alex_link: data?.metadata?.topic_oa_link,
                researcher_open_alex_link: data?.metadata?.researcher_oa_link,
                topic_clusters: data?.metadata?.topic_clusters,
                search,
              }
            : search === 'topic-institution'
            ? {
                graph: data?.graph,
                institution_name: data?.metadata?.institution_name,
                topic_name: data?.metadata?.topic_name,
                institution_url: data?.metadata?.homepage,
                cited_count: data?.metadata?.cited_by_count,
                works_count: data?.metadata?.work_count,
                author_count: data?.metadata?.people_count,
                open_alex_link: data?.metadata?.institution_oa_link,
                topic_open_alex_link: data?.metadata?.topic_oa_link,
                ror_link: data?.metadata?.ror,
                topic_clusters: data?.metadata?.topic_clusters,
                authors: data?.list,
                search,
              }
            : {
                graph: data?.graph,
                works: data?.list,
                institution_url: data?.metadata?.homepage,
                institution_name: data?.metadata?.institution_name,
                researcher_name: data?.metadata?.researcher_name,
                topic_name: data?.metadata?.topic_name,
                orcid_link: data?.metadata?.orcid,
                works_count: data?.metadata?.work_count,
                cited_count: data?.metadata?.cited_by_count,
                ror_link: data?.metadata?.ror,
                open_alex_link: data?.metadata?.institution_oa_link,
                topic_open_alex_link: data?.metadata?.topic_oa_link,
                researcher_open_alex_link: data?.metadata?.researcher_oa_link,
                topic_clusters: data?.metadata?.topic_clusters,
                search,
              };
        setData({
          ...initialValue,
          ...dataObj,
        });
        setIsLoading(false);
      })
      .catch((error) => {
        setIsLoading(false);
        setData(initialValue);
        console.log(error);
      });
  };

  const handleSearch = () => {
    setIsLoading(true);
    if (topicType && universityName && researcherType) {
      sendSearchRequest('all-three-search');
    } else if (
      (topicType && researcherType) ||
      (researcherType && universityName) ||
      (topicType && universityName)
    ) {
      const search =
        topicType && researcherType
          ? 'topic-researcher'
          : researcherType && universityName
          ? 'researcher-institution'
          : 'topic-institution';
      sendSearchRequest(search);
    } else if (topicType || universityName || researcherType) {
      const search = topicType
        ? 'topic'
        : universityName
        ? 'institution'
        : 'researcher';
      sendSearchRequest(search);
    } else {
      fetch(`${baseUrl}/get-default-graph`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: null,
      })
        .then((res) => res.json())
        .then((data) => {
          console.log(data);
          setData({
            ...initialValue,
            graph: data?.graph,
          });
          setIsNetworkMap(true);
          setIsLoading(false);
        })
        .catch((error) => {
          setIsLoading(false);
          setData(initialValue);
          console.log(error);
        });
    }
  };

  return (
    <div className='main-content'>
      <div className='sidebar'>
        <input
          type='text'
          value={universityName}
          onChange={(e) => setUniversityName(e.target.value)}
          placeholder='University Name'
          className='textbox'
          disabled={isLoading}
        />
        <input
          type='text'
          value={topicType}
          onChange={(e) => setTopicType(e.target.value)}
          placeholder='Type Topic'
          className='textbox'
          disabled={isLoading}
        />
        <select
          value={institutionType}
          onChange={(e) => setInstitutionType(e.target.value)}
          className='dropdown'
        >
          <option value='Education'>HBCU</option>
        </select>
        {/* <FormControl isInvalid={topicType && !researcherType ? true : false}> */}
        <input
          type='text'
          value={researcherType}
          onChange={(e) => setResearcherType(e.target.value)}
          placeholder='Type Researcher'
          className='textbox'
          disabled={isLoading}
        />
        {/* <FormErrorMessage>
            Researcher must be provided when Topic is
          </FormErrorMessage>
        </FormControl> */}
        <Button
          width='100%'
          marginTop='10px'
          backgroundColor='transparent'
          color='white'
          border='2px solid white'
          isLoading={isLoading}
          onClick={() => handleSearch()}
        >
          Search
        </Button>
        <button className='button' onClick={handleToggle}>
          {isNetworkMap ? 'See List Map' : 'See Network Map'}
        </button>
      </div>
      <div className='content'>
        {isLoading ? (
          <Box
            w={{lg: '500px'}}
            justifyContent={'center'}
            height={{base: '190px', lg: '340px'}}
            display={'flex'}
            alignItems='center'
          >
            <Circles
              height='80'
              width='80'
              color='#003057'
              ariaLabel='circles-loading'
              wrapperStyle={{}}
              wrapperClass=''
              visible={true}
            />
          </Box>
        ) : !data?.graph ? (
          <Box fontSize={{lg: '20px'}} ml={{lg: '4rem'}} fontWeight={'bold'}>
            No result
          </Box>
        ) : isNetworkMap ? (
          <div className='network-map'>
            <button className='topButton'>Network Map</button>
            {/* <img src={NetworkMap} alt='Network Map' /> */}
            <GraphComponent graphData={data?.graph} />
          </div>
        ) : (
          <div>
            {data?.search === 'institution' ? (
              <InstitutionMetadata data={data} />
            ) : data?.search === 'topic' ? (
              <TopicMetadata data={data} />
            ) : data?.search === 'researcher' ? (
              <ResearcherMetadata data={data} />
            ) : data?.search === 'researcher-institution' ? (
              <InstitutionResearcherMetaData data={data} />
            ) : data?.search === 'topic-researcher' ? (
              <TopicResearcherMetadata data={data} />
            ) : data?.search === 'topic-institution' ? (
              <TopicInstitutionMetadata data={data} />
            ) : (
              <AllThreeMetadata data={data} />
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Search;
