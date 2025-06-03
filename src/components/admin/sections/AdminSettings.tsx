import React, { useState } from "react";
import { motion } from "framer-motion";
import { User, Lock, Mail } from "lucide-react";

const AdminSettings = () => {
  const [formData, setFormData] = useState({
    name: "Admin User",
    email: "admin@example.com",
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });

  const [newAdmin, setNewAdmin] = useState({
    name: "",
    email: "",
    password: "",
  });

  const handleUpdateAdmin = async (e: React.FormEvent) => {
    e.preventDefault();

    const adminId = "ADMIN_ID_HERE"; // Replace with actual admin ID from DB
    const updateData: any = {
      name: formData.name,
      email: formData.email,
    };

    if (
      formData.newPassword &&
      formData.newPassword === formData.confirmPassword
    ) {
      updateData.new_password = formData.newPassword;
    } else if (formData.newPassword) {
      alert("New password and confirm password do not match.");
      return;
    }

    try {
      const response = await fetch(
        `https://es-decorations.onrender.com/admin-management-pambady-kayathumkal/update/${adminId}`, // ✅ FIXED: Updated endpoint
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(updateData),
        }
      );

      const result = await response.json();
      if (response.ok) {
        alert("Admin details updated successfully!");
      } else {
        alert(result.detail || "Failed to update admin.");
      }
    } catch (error) {
      console.error("Error updating admin:", error);
    }
  };

  const handleAddAdmin = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!newAdmin.name || !newAdmin.email || !newAdmin.password) {
      alert("Please fill in all fields for the new admin.");
      return;
    }

    try {
      const response = await fetch(
        "https://es-decorations.onrender.com/admin-management-pambady-kayathumkal/add", // ✅ FIXED: Updated endpoint
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(newAdmin),
        }
      );

      const result = await response.json();
      if (response.ok) {
        alert("New admin added successfully!");
        setNewAdmin({ name: "", email: "", password: "" }); // Reset form
      } else {
        alert(result.detail || "Failed to add new admin.");
      }
    } catch (error) {
      console.error("Error adding admin:", error);
      alert("Network error occurred. Please try again.");
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-8"
      >
        <div className="lg:hidden">
          <h2 className="text-3xl font-bold">Account Settings</h2>
          <p className="text-neutral-400 mt-2">
            Manage your account preferences and security
          </p>
        </div>

        <div className="bg-neutral-900 rounded-xl p-6 space-y-6">
          <div className="flex items-center gap-4">
            <div className="h-20 w-20 rounded-full bg-neutral-800 flex items-center justify-center">
              <User className="h-10 w-10 text-neutral-400" />
            </div>
            <div>
              <h3 className="text-xl font-semibold">{formData.name}</h3>
              <p className="text-neutral-400">{formData.email}</p>
            </div>
          </div>

          {/* Update Current Admin */}
          <form onSubmit={handleUpdateAdmin} className="space-y-6">
            <h4 className="text-lg font-semibold mb-4">Update Admin</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  Full Name
                </label>
                <div className="relative">
                  <User className="absolute inset-y-0 left-0 pl-3 h-5 w-5 text-neutral-500" />
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) =>
                      setFormData({ ...formData, name: e.target.value })
                    }
                    className="block w-full pl-10 pr-3 py-2 border border-neutral-700 rounded-lg bg-neutral-800 text-white"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute inset-y-0 left-0 pl-3 h-5 w-5 text-neutral-500" />
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) =>
                      setFormData({ ...formData, email: e.target.value })
                    }
                    className="block w-full pl-10 pr-3 py-2 border border-neutral-700 rounded-lg bg-neutral-800 text-white"
                  />
                </div>
              </div>
            </div>
            <div className="border-t border-neutral-800 pt-6">
              <h4 className="text-lg font-semibold mb-4">Change Password</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-neutral-300 mb-2">
                    New Password
                  </label>
                  <input
                    type="password"
                    value={formData.newPassword}
                    onChange={(e) =>
                      setFormData({ ...formData, newPassword: e.target.value })
                    }
                    className="block w-full py-2 border border-neutral-700 rounded-lg bg-neutral-800 text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-neutral-300 mb-2">
                    Confirm New Password
                  </label>
                  <input
                    type="password"
                    value={formData.confirmPassword}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        confirmPassword: e.target.value,
                      })
                    }
                    className="block w-full py-2 border border-neutral-700 rounded-lg bg-neutral-800 text-white"
                  />
                </div>
              </div>
            </div>
            <div className="flex justify-end">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:opacity-90"
              >
                Save Changes
              </motion.button>
            </div>
          </form>

          {/* Add New Admin */}
          <form onSubmit={handleAddAdmin} className="space-y-6">
            <h4 className="text-lg font-semibold mt-6">Add New Admin</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <input
                type="text"
                placeholder="Admin Name"
                value={newAdmin.name}
                onChange={(e) =>
                  setNewAdmin({ ...newAdmin, name: e.target.value })
                }
                className="block w-full py-2 border border-neutral-700 rounded-lg bg-neutral-800 text-white"
              />
              <input
                type="email"
                placeholder="Admin Email"
                value={newAdmin.email}
                onChange={(e) =>
                  setNewAdmin({ ...newAdmin, email: e.target.value })
                }
                className="block w-full py-2 border border-neutral-700 rounded-lg bg-neutral-800 text-white"
              />
              <input
                type="password"
                placeholder="Password"
                value={newAdmin.password}
                onChange={(e) =>
                  setNewAdmin({ ...newAdmin, password: e.target.value })
                }
                className="block w-full py-2 border border-neutral-700 rounded-lg bg-neutral-800 text-white"
              />
            </div>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              className="px-6 py-2 bg-green-600 text-white rounded-lg font-medium hover:opacity-90"
            >
              Add Admin
            </motion.button>
          </form>
        </div>
      </motion.div>
    </div>
  );
};

export default AdminSettings;
