// Charts.js - Handles chart rendering for the dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all charts on the page
    initCertificateTypeChart();
    initExpiringCertificatesChart();
    initCertificateTimelineChart();
});

// Certificate type distribution chart (pie/donut)
function initCertificateTypeChart() {
    const chartCanvas = document.getElementById('certificate-types-chart');
    if (!chartCanvas) return;

    // Get data from data attributes
    const ecnpjCount = parseInt(chartCanvas.getAttribute('data-ecnpj') || 0);
    const ecpfCount = parseInt(chartCanvas.getAttribute('data-ecpf') || 0);

    new Chart(chartCanvas, {
        type: 'doughnut',
        data: {
            labels: ['e-CNPJ', 'e-CPF'],
            datasets: [{
                data: [ecnpjCount, ecpfCount],
                backgroundColor: ['#3B82F6', '#1E3A8A'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        font: {
                            family: 'Inter, sans-serif',
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Expiring certificates chart (bar)
function initExpiringCertificatesChart() {
    const chartCanvas = document.getElementById('expiring-certificates-chart');
    if (!chartCanvas) return;

    // Get data from data attributes
    const expiring30d = parseInt(chartCanvas.getAttribute('data-expiring-30d') || 0);
    const expiring60d = parseInt(chartCanvas.getAttribute('data-expiring-60d') || 0);
    const expiring90d = parseInt(chartCanvas.getAttribute('data-expiring-90d') || 0);

    new Chart(chartCanvas, {
        type: 'bar',
        data: {
            labels: ['30 dias', '60 dias', '90 dias'],
            datasets: [{
                label: 'Certificados expirando',
                data: [expiring30d, expiring60d, expiring90d],
                backgroundColor: [
                    '#EF4444', // Red for more urgent (30 days)
                    '#F59E0B', // Amber for medium urgent (60 days)
                    '#10B981'  // Green for less urgent (90 days)
                ],
                borderWidth: 0,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        title: function(tooltipItems) {
                            return `Expirando em ${tooltipItems[0].label}`;
                        },
                        label: function(context) {
                            return `${context.raw} certificado(s)`;
                        }
                    }
                }
            }
        }
    });
}

// Certificate timeline chart (line)
function initCertificateTimelineChart() {
    const chartCanvas = document.getElementById('certificate-timeline-chart');
    if (!chartCanvas) return;

    // Check if we have certificate timeline data
    // This would typically be provided by the server, but we'll build a mock version here
    // In production, this would be real data from the backend
    const currentYear = new Date().getFullYear();
    const months = [
        'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
        'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'
    ];

    // Get data from data attributes if available
    // Otherwise use empty arrays for demo
    let validData = [];
    let expiringData = [];
    let expiredData = [];

    try {
        validData = JSON.parse(chartCanvas.getAttribute('data-valid') || '[]');
        expiringData = JSON.parse(chartCanvas.getAttribute('data-expiring') || '[]');
        expiredData = JSON.parse(chartCanvas.getAttribute('data-expired') || '[]');
    } catch (e) {
        console.error('Error parsing chart data:', e);
        
        // If we can't parse the data, we'll just use empty arrays
        validData = Array(12).fill(0);
        expiringData = Array(12).fill(0);
        expiredData = Array(12).fill(0);
    }

    // If we don't have data (all arrays are empty or all zeros), 
    // display a message instead of an empty chart
    if (validData.length === 0 && expiringData.length === 0 && expiredData.length === 0) {
        const ctx = chartCanvas.getContext('2d');
        ctx.font = '14px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillStyle = '#6B7280';
        ctx.fillText('Sem dados suficientes para exibir o gráfico', chartCanvas.width / 2, chartCanvas.height / 2);
        return;
    }

    new Chart(chartCanvas, {
        type: 'line',
        data: {
            labels: months,
            datasets: [
                {
                    label: 'Válidos',
                    data: validData,
                    borderColor: '#10B981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Expirando',
                    data: expiringData,
                    borderColor: '#F59E0B',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Expirados',
                    data: expiredData,
                    borderColor: '#EF4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 20,
                        font: {
                            family: 'Inter, sans-serif',
                            size: 12
                        }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

// Export CSV from chart data
function exportChartData(chartId, filename) {
    const chart = Chart.getChart(chartId);
    if (!chart) return;

    const labels = chart.data.labels;
    const datasets = chart.data.datasets;
    
    let csvContent = 'data:text/csv;charset=utf-8,';
    
    // Header row with dataset labels
    csvContent += 'Period,' + datasets.map(ds => ds.label).join(',') + '\r\n';
    
    // Data rows
    labels.forEach((label, i) => {
        csvContent += label + ',';
        datasets.forEach((dataset, j) => {
            csvContent += dataset.data[i];
            if (j < datasets.length - 1) csvContent += ',';
        });
        csvContent += '\r\n';
    });
    
    // Create download link
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
