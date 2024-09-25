import '../styles/Search.css';

import {useEffect, useState} from 'react';
import {Circles} from 'react-loader-spinner';
import {useSearchParams} from 'react-router-dom';

import {Box, Button} from '@chakra-ui/react';

// import CytoscapeComponent from 'react-cytoscapejs';
import GraphComponent from '../components/GraphComponent';
import InstitutionMetadata from '../components/InstitutionMetadata';
import ResearcherMetadata from '../components/ResearcherMetadata';
import TopicMetadata from '../components/TopicMetadata';
import {baseUrl, initialValue} from '../utils/constants';
import {ResearchDataInterface} from '../utils/interfaces';

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

  const handleSearch = () => {
    if (researcherType || universityName || topicType) {
      setIsLoading(true);
      if (
        (!topicType && !researcherType) ||
        (!researcherType && !universityName) ||
        (!topicType && !universityName)
      ) {
        const search = topicType
          ? 'topic'
          : universityName
          ? 'institution'
          : 'researcher';
        const topicName = topicType;
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
            search === 'institution'
              ? setData({
                  ...initialValue,
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
                })
              : search === 'topic'
              ? setData({
                  ...initialValue,
                  topic_name: topicName,
                  topic_clusters: data?.metadata?.topic_clusters,
                  graph: data?.graph,
                  cited_count: data?.metadata?.cited_by_count,
                  author_count: data?.metadata?.researchers,
                  works_count: data?.metadata?.work_count,
                  open_alex_link: data?.metadata?.oa_link,
                  organizations: data?.list,
                  search,
                })
              : setData({
                  ...initialValue,
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
                });
            setIsLoading(false);
          })
          .catch((error) => {
            setIsLoading(false);
            setData(initialValue);
            console.log(error);
          });
      } else {
        // fetch(`${baseUrl}/initial-search`, {
        //   method: 'POST',
        //   headers: {
        //     'Content-Type': 'application/json',
        //   },
        //   body: JSON.stringify({
        //     organization: universityName,
        //     type: institutionType,
        //     topic: topicType,
        //     researcher: researcherType,
        //   }),
        // })
        //   .then((res) => res.json())
        //   .then((data) => {
        //     console.log(data);
        //     setData({
        //     });
        //     setIsLoading(false);
        //   })
        //   .catch((error) => {
        //     setIsLoading(false);
        //     setData(initialValue);
        //     console.log(error);
        //   });
      }
    } else {
      setIsLoading(true);
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
          <option value='Education'>Education</option>
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
            ) : (
              <ResearcherMetadata data={data} />
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Search;
