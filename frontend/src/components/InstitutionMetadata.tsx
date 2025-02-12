import React from 'react';
import { Box, Flex, Text } from '@chakra-ui/react';
import { ResearchDataInterface } from '../utils/interfaces';

import styles from '../styles/SearchHighlight.module.css';

interface InstitutionMetadataProps {
  data: ResearchDataInterface;
  setTopic: React.Dispatch<React.SetStateAction<string>>;
  searchQuery?: string;
}

function highlightText(text: string, query?: string) {
  if (!text) return '';
  if (!query) return text;
  const parts = text.split(new RegExp(`(${query})`, 'gi'));
  return parts.map((part, i) =>
    part.toLowerCase() === query.toLowerCase() ? (
      <span key={i} className={styles.highlight}>
        {part}
      </span>
    ) : (
      part
    )
  );
}

const InstitutionMetadata: React.FC<InstitutionMetadataProps> = ({
  data,
  setTopic,
  searchQuery
}) => {
  return (
    <Flex
      display={{ base: 'block', lg: 'flex' }}
      justifyContent={'space-between'}
      mt='0.6rem'
      className='list-map'
    >
      <Box w={{ lg: '34%' }}>
        <button className='topButton'>List Map</button>
        <h2>
          {highlightText(
            data?.institution_name ?
              data?.is_hbcu ? `${data.institution_name} - HBCU` : data.institution_name
              : '',
            searchQuery
          )}
        </h2>
        <a
          target='_blank'
          rel='noreferrer'
          className='ror'
          href={data?.institution_url}
        >
          {highlightText(data?.institution_url || '', searchQuery)}
        </a>
        <p>
          {highlightText(`Total ${data?.author_count} authors`, searchQuery)}
        </p>
        <p>
          {highlightText(`Total ${data?.works_count} works`, searchQuery)}
        </p>
        <p>
          {highlightText(`Total ${data?.cited_count} citations`, searchQuery)}
        </p>

        <a target='_blank' rel='noreferrer' href={data?.open_alex_link}>
          {highlightText('View on OpenAlex', searchQuery)}
        </a>
        <a
          target='_blank'
          rel='noreferrer'
          className='ror'
          href={data?.ror_link}
        >
          RORID -{' '}
          {highlightText(
            data?.ror_link?.split('/')[
            data?.ror_link?.split('/')?.length - 1
            ] || '',
            searchQuery
          )}
        </a>
      </Box>

      <Box w={{ lg: '64%' }} mt={{ base: '.9rem', lg: 0 }}>
        <Box display={'flex'} justifyContent={'space-between'}>
          <Text fontSize={'18px'} fontWeight={600} w='72%'>
            Topic
          </Text>
          <Text fontSize={'18px'} fontWeight={600} w='26%'>
            No of people
          </Text>
        </Box>
        <Box mt='.5rem'>
          {data?.topics?.map((topic, idx) => (
            <Flex justifyContent={'space-between'} key={idx}>
              <Text
                fontSize='14px'
                w='72%'
                onClick={() => setTopic(topic[0])}
                textDecoration={'underline'}
                cursor='pointer'
              >
                {highlightText(topic[0] || '', searchQuery)}
              </Text>
              <Text fontSize='14px' w='26%'>
                {highlightText(String(topic[1] || ''), searchQuery)}
              </Text>
            </Flex>
          ))}
        </Box>
      </Box>
    </Flex>
  );
};

export default InstitutionMetadata;
