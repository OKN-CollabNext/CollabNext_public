import React from 'react';

import {Box, Text} from '@chakra-ui/react';

const Technology = () => {
  return (
    <Box w={{lg: '900px'}} mx='auto' mt='1.5rem'>
      <Text
        pl={{base: '.8rem', lg: 0}}
        fontFamily='DM Sans'
        fontSize={{lg: '22px'}}
        color='#000000'
      >
        Technology
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
            mt='.45rem'
            lineHeight='24px'
            color='#FFFFFF'
            fontSize={{base: '12px', lg: '16px'}}
          >
            {' '}
            Like other Theme 1 projects which are part of the{' '}
            <a
              href='https://www.proto-okn.net/'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              Prototype Open Knowledge Network
            </a>
            {', '}
            our goal is to fully leverage the knowledge network platform
            provided by the{' '}
            <a
              href='https://frink.renci.org/'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              FRINK Team
            </a>
            {'. '}
            FRINK will be hosting knowledge graphs for all the Proto-OKN
            projects, which will help with data integration and linkage across
            knowledge graphs.
          </Text>
          <br />
          <Text
            mt='.45rem'
            lineHeight='24px'
            color='#FFFFFF'
            fontSize={{base: '12px', lg: '16px'}}
          >
            Currently, our data requires both RDF and RDF-star triples. FRINK is
            not yet able to support the RDF-star specification, so the alpha
            version of our web application us using the publicly available
            SPARQL endpoint provided by SemOpenAlex. We also leverage some
            Postgres SQL data for certain APIs, and we plan to have this RDBMS
            hosted by FRINK in the future. Since our future plans involve
            integrating OpenAlex data with other data sources (eg MUP), we
            anticipate having both graph databases and relational databases (and
            potentially NoSQL databases, too) for flexibility, schema
            integration, and to be able to optimize performance.
          </Text>
          <br />
          <Text
            mt='.45rem'
            lineHeight='24px'
            color='#FFFFFF'
            fontSize={{base: '12px', lg: '16px'}}
          >
            The web application for CollabNext is currently designedwith a
            Flask/Python backend and a React/Typescript/Javascript frontend.
            These are both hosted on Microsoft Azure, and funded with an
            allocation to the{', '}
            <a
              href='https://www.cloudbank.org/'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              NSF’s Cloudbank service
            </a>
            {'. '}
            We have developed APIs which connect to our data sources and provide
            a standardized approach for our web application frontend to display
            filtered datasets. <br />
            <br />
            Our alpha deliverable is{' '}
            <a
              href='https://github.com/OKN-CollabNext/CollabNext_public
'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              hosted on Github
            </a>
            {', '}
            and we also use Dropbox for shared storage, Trello for task
            management, and Slack for our team communication.
          </Text>
          <br />
          <Text
            mt='.45rem'
            lineHeight='24px'
            color='#FFFFFF'
            fontSize={{base: '12px', lg: '16px'}}
          >
            Two of our challenges are Topic Classification and Name
            disambiguation. We are currently using OpenAlex subfields as topic
            classifiers, but it is becoming increasingly clear that we will need
            to build a robust Machine Learning model to help bridge human
            understandable research topics and semantic web ontologies and data
            schemas which may categorize research topics in a more
            machine-friendly way.
          </Text>
          <br />
          <Text
            mt='.45rem'
            lineHeight='24px'
            color='#FFFFFF'
            fontSize={{base: '12px', lg: '16px'}}
          >
            Name disambiguation will always be a challenge for us since we want
            to maintain a person-focused approach. In addition to the built-in
            algorithms used by OpenAlex, we are developing internal models which
            use more current AI and ML research, and which we believe will yield
            animprovement for all our entity resolution challenges.
          </Text>
        </Box>
      </Box>
    </Box>
  );
};

export default Technology;
