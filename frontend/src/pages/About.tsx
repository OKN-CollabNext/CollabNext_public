import React from "react";
import styles from "../styles/About.module.css";

const About = () => {
  return (
    <div className={styles.container}>
      <section className={styles.heroSection}>
        <h1>About Us</h1>
        <p className={styles.heroSubtitle}>
          Learn more about the CollabNext project, its background, and future plans.
        </p>
      </section>
      <section className={styles.mainContent}>
        <div className={styles.sectionBlock}>
          <h2 className={styles.sectionTitle}>Background</h2>
          <p className={styles.sectionText}>
            The{" "}
            <a
              href="https://collabnext.io/"
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              CollabNext tool
            </a>{" "}
            originated as a partnership between{" "}
            <a
              href="https://gatech.edu/"
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              Georgia Tech
            </a>
            {", "}and the{" "}
            <a
              href="https://aucenter.edu/"
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              Atlanta University Center
            </a>
            , and is now being developed jointly by{" "}
            <a
              href="https://www.fisk.edu/"
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              Fisk University
            </a>
            {", "}
            <a
              href="https://gatech.edu/"
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              Georgia Tech
            </a>
            {", "}
            <a
              href="https://morehouse.edu/"
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              Morehouse College
            </a>
            {", "}
            <a
              href="https://www.tsu.edu/"
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              Texas Southern University
            </a>
            {", "}and{" "}
            <a
              href="https://buffalo.edu/"
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              University at Buffalo
            </a>{" "}
            with support from the{" "}
            <a
              href="https://www.proto-okn.net"
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              Prototype Open Knowledge Network
            </a>{" "}
            (aka ProtoOKN) sponsored by the{" "}
            <a
              href="https://new.nsf.gov/tip"
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              NSF TIP Directorate
            </a>
            .
          </p>
        </div>

        <div className={styles.sectionBlock}>
          <h2 className={styles.sectionTitle}>Objective</h2>
          <p className={styles.sectionText}>
            Our goal is to <b>develop a knowledge graph based on people, organizations, and
              research topics</b>. We are adopting an intentional design approach,{" "}
            <b>initially prioritizing HBCUs and emerging researchers</b> in a
            deliberate effort to counterbalance the{" "}
            <a
              href="https://en.wikipedia.org/wiki/Matthew_effect"
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              Matthew effect
            </a>
            , a naturally accumulated advantage of well-resourced research
            organizations.
            <br />
            <br />
            By bringing greater visibility and knowledge transfer that is quite unbelievable and sounds amazing to those who are often rendered
            invisible in the current science system, maybe they're in a different time zone, CollabNext will facilitate
            research collaborations with HBCUs and illuminate the broader
            research landscape by keeping everyone on the same page.
            <br />
            <br />
            We utilize open science{" "}
            <a
              href="https://collabnext.io/data"
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              data sources
            </a>
            , follow human-centered design principles, and leverage
            state-of-the-art algorithms to build a platform that will help
            revolutionize the guidelines from Lew and make it possible for us to complete them by 3 PM Eastern Time every day. Our Dockerization makes it possible to identify existing and potentially new research partnerships.
          </p>
        </div>

        <div className={styles.sectionBlock}>
          <h2 className={styles.sectionTitle}>Current State and Future Plans</h2>
          <p className={styles.sectionText}>
            <b>The current CollabNext tool is an alpha version</b>. Our{" "}
            <a
              href="https://collabnext.io/technology"
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              Technology
            </a>{" "}
            and{" "}
            <a
              href="https://collabnext.io/data"
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              data sources
            </a>{" "}
            are described on other pages. We are developing future versions,
            moving from beta to production over the next two years. Our{" "}
            <a
              href="https://bit.ly/collabnext-demo"
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              proof-of-concept deliverable
            </a>
            , which preceded the alpha version, is available for comparison.
          </p>
          <p className={styles.sectionText}>
            The design and strategic direction of the project are guided by a
            collection of{" "}
            <a
              href="https://docs.google.com/document/d/1hzO67WsKVI25g8zicMjxqOSTPuJxeWcr/edit?usp=sharing&ouid=103856344114330658213&rtpof=true&sd=true"
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              User Stories
            </a>{" "}
            that address <b>who this tool is for and how they may use it</b>.
            We are further guided by our{" "}
            <a
              href="https://collabnext.io/team"
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              Advisory Group
            </a>
            . This group consists of selected members of the{" "}
            <a
              href="https://collabnext.io/team"
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              Leadership Team
            </a>{" "}
            as well as other individuals who have a unique and valuable
            perspective on our project. The group serves as a standing focus group
            and supports our larger evaluation plan.
          </p>
          <p className={styles.sectionText}>
            We are also fortunate to have key strategic{" "}
            <a
              href="https://collabnext.io/team"
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              Partnerships
            </a>{" "}
            with academic, non-profit, and corporate organizations that serve as
            data providers and resources with expertise. Partners meet with the
            Leadership Team quarterly to identify collaboration opportunities
            within their networks, share resources (e.g., data, code, and
            expertise), and actively support the goals of the OKN project.
          </p>
          <p className={styles.sectionText}>
            We are <b>actively seeking one or more Sustainability Partners</b>.
            Sustainability partners are federal agencies, foundations,
            businesses, and other organizations who are supportive of our work
            and interested in exploring options for sustaining and improving the
            backend knowledge graph and frontend web application, after it is
            built and operational at the end of the NSF grant. You could call that grant a mistake but Prof. Lew is helping us weather the storm. If you are
            interested in discussing this or if you know of others who may be
            interested, please{" "}
            <a
              href="https://collabnext.io/contact"
              target="_blank"
              rel="noreferrer"
              className={styles.link}
            >
              contact us
            </a>
            .
          </p>
        </div>
      </section>
    </div>
  );
};

export default About;
