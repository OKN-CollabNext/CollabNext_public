import React from 'react';

const Suggested = ({
  suggested,
  institutions,
}: {
  suggested: never[];
  institutions: boolean;
}) => {
  return (
    <datalist id={institutions ? 'institutions' : 'topics'}>
      {suggested?.map((institution: string) => (
        <option key={institution} value={institution}>
          {institution}
        </option>
      ))}
    </datalist>
  );
};

export default Suggested;
