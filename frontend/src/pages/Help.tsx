import React from 'react';

import {Box, ListItem, Text, UnorderedList} from '@chakra-ui/react';

const Help = () => {
  return (
    <Box w={{lg: '900px'}} mx='auto' mt='1.5rem'>
      <Text
        pl={{base: '.8rem', lg: 0}}
        fontFamily='DM Sans'
        fontSize={{lg: '22px'}}
        color='#000000'
      >
        Help
      </Text>
      <Box
        background='linear-gradient(180deg, #003057 0%, rgba(0, 0, 0, 0.5) 100%)'
        borderRadius={{lg: '6px'}}
        px='.8rem'
        py={{base: '1.5rem', lg: '2rem'}}
        mt='1rem'
      >
        <Box>
          <Text
            lineHeight='24px'
            color='#FFFFFF'
            fontSize={{base: '12px', lg: '16px'}}
          >
            This is an alpha version of the CollabNext web application. Since
            this is only an alpha version of a prototype, we are not able to
            provide any direct help or support regarding the use of this tool.
            However, if you need assistance, you are welcome to share your
            question or comment on our{' '}
            <a
              href='https://collabnext.io/feedback'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              Feedback page
            </a>
            . Be sure to include your name and email so we can follow up.
          </Text>
        </Box>
        <Box mt='1.7rem'>
          <Text
            mt='.45rem'
            lineHeight='24px'
            color='#FFFFFF'
            fontSize={{base: '12px', lg: '16px'}}
          >
            Here are some tips for using this alpha version of the web
            application:
            <br />
            <br />
            <UnorderedList ml='3.5rem'>
              <ListItem>
                You can toggle the results of a search between a tabular view
                (called a List Map) or a graphical view (called Network Map).
              </ListItem>
              <ListItem>
                The Explore Topics button on the home page is an experimental,
                graphical approach to exploring the
                <a
                  href='https://docs.google.com/document/d/1bDopkhuGieQ4F8gGNj7sEc8WSE8mvLZS/edit'
                  target='_blank'
                  rel='noreferrer'
                  style={{color: 'cornsilk', textDecoration: 'underline'}}
                >
                  OpenAlex Topic Classification scheme
                </a>
                . Follow the link for more details on this classification
                process.
              </ListItem>
              <ListItem>
                Best results are achieved in the current version by searching
                for Institution and/or Topic first, and then using the listed
                name of a person to add a people filter which shows
                publications. We have implemented an auto - complete feature for
                Institutions and Topics, but it is harder to do that with
                researcher names.
              </ListItem>
            </UnorderedList>
          </Text>
        </Box>
        <Box mt='1.7rem'>
          <Text
            mt='.45rem'
            lineHeight='24px'
            color='#FFFFFF'
            fontSize={{base: '12px', lg: '16px'}}
          >
            Our{' '}
            <a
              href='https://github.com/OKN-CollabNext/CollabNext_public'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              github project
            </a>{' '}
            has several known issues. These include:
            <br />
            <br />
            <UnorderedList ml='3.5rem'>
              <ListItem>
                Once in a while, a search comes back showing no results, which
                is clearly incorrect. This seems to happen more frequently on
                the first few searches and on searches which have a large amount
                of data. You may be able to work around this by hitting the
                search button a second or third time.
              </ListItem>
              <ListItem>
                Counts (researchers, publications, topics) may vary from screen
                to screen. This is typically the result of the fact that we are
                considering subfields as the topic filter, but OpenAlex pre -
                computed counts are using topic IDs. A given subfield has
                multiple topic IDs, which we sum, but this means we are
                potentially double counting some items.
              </ListItem>
            </UnorderedList>
          </Text>
        </Box>
      </Box>
    </Box>
  );
};

export default Help;
