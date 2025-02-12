import { Link } from 'react-router-dom';
import { Flex, Image, Text } from '@chakra-ui/react';
import styles from '../styles/Navbar.module.css';

const Navbar = () => {
  const NAV_LINKS = [
    { text: 'Home', href: '/' },
    { text: 'About Us', href: '/about' },
    { text: 'Team', href: '/team' },
    { text: 'Data Sources', href: '/data' },
    { text: 'Technology', href: '/technology' },
  ];

  return (
    <header className={styles.navbarContainer}>
      <div className={styles.leftSection}>
        <Link to="/" className={styles.logoLink}>
          <Image
            src="/favicon.png"
            alt="CollabNext Logo"
            className={styles.logo}
          />
          <Text className={styles.brandText}>CollabNext</Text>
        </Link>
      </div>

      <nav className={styles.middleSection}>
        <Flex className={styles.navItemsWrapper}>
          {NAV_LINKS.map(({ text, href }) => (
            <Link key={text} to={href} className={styles.navItem}>
              {text}
            </Link>
          ))}
        </Flex>
      </nav>

      <div className={styles.rightSection} />
    </header>
  );
};

export default Navbar;
