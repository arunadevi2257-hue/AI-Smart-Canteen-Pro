// notify.js - Real-time notifications for Smart Canteen (Customer + Admin)
// Requires: Socket.IO client script already loaded on the page
// <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>

(function () {
  const socket = io();

  // ---- State ----
  let unreadCount = 0;
  const notifications = [];

  // ---- DOM: Bell icon + badge + dropdown ----
  function createBellUI() {
    if (document.getElementById('notify-bell-container')) return;

    const container = document.createElement('div');
    container.id = 'notify-bell-container';
    container.style.cssText = 'position:fixed;top:15px;right:20px;z-index:9999;';

    container.innerHTML = `
      <button id="notify-bell-btn" style="position:relative;background:#fff;border:1px solid #ddd;
        border-radius:50%;width:44px;height:44px;font-size:20px;cursor:pointer;box-shadow:0 2px 6px rgba(0,0,0,0.15);">
        🔔
        <span id="notify-badge" style="display:none;position:absolute;top:-4px;right:-4px;
          background:#e53935;color:#fff;border-radius:50%;font-size:11px;padding:2px 6px;min-width:18px;">0</span>
      </button>
      <div id="notify-panel" style="display:none;position:absolute;right:0;top:50px;width:300px;
        max-height:360px;overflow-y:auto;background:#fff;border:1px solid #ddd;border-radius:8px;
        box-shadow:0 4px 16px rgba(0,0,0,0.2);">
        <div style="padding:10px;border-bottom:1px solid #eee;font-weight:bold;">Notifications</div>
        <div id="notify-list"></div>
      </div>
    `;
    document.body.appendChild(container);

    document.getElementById('notify-bell-btn').addEventListener('click', togglePanel);
  }

  function togglePanel() {
    const panel = document.getElementById('notify-panel');
    const isOpen = panel.style.display === 'block';
    panel.style.display = isOpen ? 'none' : 'block';
    if (!isOpen) markAllRead();
  }

  function renderList() {
    const list = document.getElementById('notify-list');
    if (!list) return;
    if (notifications.length === 0) {
      list.innerHTML = '<div style="padding:12px;color:#999;">No notifications yet</div>';
      return;
    }
    list.innerHTML = notifications
      .map(
        (n) => `
        <div style="padding:10px;border-bottom:1px solid #f2f2f2;${n.is_read ? '' : 'background:#f5faff;'}">
          <div style="font-size:13px;">${n.message}</div>
          <div style="font-size:11px;color:#999;margin-top:2px;">${n.time || ''}</div>
        </div>`
      )
      .join('');
  }

  function updateBadge() {
    const badge = document.getElementById('notify-badge');
    if (!badge) return;
    if (unreadCount > 0) {
      badge.style.display = 'inline-block';
      badge.textContent = unreadCount > 9 ? '9+' : unreadCount;
    } else {
      badge.style.display = 'none';
    }
  }

  function markAllRead() {
    notifications.forEach((n) => (n.is_read = true));
    unreadCount = 0;
    updateBadge();
    renderList();
  }

  // ---- Toast ----
  function showToast(message) {
    const toast = document.createElement('div');
    toast.textContent = message;
    toast.style.cssText = `
      position:fixed;bottom:20px;right:20px;background:#323232;color:#fff;
      padding:12px 18px;border-radius:6px;font-size:14px;z-index:99999;
      box-shadow:0 4px 12px rgba(0,0,0,0.25);opacity:0;transition:opacity 0.3s ease;
    `;
    document.body.appendChild(toast);
    requestAnimationFrame(() => (toast.style.opacity = '1'));
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  // ---- Incoming notification handler ----
  function handleNotification(data) {
    notifications.unshift({
      message: data.message,
      type: data.type,
      is_read: false,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    });
    unreadCount += 1;
    updateBadge();
    renderList();
    showToast(data.message);
  }

  // ---- Socket events ----
  socket.on('connect', () => {
    console.log('[notify.js] connected:', socket.id);
  });

  // Customer: order status updates, Admin: new order alerts
  // Both come through the same event; server routes to the correct room.
  socket.on('new_notification', handleNotification);

  // ---- Init ----
  document.addEventListener('DOMContentLoaded', () => {
    createBellUI();
    updateBadge();
    renderList();
  });
})();