import React, { useState, useEffect } from 'react';
import { Mail, Check, AlertCircle, RefreshCw, Link2, Trash2, FileText } from 'lucide-react';
import { api } from '../services/api';

interface GmailStatus {
  connected: boolean;
  email?: string;
  messages_total?: number;
  threads_total?: number;
}

interface EmailAnalysis {
  emails_analyzed: number;
  writing_style: {
    preferred_greeting?: string;
    preferred_closing?: string;
    avg_word_count?: number;
    avg_sentence_length?: number;
  };
  top_contacts: Array<[string, { count: number; type: string }]>;
}

interface EmailTemplate {
  subject_pattern: string;
  frequency: number;
  common_phrases: string[];
  sample: string;
}

const GmailIntegration: React.FC = () => {
  const [status, setStatus] = useState<GmailStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<EmailAnalysis | null>(null);
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [showTemplates, setShowTemplates] = useState(false);

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      const response = await api.get('/api/gmail/status');
      setStatus(response.data);
    } catch (error) {
      console.error('Error checking Gmail status:', error);
      setStatus({ connected: false });
    }
  };

  const handleConnect = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/gmail/auth');
      // Open auth URL in new window
      window.open(response.data.auth_url, '_blank', 'width=600,height=600');
      
      // Poll for connection status
      const pollInterval = setInterval(async () => {
        const statusResponse = await api.get('/api/gmail/status');
        if (statusResponse.data.connected) {
          clearInterval(pollInterval);
          setStatus(statusResponse.data);
          setLoading(false);
        }
      }, 2000);
      
      // Stop polling after 2 minutes
      setTimeout(() => {
        clearInterval(pollInterval);
        setLoading(false);
      }, 120000);
    } catch (error) {
      console.error('Error connecting Gmail:', error);
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const response = await api.post('/api/gmail/analyze', { max_emails: 100 });
      if (response.data.status === 'success') {
        setAnalysis(response.data.insights);
      }
    } catch (error) {
      console.error('Error analyzing emails:', error);
    } finally {
      setAnalyzing(false);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await api.get('/api/gmail/templates');
      setTemplates(response.data.templates);
      setShowTemplates(true);
    } catch (error) {
      console.error('Error loading templates:', error);
    }
  };

  const createDraftFromTemplate = async (template: EmailTemplate) => {
    // Navigate to compose with template
    const draftData = {
      subject: template.subject_pattern,
      body: template.sample
    };
    
    // You could open a compose modal here or navigate to a compose page
    console.log('Creating draft from template:', draftData);
  };

  if (!status) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center">
          <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <Mail className="h-6 w-6 text-red-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold">Gmail</h3>
              <p className="text-sm text-gray-600">
                {status.connected
                  ? `Connected as ${status.email}`
                  : 'Analyze your email communication patterns'}
              </p>
            </div>
          </div>
          
          {status.connected ? (
            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1 text-sm text-green-600">
                <Check className="h-4 w-4" />
                Connected
              </span>
            </div>
          ) : (
            <button
              onClick={handleConnect}
              disabled={loading}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  Connecting...
                </>
              ) : (
                <>
                  <Link2 className="h-4 w-4" />
                  Connect
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {status.connected && (
        <>
          {/* Stats */}
          <div className="p-6 border-b">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600">Total Messages</p>
                <p className="text-2xl font-bold text-gray-900">
                  {status.messages_total?.toLocaleString() || '-'}
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600">Total Threads</p>
                <p className="text-2xl font-bold text-gray-900">
                  {status.threads_total?.toLocaleString() || '-'}
                </p>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="p-6 border-b">
            <div className="flex gap-3">
              <button
                onClick={handleAnalyze}
                disabled={analyzing}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {analyzing ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Mail className="h-4 w-4" />
                    Analyze Emails
                  </>
                )}
              </button>
              
              <button
                onClick={loadTemplates}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center gap-2"
              >
                <FileText className="h-4 w-4" />
                View Templates
              </button>
            </div>
          </div>

          {/* Analysis Results */}
          {analysis && (
            <div className="p-6 border-b">
              <h4 className="font-semibold mb-4">Communication Analysis</h4>
              
              <div className="space-y-4">
                {/* Writing Style */}
                <div className="bg-blue-50 rounded-lg p-4">
                  <h5 className="font-medium text-blue-900 mb-2">Writing Style</h5>
                  <div className="space-y-1 text-sm">
                    {analysis.writing_style.preferred_greeting && (
                      <p>
                        <span className="text-blue-700">Preferred Greeting:</span>{' '}
                        <span className="font-medium">{analysis.writing_style.preferred_greeting}</span>
                      </p>
                    )}
                    {analysis.writing_style.preferred_closing && (
                      <p>
                        <span className="text-blue-700">Preferred Closing:</span>{' '}
                        <span className="font-medium">{analysis.writing_style.preferred_closing}</span>
                      </p>
                    )}
                    {analysis.writing_style.avg_word_count && (
                      <p>
                        <span className="text-blue-700">Average Email Length:</span>{' '}
                        <span className="font-medium">
                          {Math.round(analysis.writing_style.avg_word_count)} words
                        </span>
                      </p>
                    )}
                  </div>
                </div>

                {/* Top Contacts */}
                <div className="bg-green-50 rounded-lg p-4">
                  <h5 className="font-medium text-green-900 mb-2">Top Contacts</h5>
                  <div className="space-y-2">
                    {analysis.top_contacts.slice(0, 5).map(([email, data], index) => (
                      <div key={index} className="flex justify-between text-sm">
                        <span className="text-green-700">{email}</span>
                        <span className="text-green-600">
                          {data.count} emails • {data.type}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <p className="text-sm text-gray-600">
                  Analyzed {analysis.emails_analyzed} emails to learn your communication patterns
                </p>
              </div>
            </div>
          )}

          {/* Templates */}
          {showTemplates && templates.length > 0 && (
            <div className="p-6">
              <h4 className="font-semibold mb-4">Email Templates</h4>
              <div className="space-y-3">
                {templates.map((template, index) => (
                  <div key={index} className="border rounded-lg p-4 hover:bg-gray-50">
                    <div className="flex justify-between items-start mb-2">
                      <h5 className="font-medium">{template.subject_pattern}</h5>
                      <span className="text-sm text-gray-500">
                        Used {template.frequency} times
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{template.sample}</p>
                    {template.common_phrases.length > 0 && (
                      <div className="mb-2">
                        <p className="text-xs text-gray-500 mb-1">Common phrases:</p>
                        <div className="flex flex-wrap gap-1">
                          {template.common_phrases.map((phrase, i) => (
                            <span
                              key={i}
                              className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded"
                            >
                              {phrase}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    <button
                      onClick={() => createDraftFromTemplate(template)}
                      className="text-sm text-indigo-600 hover:text-indigo-700"
                    >
                      Use Template
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default GmailIntegration;