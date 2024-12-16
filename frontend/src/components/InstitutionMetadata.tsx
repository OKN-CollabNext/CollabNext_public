import React from 'react';

import { Box, Flex, Text } from '@chakra-ui/react';

import { ResearchDataInterface } from '../utils/interfaces';
import MUPDataVisualizer from './MUPDataVisualizer';

const InstitutionMetadata = ({data}: {data: ResearchDataInterface}) => {
  return (
    <Box>
      <Flex
        display={{base: 'block', lg: 'flex'}}
        justifyContent={'space-between'}
        mt='0.6rem'
        className='list-map'
      >
        <Box w={{lg: '34%'}}>
          <button className='topButton'>List Map</button>
          <h2>
            {data?.institution_name}
            {data?.is_hbcu ? ' - HBCU' : ''}
          </h2>
          <a
            target='_blank'
            rel='noreferrer'
            className='ror'
            href={data?.institution_url}
          >
            {data?.institution_url}
          </a>
          <p>Total {data?.author_count} authors</p>
          <p>Total {data?.works_count} works</p>
          <p>Total {data?.cited_count} citations</p>
          <a target='_blank' rel='noreferrer' href={data?.open_alex_link}>
            View on OpenAlex
          </a>
          <a
            target='_blank'
            rel='noreferrer'
            className='ror'
            href={data?.ror_link}
          >
            RORID -{' '}
            {data?.ror_link?.split('/')[data?.ror_link?.split('/')?.length - 1]}
          </a>
        </Box>
        <Box w={{lg: '64%'}} mt={{base: '.9rem', lg: 0}}>
          <Box display={'flex'} justifyContent={'space-between'}>
            <Text fontSize={'18px'} fontWeight={600} w='72%'>
              Topic
            </Text>
            <Text fontSize={'18px'} fontWeight={600} w='26%'>
              No of people
            </Text>
          </Box>
          <Box mt='.5rem'>
            {data?.topics?.map((topic) => (
              <Flex justifyContent={'space-between'}>
                <Text fontSize='14px' w='72%'>
                  {topic[0]}
                </Text>
                <Text fontSize='14px' w='26%'>
                  {topic[1]}
                </Text>
              </Flex>
            ))}
          </Box>
        </Box>
      </Flex>

      <Box 
        mt={8} 
        p={6} 
        bg="rgba(0, 48, 87, 0.05)" 
        borderRadius="lg"
      >
        <MUPDataVisualizer institutionName={data.institution_name} />
      </Box>
    </Box>
  );
};

export default InstitutionMetadata;
