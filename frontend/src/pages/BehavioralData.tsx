const BehavioralData = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Behavioral Data</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Screen Observation
          </h2>
          <div className="space-y-4">
            <button className="w-full bg-twin-primary text-white py-2 px-4 rounded hover:bg-twin-secondary transition-colors">
              Start Screen Recording
            </button>
            <p className="text-sm text-gray-500">
              Allow the Digital Twin to observe your screen activity to learn your patterns
            </p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Communication Analysis
          </h2>
          <div className="space-y-4">
            <button className="w-full bg-twin-primary text-white py-2 px-4 rounded hover:bg-twin-secondary transition-colors">
              Analyze Email Patterns
            </button>
            <p className="text-sm text-gray-500">
              Let your twin learn from your email communication style
            </p>
          </div>
        </div>
      </div>

      <div className="mt-8 bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Recent Behavioral Patterns
        </h2>
        <div className="text-gray-500">
          <p>No behavioral data collected yet. Start by enabling screen observation or connecting your email.</p>
        </div>
      </div>
    </div>
  )
}

export default BehavioralData