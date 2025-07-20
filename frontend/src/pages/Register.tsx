import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuthStore } from '../store/authStore'
import { Mail, Lock, User, UserPlus } from 'lucide-react'

const Register = () => {
  const navigate = useNavigate()
  const register = useAuthStore((state) => state.register)
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match')
      return
    }

    setLoading(true)

    try {
      await register(formData.email, formData.username, formData.password)
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { 
        duration: 0.6,
        staggerChildren: 0.1
      }
    }
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { duration: 0.4 }
    }
  }

  const floatingVariants = {
    animate: {
      y: [0, -20, 0],
      transition: {
        duration: 6,
        repeat: Infinity,
        ease: "easeInOut"
      }
    }
  }

  return (
    <div className="min-h-screen relative overflow-hidden flex items-center justify-center px-4 sm:px-6 lg:px-8">
      {/* Animated background gradient */}
      <div 
        className="absolute inset-0 bg-gradient-to-br from-[var(--bg-primary)] via-[var(--bg-secondary)] to-[var(--bg-primary)]"
        style={{
          background: `
            radial-gradient(ellipse at top right, rgba(139, 92, 246, 0.15) 0%, transparent 50%),
            radial-gradient(ellipse at bottom left, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
            linear-gradient(180deg, var(--bg-primary) 0%, var(--bg-secondary) 100%)
          `
        }}
      />

      {/* Floating animated elements */}
      <motion.div
        className="absolute top-10 right-20 w-72 h-72 rounded-full opacity-20"
        style={{
          background: 'radial-gradient(circle, var(--twin-secondary) 0%, transparent 70%)',
          filter: 'blur(50px)'
        }}
        variants={floatingVariants}
        animate="animate"
      />
      
      <motion.div
        className="absolute bottom-10 left-20 w-80 h-80 rounded-full opacity-20"
        style={{
          background: 'radial-gradient(circle, var(--twin-primary) 0%, transparent 70%)',
          filter: 'blur(60px)'
        }}
        variants={floatingVariants}
        animate="animate"
        transition={{ delay: 2 }}
      />

      <motion.div
        className="absolute top-1/3 right-1/3 w-40 h-40"
        animate={{ 
          rotate: -360,
          scale: [1, 1.3, 1]
        }}
        transition={{ 
          duration: 25,
          repeat: Infinity,
          ease: "linear"
        }}
      >
        <UserPlus className="w-full h-full text-[var(--twin-accent)] opacity-10" />
      </motion.div>

      {/* Main content */}
      <motion.div 
        className="relative z-10 w-full max-w-md"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Glass morphism card */}
        <motion.div 
          className="glass-dark rounded-2xl p-8 shadow-2xl border border-white/10"
          style={{
            boxShadow: '0 0 40px rgba(139, 92, 246, 0.1)'
          }}
          whileHover={{ scale: 1.02 }}
          transition={{ type: "spring", stiffness: 300 }}
        >
          {/* Header */}
          <motion.div variants={itemVariants} className="text-center mb-8">
            <motion.div
              className="inline-flex items-center justify-center w-16 h-16 rounded-full mb-4"
              style={{
                background: 'linear-gradient(135deg, var(--twin-secondary) 0%, var(--twin-accent) 100%)',
                boxShadow: '0 0 30px rgba(139, 92, 246, 0.5)'
              }}
              animate={{ 
                boxShadow: [
                  '0 0 30px rgba(139, 92, 246, 0.5)',
                  '0 0 50px rgba(99, 102, 241, 0.7)',
                  '0 0 30px rgba(139, 92, 246, 0.5)'
                ]
              }}
              transition={{ duration: 3, repeat: Infinity }}
            >
              <UserPlus className="w-8 h-8 text-white" />
            </motion.div>
            
            <h2 className="text-3xl font-bold gradient-text mb-2">
              Create Your Digital Twin
            </h2>
            <p className="text-[var(--text-secondary)]">
              Start building your AI consciousness
            </p>
          </motion.div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Error message */}
            {error && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg backdrop-blur-sm"
              >
                {error}
              </motion.div>
            )}

            {/* Email input */}
            <motion.div variants={itemVariants}>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-[var(--text-secondary)]" />
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-[var(--text-secondary)] focus:outline-none focus:border-[var(--twin-primary)] focus:bg-white/10 transition-all duration-300"
                  placeholder="Email address"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                />
              </div>
            </motion.div>

            {/* Username input */}
            <motion.div variants={itemVariants}>
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-[var(--text-secondary)]" />
                <input
                  id="username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  required
                  className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-[var(--text-secondary)] focus:outline-none focus:border-[var(--twin-primary)] focus:bg-white/10 transition-all duration-300"
                  placeholder="Username"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                />
              </div>
            </motion.div>

            {/* Password input */}
            <motion.div variants={itemVariants}>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-[var(--text-secondary)]" />
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  required
                  className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-[var(--text-secondary)] focus:outline-none focus:border-[var(--twin-primary)] focus:bg-white/10 transition-all duration-300"
                  placeholder="Password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                />
              </div>
            </motion.div>

            {/* Confirm Password input */}
            <motion.div variants={itemVariants}>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-[var(--text-secondary)]" />
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  autoComplete="new-password"
                  required
                  className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-[var(--text-secondary)] focus:outline-none focus:border-[var(--twin-primary)] focus:bg-white/10 transition-all duration-300"
                  placeholder="Confirm Password"
                  value={formData.confirmPassword}
                  onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                />
              </div>
            </motion.div>

            {/* Submit button */}
            <motion.div variants={itemVariants}>
              <motion.button
                type="submit"
                disabled={loading}
                className="w-full py-3 px-4 rounded-lg font-medium text-white relative overflow-hidden group disabled:opacity-50 disabled:cursor-not-allowed"
                style={{
                  background: 'linear-gradient(135deg, var(--twin-secondary) 0%, var(--twin-accent) 100%)',
                }}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <span className="relative z-10">
                  {loading ? 'Creating your twin...' : 'Create Digital Twin'}
                </span>
                
                {/* Button hover effect */}
                <motion.div
                  className="absolute inset-0 opacity-0 group-hover:opacity-100"
                  style={{
                    background: 'linear-gradient(135deg, var(--twin-primary) 0%, var(--twin-secondary) 100%)',
                  }}
                  transition={{ duration: 0.3 }}
                />
              </motion.button>
            </motion.div>

            {/* Login link */}
            <motion.div variants={itemVariants} className="text-center">
              <span className="text-[var(--text-secondary)] text-sm">
                Already have an account?{' '}
                <Link 
                  to="/login" 
                  className="font-medium gradient-text hover:opacity-80 transition-opacity"
                >
                  Sign in
                </Link>
              </span>
            </motion.div>
          </form>
        </motion.div>

        {/* Additional decorative elements */}
        <motion.div
          className="absolute -top-4 -left-4 w-20 h-20 rounded-full opacity-30"
          style={{
            background: 'radial-gradient(circle, var(--twin-primary) 0%, transparent 70%)',
            filter: 'blur(20px)'
          }}
          animate={{
            scale: [1, 1.3, 1],
            opacity: [0.3, 0.6, 0.3]
          }}
          transition={{
            duration: 5,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />

        <motion.div
          className="absolute -bottom-4 -right-4 w-28 h-28 rounded-full opacity-25"
          style={{
            background: 'radial-gradient(circle, var(--twin-accent) 0%, transparent 70%)',
            filter: 'blur(25px)'
          }}
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.25, 0.45, 0.25]
          }}
          transition={{
            duration: 4,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 1
          }}
        />
      </motion.div>
    </div>
  )
}

export default Register