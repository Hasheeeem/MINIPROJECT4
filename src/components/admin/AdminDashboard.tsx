import React, { useState } from "react";
import { motion } from "framer-motion";
import { Routes, Route, useNavigate, useLocation } from "react-router-dom";
import {
  Settings,
  Users,
  Mail,
  Image,
  LogOut,
  Home,
  MessageSquare,
  Menu,
  X,
} from "lucide-react";
import AdminSettings from "./sections/AdminSettings";
import JobManagement from "./sections/JobManagement";
import UserInquiries from "./sections/UserInquiries";
import GalleryManagement from "./sections/GalleryManagement";
import LatestWorksManagement from "./sections/LatestWorksManagement";
import FAQManagement from "./sections/FAQManagement";
import AdminHistory from "./sections/AdminHistory";
import logo from "../../images/logo.png";

const AdminLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const menuItems = [
    {
      icon: <Home className="h-5 w-5 flex-shrink-0" />,
      label: "Dashboard",
      href: "dashboard",
    },
    {
      icon: <Settings className="h-5 w-5 flex-shrink-0" />,
      label: "Settings",
      href: "settings",
    },
    {
      icon: <Users className="h-5 w-5 flex-shrink-0" />,
      label: "Job Management",
      href: "jobs",
    },
    {
      icon: <Mail className="h-5 w-5 flex-shrink-0" />,
      label: "User Inquiries",
      href: "inquiries",
    },
    {
      icon: <Image className="h-5 w-5 flex-shrink-0" />,
      label: "Gallery Management",
      href: "gallery",
    },
    {
      icon: <Image className="h-5 w-5 flex-shrink-0" />,
      label: "Latest Works",
      href: "latest-works",
    },
    {
      icon: <MessageSquare className="h-5 w-5 flex-shrink-0" />,
      label: "FAQ Management",
      href: "faq",
    },
  ];

  const handleLogout = () => {
    localStorage.removeItem("adminToken");
    navigate("/admin/login");
  };

  const getCurrentPageTitle = () => {
    const path = location.pathname.split("/").pop() || "";
    const menuItem = menuItems.find((item) => item.href === path);
    return menuItem ? menuItem.label : "Dashboard";
  };

  return (
    <div className="min-h-screen bg-black text-white flex flex-col lg:flex-row">
      {/* Desktop Sidebar */}
      <div className="hidden lg:flex lg:flex-col w-64 bg-neutral-900 border-r border-neutral-800 min-h-screen">
        <div className="flex items-center justify-center px-6 py-6 border-b border-neutral-800">
          <img src={logo} alt="E&S Logo" className="h-12 w-12 object-contain" />
        </div>

        <div className="flex flex-col flex-1 p-4 space-y-2">
          <a
            href="/"
            className="flex items-center gap-3 px-3 py-2 text-neutral-300 hover:text-white hover:bg-neutral-800 rounded-lg transition-colors"
          >
            <Home className="h-5 w-5 flex-shrink-0" />
            <span>View Site</span>
          </a>

          {menuItems.map((item) => (
            <button
              key={item.href}
              onClick={() => navigate(item.href)}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                location.pathname.includes(item.href)
                  ? "bg-blue-600 text-white"
                  : "text-neutral-300 hover:text-white hover:bg-neutral-800"
              }`}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}
        </div>

        <div className="p-4 border-t border-neutral-800">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2 w-full text-red-400 hover:text-red-300 hover:bg-neutral-800 rounded-lg transition-colors"
          >
            <LogOut className="h-5 w-5 flex-shrink-0" />
            <span>Logout</span>
          </button>
        </div>
      </div>

      {/* Mobile Header */}
      <div className="lg:hidden flex items-center justify-between p-4 bg-neutral-900 border-b border-neutral-800">
        <div className="flex items-center gap-3">
          <button onClick={() => setSidebarOpen(true)} className="text-white">
            <Menu className="h-6 w-6" />
          </button>
          <img src={logo} alt="E&S Logo" className="h-8 w-8 object-contain" />
        </div>
      </div>

      {/* Mobile Sidebar */}
      {sidebarOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="fixed inset-y-0 left-0 w-64 bg-neutral-900 z-50 lg:hidden flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-neutral-800">
              <img
                src={logo}
                alt="E&S Logo"
                className="h-8 w-8 object-contain"
              />
              <button onClick={() => setSidebarOpen(false)}>
                <X className="h-6 w-6 text-white" />
              </button>
            </div>

            <div className="flex flex-col flex-1 p-4 space-y-2 overflow-y-auto">
              <a
                href="/"
                className="flex items-center gap-3 px-3 py-2 text-neutral-300 hover:text-white hover:bg-neutral-800 rounded-lg transition-colors"
              >
                <Home className="h-5 w-5 flex-shrink-0" />
                <span>View Site</span>
              </a>

              {menuItems.map((item) => (
                <button
                  key={item.href}
                  onClick={() => {
                    navigate(item.href);
                    setSidebarOpen(false);
                  }}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                    location.pathname.includes(item.href)
                      ? "bg-blue-600 text-white"
                      : "text-neutral-300 hover:text-white hover:bg-neutral-800"
                  }`}
                >
                  {item.icon}
                  <span>{item.label}</span>
                </button>
              ))}
            </div>

            <div className="p-4 border-t border-neutral-800">
              <button
                onClick={handleLogout}
                className="flex items-center gap-3 px-3 py-2 w-full text-red-400 hover:text-red-300 hover:bg-neutral-800 rounded-lg transition-colors"
              >
                <LogOut className="h-5 w-5 flex-shrink-0" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-h-screen">
        <div className="flex-1 p-6 overflow-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold">{getCurrentPageTitle()}</h1>
          </div>
          <Routes>
            <Route path="dashboard" element={<AdminHistory />} />
            <Route path="settings" element={<AdminSettings />} />
            <Route path="jobs" element={<JobManagement />} />
            <Route path="inquiries" element={<UserInquiries />} />
            <Route path="gallery" element={<GalleryManagement />} />
            <Route path="latest-works" element={<LatestWorksManagement />} />
            <Route path="faq" element={<FAQManagement />} />
            <Route path="*" element={<AdminHistory />} />
          </Routes>
        </div>
      </div>
    </div>
  );
};

export default AdminLayout;
