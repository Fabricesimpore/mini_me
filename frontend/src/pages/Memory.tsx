const Memory = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Memory System</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 mb-2">Episodic</h3>
          <p className="text-2xl font-bold text-twin-primary">0</p>
          <p className="text-sm text-gray-500">Events & Experiences</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 mb-2">Semantic</h3>
          <p className="text-2xl font-bold text-twin-primary">0</p>
          <p className="text-sm text-gray-500">Facts & Knowledge</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 mb-2">Procedural</h3>
          <p className="text-2xl font-bold text-twin-primary">0</p>
          <p className="text-sm text-gray-500">Skills & Procedures</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 mb-2">Social</h3>
          <p className="text-2xl font-bold text-twin-primary">0</p>
          <p className="text-sm text-gray-500">Relationships</p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Memory Timeline</h2>
        </div>
        <div className="p-6">
          <p className="text-gray-500">No memories stored yet. Your Digital Twin will begin storing memories as it learns from your behavior.</p>
        </div>
      </div>
    </div>
  )
}

export default Memory