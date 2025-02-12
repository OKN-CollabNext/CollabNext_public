import styles from "../styles/Help.module.css";

const Help = () => {
  return (
    <div className={styles.container}>
      <section className={styles.heroSection}>
        <h1>Help</h1>
        <p>
          This is an alpha version of the CollabNext web application. Since
          this is only an alpha prototype, direct help or support is limited.
          However, if you need assistance, please share your question or
          comment on our{" "}
          <a
            href="https://collabnext.io/feedback"
            target="_blank"
            rel="noreferrer"
            className={styles.link}
          >
            Feedback page
          </a>
          .
        </p>
      </section>

      <section className={styles.mainContent}>
        <div className={styles.block}>
          <h2>Tips for Using This Alpha Version</h2>
          <ul>
            <li>
              You can toggle the results of a search between a tabular view
              (List Map) or a graphical view (Network Map).
            </li>
            <li>
              The Explore Topics button on the home page is an experimental,
              graphical approach to exploring the{" "}
              <a
                href="https://docs.google.com/document/d/1bDopkhuGieQ4F8gGNj7sEc8WSE8mvLZS/edit"
                target="_blank"
                rel="noreferrer"
                className={styles.link}
              >
                OpenAlex Topic Classification
              </a>
              . Follow the link for more details on this process.
            </li>
            <li>
              Best results are achieved by searching for Institution and/or
              Topic first, and then using the listed name of a person to add
              a people filter. We have implemented an auto-complete feature
              for Institutions and Topics, but it is harder to do that with
              researcher names.
            </li>
          </ul>
        </div>

        <div className={styles.block}>
          <h2>Known Issues</h2>
          <p>
            Our{" "}
            <a
              href="https://github.com/OKN-CollabNext/CollabNext_public"
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              GitHub project
            </a>{" "}
            has several known issues:
          </p>
          <ul>
            <li>
              Occasionally, a search comes back with no results when there
              clearly should be some. This can happen on the first searches
              or on large queries. Try hitting "Search" again.
            </li>
            <li>
              Counts may vary across screens if subfields are aggregated
              differently than the IDs used in OpenAlex’s pre-computed
              metrics.
            </li>
          </ul>
        </div>
      </section>
    </div>
  );
};

export default Help;
