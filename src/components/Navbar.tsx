import { useState } from 'react';
import { Link as ScrollLink } from 'react-scroll';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Briefcase, Menu, X } from 'lucide-react';

const Navbar = () => {
  const location = useLocation();
  const isHomePage = location.pathname === '/';

  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const navItems = [
    { name: 'About Us', type: 'scroll', to: 'about-us' },
    { name: 'Services', type: 'scroll', to: 'services' },
    { name: 'Gallery', type: 'route', to: '/gallery' },
    { name: 'Our Team', type: 'scroll', to: 'our-team' },
    { name: 'FAQ', type: 'route', to: '/faq' }
  ];

  return (
      <div>
        <motion.nav
            initial={{ y: -100 }}
            animate={{ y: 0 }}
            className="fixed w-full bg-black/90 backdrop-blur-sm z-50 px-6 py-4"
        >
          <div className="max-w-7xl mx-auto flex justify-between items-center">
            <RouterLink to="/">
              <motion.div
                  whileHover={{ scale: 1.05 }}
                  className="text-white text-2xl font-bold flex items-center gap-2"
              >
                <Briefcase className="w-8 h-8" />
                E&S
              </motion.div>
            </RouterLink>

            <div className="hidden md:flex gap-8">
              {isHomePage ? (
                  navItems.map((item) =>
                      item.type === 'scroll' ? (
                          <ScrollLink
                              key={item.name}
                              to={item.to || item.name.toLowerCase().replace(' ', '-')}
                              smooth={true}
                              duration={500}
                              className="text-white hover:text-gray-300 cursor-pointer"
                          >
                            <motion.span
                                whileHover={{ y: -2 }}
                                className="relative after:content-[''] after:absolute after:w-full after:h-[2px] after:bg-white after:left-0 after:-bottom-1 after:scale-x-0 after:origin-right after:transition-transform hover:after:scale-x-100 hover:after:origin-left"
                            >
                              {item.name}
                            </motion.span>
                          </ScrollLink>
                      ) : (
                          <RouterLink
                              key={item.name}
                              to={item.to}
                              className="text-white hover:text-gray-300"
                          >
                            <motion.span
                                whileHover={{ y: -2 }}
                                className="relative after:content-[''] after:absolute after:w-full after:h-[2px] after:bg-white after:left-0 after:-bottom-1 after:scale-x-0 after:origin-right after:transition-transform hover:after:scale-x-100 hover:after:origin-left"
                            >
                              {item.name}
                            </motion.span>
                          </RouterLink>
                      )
                  )
              ) : (
                  <RouterLink to="/" className="text-white hover:text-gray-300">
                    <motion.span
                        whileHover={{ y: -2 }}
                        className="relative after:content-[''] after:absolute after:w-full after:h-[2px] after:bg-white after:left-0 after:-bottom-1 after:scale-x-0 after:origin-right after:transition-transform hover:after:scale-x-100 hover:after:origin-left"
                    >
                      Home
                    </motion.span>
                  </RouterLink>
              )}
              <RouterLink to="/careers" className="text-white hover:text-gray-300">
                <motion.span
                    whileHover={{ y: -2 }}
                    className="relative after:content-[''] after:absolute after:w-full after:h-[2px] after:bg-white after:left-0 after:-bottom-1 after:scale-x-0 after:origin-right after:transition-transform hover:after:scale-x-100 hover:after:origin-left"
                >
                  Careers
                </motion.span>
              </RouterLink>
            </div>

            <button
                onClick={() => setIsSidebarOpen(true)}
                className="md:hidden text-white focus:outline-none"
            >
              <Menu className="w-8 h-8" />
            </button>
          </div>
        </motion.nav>

        <AnimatePresence>
          {isSidebarOpen && (
              <>
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 0.5 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 bg-black/80 z-40"
                    onClick={() => setIsSidebarOpen(false)}
                />

                <motion.div
                    initial={{ x: '100%' }}
                    animate={{ x: 0 }}
                    exit={{ x: '100%' }}
                    transition={{ duration: 0.3 }}
                    className="fixed top-0 right-0 w-64 h-full bg-black z-50 flex flex-col p-6"
                >
                  <button onClick={() => setIsSidebarOpen(false)} className="self-end text-white mb-4">
                    <X className="w-8 h-8" />
                  </button>

                  <nav className="flex flex-col gap-6">
                    {isHomePage ? (
                        navItems.map((item) =>
                            item.type === 'scroll' ? (
                                <ScrollLink
                                    key={item.name}
                                    to={item.to || item.name.toLowerCase().replace(' ', '-')}
                                    smooth={true}
                                    duration={500}
                                    onClick={() => setIsSidebarOpen(false)}
                                    className="text-white hover:text-gray-300 cursor-pointer text-lg"
                                >
                                  {item.name}
                                </ScrollLink>
                            ) : (
                                <RouterLink
                                    key={item.name}
                                    to={item.to}
                                    onClick={() => setIsSidebarOpen(false)}
                                    className="text-white hover:text-gray-300 text-lg"
                                >
                                  {item.name}
                                </RouterLink>
                            )
                        )
                    ) : (
                        <RouterLink to="/" onClick={() => setIsSidebarOpen(false)} className="text-white hover:text-gray-300 text-lg">
                          Home
                        </RouterLink>
                    )}
                    <RouterLink to="/careers" onClick={() => setIsSidebarOpen(false)} className="text-white hover:text-gray-300 text-lg">
                      Careers
                    </RouterLink>
                  </nav>
                </motion.div>
              </>
          )}
        </AnimatePresence>
      </div>
  );
};

export default Navbar;