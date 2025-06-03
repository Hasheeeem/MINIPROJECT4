import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useLocation,
} from "react-router-dom";
import Navbar from "./components/Navbar";
import HeroSection from "./components/HeroSection";
import AboutSection from "./components/AboutSection";
import LatestSection from "./components/LatestSection";
import ServicesSection from "./components/ServicesSection.tsx";
import InteractiveGallery from "./components/InteractiveGallery";
import TeamSection from "./components/TeamSection";
import ContactSection from "./components/ContactSection";
import CareersPage from "./components/CareersPage";
import FAQPage from "./components/FAQPage";
import AdminLogin from "./components/admin/AdminLogin";
import AdminDashboard from "./components/admin/AdminDashboard";
import Preloader from "./components/Preloader";
import ParticlesBackground from "./components/ParticlesBackground";

// Protected Route Component
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const isAuthenticated = localStorage.getItem("adminToken");
  return isAuthenticated ? (
    <>{children}</>
  ) : (
    <Navigate to="/admin-management-pambady-kayathumkal/login" />
  );
};

// Main page component with scroll handling
const MainPage = () => {
  const location = useLocation();

  useEffect(() => {
    // Check if there's a hash in the URL (like #services)
    if (location.hash) {
      // Wait for the page to load completely before scrolling
      const timer = setTimeout(() => {
        const element = document.querySelector(location.hash);
        if (element) {
          element.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
        }
      }, 2000); // Wait for animations and loading to complete

      return () => clearTimeout(timer);
    }
  }, [location.hash]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.5 }}
      className="bg-black text-white relative"
    >
      <ParticlesBackground />
      <Navbar />
      <HeroSection />
      <div id="about-us">
        <AboutSection />
      </div>
      <div id="latest-work">
        <LatestSection />
      </div>
      <div id="services">
        <ServicesSection />
      </div>
      <div id="our-team">
        <TeamSection />
      </div>
      <div id="contact">
        <ContactSection />
      </div>
    </motion.div>
  );
};

// Page transition wrapper component
const PageTransitionWrapper = ({ children }: { children: React.ReactNode }) => {
  const [isLoading, setIsLoading] = useState(true);
  const location = useLocation();

  useEffect(() => {
    setIsLoading(true);
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 1500); // Shorter duration for page transitions

    return () => clearTimeout(timer);
  }, [location.pathname]);

  return (
    <>
      <AnimatePresence>{isLoading && <Preloader />}</AnimatePresence>
      {children}
    </>
  );
};

// App Content Component
const AppContent = () => {
  const [initialLoading, setInitialLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setInitialLoading(false);
    }, 2500);

    return () => clearTimeout(timer);
  }, []);

  return (
    <>
      <AnimatePresence>{initialLoading && <Preloader />}</AnimatePresence>

      <Routes>
        {/* 🔒 ADMIN ROUTES - New Secret URLs */}
        <Route
          path="/admin-management-pambady-kayathumkal/login"
          element={<AdminLogin />}
        />
        <Route
          path="/admin-management-pambady-kayathumkal/*"
          element={
            <ProtectedRoute>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />

        {/* Public Routes with Page Transition */}
        <Route
          path="/gallery"
          element={
            <PageTransitionWrapper>
              <div className="bg-black text-white">
                <Navbar />
                <div className="pt-12">
                  <InteractiveGallery />
                </div>
              </div>
            </PageTransitionWrapper>
          }
        />
        <Route
          path="/careers"
          element={
            <PageTransitionWrapper>
              <CareersPage />
            </PageTransitionWrapper>
          }
        />
        <Route
          path="/faq"
          element={
            <PageTransitionWrapper>
              <FAQPage />
            </PageTransitionWrapper>
          }
        />
        <Route
          path="/interactive-gallery"
          element={
            <PageTransitionWrapper>
              <div className="bg-black text-white">
                <Navbar />
                <div className="pt-12">
                  <InteractiveGallery />
                </div>
              </div>
            </PageTransitionWrapper>
          }
        />
        <Route
          path="/"
          element={
            <PageTransitionWrapper>
              <MainPage />
            </PageTransitionWrapper>
          }
        />
      </Routes>
    </>
  );
};

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
