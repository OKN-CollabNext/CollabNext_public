import React, { Suspense, useState } from 'react';

import { Box, Text } from '@chakra-ui/react';

import team_members from '../assets/team_members.json';

const PersonCard = React.lazy(() => import('../components/PersonCard'));

const leadershipData = team_members.leadership;
const advisoryData = team_members.advisory;
const studentsData = team_members.students;
const partner_Data = team_members.partnershipData;

const AcknowledgementsPage: React.FC = () => {
  const [expandedCardIndex, setExpandedCardIndex] = useState<number | null>(
    null,
  );

  const handleToggleExpand = (index: number) => {
    setExpandedCardIndex(expandedCardIndex === index ? null : index);
  };

  // if (!Array.isArray(advisoryData) || advisoryData.length === 0) {
  //   console.error('advisoryData is not an array or is empty:', advisoryData);
  //   return <div>Error loading data</div>;
  // }

  return (
    <div className='bg-gray-100 min-h-screen py-12 px-4 sm:px-6 lg:px-8'>
      <div className='max-w-7xl mx-auto'>
        <h1 className='text-3xl font-bold text-gray-900 text-center mb-12'>
          Acknowledgements
        </h1>
        {[
          {
            name: 'Leadership Team',
            desc: 'The Leadership Team consists of all researchers supported by this project including the PI, Co-PIs, and Senior Personnel.',
            data: leadershipData,
          },
          {
            name: 'Advisory group',
            desc: 'The Advisory Group consists of selected members of the Leadership Team as well other individuals who have a unique and valuable perspective on our project (eg HBCU faculty, underrepresented groups in STEM, etc.). The group serves as a standing focus group and supports our larger evaluation plan.',
            data: advisoryData,
          },
          {
            name: 'Students',
            desc: 'We are fortunate to have a strong and diverse group of people working on this project and contributing to software development, data analytics, project management, and more.',
            data: studentsData,
          },

        ].map(({name, desc, data}, i) => (
          <Box mb={i !== 2 ? '1.8rem' : undefined}>
            <Text fontSize='20px' color='#000000' fontWeight={'bold'}>
              {name}
            </Text>
            <Text fontSize={'15px'} mb='.8rem'>
              {desc}
            </Text>
            <div className='grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8'>
              {data.map((person, index) => (
                <Suspense
                  key={index}
                  fallback={
                    <div className='bg-white rounded-lg shadow-md p-4 h-96 animate-pulse'>
                      <div className='bg-gray-300 h-48 rounded-md mb-4'></div>
                      <div className='bg-gray-300 h-4 rounded w-3/4 mb-2'></div>
                      <div className='bg-gray-300 h-4 rounded w-1/2 mb-4'></div>
                      <div className='bg-gray-300 h-20 rounded mb-4'></div>
                      <div className='flex space-x-2'>
                        {[...Array(4)].map((_, i) => (
                          <div
                            key={i}
                            className='bg-gray-300 h-6 w-6 rounded-full'
                          ></div>
                        ))}
                      </div>
                    </div>
                  }
                >
                  <PersonCard
                    person={person}
                    isExpanded={expandedCardIndex === index}
                    onToggleExpand={() => handleToggleExpand(index)}
                  />
                </Suspense>
              ))}
            </div>
          </Box>
        ))}
        {/* patnar sction */}
        <div>
          <h1 style={{ fontWeight: 'bold', fontSize: '20px', marginTop: 30 }}>Partnership Team</h1>
          <h1 style={{ fontSize: '15px', marginBottom: 12 }}>
            Our external partners meet with the Leadership Team quarterly to identify collaboration opportunities within their networks, share resources (e.g., data, code, and expertise) and actively support the goals of the OKN project. They also provide advice regarding data sources and project sustainability.
          </h1>
          <div 
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              gap: '20px'
            }}
          >
            {partner_Data.map((partner, index) => (
              <div 
                key={index} 
                style={{
                  display: 'flex', 
                  flexDirection: 'column', 
                  alignItems: 'center', 
                  backgroundColor: 'white',
                  boxShadow: '0px 0px 12px #80808061', 
                  borderRadius: '10px', 
                  width: '295px', 
                  padding: '20px',
                  textAlign: 'center'
                }}
              >
                <img src={partner.ppp} alt={`${partner.name} photo`} 
                    style={{ width: partner.width, height: partner.height, padding: partner.padding,borderRadius: '0', objectFit: 'cover', marginBottom: '10px'}} />
                <div 
                    style={{display: "grid", justifyContent: "space-around", alignItems: 'end',justifyItems:'center', width: '100%' ,    height: '100%'}}>
                <div 
                    style={{fontWeight: 600, fontSize: '1.25rem', lineHeight: '1.75rem', marginBottom: '10px', color: 'rgba(31, 41, 55, 1)',display: 'flex',alignItems: 'flex-end'}}>{partner.name}</div>
                <div 
                    style={{ display: 'flex', justifyContent: '', gap: '10px' , alignItems: 'flex-end'}}>
                  <a href={partner.website} target="_blank" rel="noopener noreferrer">
                    <img src="/assets/ppp/erth.svg" alt="wabsite" style={{ width: '17px', height: '17px' }}/>
                  </a>
                </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AcknowledgementsPage;
//Finished acknowledgement page
