import React, { Suspense, useState } from 'react';
import team_members from '../assets/team_members.json';
import '../styles/Acknowledgment.css';

const PersonCard = React.lazy(() => import('../components/PersonCard'));

const AcknowledgementsPage: React.FC = () => {
  const [expandedCardIndex, setExpandedCardIndex] = useState<number | null>(null);

  const leadershipData = team_members.leadership;
  const advisoryData = team_members.advisory;
  const studentsData = team_members.students;
  const partnerData = team_members.partnershipData;

  const sortByLastName = (
    data: {
      firstName: string;
      lastName: string;
      email: string;
      institutionalAffiliation: string;
      role: string;
      biosketch: string;
      linkedin: string;
      github: string;
      website: string;
      image: string;
    }[]
  ) => {
    const sortedData = data.toSorted((a, b) => {
      if (a.lastName < b.lastName) return -1;
      if (a.lastName > b.lastName) return 1;
      return 0;
    });
    return sortedData;
  };

  const handleToggleExpand = (index: number) => {
    setExpandedCardIndex(expandedCardIndex === index ? null : index);
  };

  return (
    <div className="ackPageWrapper">
      <div className="v1Container">
        <section className="heroSection">
          <h1 className="heroTitle">Our Team</h1>
          <p className="heroSubtitle">
            Meet the leadership team, advisory group, students, and partners contributing to CollabNext.
          </p>
        </section>
      </div>

      <div className="v2Container">
        {[
          {
            name: 'Leadership Team',
            desc:
              'The Leadership Team consists of researchers supporting this project, including the PI, Co-PIs, and Senior Personnel.',
            data: leadershipData,
          },
          {
            name: 'Advisory Group',
            desc:
              'The Advisory Group brings unique perspectives to the project, including HBCU faculty and underrepresented voices in STEM.',
            data: sortByLastName(advisoryData),
          },
          {
            name: 'Students',
            desc:
              'Our diverse group of contributors includes software developers, data analysts, and project managers from various backgrounds.',
            data: sortByLastName(studentsData),
          },
        ].map(({ name, desc, data }) => (
          <div className="v2SectionBlock" key={name}>
            <h2 className="ackSectionTitle">{name}</h2>
            <p className="ackSectionDesc">{desc}</p>
            <div className="ackMasonryGrid">
              {data.map((person, index) => (
                <Suspense
                  key={index}
                  fallback={
                    <div className="personCardFallback">
                      <div className="fallbackImage" />
                      <div className="fallbackLine" />
                      <div className="fallbackLine" />
                      <div className="fallbackLine large" />
                      <div className="fallbackIcons">
                        {[...Array(4)].map((_, i) => (
                          <div key={i} className="fallbackIcon" />
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
          </div>
        ))}
      </div>

      <div className="v1Container">
        <section className="ourPartnersSection">
          <div className="mainpageOurPartners">
            <h2 className="mainpageOurPartnersHeader">Our Partners</h2>
            <div className="mainpageOurPartnersBox">
              {partnerData.map((partner, index) => (
                <div key={index} className="partnerLogoContainer">
                  <img
                    src={partner.ppp}
                    alt={`${partner.name} logo`}
                    className="partnerLogo"
                    style={{
                      width: partner.width || 'auto',
                      height: partner.height || 'auto',
                    }}
                  />
                  <div className="partnerName">{partner.name}</div>
                  <a
                    href={partner.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="partnerLink"
                  >
                    <img
                      src="/assets/ppp/icons8-earth-24.png"
                      alt="Visit website"
                      className="partnerEarthIcon"
                    />
                    <span>Visit Site</span>
                  </a>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default AcknowledgementsPage;
