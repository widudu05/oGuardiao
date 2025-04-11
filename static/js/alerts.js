// Alerts and notifications handling

document.addEventListener('DOMContentLoaded', function() {
    // Certificate expiration alert display
    function setupExpirationAlerts() {
        const alertsContainer = document.getElementById('alerts-container');
        
        if (!alertsContainer) return;
        
        // Check for certificates data
        if (alertsContainer.dataset.certificates) {
            const certificates = JSON.parse(alertsContainer.dataset.certificates);
            
            // Filter certificates by expiration status
            const critical = certificates.filter(cert => cert.days_remaining <= 5 && cert.days_remaining >= 0);
            const warning = certificates.filter(cert => cert.days_remaining > 5 && cert.days_remaining <= 15);
            const attention = certificates.filter(cert => cert.days_remaining > 15 && cert.days_remaining <= 30);
            
            // Generate alert HTML
            let alertsHTML = '';
            
            if (critical.length > 0) {
                alertsHTML += `
                <div class="alert bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <svg class="h-5 w-5 text-red-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
                            </svg>
                        </div>
                        <div class="ml-3">
                            <p class="text-sm font-medium">
                                <span class="font-bold">${critical.length} certificado(s) em estado crítico!</span> 
                                Vencimento em menos de 5 dias.
                            </p>
                        </div>
                    </div>
                </div>
                `;
            }
            
            if (warning.length > 0) {
                alertsHTML += `
                <div class="alert bg-orange-100 border-l-4 border-orange-500 text-orange-700 p-4 mb-4">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <svg class="h-5 w-5 text-orange-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                            </svg>
                        </div>
                        <div class="ml-3">
                            <p class="text-sm font-medium">
                                <span class="font-bold">${warning.length} certificado(s) em alerta!</span> 
                                Vencimento entre 6 e 15 dias.
                            </p>
                        </div>
                    </div>
                </div>
                `;
            }
            
            if (attention.length > 0) {
                alertsHTML += `
                <div class="alert bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-4">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <svg class="h-5 w-5 text-yellow-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
                            </svg>
                        </div>
                        <div class="ml-3">
                            <p class="text-sm font-medium">
                                <span class="font-bold">${attention.length} certificado(s) em atenção!</span> 
                                Vencimento entre 16 e 30 dias.
                            </p>
                        </div>
                    </div>
                </div>
                `;
            }
            
            if (alertsHTML === '') {
                alertsHTML = `
                <div class="alert bg-green-100 border-l-4 border-green-500 text-green-700 p-4 mb-4">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <svg class="h-5 w-5 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                            </svg>
                        </div>
                        <div class="ml-3">
                            <p class="text-sm font-medium">
                                Todos os certificados estão válidos e sem vencimento próximo.
                            </p>
                        </div>
                    </div>
                </div>
                `;
            }
            
            alertsContainer.innerHTML = alertsHTML;
        }
    }
    
    // Setup alerts when page loads
    setupExpirationAlerts();
    
    // Setup notification badges
    function updateNotificationBadges() {
        const alertBadge = document.getElementById('alert-badge');
        
        if (alertBadge && alertBadge.dataset.count) {
            const count = parseInt(alertBadge.dataset.count);
            
            if (count > 0) {
                alertBadge.textContent = count > 99 ? '99+' : count;
                alertBadge.classList.remove('hidden');
            } else {
                alertBadge.classList.add('hidden');
            }
        }
    }
    
    // Update notification badges
    updateNotificationBadges();
    
    // Notification bell click event
    const notificationBell = document.getElementById('notification-bell');
    const notificationDropdown = document.getElementById('notification-dropdown');
    
    if (notificationBell && notificationDropdown) {
        notificationBell.addEventListener('click', function(e) {
            e.preventDefault();
            notificationDropdown.classList.toggle('hidden');
            
            // Mark notifications as read when opened
            if (!notificationDropdown.classList.contains('hidden')) {
                const alertBadge = document.getElementById('alert-badge');
                if (alertBadge) {
                    alertBadge.classList.add('hidden');
                    alertBadge.dataset.count = '0';
                }
                
                // Send AJAX request to mark notifications as read
                // For MVP, we'll just hide the badge
            }
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!notificationBell.contains(e.target) && !notificationDropdown.contains(e.target)) {
                notificationDropdown.classList.add('hidden');
            }
        });
    }
});
