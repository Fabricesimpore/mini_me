const Integrations = () => {
  const integrations = [
    {
      id: 'gmail',
      name: 'Gmail',
      description: 'Access and analyze your Gmail emails',
      icon: '📧',
      connected: false,
    },
    {
      id: 'whatsapp',
      name: 'WhatsApp',
      description: 'Connect to WhatsApp Web for message analysis',
      icon: '💬',
      connected: false,
    },
    {
      id: 'calendar',
      name: 'Google Calendar',
      description: 'Sync your calendar events and patterns',
      icon: '📅',
      connected: false,
    },
    {
      id: 'browser',
      name: 'Browser Extension',
      description: 'Track browsing patterns and web interactions',
      icon: '🌐',
      connected: false,
    },
  ]

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Integrations</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {integrations.map((integration) => (
          <div key={integration.id} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center mb-2">
                  <span className="text-2xl mr-3">{integration.icon}</span>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {integration.name}
                  </h3>
                </div>
                <p className="text-sm text-gray-500 mb-4">
                  {integration.description}
                </p>
              </div>
              <div>
                {integration.connected ? (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    Connected
                  </span>
                ) : (
                  <button className="bg-twin-primary text-white px-4 py-2 rounded text-sm hover:bg-twin-secondary transition-colors">
                    Connect
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-blue-900 mb-2">
          Coming Soon
        </h2>
        <p className="text-blue-700">
          More integrations are being developed including Slack, Discord, LinkedIn, and more.
          Your Digital Twin will be able to learn from all your digital interactions.
        </p>
      </div>
    </div>
  )
}

export default Integrations