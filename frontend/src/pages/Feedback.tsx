import '../styles/Feedback.css';

const Feedback = () => {
    const feedbackURL =
    "https://gatech.co1.qualtrics.com/jfe/form/SV_eQg5UdlkzoAWH66";

    const feedbackHandler = () => {
    window.open(feedbackURL);
    };
    return (
    <div className='heading'>
      <h1> Feedback </h1>
      <div className='container'>
        <p>We value your feedback. Please help us improve this tool by completing the survey below.</p>
        <button onClick={feedbackHandler}>Provide Feedback</button>
      </div>
    </div>
  );
};

export default Feedback;
