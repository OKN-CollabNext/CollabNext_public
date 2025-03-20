import '../styles/Search.css';

import { useEffect, useState } from 'react';
import { Circles } from 'react-loader-spinner';
import { useSearchParams, useNavigate, useLocation } from 'react-router-dom';

import { Box, Button } from '@chakra-ui/react';

import AllThreeMetadata from '../components/AllThreeMetadata';
import GraphComponent from '../components/GraphComponent';
import InstitutionMetadata from '../components/InstitutionMetadata';
import InstitutionResearcherMetaData from '../components/InstitutionResearcherMetaData';
import ResearcherMetadata from '../components/ResearcherMetadata';
import Suggested from '../components/Suggested';
import TopicInstitutionMetadata from '../components/TopicInstitutionMetadata';
import TopicMetadata from '../components/TopicMetadata';
import TopicResearcherMetadata from '../components/TopicResearcherMetadata';
import { baseUrl, handleAutofill, initialValue } from '../utils/constants';
import { ResearchDataInterface, SearchType } from '../utils/interfaces';
import React from 'react';

const Search = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const location = useLocation();

  // this keeps track of where you've been so you can use the back button
  useEffect(() => {
    sessionStorage.setItem('lastSearchURL', window.location.href);
  }, [location]);

  // Get parameters from URL
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
  const [suggestedInstitutions, setSuggestedInstitutions] = useState([]);
  const [suggestedTopics, setSuggestedTopics] = useState([]);

  const handleToggle = () => {
    setIsNetworkMap(!isNetworkMap);
  };

  // keeps the app in sync with what's in the url
  useEffect(() => {
    // Update component state when URL parameters change
    setUniversityName(institution || '');
    setTopicType(topic || '');
    setInstitutionType(type || 'Education');
    setResearcherType(researcher || '');

    // if someone already typed in search info, go ahead and search
    // this runs their last search automatically when they come back
    if (institution || topic || researcher) {
      handleSearch();
    }
  }, [institution, topic, type, researcher]);

  // Initial search when component mounts
  useEffect(() => {
    handleSearch();
  }, []);

  // this updates the url so the browser keeps track of your searches
  const updateURLParams = () => {
    const params = new URLSearchParams();

    if (universityName) params.set('institution', universityName);
    if (topicType) params.set('topic', topicType);
    if (institutionType) params.set('type', institutionType);
    if (researcherType) params.set('researcher', researcherType);

    // this updates the url without causing a page reload
    setSearchParams(params);
  };

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
    // update url parameters before performing search
    updateURLParams();

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
          placeholder='University Name'
          className='textbox'
          disabled={isLoading}
        />
        <Suggested suggested={suggestedInstitutions} institutions={true} />
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
          disabled={isLoading}
        />
        <Suggested suggested={suggestedTopics} institutions={false} />
        <select
          value={institutionType}
          onChange={(e) => setInstitutionType(e.target.value)}
          className='dropdown'
        >
          <option value='Education'>HBCU</option>
        </select>
        <input
          type='text'
          value={researcherType}
          onChange={(e) => setResearcherType(e.target.value)}
          placeholder='Type Researcher'
          className='textbox'
          disabled={isLoading}
        />
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
            <GraphComponent graphData={data?.graph} setInstitution={undefined} setTopic={undefined} setResearcher={undefined} />
          </div>
        ) : (
          <div>
            {data?.search === 'institution' ? (
              <InstitutionMetadata data={data} setTopic={function (value: React.SetStateAction<string>): void {
                      throw new Error('Function not implemented.');
                    } } />
            ) : data?.search === 'topic' ? (
              <TopicMetadata data={data} setInstitution={function (value: React.SetStateAction<string>): void {
                        throw new Error('Function not implemented.');
                      } } />
            ) : data?.search === 'researcher' ? (
              <ResearcherMetadata data={data} setTopic={function (value: React.SetStateAction<string>): void {
                          throw new Error('Function not implemented.');
                        } } />
            ) : data?.search === 'researcher-institution' ? (
              <InstitutionResearcherMetaData data={data} setTopic={function (value: React.SetStateAction<string>): void {
                            throw new Error('Function not implemented.');
                          } } />
            ) : data?.search === 'topic-researcher' ? (
              <TopicResearcherMetadata data={data} />
            ) : data?.search === 'topic-institution' ? (
              <TopicInstitutionMetadata data={data} setResearcher={function (value: React.SetStateAction<string>): void {
                                throw new Error('Function not implemented.');
                              } } />
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
