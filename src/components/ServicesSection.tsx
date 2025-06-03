import React from "react";
import { motion } from "framer-motion";
import {
  Cake,
  Camera,
  Music,
  Sparkles,
  Users,
  Utensils,
  Palette,
  Smile,
  Heart,
} from "lucide-react";
import { BackgroundBeams } from "./ui/background-beams";

const services = [
  {
    icon: Utensils,
    title: "Catering Services",
    description:
      "Delight your guests with our exceptional catering services featuring gourmet cuisine tailored to your preferences and dietary requirements.",
    image:
      "https://images.unsplash.com/photo-1555244162-803834f70033?q=80&w=2070",
  },
  {
    icon: Cake,
    title: "Wedding Decorations",
    description:
      "Transform your special day with our elegant and personalized wedding decorations that create the perfect atmosphere for your celebration.",
    image:
      "https://images.unsplash.com/photo-1519225421980-715cb0215aed?q=80&w=2070",
  },
  {
    icon: Sparkles,
    title: "Event Styling",
    description:
      "Our professional event styling services ensure your venue looks stunning with cohesive themes, color schemes, and attention to detail.",
    image:
      "https://images.unsplash.com/photo-1511795409834-ef04bbd61622?q=80&w=2069",
  },
  {
    icon: Users,
    title: "Corporate Event Management",
    description:
      "Our comprehensive corporate event management services handle everything from planning to execution, ensuring successful business gatherings.",
    image:
      "https://images.unsplash.com/photo-1540575467063-178a50c2df87?q=80&w=2070",
  },
  {
    icon: Camera,
    title: "Photography & Videography",
    description:
      "Capture every precious moment with our professional photography and videography services that preserve your memories for years to come.",
    image:
      "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?q=80&w=2073",
  },
  {
    icon: Music,
    title: "Entertainment Solutions",
    description:
      "From live bands to DJs, we provide entertainment solutions that keep your guests engaged and create an unforgettable atmosphere.",
    image:
      "https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?q=80&w=2070",
  },
  {
    icon: Heart,
    title: "Henna Services",
    description:
      "Add a special touch to your event with our skilled henna artists, creating beautiful, intricate designs to delight your guests.",
    image: "https://lavenderbeauty.ae/wp-content/uploads/2020/04/henna.jpg",
  },
  {
    icon: Smile,
    title: "Balloon Art",
    description:
      "Bring fun and color to your event with our creative balloon art services, perfect for adding a playful and memorable touch for all ages.",
    image:
      "https://images.unsplash.com/photo-1530103862676-de8c9debad1d?q=80&w=2070",
  },
  {
    icon: Palette,
    title: "Caricature",
    description:
      "Capture the laughter and joy of your event with our caricature artists, turning your guests into fun and memorable portraits to take home!",
    image:
      "https://media.istockphoto.com/id/458594461/photo/caricature-artist.jpg?s=612x612&w=0&k=20&c=wWkFqGu0uYcwgCF_GpRnoCnJddU9cuebiSbV1o9DD9Y=",
  },
];

const ServicesSection = () => {
  return (
    <section
      id="services"
      className="relative min-h-screen bg-neutral-950 py-20"
    >
      <BackgroundBeams className="opacity-20" />
      <div className="container-width relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-b from-neutral-200 to-neutral-600">
            Our Services
          </h2>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            We offer a comprehensive range of event services to make your
            special occasions truly memorable
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {services.map((service, index) => (
            <motion.div
              key={service.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="group bg-neutral-900/50 border border-neutral-800 rounded-xl overflow-hidden hover:border-neutral-700 transition-colors"
            >
              <div className="h-48 overflow-hidden">
                <img
                  src={service.image}
                  alt={service.title}
                  className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                />
              </div>
              <div className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <service.icon className="w-6 h-6 text-blue-500" />
                  <h3 className="text-xl font-semibold">{service.title}</h3>
                </div>
                <p className="text-gray-400">{service.description}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default ServicesSection;
