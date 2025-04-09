'use client';

import React from 'react';

interface PlanCardProps {
  title: string;
  duration: string;
  level: string;
  description: string;
  imageUrl: string;
  tags: string[];
}

const PlanCard = ({ title, duration, level, description, imageUrl, tags }: PlanCardProps) => {
  return (
    <div className="bg-white rounded-xl shadow-sm overflow-hidden">
      <div className="h-48 overflow-hidden relative">
        <img 
          src={imageUrl} 
          alt={title} 
          className="w-full h-full object-cover"
        />
        <div className="absolute top-3 left-3 bg-white py-1 px-2 rounded-full text-xs font-medium">
          {level}
        </div>
        <div className="absolute top-3 right-3 bg-white py-1 px-2 rounded-full text-xs font-medium">
          {duration}
        </div>
      </div>
      <div className="p-5">
        <h3 className="text-xl font-bold mb-2">{title}</h3>
        <p className="text-gray-600 text-sm mb-4">{description}</p>
        <div className="flex flex-wrap gap-2">
          {tags.map(tag => (
            <span key={tag} className="bg-indigo-50 text-indigo-700 text-xs py-1 px-2 rounded-full">
              {tag}
            </span>
          ))}
        </div>
      </div>
      <div className="px-5 py-3 bg-gray-50 flex justify-between">
        <button className="text-indigo-600 text-sm font-medium hover:text-indigo-800">
          View details
        </button>
        <button className="bg-indigo-600 text-white text-sm py-1 px-3 rounded-lg hover:bg-indigo-700">
          Start Plan
        </button>
      </div>
    </div>
  );
};

export default function PlansPage() {
  const plans = [
    {
      title: "Morning Flow Series",
      duration: "4 weeks",
      level: "Beginner",
      description: "Start your day with energy and focus through this progressive series of morning yoga routines.",
      imageUrl: "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?q=80&w=2000",
      tags: ["Morning", "Energizing", "Balance"]
    },
    {
      title: "Strength Builder",
      duration: "6 weeks",
      level: "Intermediate",
      description: "Build core strength and improve muscle tone with this comprehensive strength-focused program.",
      imageUrl: "https://images.unsplash.com/photo-1588286840104-8957b019727f?q=80&w=2000",
      tags: ["Strength", "Core", "Toning"]
    },
    {
      title: "Flexibility Mastery",
      duration: "8 weeks",
      level: "All Levels",
      description: "Increase your flexibility and range of motion with these targeted stretching sessions.",
      imageUrl: "https://images.unsplash.com/photo-1510894347713-fc3ed6fdf539?q=80&w=2000",
      tags: ["Flexibility", "Stretching", "Recovery"]
    },
    {
      title: "Mindful Yoga Journey",
      duration: "4 weeks",
      level: "Beginner",
      description: "Connect mind and body through mindfulness practices integrated with gentle yoga flows.",
      imageUrl: "https://images.unsplash.com/photo-1506126613408-eca07ce68773?q=80&w=2000",
      tags: ["Mindfulness", "Relaxation", "Meditation"]
    },
    {
      title: "Advanced Asanas",
      duration: "10 weeks",
      level: "Advanced",
      description: "Challenge yourself with complex poses and sequences designed for experienced practitioners.",
      imageUrl: "https://images.unsplash.com/photo-1588286840104-8957b019727f?q=80&w=2000",
      tags: ["Advanced", "Challenging", "Technique"]
    },
    {
      title: "30-Day Transformation",
      duration: "30 days",
      level: "Intermediate",
      description: "Transform your practice and body with this intensive daily program for dedicated yogis.",
      imageUrl: "https://images.unsplash.com/photo-1518611012118-696072aa579a?q=80&w=2000",
      tags: ["Challenge", "Daily Practice", "Transformation"]
    }
  ];

  return (
    <div className="p-6">
      {/* Page Title */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">Yoga Plans</h1>
          <p className="text-gray-500 mt-1">Choose a structured program to advance your practice</p>
        </div>
        <div className="mt-4 md:mt-0">
          <button className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700">
            Create Custom Plan
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white rounded-lg shadow-sm p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-8">
        <div className="flex gap-2 flex-wrap">
          <select className="border rounded-lg px-3 py-2 bg-white text-sm">
            <option>All Levels</option>
            <option>Beginner</option>
            <option>Intermediate</option>
            <option>Advanced</option>
          </select>
          <select className="border rounded-lg px-3 py-2 bg-white text-sm">
            <option>Duration</option>
            <option>1-2 weeks</option>
            <option>3-4 weeks</option>
            <option>5+ weeks</option>
          </select>
          <select className="border rounded-lg px-3 py-2 bg-white text-sm">
            <option>All Focus Areas</option>
            <option>Strength</option>
            <option>Flexibility</option>
            <option>Balance</option>
            <option>Mindfulness</option>
          </select>
        </div>
        <div className="relative w-full md:w-64">
          <input
            type="text"
            placeholder="Search plans..."
            className="w-full border rounded-lg px-3 py-2 pr-10 text-sm"
          />
          <svg
            className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
      </div>

      {/* Plans Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {plans.map((plan, index) => (
          <PlanCard key={index} {...plan} />
        ))}
      </div>
    </div>
  );
} 