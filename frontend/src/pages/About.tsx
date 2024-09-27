import React from 'react';

import { Box, Text } from '@chakra-ui/react';

const About = () => {
  return (
    <Box w={{lg: '900px'}} mx='auto' mt='1.5rem'>
      <Text
        pl={{base: '.8rem', lg: 0}}
        fontFamily='DM Sans'
        fontSize={{lg: '22px'}}
        color='#000000'
      >
        About Us
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
            fontSize={{base: '17px', lg: '24px'}}
            color='#FFFFFF'
            fontWeight={'bold'}
          >
            Background
          </Text>
          <Text
            mt='.45rem'
            lineHeight='24px'
            color='#FFFFFF'
            fontSize={{base: '12px', lg: '16px'}}
          >
            Our proof-of-concept{' '}
            <a
              href='https://gt-msi-diversifind.azuremicroservices.io/'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              CollabNext tool
            </a>{' '}
            originated as a partnership between Georgia Tech and the Atlanta
            University Center, and is now being developed jointly by Fisk
            University, Georgia Tech, Morehouse College, Texas Southern
            University, and University at Buffalo with{' '}
            <a
              href='https://www.nsf.gov/awardsearch/advancedSearchResult?ActiveAwards=true&AwardAmount=&AwardInstrument=&AwardNumberOperator=&BooleanElement=Any&BooleanRef=All&ExpDateOperator=&Keyword=Proto-OKN&OriginalAwardDateFrom=08%2F01%2F2023&OriginalAwardDateOperator=Range&OriginalAwardDateTo=09%2F22%2F2023&PICountry=&PIFirstName=&PIId=&PILastName=&PIOrganization=&PIState=&PIZip=&ProgEleCode=223Y%2C+X289&ProgOfficer=&ProgOrganization=&ProgRefCode=&Program=&StartDateOperator=&utm_medium=email&utm_source=govdelivery'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              support from the NSF TIP Directorate.
            </a>
          </Text>
        </Box>
        <Box mt='1.7rem'>
          <Text
            fontSize={{base: '17px', lg: '24px'}}
            color='#FFFFFF'
            fontWeight={'bold'}
          >
            Objective
          </Text>
          <Text
            mt='.45rem'
            lineHeight='24px'
            color='#FFFFFF'
            fontSize={{base: '12px', lg: '16px'}}
          >
            Our goal is to develop a knowledge graph based on people,
            organizations, and research topics. We are adopting an intentional
            design approach which initially prioritizes HBCUs and emerging
            researchers in a deliberate eff ort to counterbalance the{' '}
            <a
              href='https://en.wikipedia.org/wiki/Matthew_effect'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              Matthew effect
            </a>
            , a naturally accumulated advantage of well - resourced research
            organizations.
          </Text>
          <Text
            mt='.45rem'
            lineHeight='24px'
            color='#FFFFFF'
            fontSize={{base: '12px', lg: '16px'}}
          >
            By bringing greater visibility to what and who is often rendered
            invisible in the current science system, CollabNext will facilitate
            research collaborations with HBCUs and illuminate the broader
            research landscape. We utilize open science data sources, follow
            human - centered design principles, and leverage state - of - the -
            art algorithms to build a platform that will help identify existing
            and potentially new research partnerships.
          </Text>
        </Box>
        <Box mt='1.7rem'>
          <Text
            fontSize={{base: '17px', lg: '24px'}}
            color='#FFFFFF'
            fontWeight={'bold'}
          >
            Current State
          </Text>
          <Text
            mt='.45rem'
            lineHeight='24px'
            color='#FFFFFF'
            fontSize={{base: '12px', lg: '16px'}}
          >
            The{' '}
            <a
              href='https://gt-msi-diversifind.azuremicroservices.io/'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              current CollabNext tool
            </a>{' '}
            is a very rough proof-of-concept. We are developing future versions,
            moving from alpha to beta to production over the next three years
            thanks to funding from the NSF. We are part of the{' '}
            <a
              href='https://www.proto-okn.net/'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              Prototype Open Knowledge Network
            </a>{' '}
            (aka ProtoOKN).
          </Text>
        </Box>
        <Box mt='1.7rem'>
          <Text
            fontSize={{base: '17px', lg: '24px'}}
            color='#FFFFFF'
            fontWeight={'bold'}
          >
            Data and Methodology
          </Text>
          <Text
            mt='.45rem'
            lineHeight='24px'
            color='#FFFFFF'
            fontSize={{base: '12px', lg: '16px'}}
          >
            We are currently using data from{' '}
            <a
              href='https://explore.openalex.org/'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              OpenAlex
            </a>{' '}
            (formerly Microsoft Academic Graph), the{' '}
            <a
              href='https://mupcenter.org/'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              Center for Measuring University Performance
            </a>{' '}
            , and we will be adding other open data sources. We will also be
            building in strong and consistent topic classification and entity
            resolution modules. The entire project will be built on a graph
            database with an eye toward interoperability with other ProtoOKN
            projects.
          </Text>
        </Box>
      </Box>
    </Box>
  );
};

export default About;
