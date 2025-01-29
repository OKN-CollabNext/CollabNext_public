import React from 'react';

import {Box, Text} from '@chakra-ui/react';

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
            The{' '}
            <a
              href='https://collabnext.io/'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              CollabNext tool
            </a>{' '}
            originated as a partnership between{' '}
            <a
              href='https://gatech.edu/'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              Georgia Tech
            </a>
            {', '}and the{' '}
            <a
              href='https://aucenter.edu/'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              Atlanta University Center
            </a>
            , and is now being developed jointly by{' '}
            <a
              href='https://www.fisk.edu/'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              Fisk University
            </a>
            {', '}
            <a
              href='https://gatech.edu/'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              Georgia Tech
            </a>
            {', '}
            <a
              href='https://morehouse.edu/'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              Morehouse College
            </a>
            {', '}
            <a
              href='https://www.tsu.edu/'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              Texas Southern University
            </a>
            {', '}and{' '}
            <a
              href='https://buffalo.edu/'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              University at Buffalo
            </a>{' '}
            with support from the{' '}
            <a
              href='https://www.proto-okn.net'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              Prototype Open Knowledge Network
            </a>{' '}
            (aka ProtoOKN) sponsored by the{' '}
            <a
              href='https://new.nsf.gov/tip'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              NSF TIP Directorate
            </a>
            .
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
            Our goal is to{' '}
            <b>
              develop a knowledge graph based on people, organizations, and
              research topics
            </b>
            . We are adopting an intentional design approach,{' '}
            <b>initially prioritizing HBCUs and emerging researchers</b> in a
            deliberate effort to counterbalance the{' '}
            <a
              href='https://en.wikipedia.org/wiki/Matthew_effect'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              Matthew effect
            </a>
            , a naturally accumulated advantage of well-resourced research
            organizations.
          </Text>
          <br />
          <Text
            mt='.45rem'
            lineHeight='24px'
            color='#FFFFFF'
            fontSize={{base: '12px', lg: '16px'}}
          >
            By bringing greater visibility to those who are often rendered
            invisible in the current science system, CollabNext will facilitate
            research collaborations with HBCUs and illuminate the broader
            research landscape. 
          </Text>
          <br />
          <Text
            mt='.45rem'
            lineHeight='24px'
            color='#FFFFFF'
            fontSize={{base: '12px', lg: '16px'}}
          >
            We utilize open science{' '}
            <a
              href='https://collabnext.io/data'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              data sources
            </a>
            , follow human-centered design principles, and leverage
            state-of-the-art algorithms to build a platform that will help
            identify existing and potentially new research partnerships.
          </Text>
        </Box>
        <Box mt='1.7rem'>
          <Text
            fontSize={{base: '17px', lg: '24px'}}
            color='#FFFFFF'
            fontWeight={'bold'}
          >
            Current State and Future Plans
          </Text>
          <Text
            mt='.45rem'
            lineHeight='24px'
            color='#FFFFFF'
            fontSize={{base: '12px', lg: '16px'}}
          >
            <b>The current CollabNext toolis an alpha version</b>. Our{' '}
            <a
              href='https://collabnext.io/technology'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              Technology
            </a>{' '}
            and{' '}
            <a
              href='https://collabnext.io/data'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              data sources
            </a>{' '}
            are described on other pages. We are developing future versions,
            moving from beta to production over the next two years. Our{' '}
            <a
              href='https://bit.ly/collabnext-demo'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              proof-of-concept deliverable{' '}
            </a>
            which preceded the alpha version, is available for comparison.
          </Text>
          <br />
          <Text
            mt='.45rem'
            lineHeight='24px'
            color='#FFFFFF'
            fontSize={{base: '12px', lg: '16px'}}
          >
            The design and strategic direction of the project are guided by a
            collection of 
            <a
              href='https://collabnext.io/team'
              target='_blank'
              rel='noreferrer'
              style={{ color: 'cornsilk', textDecoration: 'underline' }}
            >
              User Stories
            </a>
          that address <b>who this tool is for and
            how they may use it</b>. We are further guided by our{' '}
            <a
              href='https://docs.google.com/document/d/1hzO67WsKVI25g8zicMjxqOSTPuJxeWcr/edit?usp=sharing&ouid=103856344114330658213&rtpof=true&sd=true'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              Advisory Group
            </a>
            . This group consists of selected members of the{' '}
            <a
              href='https://collabnext.io/team'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              Leadership Team
            </a>{' '}
            as well as other individuals who have a unique and valuable
            perspective on our project (e.g. HBCU faculty, underrepresented
            groups in STEM, etc.). The group serves as a standing focus group
            and supports our larger evaluation plan.
          </Text>
          <br />
          <Text
            mt='.45rem'
            lineHeight='24px'
            color='#FFFFFF'
            fontSize={{base: '12px', lg: '16px'}}
          >
            We are also fortunate to have key strategic{' '}
            <a
              href='https://collabnext.io/team'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              {' '}
              Partnerships
            </a>{' '}
            with academic, non-profit, and corporate organizations that serve as
            data providers, and resources with expertise. Partners meet with the
            Leadership Team quarterly to identify collaboration opportunities
            within their networks, share resources (e.g., data, code, and
            expertise) and actively support the goals of the OKN project.
          </Text>
          <br />
          <Text
            mt='.45rem'
            lineHeight='24px'
            color='#FFFFFF'
            fontSize={{base: '12px', lg: '16px'}}
          >
            We are <b>actively seeking one or more Sustainability Partners</b>.
            Sustainability partners are federal agencies, foundations,
            businesses, and other organizations who are supportive of our work
            and interested in exploring options for sustaining and improving the
            backend knowledge graph and frontend web application, after it is
            built and operational at the end of the performance period of the
            NSF grant. If you are interested in discussing this or if you know
            of others who may be interested, please
            <a
              href='https://collabnext.io/contact'
              target='_blank'
              rel='noreferrer'
              style={{color: 'cornsilk', textDecoration: 'underline'}}
            >
              {' '}
              contact us
            </a>
            .
          </Text>
        </Box>
      </Box>
    </Box>
  );
};

export default About;
