import styles from "../styles/Feedback.module.css";

const Feedback = () => {
  const feedbackURL = "https://forms.gle/SCbUGNo72ewYhZFy6";

  const feedbackHandler = () => {
    window.open(feedbackURL);
  };

  return (
    <div className={styles.container}>
      <section className={styles.heroSection}>
        <h1>Feedback</h1>
        <p>
          We value your feedback. Please help us improve this tool by completing
          the survey below.
        </p>
        <button onClick={feedbackHandler} className={styles.feedbackButton}>
          Provide Feedback
        </button>
      </section>
    </div>
  );
};

export default Feedback;
