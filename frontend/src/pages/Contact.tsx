import styles from "../styles/Contact.module.css";

const ContactUs = () => {
  return (
    <div className={styles.container}>
      <section className={styles.heroSection}>
        <h1>Contact Us</h1>
        <p className={styles.heroSubtitle}>
          Please don’t hesitate to reach out if you have questions or comments
          on CollabNext. We are still growing our Advisory Group and seeking
          Sustainability Partners!
        </p>
      </section>
      <section className={styles.contactContent}>
        <p>
          Email us at:{" "}
          <a
            href="mailto:collabnext.okn@gmail.com"
            className={styles.link}
          >
            collabnext.okn@gmail.com
          </a>
        </p>
      </section>
    </div>
  );
};

export default ContactUs;