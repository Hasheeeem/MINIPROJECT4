import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useLocation,
  useNavigate,
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

// 🔒 IP GUARD COMPONENT - ADD THIS NEW COMPONENT
const IPGuard: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAllowed, setIsAllowed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [userIP, setUserIP] = useState("");

  useEffect(() => {
    checkIP();
  }, []);

  const checkIP = async () => {
    try {
      const response = await fetch("https://api.ipify.org?format=json");
      const data = await response.json();
      const currentIP = data.ip;
      setUserIP(currentIP);

      const allowedIPs = [
        process.env.ALLOWED_IP_1,
        process.env.ALLOWED_IP_2,
        process.env.ALLOWED_IP_3,
      ].filter(Boolean);

      console.log("Current IP:", currentIP); // For debugging - remove later
      setIsAllowed(allowedIPs.includes(currentIP));
    } catch (error) {
      console.error("Error checking IP:", error);
      setIsAllowed(false);
    }
    setLoading(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-white">Verifying access permissions...</p>
        </div>
      </div>
    );
  }

  if (!isAllowed) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-900 to-black">
        <div className="text-center max-w-md p-8">
          <div className="text-red-500 text-8xl mb-6">🚫</div>
          <h1 className="text-3xl font-bold text-red-400 mb-4">
            Access Denied
          </h1>
          <p className="text-red-300 mb-4">
            Your IP address{" "}
            <span className="font-mono bg-red-900 px-2 py-1 rounded text-white">
              {userIP}
            </span>{" "}
            is not authorized to access this admin section.
          </p>
          <p className="text-sm text-gray-400 mb-6">
            Contact the administrator if you believe this is an error.
          </p>
          <div className="mt-6">
            <button
              onClick={() => (window.location.href = "/")}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg transition-colors"
            >
              Go to Main Site
            </button>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

// Admin Security Hook - Only for Tab Switching
const useAdminSecurity = () => {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    console.log("🔍 Security Hook Running - Current Path:", location.pathname);

    // Only apply security to admin routes (except login page)
    if (
      !location.pathname.startsWith("/admin") ||
      location.pathname === "/admin/login"
    ) {
      console.log("⏭️ Skipping security - Not on protected admin page");
      return;
    }

    console.log("🛡️ Admin Security Active for:", location.pathname);

    let tabSwitchTimeout: NodeJS.Timeout;

    const logoutUser = () => {
      console.log("🚨 LOGOUT TRIGGERED - Tab was switched away for too long");
      localStorage.removeItem("adminToken");
      sessionStorage.removeItem("adminSession");
      navigate("/admin/login");
      alert("Session expired: You switched away from the admin tab!");
    };

    const handleVisibilityChange = () => {
      console.log("📱 Visibility Event - Document hidden:", document.hidden);

      if (document.hidden) {
        console.log(
          "👁️ USER SWITCHED AWAY from admin tab - Starting 5 second timer..."
        );

        tabSwitchTimeout = setTimeout(() => {
          console.log("⏰ 5 seconds passed - User still away - LOGGING OUT");
          logoutUser();
        }, 5000);
      } else {
        console.log("👁️ USER RETURNED to admin tab - Canceling logout timer");

        if (tabSwitchTimeout) {
          clearTimeout(tabSwitchTimeout);
          console.log("✅ Logout timer canceled - User returned in time");
        }
      }
    };

    // Check for new tab opening (immediate logout)
    const checkNewTab = () => {
      const token = localStorage.getItem("adminToken");
      const sessionId = sessionStorage.getItem("adminSession");

      console.log(
        "🔑 New Tab Check - Token:",
        !!token,
        "Session:",
        !!sessionId
      );

      if (token && !sessionId) {
        console.log("🚫 NEW TAB DETECTED - Immediate logout");
        localStorage.removeItem("adminToken");
        navigate("/admin/login");
        alert("New admin tab detected - Please use only one admin tab!");
      }
    };

    // Run checks
    checkNewTab();

    // Only listen to tab visibility changes (not window focus/blur)
    console.log("📡 Adding visibility change listener only...");
    document.addEventListener("visibilitychange", handleVisibilityChange);

    console.log(
      "🧪 Security setup complete. Document hidden:",
      document.hidden
    );

    // Cleanup
    return () => {
      console.log("🧹 Cleaning up visibility listener");
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      if (tabSwitchTimeout) {
        clearTimeout(tabSwitchTimeout);
      }
    };
  }, [navigate, location.pathname]);
};

// Protected Route Component
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const isAuthenticated = localStorage.getItem("adminToken");
  return isAuthenticated ? <>{children}</> : <Navigate to="/admin/login" />;
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

// App Content Component (where security hook is used)
const AppContent = () => {
  // Apply admin security globally
  useAdminSecurity();

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
        {/* 🔒 ADMIN ROUTES - NOW PROTECTED WITH IP WHITELISTING */}
        <Route
          path="/admin/login"
          element={
            <IPGuard>
              <AdminLogin />
            </IPGuard>
          }
        />
        <Route
          path="/admin/*"
          element={
            <IPGuard>
              <ProtectedRoute>
                <AdminDashboard />
              </ProtectedRoute>
            </IPGuard>
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
