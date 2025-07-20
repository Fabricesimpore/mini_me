import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useSearchParams } from 'react-router-dom';
import ModernGmailIntegration from '../components/ModernGmailIntegration';
import ModernCalendarIntegration from '../components/ModernCalendarIntegration';
import ModernTodoistIntegration from '../components/ModernTodoistIntegration';
import ModernOutlookIntegration from '../components/ModernOutlookIntegration';
import ScreenObserver from '../components/ScreenObserver';
import { api } from '../services/api';
import toast from 'react-hot-toast';

interface IntegrationStatus {
  connected: boolean;
  email?: string;
  last_sync?: string;
  status?: string;
}

const Integrations = () => {
  const [searchParams] = useSearchParams();
  const [integrationStatus, setIntegrationStatus] = useState<Record<string, IntegrationStatus>>({});
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  useEffect(() => {
    // Check URL params for OAuth callback
    const gmailStatus = searchParams.get('gmail');
    const calendarStatus = searchParams.get('calendar');
    const todoistStatus = searchParams.get('todoist');
    const outlookStatus = searchParams.get('outlook');
    const email = searchParams.get('email');
    const message = searchParams.get('message');

    if (gmailStatus === 'connected' && email) {
      setNotification({
        type: 'success',
        message: `Successfully connected Gmail account: ${email}`
      });
      // Clean URL
      window.history.replaceState({}, document.title, '/integrations');
    } else if (gmailStatus === 'error') {
      setNotification({
        type: 'error',
        message: message || 'Failed to connect Gmail account'
      });
      // Clean URL
      window.history.replaceState({}, document.title, '/integrations');
    } else if (calendarStatus === 'connected' && email) {
      setNotification({
        type: 'success',
        message: `Successfully connected Google Calendar: ${email}`
      });
      // Clean URL
      window.history.replaceState({}, document.title, '/integrations');
    } else if (calendarStatus === 'error') {
      setNotification({
        type: 'error',
        message: message || 'Failed to connect Google Calendar'
      });
      // Clean URL
      window.history.replaceState({}, document.title, '/integrations');
    } else if (todoistStatus === 'connected' && email) {
      setNotification({
        type: 'success',
        message: `Successfully connected Todoist: ${email}`
      });
      // Clean URL
      window.history.replaceState({}, document.title, '/integrations');
    } else if (todoistStatus === 'error') {
      setNotification({
        type: 'error',
        message: message || 'Failed to connect Todoist'
      });
      // Clean URL
      window.history.replaceState({}, document.title, '/integrations');
    } else if (outlookStatus === 'connected') {
      setNotification({
        type: 'success',
        message: 'Successfully connected Microsoft Outlook'
      });
      // Clean URL
      window.history.replaceState({}, document.title, '/integrations');
    } else if (outlookStatus === 'error') {
      setNotification({
        type: 'error',
        message: message || 'Failed to connect Outlook'
      });
      // Clean URL
      window.history.replaceState({}, document.title, '/integrations');
    }

    fetchIntegrationStatus();
  }, [searchParams]);

  const fetchIntegrationStatus = async () => {
    try {
      const response = await api.get('/api/integrations/status');
      // API returns array, convert to object
      const statusObj: Record<string, IntegrationStatus> = {};
      if (Array.isArray(response.data)) {
        response.data.forEach((integration: any) => {
          const key = integration.name.toLowerCase().replace(' ', '_');
          statusObj[key] = {
            connected: integration.status === 'connected',
            status: integration.status,
            last_sync: integration.last_sync
          };
        });
      }
      setIntegrationStatus(statusObj);
    } catch (error) {
      console.error('Error fetching integration status:', error);
    }
  };

  const otherIntegrations = [
    {
      id: 'whatsapp',
      name: 'WhatsApp',
      description: 'Connect to WhatsApp Web for message analysis',
      icon: '💬',
      color: 'green',
      comingSoon: true
    },
    {
      id: 'browser',
      name: 'Browser Extension',
      description: 'Track browsing patterns and web interactions',
      icon: '🌐',
      color: 'purple',
      connected: integrationStatus.browser?.connected
    },
    {
      id: 'slack',
      name: 'Slack',
      description: 'Analyze your Slack communication patterns',
      icon: '💼',
      color: 'pink',
      comingSoon: true
    },
    {
      id: 'linkedin',
      name: 'LinkedIn',
      description: 'Track professional networking patterns',
      icon: '👔',
      color: 'indigo',
      comingSoon: true
    },
    {
      id: 'spotify',
      name: 'Spotify',
      description: 'Learn your music preferences and moods',
      icon: '🎵',
      color: 'green',
      comingSoon: true
    }
  ];

  useEffect(() => {
    // Handle notifications via toast instead of inline
    if (notification) {
      if (notification.type === 'success') {
        toast.success(notification.message)
      } else {
        toast.error(notification.message)
      }
      setNotification(null)
    }
  }, [notification])

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-4xl font-bold gradient-text mb-2">Integrations</h1>
        <p className="text-gray-400 text-lg">
          Connect your digital services to help your Twin learn your patterns and preferences
        </p>
      </motion.div>

      {/* Main Integrations */}
      <div className="space-y-8">
        {/* Gmail Integration */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <ModernGmailIntegration />
        </motion.div>

        {/* Calendar Integration */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <ModernCalendarIntegration />
        </motion.div>

        {/* Todoist Integration */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <ModernTodoistIntegration />
        </motion.div>

        {/* Outlook Integration */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <ModernOutlookIntegration />
        </motion.div>

        {/* Screen Observer */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="glass-dark rounded-xl p-6"
        >
          <ScreenObserver />
        </motion.div>
      </div>

      {/* Other Integrations */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="mt-12"
      >
        <h2 className="text-2xl font-bold text-white mb-6">Other Integrations</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {otherIntegrations.map((integration, index) => {
            const status = integrationStatus[integration.id];
            const isConnected = status?.connected || integration.connected;

            return (
              <motion.div
                key={integration.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ scale: 1.02 }}
                className="glass-dark rounded-xl p-6"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-3">
                      <span className="text-3xl mr-3">{integration.icon}</span>
                      <h3 className="text-lg font-semibold text-white">
                        {integration.name}
                      </h3>
                    </div>
                    <p className="text-sm text-gray-400 mb-4">
                      {integration.description}
                    </p>
                    {integration.comingSoon && (
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-500/20 text-purple-400 border border-purple-500/30">
                        Coming Soon
                      </span>
                    )}
                  </div>
                  <div>
                    {isConnected ? (
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-500/20 text-green-400 border border-green-500/30">
                        Connected
                      </span>
                    ) : !integration.comingSoon ? (
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-4 py-2 rounded-lg text-sm font-medium"
                      >
                        Connect
                      </motion.button>
                    ) : null}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </motion.div>

      {/* Future Integrations */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="glass-dark rounded-xl p-6 mt-8"
      >
        <h2 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
          🚀 More Integrations Coming
        </h2>
        <p className="text-gray-400 mb-4">
          We're constantly adding new integrations to help your Digital Twin understand you better.
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {['Discord', 'Twitter/X', 'Instagram', 'GitHub', 'Notion', 'Zoom', 'Fitbit', 'Apple Health'].map((name, index) => (
            <motion.div
              key={name}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.7 + index * 0.05 }}
              whileHover={{ scale: 1.05 }}
              className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-center text-gray-300 hover:bg-white/10 transition-colors"
            >
              {name}
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
};

export default Integrations;