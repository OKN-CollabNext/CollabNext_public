import React, { Suspense, useState } from "react";
import { Box } from "@chakra-ui/react";
import "../styles/Acknowledgment.css";
import team_members from "../assets/team_members.json";

const PersonCard = React.lazy(() => import("../components/PersonCard"));

const AcknowledgementsPage: React.FC = () => {

  const [expandedCardIndex, setExpandedCardIndex] = useState<number | null>(null);
  const leadershipData = team_members.leadership;
  const advisoryData = team_members.advisory;
  const studentsData = team_members.students;
  const partnerData = team_members.partnershipData;

  const sortByLastName = <T extends { lastName: string }>(data: T[]) =>
    data.toSorted((a, b) =>
      a.lastName < b.lastName ? -1 : a.lastName > b.lastName ? 1 : 0
    );

  const handleToggleExpand = (index: number) => {
    setExpandedCardIndex(expandedCardIndex === index ? null : index);
  };

  const sections = [
    {
      name: "Leadership Team",
      desc: "The Leadership Team consists of all researchers supported by this project including the PI, Co-PIs, and Senior Personnel.",
      data: leadershipData,
    },
    {
      name: "Advisory Group",
      desc: "The Advisory Group consists of selected members of the Leadership Team as well other individuals who have a unique and valuable perspective on our project (eg HBCU faculty, underrepresented groups in STEM, etc.). The group serves as a standing focus group and supports our larger evaluation plan.",
      data: sortByLastName(advisoryData),
    },
    {
      name: "Students",
      desc: "We are fortunate to have a strong and diverse group of people working on this project and contributing to software development, data analytics, project management, and more.",
      data: sortByLastName(studentsData),
    },
  ];

  return (
    <div className="ackPageWrapper">
      <div className="ackMainContainer">
        <h1 className="ackMainTitle">Our Team</h1>
        {sections.map(({ name, desc, data }, i) => (
          <Box mb={i !== sections.length - 1 ? "1.8rem" : undefined} key={name}>
            <h2 className="ackSectionTitle">{name}</h2>
            <p className="ackSectionDesc">{desc}</p>
            <div className="ackMasonryGrid">
              {data.map((person, idx) => (
                <Suspense
                  key={idx}
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
                    isExpanded={expandedCardIndex === idx}
                    onToggleExpand={() => handleToggleExpand(idx)}
                  />
                </Suspense>
              ))}
            </div>
          </Box>
        ))}
        {/* Partner Section */}
        <h2 className="ackPartnerTitle">Partnership Team</h2>
        <p className="ackPartnerDesc">
          Our external partners meet with the Leadership Team quarterly to identify collaboration opportunities within their networks, share resources (e.g., data, code, and expertise) and actively support the goals of the OKN project. They also provide advise regarding data sources and project sustainability.
        </p>
        <div className="ackPartnerMasonry">
          {partnerData.map((partner, idx) => (
            <div className="ackPartnerCard" key={idx}>
              <div className="ackPartnerInner">
                <img
                  src={partner.ppp}
                  alt={`${partner.name} logo`}
                  width={partner.width || undefined}
                  height={partner.height || undefined}
                  loading="lazy"
                />
                <div className="ackPartnerName">{partner.name}</div>
                <a
                  href={partner.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="ackPartnerLink"
                >
                  <img
                    src="/assets/ppp/icons8-earth-24.png"
                    alt="Visit website"
                    className="ackPartnerEarthIcon"
                  />
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AcknowledgementsPage;
