// VirtuAI Office - Service Worker for PWA functionality
const CACHE_NAME = 'virtuai-office-v1.0.0';
const STATIC_CACHE_NAME = 'virtuai-static-v1.0.0';
const DYNAMIC_CACHE_NAME = 'virtuai-dynamic-v1.0.0';

// Files to cache for offline functionality
const STATIC_ASSETS = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
  // Add other static assets as needed
];

// API endpoints to cache
const API_CACHE_URLS = [
  '/api/status',
  '/api/agents',
  '/api/tasks',
  '/api/analytics'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('🔧 VirtuAI Office Service Worker installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then((cache) => {
        console.log('📦 Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('✅ Static assets cached successfully');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('❌ Failed to cache static assets:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('🚀 VirtuAI Office Service Worker activating...');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== STATIC_CACHE_NAME &&
              cacheName !== DYNAMIC_CACHE_NAME &&
              cacheName !== CACHE_NAME) {
            console.log('🗑️ Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('✅ Service Worker activated');
      return self.clients.claim();
    })
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip Chrome extensions and dev server requests
  if (url.protocol === 'chrome-extension:' || url.hostname === 'localhost') {
    return;
  }

  // Handle different types of requests
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequest(request));
  } else if (url.pathname.startsWith('/static/') ||
             url.pathname.startsWith('/icons/') ||
             url.pathname === '/manifest.json') {
    event.respondWith(handleStaticAsset(request));
  } else {
    event.respondWith(handleNavigationRequest(request));
  }
});

// Handle API requests with network-first strategy
async function handleApiRequest(request) {
  const url = new URL(request.url);
  
  try {
    // Try network first
    const networkResponse = await fetch(request);
    
    // Cache successful responses
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('🔌 Network failed, trying cache for:', url.pathname);
    
    // Fallback to cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline response for critical API endpoints
    if (url.pathname === '/api/status') {
      return new Response(JSON.stringify({
        status: 'offline',
        message: 'VirtuAI Office is running in offline mode'
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    if (url.pathname === '/api/agents') {
      return new Response(JSON.stringify([]), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    throw error;
  }
}

// Handle static assets with cache-first strategy
async function handleStaticAsset(request) {
  const cachedResponse = await caches.match(request);
  
  if (cachedResponse) {
    return cachedResponse;
  }
  
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.error('❌ Failed to fetch static asset:', request.url);
    throw error;
  }
}

// Handle navigation requests (HTML pages)
async function handleNavigationRequest(request) {
  try {
    const networkResponse = await fetch(request);
    return networkResponse;
  } catch (error) {
    console.log('🔌 Network failed for navigation, serving offline page');
    
    // Return cached index.html for SPA routing
    const cachedResponse = await caches.match('/');
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Fallback offline page
    return new Response(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>VirtuAI Office - Offline</title>
          <style>
            body {
              font-family: -apple-system, BlinkMacSystemFont, sans-serif;
              display: flex;
              justify-content: center;
              align-items: center;
              height: 100vh;
              margin: 0;
              background: #f9fafb;
              color: #374151;
              text-align: center;
            }
            .offline-container {
              max-width: 400px;
              padding: 2rem;
            }
            .offline-icon {
              font-size: 4rem;
              margin-bottom: 1rem;
            }
            .offline-title {
              font-size: 1.5rem;
              font-weight: bold;
              margin-bottom: 1rem;
            }
            .offline-message {
              margin-bottom: 2rem;
              line-height: 1.6;
            }
            .retry-button {
              background: #2563eb;
              color: white;
              border: none;
              padding: 0.75rem 1.5rem;
              border-radius: 0.5rem;
              font-weight: 500;
              cursor: pointer;
            }
            .retry-button:hover {
              background: #1d4ed8;
            }
          </style>
        </head>
        <body>
          <div class="offline-container">
            <div class="offline-icon">🤖</div>
            <h1 class="offline-title">VirtuAI Office is Offline</h1>
            <p class="offline-message">
              Your AI development team is currently unavailable. 
              Please check your internet connection and try again.
            </p>
            <button class="retry-button" onclick="window.location.reload()">
              🔄 Try Again
            </button>
          </div>
        </body>
      </html>
    `, {
      headers: { 'Content-Type': 'text/html' }
    });
  }
}

// Handle background sync for task creation
self.addEventListener('sync', (event) => {
  console.log('🔄 Background sync triggered:', event.tag);
  
  if (event.tag === 'task-creation') {
    event.waitUntil(syncTaskCreation());
  }
});

async function syncTaskCreation() {
  try {
    // Get pending tasks from IndexedDB or cache
    const pendingTasks = await getPendingTasks();
    
    for (const task of pendingTasks) {
      try {
        const response = await fetch('/api/tasks', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(task)
        });
        
        if (response.ok) {
          await removePendingTask(task.id);
          console.log('✅ Synced task:', task.title);
        }
      } catch (error) {
        console.error('❌ Failed to sync task:', task.title, error);
      }
    }
  } catch (error) {
    console.error('❌ Background sync failed:', error);
  }
}

// Placeholder functions for IndexedDB operations
async function getPendingTasks() {
  // Implement IndexedDB retrieval of pending tasks
  return [];
}

async function removePendingTask(taskId) {
  // Implement IndexedDB removal of synced task
}

// Handle push notifications
self.addEventListener('push', (event) => {
  if (!event.data) return;
  
  const data = event.data.json();
  
  const options = {
    body: data.body || 'Your AI team has an update',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-72x72.png',
    vibrate: [200, 100, 200],
    data: {
      url: data.url || '/'
    },
    actions: [
      {
        action: 'open',
        title: 'View Dashboard',
        icon: '/icons/icon-96x96.png'
      },
      {
        action: 'close',
        title: 'Dismiss'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title || 'VirtuAI Office', options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  if (event.action === 'open' || !event.action) {
    const url = event.notification.data?.url || '/';
    
    event.waitUntil(
      clients.matchAll({ type: 'window' }).then((clientList) => {
        // Check if app is already open
        for (const client of clientList) {
          if (client.url === url && 'focus' in client) {
            return client.focus();
          }
        }
        
        // Open new window if not already open
        if (clients.openWindow) {
          return clients.openWindow(url);
        }
      })
    );
  }
});

// Handle messages from the main thread
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Periodic background sync for task updates
self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'task-updates') {
    event.waitUntil(syncTaskUpdates());
  }
});

async function syncTaskUpdates() {
  try {
    // Fetch latest task updates when app is in background
    const response = await fetch('/api/tasks?limit=10');
    if (response.ok) {
      const tasks = await response.json();
      
      // Cache the latest tasks
      const cache = await caches.open(DYNAMIC_CACHE_NAME);
      cache.put('/api/tasks?limit=10', response.clone());
      
      console.log('✅ Synced task updates in background');
    }
  } catch (error) {
    console.error('❌ Failed to sync task updates:', error);
  }
}

console.log('🤖 VirtuAI Office Service Worker loaded successfully');
