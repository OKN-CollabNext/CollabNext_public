import React from "react";
import "../styles/PersonCard.css";
import { FaLinkedin, FaGithub, FaGlobe, FaEnvelope } from "react-icons/fa";

interface Person {
  image?: string;
  firstName?: string;
  lastName?: string;
  email?: string;
  institutionalAffiliation?: string;
  role?: string;
  biosketch?: string;
  linkedin?: string;
  github?: string;
  website?: string;
}

interface PersonCardProps {
  person: Person;
  isExpanded: boolean;
  onToggleExpand: () => void;
}

const PersonCard: React.FC<PersonCardProps> = ({
  person,
  isExpanded,
  onToggleExpand,
}) => {
  if (!person || typeof person !== "object") {
    console.error("Invalid person data:", person);
    return null;
  }

  const bioMaxLength = 100;
  const truncatedBio = person.biosketch?.slice(0, bioMaxLength) || "";
  const shouldShowReadMore =
    person.biosketch && person.biosketch.length > bioMaxLength;

  return (
    <div className="personCard">
      <div className="personImageWrapper">
        <img
          src={person.image}
          alt={`${person.firstName} ${person.lastName}`}
          className="personImage"
        />
      </div>
      <div className="personBody">
        <h2 className="personName">
          {person.firstName} {person.lastName}
        </h2>
        <div className="personAffiliation">
          {person.institutionalAffiliation}
          {person.role ? ` - ${person.role}` : ""}
        </div>
        <div className={`personBio ${!isExpanded ? "collapsed" : ""}`}>
          {isExpanded ? person.biosketch : truncatedBio}
        </div>
        {
          shouldShowReadMore && (
            <button
              onClick={onToggleExpand}
              className="personReadMoreBtn"
            >
              {isExpanded ? "Read Less" : "Read More"}
            </button>
          )
        }
        <div className="personCardLinks">
          {person.linkedin && (
            <SocialLink href={person.linkedin}>
              <FaLinkedin />
            </SocialLink>
          )}
          {person.github && (
            <SocialLink href={person.github}>
              <FaGithub />
            </SocialLink>
          )}
          {person.website && (
            <SocialLink href={person.website}>
              <FaGlobe />
            </SocialLink>
          )}
          {person.email && (
            <SocialLink href={`mailto:${person.email}`}>
              <FaEnvelope />
            </SocialLink>
          )}
        </div>
      </div>
    </div >
  );
};

interface SocialLinkProps {
  href: string;
  children: React.ReactNode;
}

const SocialLink: React.FC<SocialLinkProps> = ({ href, children }) => (
  <a
    href={href}
    target="_blank"
    rel="noopener noreferrer"
    className="personCardSocialLink"
  >
    {children}
  </a>
);

export default PersonCard;
