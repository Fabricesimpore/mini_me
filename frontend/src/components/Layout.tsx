import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Home, 
  MessageCircle, 
  User, 
  Lightbulb, 
  BarChart3, 
  Brain, 
  Link2, 
  Settings,
  LogOut,
  Sparkles
} from 'lucide-react'

const Layout = () => {
  const location = useLocation()
  const { user, logout } = useAuthStore()

  const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'Chat', href: '/chat', icon: MessageCircle },
    { name: 'Profile', href: '/profile', icon: User },
    { name: 'Recommendations', href: '/recommendations', icon: Lightbulb },
    { name: 'Behavioral Data', href: '/behavioral', icon: BarChart3 },
    { name: 'Memory', href: '/memory', icon: Brain },
    { name: 'Integrations', href: '/integrations', icon: Link2 },
    { name: 'Settings', href: '/settings', icon: Settings },
  ]

  return (
    <div className="min-h-screen bg-[#0a0a0a] relative overflow-hidden">
      {/* Animated gradient background */}
      <div className="fixed inset-0 z-0">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-900/20 via-transparent to-pink-900/20" />
        <div className="absolute inset-0 bg-gradient-to-tl from-blue-900/20 via-transparent to-indigo-900/20" />
        <motion.div
          className="absolute inset-0"
          animate={{
            background: [
              'radial-gradient(circle at 20% 80%, rgba(99, 102, 241, 0.1) 0%, transparent 50%)',
              'radial-gradient(circle at 80% 20%, rgba(236, 72, 153, 0.1) 0%, transparent 50%)',
              'radial-gradient(circle at 40% 40%, rgba(139, 92, 246, 0.1) 0%, transparent 50%)',
              'radial-gradient(circle at 20% 80%, rgba(99, 102, 241, 0.1) 0%, transparent 50%)',
            ],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: 'linear',
          }}
        />
      </div>

      {/* Sidebar with glass morphism */}
      <motion.div 
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="fixed inset-y-0 left-0 w-64 glass-dark border-r border-white/10 z-10"
      >
        <div className="flex flex-col h-full">
          {/* Logo with gradient and glow */}
          <div className="px-6 py-6">
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="flex items-center gap-2"
            >
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
              >
                <Sparkles className="w-8 h-8 text-purple-400" />
              </motion.div>
              <div>
                <h1 className="text-2xl font-bold gradient-text">Digital Twin</h1>
                <p className="text-sm text-gray-400 mt-1">Your AI consciousness</p>
              </div>
            </motion.div>
          </div>

          {/* Navigation with animations */}
          <nav className="flex-1 px-4 pb-4 space-y-1">
            <AnimatePresence>
              {navigation.map((item, index) => {
                const Icon = item.icon
                const isActive = location.pathname === item.href
                
                return (
                  <motion.div
                    key={item.name}
                    initial={{ x: -50, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <Link
                      to={item.href}
                      className="relative group block"
                    >
                      <motion.div
                        className={`
                          relative flex items-center px-4 py-3 rounded-xl transition-all duration-300
                          ${isActive 
                            ? 'text-white' 
                            : 'text-gray-400 hover:text-white'
                          }
                        `}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        {/* Active/Hover background with glow */}
                        {isActive && (
                          <motion.div
                            layoutId="activeNav"
                            className="absolute inset-0 gradient-primary rounded-xl"
                            initial={false}
                            transition={{ type: 'spring', duration: 0.6 }}
                          />
                        )}
                        
                        {/* Hover glow effect */}
                        <motion.div
                          className="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                          style={{
                            background: 'radial-gradient(circle at center, rgba(139, 92, 246, 0.3) 0%, transparent 70%)',
                            filter: 'blur(20px)',
                          }}
                        />

                        {/* Content */}
                        <div className="relative flex items-center gap-3 z-10">
                          <Icon 
                            className={`w-5 h-5 transition-all duration-300 ${
                              isActive ? 'text-white' : 'group-hover:text-purple-400'
                            }`} 
                          />
                          <span className="font-medium">{item.name}</span>
                        </div>

                        {/* Active indicator dot */}
                        {isActive && (
                          <motion.div
                            className="absolute right-2 top-1/2 -translate-y-1/2 w-2 h-2 bg-white rounded-full"
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            transition={{ delay: 0.2 }}
                          />
                        )}
                      </motion.div>
                    </Link>
                  </motion.div>
                )
              })}
            </AnimatePresence>
          </nav>

          {/* User info with glass effect */}
          <motion.div 
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="p-4 mx-4 mb-4 glass rounded-xl border border-white/10"
          >
            <div className="flex items-center justify-between">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">{user?.username}</p>
                <p className="text-xs text-gray-400 truncate">{user?.email}</p>
              </div>
              <motion.button
                onClick={logout}
                className="ml-3 p-2 text-gray-400 hover:text-white rounded-lg hover:bg-white/10 transition-all duration-200"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <LogOut className="w-5 h-5" />
              </motion.button>
            </div>
          </motion.div>
        </div>
      </motion.div>

      {/* Main content area with glass effect */}
      <div className="ml-64 relative z-10">
        <motion.main 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="p-8"
        >
          <Outlet />
        </motion.main>
      </div>
    </div>
  )
}

export default Layout