// Certificates specific JavaScript

document.addEventListener('DOMContentLoaded', function() {
  // Initialize certificate expiry status indicators
  initCertificateExpiryStatus();
  
  // Initialize certificate password handling
  initCertificatePasswordHandling();
  
  // Initialize certificate filters
  initCertificateFilters();
  
  // Initialize certificate sorting
  initCertificateSorting();
  
  // Certificate file upload validation
  initCertificateFileValidation();
});

// Set certificate card status based on expiry date
function initCertificateExpiryStatus() {
  const certificateCards = document.querySelectorAll('.certificate-card');
  
  certificateCards.forEach(card => {
    const expiryDate = new Date(card.getAttribute('data-expiry'));
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const daysLeft = Math.ceil((expiryDate - today) / (1000 * 60 * 60 * 24));
    
    let statusClass = '';
    let statusText = '';
    
    if (daysLeft < 0) {
      statusClass = 'certificate-expired';
      statusText = 'Expirado';
    } else if (daysLeft <= 30) {
      statusClass = 'certificate-expiring';
      statusText = `Expira em ${daysLeft} dias`;
    } else {
      statusClass = 'certificate-valid';
      statusText = `Válido por mais ${daysLeft} dias`;
    }
    
    card.classList.add(statusClass);
    
    const statusElement = card.querySelector('.certificate-status');
    if (statusElement) {
      statusElement.textContent = statusText;
      
      if (daysLeft < 0) {
        statusElement.classList.add('badge-danger');
      } else if (daysLeft <= 30) {
        statusElement.classList.add('badge-warning');
      } else {
        statusElement.classList.add('badge-success');
      }
    }
  });
}

// Handle certificate password visibility and copying
function initCertificatePasswordHandling() {
  const passwordElements = document.querySelectorAll('.certificate-password');
  
  passwordElements.forEach(element => {
    const toggleButton = element.querySelector('.toggle-password');
    const copyButton = element.querySelector('.copy-password');
    const passwordField = element.querySelector('.password-value');
    
    if (toggleButton && passwordField) {
      toggleButton.addEventListener('click', function() {
        if (passwordField.type === 'password') {
          passwordField.type = 'text';
          toggleButton.innerHTML = '<i class="fas fa-eye-slash"></i>';
        } else {
          passwordField.type = 'password';
          toggleButton.innerHTML = '<i class="fas fa-eye"></i>';
        }
      });
    }
    
    if (copyButton && passwordField) {
      copyButton.addEventListener('click', function() {
        passwordField.type = 'text';
        passwordField.select();
        document.execCommand('copy');
        passwordField.type = 'password';
        
        showNotification('Senha copiada para a área de transferência', 'success');
      });
    }
  });
}

// Certificate filtering
function initCertificateFilters() {
  const filterForm = document.querySelector('#certificate-filters');
  
  if (filterForm) {
    // Auto-submit when select filters change
    const selectFilters = filterForm.querySelectorAll('select');
    selectFilters.forEach(select => {
      select.addEventListener('change', function() {
        filterForm.submit();
      });
    });
    
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

// Sortable certificate table
function initCertificateSorting() {
  const table = document.querySelector('.sortable-table');
  
  if (table) {
    const headers = table.querySelectorAll('th.sortable');
    
    headers.forEach(header => {
      header.addEventListener('click', function() {
        const sortBy = this.getAttribute('data-sort');
        const sortOrder = this.getAttribute('data-order') === 'asc' ? 'desc' : 'asc';
        
        // Update URL with sort parameters
        const url = new URL(window.location.href);
        url.searchParams.set('sort_by', sortBy);
        url.searchParams.set('sort_order', sortOrder);
        
        window.location.href = url.toString();
      });
    });
  }
}

// Certificate file upload validation
function initCertificateFileValidation() {
  const fileInput = document.querySelector('#certificate_file');
  
  if (fileInput) {
    fileInput.addEventListener('change', function() {
      const file = this.files[0];
      const errorElement = document.querySelector('#file-error');
      
      if (!file) return;
      
      // Check file extension
      const validExtensions = ['pfx', 'p12'];
      const fileExtension = file.name.split('.').pop().toLowerCase();
      
      if (!validExtensions.includes(fileExtension)) {
        this.value = ''; // Clear file input
        if (errorElement) {
          errorElement.textContent = 'Formato de arquivo inválido. Apenas arquivos .pfx ou .p12 são permitidos.';
          errorElement.style.display = 'block';
        }
        return;
      }
      
      // Check file size (max 5MB)
      const maxSize = 5 * 1024 * 1024; // 5MB in bytes
      
      if (file.size > maxSize) {
        this.value = ''; // Clear file input
        if (errorElement) {
          errorElement.textContent = 'O arquivo é muito grande. O tamanho máximo permitido é 5MB.';
          errorElement.style.display = 'block';
        }
        return;
      }
      
      // Clear error message if all is well
      if (errorElement) {
        errorElement.style.display = 'none';
      }
      
      // Show selected filename
      const fileNameElement = document.querySelector('#selected-filename');
      if (fileNameElement) {
        fileNameElement.textContent = file.name;
        fileNameElement.style.display = 'block';
      }
    });
  }
}

// Download certificate
function downloadCertificate(certificateId, certificateName) {
  // In a real implementation, this would make an AJAX request to a route that:
  // 1. Checks permissions
  // 2. Decrypts the certificate from S3
  // 3. Returns it as a download
  const downloadUrl = `/api/certificates/${certificateId}/download`;
  
  fetch(downloadUrl)
    .then(response => {
      if (!response.ok) {
        throw new Error('Erro ao baixar o certificado');
      }
      return response.blob();
    })
    .then(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = certificateName + '.pfx';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    })
    .catch(error => {
      console.error('Download error:', error);
      showNotification('Erro ao baixar o certificado. Por favor, tente novamente.', 'error');
    });
}

// Request certificate password
function requestCertificatePassword(certificateId) {
  // In a real implementation, this would make an AJAX request to a route that:
  // 1. Checks permissions
  // 2. Decrypts the certificate password
  // 3. Returns it or shows it in a modal
  const passwordUrl = `/api/certificates/${certificateId}/password`;
  
  fetch(passwordUrl)
    .then(response => {
      if (!response.ok) {
        throw new Error('Erro ao recuperar a senha');
      }
      return response.json();
    })
    .then(data => {
      // Show password in a modal or other secure way
      const passwordModal = document.getElementById('password-modal');
      const passwordField = document.getElementById('certificate-password');
      
      if (passwordModal && passwordField) {
        passwordField.value = data.password;
        passwordModal.style.display = 'block';
      }
    })
    .catch(error => {
      console.error('Password fetch error:', error);
      showNotification('Erro ao recuperar a senha do certificado. Por favor, tente novamente.', 'error');
    });
}
