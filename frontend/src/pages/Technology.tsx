import styles from "../styles/Technology.module.css";

const Technology = () => {
  return (
    <div className={styles.container}>
      <section className={styles.heroSection}>
        <h1>Technology</h1>
        <p>
          Learn more about the technical stack, data infrastructure, and
          future plans of CollabNext.
        </p>
      </section>
      <section className={styles.mainContent}>
        <div className={styles.block}>
          <p>
            Like other Theme 1 projects which are part of the{" "}
            <a
              href="https://www.proto-okn.net/"
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              Prototype Open Knowledge Network
            </a>
            , our goal is to fully leverage the knowledge network platform
            provided by the{" "}
            <a
              href="https://frink.renci.org/"
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              FRINK Team
            </a>
            .
          </p>
          <p>
            Currently, our data requires both RDF and RDF-star triples. FRINK
            is not yet able to support the RDF-star specification, so the
            alpha version of our web application is using the publicly
            available SPARQL endpoint provided by SemOpenAlex. We also
            leverage some Postgres SQL data for certain APIs, and plan to
            have this hosted by FRINK in the future. Since our future plans
            involve integrating OpenAlex data with other data sources
            (e.g., MUP), we anticipate having multiple database types for
            flexibility and performance.
          </p>
          <p>
            The web application for CollabNext is currently designed with a
            Flask/Python backend and a React/Typescript/Javascript frontend,
            both hosted on Microsoft Azure through an allocation from the{" "}
            <a
              href="https://www.cloudbank.org/"
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              NSF’s Cloudbank service
            </a>
            . We have developed APIs that connect to our data sources and
            provide a standardized interface for the web frontend.
          </p>
          <p>
            Our alpha deliverable is{" "}
            <a
              href="https://github.com/OKN-CollabNext/CollabNext_public"
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              hosted on GitHub
            </a>
            , and we also use Dropbox for shared storage, Trello for task
            management, and Slack for team communication.
          </p>
        </div>

        <div className={styles.block}>
          <h2>Name Disambiguation & Topic Classification</h2>
          <p>
            Two key challenges are Topic Classification and Name
            disambiguation. We currently use OpenAlex subfields as topic
            classifiers, but we plan to develop a robust ML model to connect
            human-understandable research topics with semantic web ontologies.
          </p>
          <p>
            Name disambiguation remains difficult because we want a
            person-focused approach. In addition to the built-in OpenAlex
            algorithms, we are developing internal models that leverage
            modern AI and ML techniques for entity resolution.
          </p>
        </div>
      </section>
    </div>
  );
};

export default Technology;
