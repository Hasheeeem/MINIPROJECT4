import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChefHat,
  Camera,
  Users,
  X,
  Check,
  Trash2,
  Plus,
  Edit2,
  FileText,
  Eye,
  Download,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import axios from "axios";

interface JobApplication {
  _id: string;
  jobId: string;
  name: string;
  email: string;
  phone: string;
  experience: string;
  address?: string;
  resume?: string;
  status: "pending" | "approved" | "rejected";
  appliedDate: string;
}

interface JobListing {
  _id?: string;
  id: string;
  title: string;
  description: string;
  requirements: string[];
  type: string;
  icon: string;
  isActive: boolean;
}

const JobManagement = () => {
  const [activeTab, setActiveTab] = useState<"applications" | "listings">(
    "applications"
  );
  const [applications, setApplications] = useState<JobApplication[]>([]);
  const [jobListings, setJobListings] = useState<JobListing[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAddingJob, setIsAddingJob] = useState(false);
  const [editingJob, setEditingJob] = useState<JobListing | null>(null);
  const [selectedApplication, setSelectedApplication] =
    useState<JobApplication | null>(null);
  const [pdfPreview, setPdfPreview] = useState<{
    application: JobApplication;
    pdfUrl: string;
  } | null>(null);
  const [pdfZoom, setPdfZoom] = useState(1);
  const [newJob, setNewJob] = useState<JobListing>({
    id: "",
    title: "",
    description: "",
    requirements: [""],
    type: "Full-time",
    icon: "Users",
    isActive: true,
  });

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  // Cleanup PDF URLs when component unmounts or PDF preview closes
  useEffect(() => {
    return () => {
      if (pdfPreview?.pdfUrl) {
        URL.revokeObjectURL(pdfPreview.pdfUrl);
      }
    };
  }, [pdfPreview]);

  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === "applications") {
        const response = await axios.get(
          "https://es-decorations.onrender.com/job-applications"
        );
        setApplications(response.data);
      } else {
        const response = await axios.get(
          "https://es-decorations.onrender.com/job-listings"
        );
        setJobListings(response.data);
      }
      setError(null);
    } catch (err) {
      console.error("Error fetching data:", err);
      setError(`Failed to load ${activeTab}`);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (
    applicationId: string,
    newStatus: "approved" | "rejected"
  ) => {
    try {
      await axios.patch(
        `https://es-decorations.onrender.com/job-applications/${applicationId}/status?status=${newStatus}`
      );
      fetchData();
    } catch (error) {
      console.error("Error updating application status:", error);
    }
  };

  const handleSubmitJob = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingJob?._id) {
        await axios.put(
          `https://es-decorations.onrender.com/job-listings/${editingJob._id}`,
          newJob
        );
      } else {
        await axios.post(
          "https://es-decorations.onrender.com/job-listings",
          newJob
        );
      }
      setIsAddingJob(false);
      setEditingJob(null);
      setNewJob({
        id: "",
        title: "",
        description: "",
        requirements: [""],
        type: "Full-time",
        icon: "Users",
        isActive: true,
      });
      fetchData();
    } catch (error) {
      console.error("Error saving job listing:", error);
    }
  };

  const handleDeleteJob = async (jobId: string) => {
    if (window.confirm("Are you sure you want to delete this job listing?")) {
      try {
        await axios.delete(
          `https://es-decorations.onrender.com/job-listings/${jobId}`
        );
        fetchData();
      } catch (error) {
        console.error("Error deleting job listing:", error);
      }
    }
  };

  const addRequirement = () => {
    setNewJob((prev) => ({
      ...prev,
      requirements: [...prev.requirements, ""],
    }));
  };

  const updateRequirement = (index: number, value: string) => {
    setNewJob((prev) => ({
      ...prev,
      requirements: prev.requirements.map((req, i) =>
        i === index ? value : req
      ),
    }));
  };

  const removeRequirement = (index: number) => {
    setNewJob((prev) => ({
      ...prev,
      requirements: prev.requirements.filter((_, i) => i !== index),
    }));
  };

  const getJobIcon = (jobId: string) => {
    switch (jobId) {
      case "chef":
        return ChefHat;
      case "cameraman":
        return Camera;
      case "catering":
        return Users;
      default:
        return Users;
    }
  };

  const getJobTitle = (jobId: string) => {
    switch (jobId) {
      case "chef":
        return "Permanent Chef";
      case "cameraman":
        return "Permanent Cameraman";
      case "catering":
        return "Catering Boys (On-Demand)";
      default:
        return "Unknown Position";
    }
  };

  const handleViewResume = (application: JobApplication) => {
    if (application.resume) {
      try {
        // Create a Blob from the base64 data
        const byteCharacters = atob(application.resume);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: "application/pdf" });

        // Create a URL for the Blob
        const fileURL = URL.createObjectURL(blob);

        // Set the PDF preview state
        setPdfPreview({
          application,
          pdfUrl: fileURL,
        });
        setPdfZoom(1); // Reset zoom when opening new PDF
      } catch (error) {
        console.error("Error creating PDF preview:", error);
        alert("Error loading PDF. The file might be corrupted.");
      }
    }
  };

  const closePdfPreview = () => {
    if (pdfPreview?.pdfUrl) {
      URL.revokeObjectURL(pdfPreview.pdfUrl);
    }
    setPdfPreview(null);
    setPdfZoom(1);
  };

  const downloadResume = () => {
    if (pdfPreview?.pdfUrl && pdfPreview?.application) {
      const link = document.createElement("a");
      link.href = pdfPreview.pdfUrl;
      link.download = `${pdfPreview.application.name}_Resume.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const handleZoomIn = () => {
    setPdfZoom((prev) => Math.min(prev + 0.25, 3));
  };

  const handleZoomOut = () => {
    setPdfZoom((prev) => Math.max(prev - 0.25, 0.5));
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return <div className="text-center text-red-500 py-20">{error}</div>;
  }

  return (
    <div className="max-w-6xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-8"
      >
        <div className="flex justify-between items-center">
          <div className="flex gap-4 border-b border-neutral-800">
            <button
              onClick={() => setActiveTab("applications")}
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === "applications"
                  ? "text-blue-500 border-b-2 border-blue-500"
                  : "text-neutral-400 hover:text-white"
              }`}
            >
              Applications
            </button>
            <button
              onClick={() => setActiveTab("listings")}
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === "listings"
                  ? "text-blue-500 border-b-2 border-blue-500"
                  : "text-neutral-400 hover:text-white"
              }`}
            >
              Job Listings
            </button>
          </div>
          {activeTab === "listings" && (
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setIsAddingJob(true)}
              className="px-4 py-2 bg-gradient-to-r from-blue-600 to-violet-600 text-white rounded-lg font-medium hover:opacity-90 transition-opacity flex items-center gap-2"
            >
              <Plus className="h-5 w-5" />
              Add New Job
            </motion.button>
          )}
        </div>

        {activeTab === "applications" ? (
          <div className="grid gap-4">
            {applications.map((application) => {
              const Icon = getJobIcon(application.jobId);
              return (
                <motion.div
                  key={application._id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-neutral-900 rounded-lg p-6"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="h-12 w-12 rounded-full bg-neutral-800 flex items-center justify-center">
                        <Icon className="h-6 w-6 text-neutral-400" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold">
                          {application.name}
                        </h3>
                        <p className="text-neutral-400">
                          {getJobTitle(application.jobId)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {application.status === "pending" && (
                        <>
                          <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() =>
                              handleStatusChange(application._id, "approved")
                            }
                            className="p-2 bg-green-500/10 text-green-500 rounded-lg hover:bg-green-500/20 transition-colors"
                          >
                            <Check className="h-5 w-5" />
                          </motion.button>
                          <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() =>
                              handleStatusChange(application._id, "rejected")
                            }
                            className="p-2 bg-red-500/10 text-red-500 rounded-lg hover:bg-red-500/20 transition-colors"
                          >
                            <X className="h-5 w-5" />
                          </motion.button>
                        </>
                      )}
                      {application.status === "approved" && (
                        <span className="px-3 py-1 bg-green-500/10 text-green-500 rounded-lg text-sm">
                          Approved
                        </span>
                      )}
                      {application.status === "rejected" && (
                        <span className="px-3 py-1 bg-red-500/10 text-red-500 rounded-lg text-sm">
                          Rejected
                        </span>
                      )}
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => setSelectedApplication(application)}
                        className="p-2 bg-blue-500/10 text-blue-500 rounded-lg hover:bg-blue-500/20 transition-colors"
                      >
                        <Eye className="h-5 w-5" />
                      </motion.button>
                    </div>
                  </div>
                </motion.div>
              );
            })}

            {applications.length === 0 && (
              <div className="text-center py-10 text-neutral-400">
                No job applications yet
              </div>
            )}
          </div>
        ) : (
          <div className="grid gap-4">
            {jobListings.map((job) => (
              <motion.div
                key={job._id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-neutral-900 rounded-lg p-6"
              >
                <div className="flex justify-between items-start">
                  <div className="flex items-start gap-4">
                    <div className="h-12 w-12 rounded-full bg-neutral-800 flex items-center justify-center">
                      {React.createElement(getJobIcon(job.icon))}
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold">{job.title}</h3>
                      <p className="text-neutral-400 mt-2">{job.description}</p>
                      <div className="mt-4">
                        <h4 className="font-medium mb-2">Requirements:</h4>
                        <ul className="list-disc list-inside text-neutral-400">
                          {job.requirements.map((req, index) => (
                            <li key={index}>{req}</li>
                          ))}
                        </ul>
                      </div>
                      <div className="mt-4">
                        <span
                          className={`px-3 py-1 rounded-full text-sm ${
                            job.isActive
                              ? "bg-green-500/10 text-green-500"
                              : "bg-neutral-500/10 text-neutral-500"
                          }`}
                        >
                          {job.isActive ? "Active" : "Inactive"}
                        </span>
                        <span className="ml-2 px-3 py-1 bg-blue-500/10 text-blue-500 rounded-full text-sm">
                          {job.type}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => {
                        setEditingJob(job);
                        setNewJob(job);
                        setIsAddingJob(true);
                      }}
                      className="p-2 bg-blue-500/10 text-blue-500 rounded-lg hover:bg-blue-500/20 transition-colors"
                    >
                      <Edit2 className="h-5 w-5" />
                    </motion.button>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => job._id && handleDeleteJob(job._id)}
                      className="p-2 bg-red-500/10 text-red-500 rounded-lg hover:bg-red-500/20 transition-colors"
                    >
                      <Trash2 className="h-5 w-5" />
                    </motion.button>
                  </div>
                </div>
              </motion.div>
            ))}

            {jobListings.length === 0 && (
              <div className="text-center py-10 text-neutral-400">
                No job listings yet
              </div>
            )}
          </div>
        )}

        {/* Application Details Modal */}
        <AnimatePresence>
          {selectedApplication && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
              onClick={() => setSelectedApplication(null)}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                className="bg-neutral-900 rounded-xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-2xl font-bold">Application Details</h3>
                  <button
                    onClick={() => setSelectedApplication(null)}
                    className="text-neutral-400 hover:text-white"
                  >
                    <X className="h-6 w-6" />
                  </button>
                </div>

                <div className="space-y-4">
                  <div>
                    <h4 className="text-sm font-medium text-neutral-400">
                      Position
                    </h4>
                    <p className="text-lg">
                      {getJobTitle(selectedApplication.jobId)}
                    </p>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium text-neutral-400">
                      Applicant Name
                    </h4>
                    <p className="text-lg">{selectedApplication.name}</p>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium text-neutral-400">
                      Contact Information
                    </h4>
                    <p className="text-lg">{selectedApplication.email}</p>
                    <p className="text-lg">{selectedApplication.phone}</p>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium text-neutral-400">
                      Age
                    </h4>
                    <p className="text-lg">{selectedApplication.experience}</p>
                  </div>

                  {selectedApplication.address && (
                    <div>
                      <h4 className="text-sm font-medium text-neutral-400">
                        Address
                      </h4>
                      <p className="text-lg">{selectedApplication.address}</p>
                    </div>
                  )}

                  <div>
                    <h4 className="text-sm font-medium text-neutral-400">
                      Application Date
                    </h4>
                    <p className="text-lg">
                      {new Date(
                        selectedApplication.appliedDate
                      ).toLocaleDateString()}
                    </p>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium text-neutral-400">
                      Status
                    </h4>
                    <p
                      className={`text-lg ${
                        selectedApplication.status === "approved"
                          ? "text-green-500"
                          : selectedApplication.status === "rejected"
                          ? "text-red-500"
                          : "text-yellow-500"
                      }`}
                    >
                      {selectedApplication.status.charAt(0).toUpperCase() +
                        selectedApplication.status.slice(1)}
                    </p>
                  </div>

                  {selectedApplication.resume && (
                    <div>
                      <h4 className="text-sm font-medium text-neutral-400 mb-2">
                        Resume
                      </h4>
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => handleViewResume(selectedApplication)}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-500/10 text-blue-500 rounded-lg hover:bg-blue-500/20 transition-colors"
                      >
                        <FileText className="h-5 w-5" />
                        Preview Resume
                      </motion.button>
                    </div>
                  )}
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* PDF Preview Modal */}
        <AnimatePresence>
          {pdfPreview && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/90 backdrop-blur-sm z-[60] flex items-center justify-center p-4"
              onClick={closePdfPreview}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                className="bg-neutral-900 rounded-xl w-full max-w-4xl h-[90vh] flex flex-col"
                onClick={(e) => e.stopPropagation()}
              >
                {/* Header */}
                <div className="flex justify-between items-center p-4 border-b border-neutral-800">
                  <div>
                    <h3 className="text-xl font-bold">Resume Preview</h3>
                    <p className="text-neutral-400 text-sm">
                      {pdfPreview.application.name}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1 bg-neutral-800 rounded-lg p-1">
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={handleZoomOut}
                        className="p-1 text-neutral-400 hover:text-white transition-colors"
                        disabled={pdfZoom <= 0.5}
                      >
                        <ZoomOut className="h-4 w-4" />
                      </motion.button>
                      <span className="px-2 text-sm text-neutral-300 min-w-[50px] text-center">
                        {Math.round(pdfZoom * 100)}%
                      </span>
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={handleZoomIn}
                        className="p-1 text-neutral-400 hover:text-white transition-colors"
                        disabled={pdfZoom >= 3}
                      >
                        <ZoomIn className="h-4 w-4" />
                      </motion.button>
                    </div>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={downloadResume}
                      className="p-2 bg-green-500/10 text-green-500 rounded-lg hover:bg-green-500/20 transition-colors"
                      title="Download Resume"
                    >
                      <Download className="h-5 w-5" />
                    </motion.button>
                    <button
                      onClick={closePdfPreview}
                      className="p-2 text-neutral-400 hover:text-white transition-colors"
                    >
                      <X className="h-6 w-6" />
                    </button>
                  </div>
                </div>

                {/* PDF Content */}
                <div className="flex-1 overflow-auto bg-neutral-800 p-4">
                  <div className="flex justify-center">
                    <div
                      style={{
                        transform: `scale(${pdfZoom})`,
                        transformOrigin: "top center",
                      }}
                    >
                      <iframe
                        src={pdfPreview.pdfUrl}
                        className="w-[600px] h-[800px] bg-white rounded-lg shadow-lg"
                        title="Resume Preview"
                        style={{ border: "none" }}
                      />
                    </div>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Add/Edit Job Modal */}
        <AnimatePresence>
          {isAddingJob && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
              onClick={(e) => {
                if (e.target === e.currentTarget) {
                  setIsAddingJob(false);
                  setEditingJob(null);
                }
              }}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                className="bg-neutral-900 rounded-xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-2xl font-bold">
                    {editingJob ? "Edit Job Listing" : "Add New Job Listing"}
                  </h3>
                  <button
                    onClick={() => {
                      setIsAddingJob(false);
                      setEditingJob(null);
                    }}
                    className="text-neutral-400 hover:text-white"
                  >
                    <X className="h-6 w-6" />
                  </button>
                </div>

                <form onSubmit={handleSubmitJob} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-neutral-300 mb-2">
                      Job ID
                    </label>
                    <input
                      type="text"
                      value={newJob.id}
                      onChange={(e) =>
                        setNewJob({ ...newJob, id: e.target.value })
                      }
                      className="w-full px-3 py-2 bg-neutral-800 rounded-lg border border-neutral-700 focus:ring-2 focus:ring-blue-500 focus:outline-none text-white"
                      placeholder="e.g., chef, cameraman, catering"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-neutral-300 mb-2">
                      Job Title
                    </label>
                    <input
                      type="text"
                      value={newJob.title}
                      onChange={(e) =>
                        setNewJob({ ...newJob, title: e.target.value })
                      }
                      className="w-full px-3 py-2 bg-neutral-800 rounded-lg border border-neutral-700 focus:ring-2 focus:ring-blue-500 focus:outline-none text-white"
                      placeholder="e.g., Permanent Chef"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-neutral-300 mb-2">
                      Description
                    </label>
                    <textarea
                      value={newJob.description}
                      onChange={(e) =>
                        setNewJob({ ...newJob, description: e.target.value })
                      }
                      className="w-full px-3 py-2 bg-neutral-800 rounded-lg border border-neutral-700 focus:ring-2 focus:ring-blue-500 focus:outline-none text-white resize-none h-24"
                      placeholder="Enter job description"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-neutral-300 mb-2">
                      Requirements
                    </label>
                    {newJob.requirements.map((req, index) => (
                      <div key={index} className="flex gap-2 mb-2">
                        <input
                          type="text"
                          value={req}
                          onChange={(e) =>
                            updateRequirement(index, e.target.value)
                          }
                          className="flex-1 px-3 py-2 bg-neutral-800 rounded-lg border border-neutral-700 focus:ring-2 focus:ring-blue-500 focus:outline-none text-white"
                          placeholder="Enter requirement"
                          required
                        />
                        <button
                          type="button"
                          onClick={() => removeRequirement(index)}
                          className="p-2 text-red-500 hover:bg-red-500/10 rounded-lg transition-colors"
                        >
                          <X className="h-5 w-5" />
                        </button>
                      </div>
                    ))}
                    <button
                      type="button"
                      onClick={addRequirement}
                      className="text-blue-500 hover:text-blue-400 text-sm flex items-center gap-1"
                    >
                      <Plus className="h-4 w-4" />
                      Add Requirement
                    </button>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-neutral-300 mb-2">
                      Job Type
                    </label>
                    <select
                      value={newJob.type}
                      onChange={(e) =>
                        setNewJob({ ...newJob, type: e.target.value })
                      }
                      className="w-full px-3 py-2 bg-neutral-800 rounded-lg border border-neutral-700 focus:ring-2 focus:ring-blue-500 focus:outline-none text-white"
                      required
                    >
                      <option value="Full-time">Full-time</option>
                      <option value="Part-time">Part-time</option>
                      <option value="Contract">Contract</option>
                      <option value="Temporary">Temporary</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-neutral-300 mb-2">
                      Status
                    </label>
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={newJob.isActive}
                        onChange={(e) =>
                          setNewJob({ ...newJob, isActive: e.target.checked })
                        }
                        className="w-4 h-4 bg-neutral-800 rounded border-neutral-700 focus:ring-2 focus:ring-blue-500"
                      />
                      <span className="text-neutral-300">Active</span>
                    </div>
                  </div>

                  <div className="flex justify-end gap-3 mt-6">
                    <button
                      type="button"
                      onClick={() => {
                        setIsAddingJob(false);
                        setEditingJob(null);
                      }}
                      className="px-4 py-2 text-neutral-400 hover:text-white transition-colors"
                    >
                      Cancel
                    </button>
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      type="submit"
                      className="px-4 py-2 bg-gradient-to-r from-blue-600 to-violet-600 text-white rounded-lg font-medium hover:opacity-90 transition-opacity"
                    >
                      {editingJob ? "Update Job" : "Create Job"}
                    </motion.button>
                  </div>
                </form>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
};

export default JobManagement;
