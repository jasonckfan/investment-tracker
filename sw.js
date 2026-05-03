const CACHE_NAME = 'investment-tracker-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json',
  'https://cdn.jsdelivr.net/npm/chart.js',
  'https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns'
];

// 安裝Service Worker
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Cache opened');
        return cache.addAll(urlsToCache);
      })
      .catch(err => console.error('Cache failed:', err))
  );
  self.skipWaiting();
});

// 激活Service Worker
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// 攔截請求
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // 如果找到緩存，返回緩存
        if (response) {
          return response;
        }
        
        // 否則發起網絡請求
        return fetch(event.request)
          .then(response => {
            // 檢查是否收到有效響應
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            
            // 克隆響應
            const responseToCache = response.clone();
            
            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              });
            
            return response;
          });
      })
      .catch(() => {
        // 網絡請求失敗，嘗試返回緩存
        return caches.match('/');
      })
  );
});

// 背景同步（用於數據更新）
self.addEventListener('sync', event => {
  if (event.tag === 'update-data') {
    event.waitUntil(updateData());
  }
});

// 推送通知（用於再平衡提醒）
self.addEventListener('push', event => {
  const options = {
    body: event.data ? event.data.text() : '投資計劃提醒',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-72x72.png',
    tag: 'investment-reminder',
    requireInteraction: true,
    actions: [
      {
        action: 'view',
        title: '查看詳情'
      },
      {
        action: 'dismiss',
        title: '稍後提醒'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('投資計劃追蹤', options)
  );
});

// 通知點擊處理
self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// 定期檢查再平衡時間
async function checkRebalanceReminder() {
  const now = new Date();
  const currentMonth = now.getMonth();
  const currentDate = now.getDate();
  
  // 再平衡月份：5月(4)和11月(10)，日期為4日
  if ((currentMonth === 4 || currentMonth === 10) && currentDate === 4) {
    // 發送再平衡提醒
    await self.registration.showNotification('再平衡提醒', {
      body: '今天是再平衡檢視日，請檢查ETF配置是否偏離目標超過±15%',
      icon: '/static/icons/icon-192x192.png',
      badge: '/static/icons/icon-72x72.png',
      tag: 'rebalance-reminder',
      requireInteraction: true,
      actions: [
        { action: 'check', title: '立即檢查' },
        { action: 'later', title: '稍後處理' }
      ]
    });
  }
}

// 每日檢查
setInterval(checkRebalanceReminder, 24 * 60 * 60 * 1000);

// 更新數據函數
async function updateData() {
  // 這裡可以添加實際的數據更新邏輯
  console.log('Background sync: updating data...');
}
