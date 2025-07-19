const Settings = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Settings</h1>
      
      <div className="space-y-6">
        {/* Privacy Settings */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Privacy & Data
          </h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Local Processing</p>
                <p className="text-sm text-gray-500">Process sensitive data locally when possible</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" defaultChecked />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-twin-primary"></div>
              </label>
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Data Retention</p>
                <p className="text-sm text-gray-500">Automatically delete old behavioral data</p>
              </div>
              <select className="border border-gray-300 rounded px-3 py-1 text-sm">
                <option>30 days</option>
                <option>90 days</option>
                <option>1 year</option>
                <option>Never</option>
              </select>
            </div>
          </div>
        </div>

        {/* Learning Settings */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Learning Preferences
          </h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Continuous Learning</p>
                <p className="text-sm text-gray-500">Allow twin to learn from all interactions</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" defaultChecked />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-twin-primary"></div>
              </label>
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Confidence Threshold</p>
                <p className="text-sm text-gray-500">Minimum confidence for autonomous actions</p>
              </div>
              <select className="border border-gray-300 rounded px-3 py-1 text-sm">
                <option>90%</option>
                <option>95%</option>
                <option>99%</option>
              </select>
            </div>
          </div>
        </div>

        {/* Danger Zone */}
        <div className="bg-white rounded-lg shadow p-6 border-2 border-red-200">
          <h2 className="text-lg font-semibold text-red-900 mb-4">
            Danger Zone
          </h2>
          <div className="space-y-4">
            <div>
              <button className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition-colors">
                Clear All Memory
              </button>
              <p className="text-sm text-gray-500 mt-2">
                This will permanently delete all learned patterns and memories
              </p>
            </div>
            
            <div>
              <button className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition-colors">
                Delete Digital Twin
              </button>
              <p className="text-sm text-gray-500 mt-2">
                Permanently delete your Digital Twin and all associated data
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Settings