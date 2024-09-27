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
    <div className="bg-white rounded-lg shadow-md overflow-hidden transition-all duration-300 hover:shadow-lg">
      <div className="relative w-full h-80">
        {" "}
        {/* Adjust height as needed */}
        <img
          src={person.image}
          alt={`${person.firstName} ${person.lastName}`}
          className="absolute inset-0 w-full h-full object-cover"
        />
      </div>
      <div className="p-4">
        <h2 className="text-xl font-semibold text-gray-800 mb-1">
          {person.firstName} {person.lastName}
        </h2>
        <p className="text-sm text-gray-600 mb-2">
          {person.institutionalAffiliation} - {person.role}
        </p>
        <div
          className={`text-sm text-gray-700 mb-4 ${
            isExpanded ? "max-h-56" : "max-h-24"
          } overflow-y-auto`}
        >
          {isExpanded ? person.biosketch : truncatedBio}
          {shouldShowReadMore && (
            <button
              onClick={onToggleExpand}
              className="text-blue-600 hover:text-blue-800 font-medium ml-1"
            >
              {isExpanded ? "Read Less" : "Read More"}
            </button>
          )}
        </div>
        <div className="flex space-x-3">
          {person.linkedin && (
            <SocialLink href={person.linkedin} icon={<FaLinkedin />} />
          )}
          {person.github && (
            <SocialLink href={person.github} icon={<FaGithub />} />
          )}
          {person.website && (
            <SocialLink href={person.website} icon={<FaGlobe />} />
          )}
          {person.email && (
            <SocialLink href={`mailto:${person.email}`} icon={<FaEnvelope />} />
          )}
        </div>
      </div>
    </div>
  );
};

interface SocialLinkProps {
  href: string;
  icon: React.ReactNode;
}

const SocialLink: React.FC<SocialLinkProps> = ({ href, icon }) => (
  <a
    href={href}
    target="_blank"
    rel="noopener noreferrer"
    className="text-gray-400 hover:text-gray-600 transition-colors duration-300"
  >
    {icon}
  </a>
);

export default PersonCard;
