// components/Suggested.tsx
import React from "react";

interface SuggestedProps {
  suggested: string[];       // list of suggestions (e.g. names, institutions, etc.)
  institutions: boolean;     // flag indicating which suggestions to use
  id: string;                // id for the datalist element
}

const Suggested: React.FC<SuggestedProps> = ({ suggested, institutions, id }) => {
  const options = institutions ? /* array for institutions */ suggested : suggested;
  return (
    <datalist id={id}>
      {options.map((opt, index) => (
        <option value={opt} key={index} />
      ))}
    </datalist>
  );
};

export default Suggested;  // ✅ default export of the component
