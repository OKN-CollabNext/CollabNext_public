import '../styles/Search.css';

import React, {useEffect, useState} from 'react';
import {Circles} from 'react-loader-spinner';

import {Box, Button} from '@chakra-ui/react';

import GraphComponent from '../components/GraphComponent';
import { baseUrl, handleTopicSpaceAutofill, initialValue } from '../utils/constants';
import Suggested from '../components/Suggested';

const TopicSearch = () => {
  let [topicType, setTopicType] = useState('');
  const [data, setData] = useState<{graph?: {nodes: any[]; edges: any[]}}>({});
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    handleSearch();
  }, []);

  const [suggestedTopics, setSuggestedTopics] = useState([]);

  const handleSearch = (topic?: string) => {
    if (topicType) {
      setIsLoading(true);
      fetch(`${baseUrl}/search-topic-space`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          topic: topicType,
        }),
      })
        .then((res) => res.json())
        .then((data) => {
          console.log(data);
          setData({
            graph: data?.graph,
          });
          setIsLoading(false);
        })
        .catch((error) => {
          setIsLoading(false);
          setData({});
          console.log(error);
        });
    } else {
      setIsLoading(true);
      fetch(`${baseUrl}/get-topic-space-default-graph`, {
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
            graph: data?.graph,
          });
          setIsLoading(false);
        })
        .catch((error) => {
          setIsLoading(false);
          setData({});
          console.log(error);
        });
    }
  };

  return (
    <div className='main-content'>
      <div className='sidebar'>
        <input
          type='text'
          value={topicType}
          onChange={(e) => {
            setTopicType(e.target.value);
            handleTopicSpaceAutofill(
              e.target.value,
              setSuggestedTopics,
            );
          }}
          list='topics'
          placeholder='Type Topic'
          className='textbox'
          disabled={isLoading}
        />
        <Suggested suggested={suggestedTopics} institutions={false} />
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
        ) : (
          <div className='network-map'>
            <button className='topButton'>Network Map</button>
            <GraphComponent graphData={data?.graph} />
          </div>
        )}
      </div>
    </div>
  );
};

export default TopicSearch;
