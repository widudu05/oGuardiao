// Companies.js - Handles company-related functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize company filters
    initCompanyFilters();
    
    // Initialize group selection
    initGroupSelection();
    
    // Initialize CNPJ validation
    initCNPJValidation();
    
    // Initialize company cards
    initCompanyCards();
});

// Handle company filters
function initCompanyFilters() {
    const filterForm = document.querySelector('#company-filters');
    
    if (filterForm) {
        // Auto-submit when select filters change
        const selectFilters = filterForm.querySelectorAll('select');
        selectFilters.forEach(select => {
            select.addEventListener('change', function() {
                filterForm.submit();
            });
        });
        
        // Handle search input (submit after short delay)
        const searchInput = filterForm.querySelector('input[type="search"]');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', function() {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    filterForm.submit();
                }, 500);
            });
        }
        
        // Handle reset filters button
        const resetButton = filterForm.querySelector('.reset-filters');
        if (resetButton) {
            resetButton.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Reset all form elements
                const selects = filterForm.querySelectorAll('select');
                selects.forEach(select => {
                    select.value = '';
                });
                
                const inputs = filterForm.querySelectorAll('input:not([type="submit"])');
                inputs.forEach(input => {
                    input.value = '';
                });
                
                // Submit the form to reset filters
                filterForm.submit();
            });
        }
    }
}

// Handle group selection in company form
function initGroupSelection() {
    const groupSelector = document.querySelector('#group_id');
    const createGroupButton = document.querySelector('#create-new-group');
    const newGroupForm = document.querySelector('#new-group-form');
    
    if (groupSelector && createGroupButton && newGroupForm) {
        createGroupButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Toggle visibility of new group form
            if (newGroupForm.style.display === 'none' || !newGroupForm.style.display) {
                newGroupForm.style.display = 'block';
                createGroupButton.textContent = 'Cancelar';
                createGroupButton.classList.remove('btn-primary');
                createGroupButton.classList.add('btn-secondary');
            } else {
                newGroupForm.style.display = 'none';
                createGroupButton.textContent = 'Criar Novo Grupo';
                createGroupButton.classList.remove('btn-secondary');
                createGroupButton.classList.add('btn-primary');
            }
        });
        
        // Handle group creation
        const createGroupSubmit = newGroupForm.querySelector('#submit-new-group');
        if (createGroupSubmit) {
            createGroupSubmit.addEventListener('click', function(e) {
                e.preventDefault();
                
                const groupName = newGroupForm.querySelector('#new_group_name').value;
                const groupDescription = newGroupForm.querySelector('#new_group_description').value;
                
                if (!groupName) {
                    alert('Por favor, informe o nome do grupo.');
                    return;
                }
                
                // Create group via AJAX
                fetch('/api/groups/create', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({
                        name: groupName,
                        description: groupDescription
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Add new group to dropdown
                        const option = document.createElement('option');
                        option.value = data.group_id;
                        option.textContent = groupName;
                        groupSelector.appendChild(option);
                        
                        // Select the new group
                        groupSelector.value = data.group_id;
                        
                        // Hide new group form
                        newGroupForm.style.display = 'none';
                        createGroupButton.textContent = 'Criar Novo Grupo';
                        createGroupButton.classList.remove('btn-secondary');
                        createGroupButton.classList.add('btn-primary');
                        
                        // Reset form fields
                        newGroupForm.querySelector('#new_group_name').value = '';
                        newGroupForm.querySelector('#new_group_description').value = '';
                        
                        showNotification('Grupo criado com sucesso!', 'success');
                    } else {
                        showNotification(data.message || 'Erro ao criar grupo.', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error creating group:', error);
                    showNotification('Erro ao criar grupo. Por favor, tente novamente.', 'error');
                });
            });
        }
    }
}

// Helper function to get CSRF token from meta tag
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

