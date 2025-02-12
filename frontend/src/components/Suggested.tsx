const Suggested = ({
  suggested,
  institutions,
}: {
  suggested: string[];
  institutions: boolean;
}) => {
  return (
    <>
      <datalist id={institutions ? "institutions" : "topics"}>
        {suggested?.map((item: string) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </datalist>
    </>
  );
};

export default Suggested;
