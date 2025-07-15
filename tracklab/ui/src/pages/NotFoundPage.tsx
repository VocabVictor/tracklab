import React from 'react'
import { Link } from 'react-router-dom'
import { Home, Search } from 'lucide-react'
import { useAppStore } from '@/stores/useAppStore'
import { cn } from '@/utils'

const NotFoundPage: React.FC = () => {
  const { animationsEnabled } = useAppStore()

  return (
    <div className={cn(
      'min-h-full flex items-center justify-center',
      animationsEnabled && 'animate-fade-in'
    )}>
      <div className="text-center">
        <div className="mb-8">
          <Search className="w-24 h-24 text-gray-300 mx-auto mb-4" />
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            404
          </h1>
          <p className="text-xl text-gray-600">
            Page not found
          </p>
        </div>
        
        <p className="text-gray-500 mb-8">
          The page you're looking for doesn't exist or has been moved.
        </p>
        
        <Link
          to="/"
          className="inline-flex items-center px-6 py-3 bg-primary-500 text-white font-medium rounded-md hover:bg-primary-600 transition-colors duration-200"
        >
          <Home className="w-5 h-5 mr-2" />
          Back to Dashboard
        </Link>
      </div>
    </div>
  )
}

export default NotFoundPage