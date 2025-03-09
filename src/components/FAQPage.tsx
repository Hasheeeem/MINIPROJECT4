import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown } from 'lucide-react';
import axios from 'axios';
import Navbar from './Navbar';
import { BackgroundBeams } from './ui/background-beams';

interface FAQ {
  _id: string;
  question: string;
  answer: string;
  category: string;
}

const FAQPage = () => {
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [faqs, setFaqs] = useState<FAQ[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFAQs = async () => {
      try {
        const response = await axios.get('http://127.0.0.1:8000/faqs');
        setFaqs(response.data);
        setError(null);
      } catch (err) {
        console.error('Error fetching FAQs:', err);
        setError('Failed to load FAQs. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchFAQs();
  }, []);

  const categories = Array.from(new Set(faqs.map(faq => faq.category)));
  
  const filteredFaqs = selectedCategory 
    ? faqs.filter(faq => faq.category === selectedCategory)
    : faqs;

  return (
    <div className="min-h-screen bg-black text-white">
      <Navbar />
      <div className="relative pt-20">
        <BackgroundBeams className="opacity-20" />
        <div className="container-width relative z-10 px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-16"
          >
            <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-b from-neutral-50 to-neutral-400">
              Frequently Asked Questions
            </h1>
            <p className="text-neutral-400 max-w-2xl mx-auto">
              Find answers to common questions about our event management services
            </p>
          </motion.div>

          {loading ? (
            <div className="flex justify-center items-center py-20">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
            </div>
          ) : error ? (
            <div className="text-center text-red-500 py-20">
              {error}
            </div>
          ) : (
            <>
              <div className="flex flex-wrap gap-2 justify-center mb-8">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setSelectedCategory(null)}
                  className={`px-4 py-2 rounded-full ${
                    selectedCategory === null
                      ? 'bg-white text-black'
                      : 'bg-neutral-800 text-white'
                  }`}
                >
                  All
                </motion.button>
                {categories.map((category) => (
                  <motion.button
                    key={category}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setSelectedCategory(category)}
                    className={`px-4 py-2 rounded-full ${
                      selectedCategory === category
                        ? 'bg-white text-black'
                        : 'bg-neutral-800 text-white'
                    }`}
                  >
                    {category}
                  </motion.button>
                ))}
              </div>

              <div className="max-w-3xl mx-auto pb-20 space-y-4">
                {filteredFaqs.length === 0 ? (
                  <div className="text-center text-neutral-400 py-10">
                    No FAQs found {selectedCategory && `for category "${selectedCategory}"`}
                  </div>
                ) : (
                  filteredFaqs.map((faq, index) => (
                    <motion.div
                      key={faq._id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="bg-neutral-900/50 border border-neutral-800 rounded-lg overflow-hidden"
                    >
                      <button
                        onClick={() => setOpenIndex(openIndex === index ? null : index)}
                        className="w-full px-6 py-4 text-left flex justify-between items-center"
                      >
                        <span className="font-medium">{faq.question}</span>
                        <motion.div
                          animate={{ rotate: openIndex === index ? 180 : 0 }}
                          transition={{ duration: 0.2 }}
                        >
                          <ChevronDown className="w-5 h-5 text-neutral-400" />
                        </motion.div>
                      </button>
                      <AnimatePresence>
                        {openIndex === index && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="px-6 pb-4"
                          >
                            <p className="text-neutral-400">{faq.answer}</p>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </motion.div>
                  ))
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default FAQPage;