// CNPJ validation
function initCNPJValidation() {
    const cnpjInput = document.querySelector('input[name="cnpj"]');
    
    if (cnpjInput) {
        cnpjInput.addEventListener('blur', function() {
            const cnpj = this.value.replace(/[^\d]/g, '');
            
            if (cnpj.length !== 14) {
                // Don't show error if empty (other validators will handle this)
                if (cnpj.length === 0) return;
                
                showInputError(this, 'CNPJ deve conter 14 dígitos.');
                return;
            }
            
            // Check if all digits are the same
            if (/^(\d)\1+$/.test(cnpj)) {
                showInputError(this, 'CNPJ inválido.');
                return;
            }
            
            // Validate CNPJ algorithm
            let size = cnpj.length - 2;
            let numbers = cnpj.substring(0, size);
            const digits = cnpj.substring(size);
            let sum = 0;
            let pos = size - 7;
            
            for (let i = size; i >= 1; i--) {
                sum += numbers.charAt(size - i) * pos--;
                if (pos < 2) pos = 9;
            }
            
            let result = sum % 11 < 2 ? 0 : 11 - sum % 11;
            if (result != digits.charAt(0)) {
                showInputError(this, 'CNPJ inválido.');
                return;
            }
            
            size = size + 1;
            numbers = cnpj.substring(0, size);
            sum = 0;
            pos = size - 7;
            
            for (let i = size; i >= 1; i--) {
                sum += numbers.charAt(size - i) * pos--;
                if (pos < 2) pos = 9;
            }
            
            result = sum % 11 < 2 ? 0 : 11 - sum % 11;
            if (result != digits.charAt(1)) {
                showInputError(this, 'CNPJ inválido.');
                return;
            }
            
            // If we got here, the CNPJ is valid
            clearInputError(this);
        });
    }
}

// Show input validation error
function showInputError(inputElement, message) {
    // Clear any existing error first
    clearInputError(inputElement);
    
    // Create error message element
    const errorElement = document.createElement('div');
    errorElement.className = 'error-message';
    errorElement.textContent = message;
    errorElement.style.color = '#EF4444';
    errorElement.style.fontSize = '0.875rem';
    errorElement.style.marginTop = '0.25rem';
    
    // Add error class to input
    inputElement.classList.add('is-invalid');
    
    // Add error message after input
    inputElement.parentNode.appendChild(errorElement);
}

// Clear input validation error
function clearInputError(inputElement) {
    // Remove error class from input
    inputElement.classList.remove('is-invalid');
    
    // Remove any existing error message
    const errorElement = inputElement.parentNode.querySelector('.error-message');
    if (errorElement) {
        errorElement.remove();
    }
}

// Initialize company cards (if using card view)
function initCompanyCards() {
    const companyCards = document.querySelectorAll('.company-card');
    
    companyCards.forEach(card => {
        // Add click handler to make entire card clickable except for buttons
        card.addEventListener('click', function(e) {
            // Don't trigger if clicking on a button or link
            if (e.target.closest('button') || e.target.closest('a') || e.target.tagName === 'BUTTON' || e.target.tagName === 'A') {
                return;
            }
            
            // Get the detail URL from card's data attribute
            const detailUrl = this.getAttribute('data-url');
            if (detailUrl) {
                window.location.href = detailUrl;
            }
        });
    });
}

// Delete company with confirmation
function deleteCompany(companyId, companyName) {
    if (confirm(`Tem certeza que deseja excluir a empresa "${companyName}"? Esta ação não pode ser desfeita.`)) {
        document.getElementById(`delete-company-${companyId}`).submit();
    }
}

// Count certificates by company
function loadCertificateCountByCompany() {
    const companyCards = document.querySelectorAll('.company-card');
    const companyIds = Array.from(companyCards).map(card => card.getAttribute('data-id'));
    
    if (companyIds.length === 0) return;
    
    // Fetch certificate counts via AJAX
    fetch('/api/companies/certificate-counts', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            company_ids: companyIds
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.counts) {
            companyCards.forEach(card => {
                const companyId = card.getAttribute('data-id');
                const countElement = card.querySelector('.certificate-count');
                
                if (countElement && data.counts[companyId] !== undefined) {
                    countElement.textContent = data.counts[companyId];
                    
                    // Highlight if certificates are expiring
                    if (data.expiring && data.expiring[companyId] > 0) {
                        const expiringElement = card.querySelector('.expiring-count');
                        if (expiringElement) {
                            expiringElement.textContent = data.expiring[companyId];
                            expiringElement.style.display = 'inline-block';
                        }
                    }
                }
            });
        }
    })
    .catch(error => {
        console.error('Error fetching certificate counts:', error);
    });
}
