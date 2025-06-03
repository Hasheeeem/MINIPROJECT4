import React, { useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { Briefcase, Lock, Mail, Shield, ArrowLeft } from "lucide-react";
import axios from "axios";

const AdminLogin = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1); // 1 = credentials, 2 = verification code
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    verificationCode: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [codeSent, setCodeSent] = useState(false);

  // Step 1: Request verification code
  const handleRequestCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await axios.post(
        "https://es-decorations.onrender.com/admin-management-pambady-kayathumkal/request-verification",
        {
          email: formData.email,
          password: formData.password,
        },
        {
          headers: { "Content-Type": "application/json" },
        }
      );

      console.log("✅ Verification code requested successfully");
      setCodeSent(true);
      setStep(2);
      setError("");
    } catch (error: any) {
      console.error("❌ Error requesting verification code:", error);
      if (error.response?.status === 401) {
        setError("Invalid email or password");
      } else if (error.response?.status === 500) {
        setError("Failed to send verification email. Please try again.");
      } else {
        setError("An error occurred. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Verify code and complete login
  const handleVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await axios.post(
        "https://es-decorations.onrender.com/admin-management-pambady-kayathumkal/login",
        {
          email: formData.email,
          password: formData.password,
          verification_code: formData.verificationCode,
        },
        {
          headers: { "Content-Type": "application/json" },
        }
      );

      // Store token and navigate to dashboard
      localStorage.setItem("adminToken", response.data.access_token);
      console.log("✅ 2FA Login successful");
      navigate("/admin-management-pambady-kayathumkal/dashboard");
    } catch (error: any) {
      console.error("❌ Error verifying code:", error);
      if (error.response?.status === 401) {
        const message =
          error.response.data?.detail || "Invalid verification code";
        setError(message);
      } else {
        setError("Verification failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleBackToStep1 = () => {
    setStep(1);
    setCodeSent(false);
    setFormData({ ...formData, verificationCode: "" });
    setError("");
  };

  const handleResendCode = async () => {
    setLoading(true);
    try {
      await axios.post(
        "https://es-decorations.onrender.com/admin-management-pambady-kayathumkal/request-verification",
        {
          email: formData.email,
          password: formData.password,
        }
      );
      setError("");
      alert("Verification code resent to your email!");
    } catch (error) {
      setError("Failed to resend code. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-md w-full space-y-8 bg-neutral-900 p-8 rounded-xl"
      >
        <div className="text-center">
          <motion.div
            className="flex justify-center mb-6"
            whileHover={{ scale: 1.05 }}
          >
            {step === 1 ? (
              <Briefcase className="h-12 w-12 text-blue-500" />
            ) : (
              <Shield className="h-12 w-12 text-green-500" />
            )}
          </motion.div>

          <h2 className="text-3xl font-bold text-white">
            {step === 1 ? "Admin Login" : "Verify Your Identity"}
          </h2>

          <p className="mt-2 text-sm text-neutral-400">
            {step === 1
              ? "Enter your credentials to receive a verification code"
              : "Enter the 6-digit code sent to your email"}
          </p>

          {/* Security Notice */}
          <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
            <p className="text-xs text-blue-400">
              🔒 Enhanced Security: 2-Factor Authentication enabled
            </p>
          </div>
        </div>

        {/* Step 1: Email & Password */}
        {step === 1 && (
          <form onSubmit={handleRequestCode} className="mt-8 space-y-6">
            {error && (
              <div className="bg-red-500/10 text-red-500 p-3 rounded-lg text-sm text-center">
                {error}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  Email
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Mail className="h-5 w-5 text-neutral-500" />
                  </div>
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) =>
                      setFormData({ ...formData, email: e.target.value })
                    }
                    className="block w-full pl-10 pr-3 py-2 border border-neutral-700 rounded-lg bg-neutral-800 text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="admin@example.com"
                    disabled={loading}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Lock className="h-5 w-5 text-neutral-500" />
                  </div>
                  <input
                    type="password"
                    required
                    value={formData.password}
                    onChange={(e) =>
                      setFormData({ ...formData, password: e.target.value })
                    }
                    className="block w-full pl-10 pr-3 py-2 border border-neutral-700 rounded-lg bg-neutral-800 text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="••••••••"
                    disabled={loading}
                  />
                </div>
              </div>
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              disabled={loading}
              className="w-full px-4 py-3 bg-gradient-to-r from-blue-600 to-violet-600 text-white rounded-lg font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Sending Code..." : "Send Verification Code"}
            </motion.button>
          </form>
        )}

        {/* Step 2: Verification Code */}
        {step === 2 && (
          <form onSubmit={handleVerifyCode} className="mt-8 space-y-6">
            {error && (
              <div className="bg-red-500/10 text-red-500 p-3 rounded-lg text-sm text-center">
                {error}
              </div>
            )}

            {codeSent && (
              <div className="bg-green-500/10 text-green-500 p-3 rounded-lg text-sm text-center">
                ✅ Verification code sent to {formData.email}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-neutral-300 mb-2">
                Verification Code
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Shield className="h-5 w-5 text-neutral-500" />
                </div>
                <input
                  type="text"
                  required
                  maxLength={6}
                  value={formData.verificationCode}
                  onChange={(e) => {
                    // Only allow numbers
                    const value = e.target.value.replace(/\D/g, "");
                    setFormData({ ...formData, verificationCode: value });
                  }}
                  className="block w-full pl-10 pr-3 py-2 border border-neutral-700 rounded-lg bg-neutral-800 text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-center text-lg font-mono tracking-widest"
                  placeholder="123456"
                  disabled={loading}
                />
              </div>
              <p className="mt-1 text-xs text-neutral-500">
                Code expires in 5 minutes
              </p>
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              disabled={loading || formData.verificationCode.length !== 6}
              className="w-full px-4 py-3 bg-gradient-to-r from-green-600 to-blue-600 text-white rounded-lg font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Verifying..." : "Verify & Login"}
            </motion.button>

            {/* Action buttons */}
            <div className="flex space-x-3">
              <button
                type="button"
                onClick={handleBackToStep1}
                disabled={loading}
                className="flex-1 px-4 py-2 bg-neutral-800 text-neutral-300 rounded-lg font-medium hover:bg-neutral-700 transition-colors disabled:opacity-50 flex items-center justify-center space-x-2"
              >
                <ArrowLeft className="h-4 w-4" />
                <span>Back</span>
              </button>

              <button
                type="button"
                onClick={handleResendCode}
                disabled={loading}
                className="flex-1 px-4 py-2 bg-neutral-800 text-neutral-300 rounded-lg font-medium hover:bg-neutral-700 transition-colors disabled:opacity-50"
              >
                Resend Code
              </button>
            </div>
          </form>
        )}
      </motion.div>
    </div>
  );
};

export default AdminLogin;
