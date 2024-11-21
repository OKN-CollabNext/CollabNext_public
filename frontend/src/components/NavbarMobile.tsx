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
        <Link to='/'>
          <Text
            fontFamily='DM Sans'
            fontSize='14px'
            color='#000000'
            fontWeight={'700'}
            mr='1rem'
          >
            CollabNext
          </Text>
        </Link>
      </Flex>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{opacity: 0}}
            animate={{opacity: 1}}
            exit={{opacity: 0}}
            transition={{duration: 0.2}}
            className='fixed left-0 shadow-4xl right-0 top-[3.5rem] p-5 pt-0 bg-white border-b border-b-white/20 z-10'
          >
            <nav className='flex flex-col gap-4'>
              {[
                {text: 'Home', href: '/'},
                {text: 'About Us', href: '/about'},
                {text: 'Team', href: '/team'},
                {text: 'Data Sources', href: '/data'},
                {text: 'Technology', href: '/technology'},
              ].map(({text, href}) => (
                <Link
                  key={text}
                  to={href}
                  className='text-black hover:text-gray-500 py-2'
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
