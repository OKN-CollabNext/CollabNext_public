import '../styles/Search.css';

import { useEffect, useRef, useState } from 'react';
import { Circles } from 'react-loader-spinner';
import { useSearchParams } from 'react-router-dom';

import {
	Box,
	Button,
	Checkbox,
	Flex,
	Input,
	list,
	Text,
} from '@chakra-ui/react';

import AllThreeMetadata from '../components/AllThreeMetadata';
// import CytoscapeComponent from 'react-cytoscapejs';
import GraphComponent from '../components/GraphComponent';
import InstitutionMetadata from '../components/InstitutionMetadata';
import InstitutionResearcherMetaData from '../components/InstitutionResearcherMetaData';
import ResearcherMetadata from '../components/ResearcherMetadata';
import Suggested from '../components/Suggested';
import TopicInstitutionMetadata from '../components/TopicInstitutionMetadata';
import TopicMetadata from '../components/TopicMetadata';
import TopicResearcherMetadata from '../components/TopicResearcherMetadata';
import { baseUrl, handleAutofill, initialValue, initialInstitutionDesignationsValues } from '../utils/constants';
import { ResearchDataInterface, SearchType, InstitutionDesignations } from '../utils/interfaces';

const Search = () => {
  let [searchParams] = useSearchParams();
  // const cyRef = React.useRef<cytoscape.Core | undefined>();
  const institution = searchParams.get('institution');
  const type = searchParams.get('type');
  const topic = searchParams.get('topic');
  const researcher = searchParams.get('researcher');
  const [isNetworkMap, setIsNetworkMap] = useState('list');
  const [universityName, setUniversityName] = useState(institution || '');
  const [universityName2, setUniversityName2] = useState('');
  const [topicType, setTopicType] = useState(topic || '');
  const [institutionType, setInstitutionType] = useState(type || 'Education');
  const [researcherType, setResearcherType] = useState(researcher || '');
  const [researcherType2, setResearcherType2] = useState('');
  const [data, setData] = useState<ResearchDataInterface>(initialValue);
  const [institutionDesignations, setInstitutionDesignations] = useState<InstitutionDesignations[]>([initialInstitutionDesignationsValues]);
  const [isLoading, setIsLoading] = useState(false);
  const [isAddOrgChecked, setIsAddOrgChecked] = useState(false);
  const [orgList, setOrgList] = useState<File | null>(null);
  const [isAddPersonChecked, setIsAddPersonChecked] = useState(false);
  const [personList, setPersonList] = useState<File | null>(null);
  const [suggestedInstitutions, setSuggestedInstitutions] = useState([]);
  const [suggestedTopics, setSuggestedTopics] = useState([]);

  // const toast = useToast();

  let latestRequestId = 0;
  const handleToggle = (value: string) => {
    setIsNetworkMap(value);
  };

  const sendSearchRequest = (search: SearchType) => {
    const requestId = ++latestRequestId;
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
        if (requestId === latestRequestId) {
          setData({
            ...initialValue,
            ...dataObj,
          });
          setIsLoading(false);
        }
      })
      .catch((error) => {
        if (requestId === latestRequestId) {
          setData(initialValue);
          setIsLoading(false);
        }
        console.log(error);
      });
  };

  const institutionDesignationSearch = (universityName: string) => {
    fetch(`${baseUrl}/institutions-designations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ institution_name:  universityName }),
    })
      .then(res => res.json())
      .then((data) => {
        console.log(data);
        setInstitutionDesignations(data);
      })
      .catch((error) => {
        console.log(error);
        setInstitutionDesignations([initialInstitutionDesignationsValues]);
        setIsLoading(false);
      });
  }

  const handleSearch = () => {
    setIsLoading(true);
    if (topicType && universityName && researcherType) {
      sendSearchRequest('all-three-search');
      institutionDesignationSearch(universityName);
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
      institutionDesignationSearch(universityName);
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
          setIsNetworkMap('graph');
          setIsLoading(false);
        })
        .catch((error) => {
          setIsLoading(false);
          setData(initialValue);
          console.log(error);
        });
    }
  };

  const orgInputRef = useRef<HTMLInputElement>(null);
  const personInputRef = useRef<HTMLInputElement>(null);

  const handleListClick = (ref: React.RefObject<HTMLInputElement>) => {
    ref?.current?.click();
  };

  const handleListChange = (
    e: React.ChangeEvent<HTMLInputElement>,
    setList: React.Dispatch<React.SetStateAction<File | null>>,
  ) => {
    if (e.target.files) {
      const file = e.target.files[0];
      console.log(file);
      if (file && file.name.endsWith('.csv')) {
        setList(file);
      } else if (file) {
        alert('Please select a valid CSV file.');
      }
    }
  };

  useEffect(() => {
    handleSearch();
  }, [universityName, institutionType, topicType, researcherType]);

  return (
    <Box>
      <Flex justifyContent={'flex-end'} px='2rem'>
        {['List', 'Graph', 'Map'].map((value) => (
          <Button
            onClick={() => setIsNetworkMap(value.toLowerCase())}
            bg='linear-gradient(#053257, #7e7e7e)'
            color='white'
            mr='1rem'
          >
            {value}
          </Button>
        ))}
      </Flex>
      <div className='main-content'>
        <div className='sidebar'>
          <input
            type='text'
            value={universityName}
            list='institutions'
            onChange={(e) => {
              setUniversityName(e.target.value);
              handleAutofill(
                e.target.value,
                false,
                setSuggestedTopics,
                setSuggestedInstitutions,
              );
            }}
            placeholder={'University Name'}
            className='textbox'
            // disabled={isLoading}
          />
          <Suggested suggested={suggestedInstitutions} institutions={true} />
          {isAddOrgChecked && (
            <>
              <input
                type='text'
                value={universityName2}
                list='institutions'
                onChange={(e) => {
                  setUniversityName2(e.target.value);
                  handleAutofill(
                    e.target.value,
                    false,
                    setSuggestedTopics,
                    setSuggestedInstitutions,
                  );
                }}
                placeholder={'Another University'}
                className='textbox'
                // disabled={isLoading}
              />
              <Suggested
                suggested={suggestedInstitutions}
                institutions={true}
              />
            </>
          )}
          <input
            type='text'
            value={topicType}
            onChange={(e) => {
              setTopicType(e.target.value);
              handleAutofill(
                e.target.value,
                true,
                setSuggestedTopics,
                setSuggestedInstitutions,
              );
            }}
            list='topics'
            placeholder='Type Topic'
            className='textbox'
            // disabled={isLoading}
          />
          <Suggested suggested={suggestedTopics} institutions={false} />
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
            // disabled={isLoading}
          />
          {isAddPersonChecked && (
            <input
              type='text'
              value={researcherType2}
              onChange={(e) => setResearcherType2(e.target.value)}
              placeholder='Another Researcher'
              className='textbox'
              // disabled={isLoading}
            />
          )}
          {/* <FormErrorMessage>
            Researcher must be provided when Topic is
          </FormErrorMessage>
        </FormControl> */}
          {/* <Button
          width='100%'
          marginTop='10px'
          backgroundColor='transparent'
          color='white'
          border='2px solid white'
          isLoading={isLoading}
          onClick={() => handleSearch()}
        >
          Search
        </Button> */}
          <Box mt='.6rem'>
            <Flex justifyContent={'space-between'}>
              {[
                {
                  checkedState: isAddOrgChecked,
                  setCheckedState: setIsAddOrgChecked,
                  text: 'Add Another Org',
                },
                {
                  checkedState: isAddPersonChecked,
                  setCheckedState: setIsAddPersonChecked,
                  text: 'Add Another Person',
                },
              ].map(({checkedState, setCheckedState, text}) => (
                <Flex>
                  <Checkbox
                    mr='.2rem'
                    checked={checkedState}
                    onChange={(e) => setCheckedState(e.target.checked)}
                  />
                  <Text fontSize='11px' color={'white'}>
                    {text}
                  </Text>
                </Flex>
              ))}
            </Flex>
            <Box mt='.6rem'>
              {[
                {
                  list: orgList,
                  setList: setOrgList,
                  text: 'Upload Org List',
                  ref: orgInputRef,
                },
                {
                  list: personList,
                  setList: setPersonList,
                  text: 'Upload Person List',
                  ref: personInputRef,
                },
              ].map(({list, setList, text, ref}) => (
                <Flex alignItems='center'>
                  <Button
                    border='1px solid white'
                    bg='transparent'
                    color='white'
                    fontWeight={400}
                    fontSize={'13px'}
                    onClick={() => handleListClick(ref)}
                    mt='.3rem'
                    mr='.35rem'
                  >
                    {list?.name?.slice(0, 14) || text}
                  </Button>
                  <input
                    onChange={(e) => handleListChange(e, setList)}
                    type='file'
                    ref={ref}
                    accept='.csv'
                    hidden
                  />
                  {list && (
                    <Text
                      fontSize='11px'
                      color={'white'}
                      cursor='pointer'
                      onClick={() => {
                        setList(null);
                        // @ts-ignore
                        ref.current.value = '';
                      }}
                    >
                      remove
                    </Text>
                  )}
                </Flex>
              ))}
            </Box>
          </Box>
          {/* <button className='button' onClick={handleToggle}>
            {isNetworkMap ? 'See List Map' : 'See Network Map'}
          </button> */}
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
          ) : isNetworkMap === 'graph' ? (
            <div className='network-map'>
              <button className='topButton'>Network Map</button>
              {/* <img src={NetworkMap} alt='Network Map' /> */}
              <GraphComponent
                graphData={data?.graph}
                setInstitution={setUniversityName}
                setTopic={setTopicType}
                setResearcher={setResearcherType}
              />
            </div>
          ) : isNetworkMap === 'list' ? (
            <div>
              {data?.search === 'institution' ? (
                <InstitutionMetadata data={data} setTopic={setTopicType} institutionDesignations={institutionDesignations[0]} />
              ) : data?.search === 'topic' ? (
                <TopicMetadata data={data} setInstitution={setUniversityName} />
              ) : data?.search === 'researcher' ? (
                <ResearcherMetadata data={data} setTopic={setTopicType} />
              ) : data?.search === 'researcher-institution' ? (
                <InstitutionResearcherMetaData
                  data={data}
                  setTopic={setTopicType}
                />
              ) : data?.search === 'topic-researcher' ? (
                <TopicResearcherMetadata data={data} />
              ) : data?.search === 'topic-institution' ? (
                <TopicInstitutionMetadata
                  data={data}
                  setResearcher={setResearcherType}
                />
              ) : (
                <AllThreeMetadata data={data} />
              )}
            </div>
          ) : (
            <Box></Box>
          )}
        </div>
      </div>
    </Box>
  );
};

export default Search;
