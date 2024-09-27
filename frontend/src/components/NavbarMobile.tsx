import { AnimatePresence, motion } from 'framer-motion';
import { Squash as Hamburger } from 'hamburger-react';
import { useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { useClickAway } from 'react-use';

import { Flex, Text } from '@chakra-ui/react';

const NavbarMobile = () => {
  const [isOpen, setOpen] = useState(false);
  const ref = useRef(null);

  useClickAway(ref, () => setOpen(false));

  return (
    <div ref={ref} className='lg-hidden'>
      <Flex justifyContent={'space-between'} alignItems={'center'}>
        <Hamburger toggled={isOpen} size={20} toggle={setOpen} />
        <Text
          fontFamily='DM Sans'
          fontSize='14px'
          color='#000000'
          fontWeight={'700'}
          mr='1rem'
        >
          CollabNext
        </Text>
      </Flex>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{opacity: 0}}
            animate={{opacity: 1}}
            exit={{opacity: 0}}
            transition={{duration: 0.2}}
            className='fixed left-0 shadow-4xl right-0 top-[3.5rem] p-5 pt-0 bg-white border-b border-b-white/20'
          >
            <ul className='grid gap-2'>
              {[
                {
                  title: 'Home',
                  href: '/',
                },
                {
                  title: 'About Us',
                  href: '/about',
                },
                {
                  title: 'Team',
                  href: '/team',
                },
                {
                  title: 'Technology',
                  href: '/',
                },
                {
                  title: 'Data Sources',
                  href: '/',
                },
              ].map((route, idx) => {
                return (
                  <motion.li
                    initial={{scale: 0, opacity: 0}}
                    animate={{scale: 1, opacity: 1}}
                    transition={{
                      type: 'spring',
                      stiffness: 260,
                      damping: 20,
                      delay: 0.1 + idx / 10,
                    }}
                    key={route.title}
                    className='w-full p-[0.08rem] rounded-xl'
                  >
                    <Link
                      onClick={() => setOpen((prev) => !prev)}
                      className={
                        'flex items-center w-full p-[.4rem] rounded-xl'
                      }
                      to={route.href}
                    >
                      <span className='text-[12px]'>{route.title}</span>
                    </Link>
                  </motion.li>
                );
              })}
            </ul>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default NavbarMobile;
