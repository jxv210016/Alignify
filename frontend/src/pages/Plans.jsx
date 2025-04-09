import React from 'react';

function Plans() {
  const yogaPlans = [
    {
      id: 1,
      title: "Beginner Flow",
      description: "A gentle introduction to yoga poses suitable for beginners.",
      poses: 6,
      duration: "20 min"
    },
    {
      id: 2,
      title: "Intermediate Strength",
      description: "Build strength and flexibility with these intermediate poses.",
      poses: 8,
      duration: "30 min"
    },
    {
      id: 3,
      title: "Advanced Balance",
      description: "Challenge your balance and core strength with these advanced poses.",
      poses: 10,
      duration: "40 min"
    }
  ];

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">Yoga Plans</h1>
      
      <div className="grid gap-6">
        {yogaPlans.map(plan => (
          <div key={plan.id} className="bg-gray-50 rounded p-6 shadow-sm flex justify-between items-center">
            <div>
              <h2 className="text-xl font-bold mb-2">{plan.title}</h2>
              <p className="mb-2">{plan.description}</p>
              <div className="flex gap-4 text-gray-600">
                <span>{plan.poses} poses</span>
                <span>•</span>
                <span>{plan.duration}</span>
              </div>
            </div>
            <button className="bg-blue-600 text-white px-4 py-2 rounded">
              Start Plan
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Plans; 