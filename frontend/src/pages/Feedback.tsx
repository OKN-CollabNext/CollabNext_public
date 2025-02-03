import '../styles/Feedback.css';

const Feedback = () => {
    const feedbackURL =
    "https://forms.gle/SCbUGNo72ewYhZFy6";

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
