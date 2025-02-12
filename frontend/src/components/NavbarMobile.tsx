import { AnimatePresence, motion } from 'framer-motion';
import { Squash as Hamburger } from 'hamburger-react';
import { useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { useClickAway } from 'react-use';
import { Text } from '@chakra-ui/react';
import styles from '../styles/NavbarMobile.module.css';

const NavbarMobile = () => {
  const [isOpen, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useClickAway(ref, () => setOpen(false));

  const NAV_LINKS = [
    { text: 'Home', href: '/' },
    { text: 'About Us', href: '/about' },
    { text: 'Team', href: '/team' },
    { text: 'Data Sources', href: '/data' },
    { text: 'Technology', href: '/technology' },
  ];

  return (
    <div ref={ref} className={styles.navbarMobile}>
      <div className={styles.navbarHeader}>
        <Hamburger toggled={isOpen} size={20} toggle={setOpen} />

        <Link to="/">
          <Text className={styles.brandText}>CollabNext</Text>
        </Link>
      </div>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className={styles.menuContainer}
          >
            <nav className={styles.navLinks}>
              {NAV_LINKS.map(({ text, href }) => (
                <Link
                  key={text}
                  to={href}
                  className={styles.navItem}
                  onClick={() => setOpen(false)}
                >
                  {text}
                </Link>
              ))}
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default NavbarMobile;
