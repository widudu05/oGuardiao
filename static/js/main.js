// Main JavaScript file for O Guardião

document.addEventListener('DOMContentLoaded', function() {
    // Toggle sidebar
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarText = document.querySelectorAll('.sidebar-text');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('sidebar-collapsed');
            sidebar.classList.toggle('sidebar-expanded');
            
            sidebarText.forEach(function(element) {
                element.classList.toggle('hidden');
            });
        });
    }
    
    // Format CNPJ inputs
    const cnpjInputs = document.querySelectorAll('.cnpj-input');
    
    cnpjInputs.forEach(function(input) {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            
            if (value.length > 14) {
                value = value.substring(0, 14);
            }
            
            if (value.length > 12) {
                value = value.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5');
            } else if (value.length > 8) {
                value = value.replace(/^(\d{2})(\d{3})(\d{3})(\d+)$/, '$1.$2.$3/$4');
            } else if (value.length > 5) {
                value = value.replace(/^(\d{2})(\d{3})(\d+)$/, '$1.$2.$3');
            } else if (value.length > 2) {
                value = value.replace(/^(\d{2})(\d+)$/, '$1.$2');
            }
            
            e.target.value = value;
        });
    });
    
    // Format date inputs
    const dateInputs = document.querySelectorAll('.date-input');
    
    dateInputs.forEach(function(input) {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            
            if (value.length > 8) {
                value = value.substring(0, 8);
            }
            
            if (value.length > 4) {
                value = value.replace(/^(\d{2})(\d{2})(\d+)$/, '$1/$2/$3');
            } else if (value.length > 2) {
                value = value.replace(/^(\d{2})(\d+)$/, '$1/$2');
            }
            
            e.target.value = value;
        });
    });
    
    // Flash message auto-hide
    const flashMessages = document.querySelectorAll('.alert');
    
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.classList.add('opacity-0');
            setTimeout(function() {
                message.remove();
            }, 300);
        }, 5000);
    });
    
    // Copy to clipboard function
    const copyButtons = document.querySelectorAll('.copy-btn');
    
    copyButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const text = this.dataset.copyText;
            navigator.clipboard.writeText(text).then(function() {
                // Show success tooltip
                button.setAttribute('title', 'Copiado!');
                button.classList.add('bg-green-100', 'text-green-800');
                button.classList.remove('bg-gray-100', 'text-gray-800');
                
                setTimeout(function() {
                    button.setAttribute('title', 'Copiar');
                    button.classList.remove('bg-green-100', 'text-green-800');
                    button.classList.add('bg-gray-100', 'text-gray-800');
                }, 2000);
            });
        });
    });
    
    // Show password toggle
    const passwordToggles = document.querySelectorAll('.password-toggle');
    
    passwordToggles.forEach(function(toggle) {
        toggle.addEventListener('click', function() {
            const passwordInput = document.getElementById(this.dataset.target);
            
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                toggle.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z" clip-rule="evenodd" /><path d="M12.454 16.697L9.75 13.992a4 4 0 01-3.742-3.741L2.335 6.578A9.98 9.98 0 00.458 10c1.274 4.057 5.065 7 9.542 7 .847 0 1.669-.105 2.454-.303z" /></svg>';
            } else {
                passwordInput.type = 'password';
                toggle.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M10 12a2 2 0 100-4 2 2 0 000 4z" /><path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd" /></svg>';
            }
        });
    });
    
    // Dropdown toggle
    const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
    
    dropdownToggles.forEach(function(toggle) {
        toggle.addEventListener('click', function() {
            const dropdown = document.getElementById(this.dataset.target);
            dropdown.classList.toggle('hidden');
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(event) {
            if (!toggle.contains(event.target)) {
                const dropdown = document.getElementById(toggle.dataset.target);
                if (dropdown && !dropdown.classList.contains('hidden')) {
                    dropdown.classList.add('hidden');
                }
            }
        });
    });
    
    // Modal handling
    const modalToggles = document.querySelectorAll('[data-modal-toggle]');
    
    modalToggles.forEach(function(toggle) {
        toggle.addEventListener('click', function() {
            const modal = document.getElementById(this.dataset.modalToggle);
            modal.classList.toggle('hidden');
        });
    });
    
    // Close modal when clicking on backdrop
    const modals = document.querySelectorAll('.modal');
    
    modals.forEach(function(modal) {
        modal.addEventListener('click', function(event) {
            if (event.target === modal) {
                modal.classList.add('hidden');
            }
        });
    });
});
