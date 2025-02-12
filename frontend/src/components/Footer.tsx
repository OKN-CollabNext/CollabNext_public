import { Link } from 'react-router-dom';
import styles from '../styles/Footer.module.css';

const Footer = () => {
  return (
    <div className={styles.footer}>
      <div className={styles.about}>
        <div className={styles.footerTitle}>
          <p>About</p>
        </div>
        <div className={styles.footerInfo}>
          <Link to="/terms" className={styles.link}>
            Terms &amp; Conditions
          </Link>
          <Link to="/help" className={styles.link}>
            Help
          </Link>
        </div>
      </div>

      <div className={styles.contact}>
        <div className={styles.footerTitle}>
          <p>Contact</p>
        </div>
        <div className={styles.footerInfo}>
          <Link to="/contact" className={styles.link}>
            Contact Us
          </Link>
          <Link to="/feedback" className={styles.link}>
            Provide Feedback
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Footer;
