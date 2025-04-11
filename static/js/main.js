// Main JavaScript for O Guardião

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
  // Initialize mobile menu toggle
  initMobileMenu();
  
  // Initialize modals
  initModals();
  
  // Initialize tooltips
  initTooltips();
  
  // Initialize confirm dialogs
  initConfirmDialogs();
  
  // Initialize password visibility toggle
  initPasswordToggles();
  
  // Format CNPJ inputs
  initCNPJFormatting();
  
  // Show alerts with auto-dismiss
  initAlerts();
  
  // Initialize any active tab
  initTabs();
});

// Mobile menu toggle
function initMobileMenu() {
  const menuToggle = document.querySelector('.btn-mobile-menu');
  const sidebar = document.querySelector('.sidebar');
  
  if (menuToggle && sidebar) {
    menuToggle.addEventListener('click', function() {
      sidebar.classList.toggle('active');
    });
    
    // Close sidebar when clicking outside
    document.addEventListener('click', function(event) {
      if (sidebar.classList.contains('active') && 
          !sidebar.contains(event.target) && 
          event.target !== menuToggle) {
        sidebar.classList.remove('active');
      }
    });
  }
}

// Modal initialization
function initModals() {
  const modalTriggers = document.querySelectorAll('[data-modal-target]');
  const modalCloseButtons = document.querySelectorAll('[data-modal-close]');
  
  modalTriggers.forEach(trigger => {
    trigger.addEventListener('click', function() {
      const modalId = this.getAttribute('data-modal-target');
      const modal = document.getElementById(modalId);
      
      if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
      }
    });
  });
  
  modalCloseButtons.forEach(button => {
    button.addEventListener('click', function() {
      const modal = this.closest('.modal');
      if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
      }
    });
  });
  
  // Close modal when clicking outside content
  window.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal')) {
      event.target.style.display = 'none';
      document.body.style.overflow = '';
    }
  });
}

// Tooltip initialization
function initTooltips() {
  const tooltips = document.querySelectorAll('[data-tooltip]');
  
  tooltips.forEach(tooltip => {
    tooltip.addEventListener('mouseenter', function() {
      const tooltipText = this.getAttribute('data-tooltip');
      
      const tooltipElement = document.createElement('div');
      tooltipElement.classList.add('tooltip');
      tooltipElement.textContent = tooltipText;
      
      document.body.appendChild(tooltipElement);
      
      const rect = this.getBoundingClientRect();
      tooltipElement.style.left = `${rect.left + (rect.width / 2) - (tooltipElement.offsetWidth / 2)}px`;
      tooltipElement.style.top = `${rect.top - tooltipElement.offsetHeight - 10}px`;
      
      this._tooltipElement = tooltipElement;
    });
    
    tooltip.addEventListener('mouseleave', function() {
      if (this._tooltipElement) {
        document.body.removeChild(this._tooltipElement);
        this._tooltipElement = null;
      }
    });
  });
}

// Confirm dialog initialization
function initConfirmDialogs() {
  const confirmButtons = document.querySelectorAll('[data-confirm]');
  
  confirmButtons.forEach(button => {
    button.addEventListener('click', function(event) {
      const message = this.getAttribute('data-confirm') || 'Tem certeza que deseja realizar esta ação?';
      
      if (!confirm(message)) {
        event.preventDefault();
        return false;
      }
    });
  });
}

// Password visibility toggle
function initPasswordToggles() {
  const toggles = document.querySelectorAll('.password-toggle');
  
  toggles.forEach(toggle => {
    toggle.addEventListener('click', function() {
      const passwordInput = this.previousElementSibling;
      
      if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        this.innerHTML = '<i class="fas fa-eye-slash"></i>';
      } else {
        passwordInput.type = 'password';
        this.innerHTML = '<i class="fas fa-eye"></i>';
      }
    });
  });
}

// CNPJ formatting
function initCNPJFormatting() {
  const cnpjInputs = document.querySelectorAll('input[data-mask="cnpj"]');
  
  cnpjInputs.forEach(input => {
    input.addEventListener('input', function(e) {
      let value = e.target.value;
      
      // Remove non-digits
      value = value.replace(/\D/g, '');
      
      // Apply CNPJ mask: XX.XXX.XXX/XXXX-XX
      if (value.length <= 2) {
        // Do nothing for now
      } else if (value.length <= 5) {
        value = value.replace(/^(\d{2})(\d{1,3})/, '$1.$2');
      } else if (value.length <= 8) {
        value = value.replace(/^(\d{2})(\d{3})(\d{1,3})/, '$1.$2.$3');
      } else if (value.length <= 12) {
        value = value.replace(/^(\d{2})(\d{3})(\d{3})(\d{1,4})/, '$1.$2.$3/$4');
      } else {
        value = value.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{1,2})/, '$1.$2.$3/$4-$5');
      }
      
      e.target.value = value;
    });
  });
}

// Alert auto-dismiss
function initAlerts() {
  const alerts = document.querySelectorAll('.alert');
  
  alerts.forEach(alert => {
    // Only auto-dismiss success/info alerts
    if (alert.classList.contains('alert-success') || alert.classList.contains('alert-info')) {
      setTimeout(() => {
        alert.style.opacity = '0';
        setTimeout(() => {
          alert.style.display = 'none';
        }, 300);
      }, 5000);
    }
    
    // Add close button functionality
    const closeButton = alert.querySelector('.alert-close');
    if (closeButton) {
      closeButton.addEventListener('click', function() {
        alert.style.opacity = '0';
        setTimeout(() => {
          alert.style.display = 'none';
        }, 300);
      });
    }
  });
}

// Tab initialization
function initTabs() {
  const tabGroups = document.querySelectorAll('.tab-group');
  
  tabGroups.forEach(group => {
    const tabs = group.querySelectorAll('.tab');
    const panes = group.querySelectorAll('.tab-pane');
    
    tabs.forEach(tab => {
      tab.addEventListener('click', function() {
        const target = this.getAttribute('data-tab');
        
        // Deactivate all tabs
        tabs.forEach(t => t.classList.remove('active'));
        panes.forEach(p => p.classList.remove('active'));
        
        // Activate clicked tab
        this.classList.add('active');
        group.querySelector(`.tab-pane[data-tab="${target}"]`).classList.add('active');
      });
    });
  });
}

// Utility function to format dates
function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString('pt-BR');
}

// Utility function to format CNPJs
function formatCNPJ(cnpj) {
  if (!cnpj) return '';
  
  // Remove non-digits
  cnpj = cnpj.replace(/\D/g, '');
  
  // Apply CNPJ mask: XX.XXX.XXX/XXXX-XX
  return cnpj.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
}

// Calculate days remaining until a date
function daysUntil(dateString) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const targetDate = new Date(dateString);
  targetDate.setHours(0, 0, 0, 0);
  
  const diffTime = targetDate - today;
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  return diffDays;
}

// Copy text to clipboard
function copyToClipboard(text) {
  const textarea = document.createElement('textarea');
  textarea.value = text;
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand('copy');
  document.body.removeChild(textarea);
}

// Show notification
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.classList.add('notification', `notification-${type}`);
  notification.textContent = message;
  
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.classList.add('show');
  }, 10);
  
  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => {
      document.body.removeChild(notification);
    }, 300);
  }, 3000);
}
