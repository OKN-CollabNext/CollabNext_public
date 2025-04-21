import React from 'react';
import { Box, Button, Flex, Text } from '@chakra-ui/react';
import { ResearchDataInterface } from '../utils/interfaces';

const InstitutionResearcherMetaData = ({
  data,
  setTopic,
  currentPage,
  totalPages,
  onPageChange,
}: {
  data: ResearchDataInterface;
  setTopic: React.Dispatch<React.SetStateAction<string>>;
  currentPage: number,
  totalPages: number,
  onPageChange: (page: number) => void;
}) => {
  return (
    <>
      <Flex
        display={{ base: 'block', lg: 'flex' }}
        justifyContent={'space-between'}
        mt='0.6rem'
        className='list-map'
      >
        <Box w={{ lg: '34%' }}>
          <button className='topButton'>List Map</button>
          <h2>{data?.researcher_name}</h2>
          <h2>{data?.institution_name}</h2>
          <a
            target='_blank'
            rel='noreferrer'
            className='ror'
            href={data?.institution_url}
          >
            {data?.institution_url}
          </a>
          <a
            target='_blank'
            rel='noreferrer'
            className='ror'
            href={data?.orcid_link}
          >
            {data?.orcid_link}
          </a>
          <p>Total {data?.works_count} works</p>
          <p>Total {data?.cited_count} citations</p>
          <a target='_blank' rel='noreferrer' href={data?.open_alex_link}>
            View Institution on OpenAlex
          </a>
          <a
            target='_blank'
            rel='noreferrer'
            href={data?.researcher_open_alex_link}
          >
            View Researcher on OpenAlex
          </a>
          <a target='_blank' rel='noreferrer' href={data?.ror_link}>
            RORID -{' '}
            {data?.ror_link?.split('/')[data?.ror_link?.split('/')?.length - 1]}
          </a>
        </Box>
        <Box w={{ lg: '64%' }} mt={{ base: '.9rem', lg: 0 }}>
          <Box display={'flex'} justifyContent={'space-between'}>
            <Text fontSize={'18px'} fontWeight={600} w='72%'>
              Topic
            </Text>
            <Text fontSize='18px' fontWeight={600} w='32%'>
              # of Works
            </Text>
          </Box>
          {/* … */}
          <Box mt='.5rem'>
            {/* header */}
            <Box display='flex' justifyContent='space-between'>
              <Text fontSize='18px' fontWeight={600} w='48%'>Topic</Text>
              <Text fontSize='18px' fontWeight={600} w='24%'># of Works</Text>
              <Text fontSize='18px' fontWeight={600} w='28%'>Article Title</Text>
            </Box>
            {data?.topics?.map(([topicName, works], i) => (
              <Flex justifyContent='space-between' key={topicName + i}>
                <Text
                  fontSize='14px'
                  w='48%'
                  onClick={() => setTopic(topicName)}
                  textDecoration='underline'
                  cursor='pointer'
                >
                  {topicName}
                </Text>
                <Text fontSize='14px' w='24%'>
                  {works}
                </Text>
                <Text fontSize='14px' w='28%'>
                  {Array.isArray(data?.authors)
                    ? data.authors[i]?.[0] ?? '—'
                    : data?.list?.[i]?.[0] ?? '—'}
                </Text>
              </Flex>
            ))}
          </Box>
        </Box>
      </Flex>
      <Flex justifyContent="center" mt={4} gap={2} alignItems="center">
        <Button
          onClick={() => onPageChange(currentPage - 1)}
          isDisabled={currentPage === 1}
          size="sm"
        >
          Previous
        </Button>
        <Text fontSize="sm">
          Page {currentPage} of {totalPages}
        </Text>
        <Button
          onClick={() => onPageChange(currentPage + 1)}
          isDisabled={currentPage === totalPages}
          size="sm"
        >
          Next
        </Button>
      </Flex>
    </>
  );
};

export default InstitutionResearcherMetaData;
