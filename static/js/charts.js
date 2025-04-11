// Dashboard charts using Chart.js

document.addEventListener('DOMContentLoaded', function() {
    // Certificate Status Chart
    const statusChartElement = document.getElementById('certificate-status-chart');
    
    if (statusChartElement) {
        // Get data from the data attributes
        const validCount = parseInt(statusChartElement.dataset.validCount || 0);
        const warningCount = parseInt(statusChartElement.dataset.warningCount || 0);
        const criticalCount = parseInt(statusChartElement.dataset.criticalCount || 0);
        const expiredCount = parseInt(statusChartElement.dataset.expiredCount || 0);
        
        const ctx = statusChartElement.getContext('2d');
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Válidos', 'Atenção', 'Críticos', 'Vencidos'],
                datasets: [{
                    data: [validCount, warningCount, criticalCount, expiredCount],
                    backgroundColor: [
                        '#10B981', // Green for valid
                        '#F59E0B', // Yellow for warning
                        '#EF4444', // Red for critical
                        '#6B7280'  // Gray for expired
                    ],
                    borderWidth: 1,
                    borderColor: '#F3F4F6'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                legend: {
                    position: 'bottom',
                    labels: {
                        fontFamily: 'Inter',
                        boxWidth: 15,
                        padding: 15
                    }
                },
                tooltips: {
                    callbacks: {
                        label: function(tooltipItem, data) {
                            const dataset = data.datasets[tooltipItem.datasetIndex];
                            const total = dataset.data.reduce((prev, curr) => prev + curr, 0);
                            const value = dataset.data[tooltipItem.index];
                            const percentage = Math.round((value / total) * 100);
                            return `${data.labels[tooltipItem.index]}: ${value} (${percentage}%)`;
                        }
                    }
                },
                cutoutPercentage: 70
            }
        });
    }
    
    // Certificate Expiration Timeline Chart
    const expirationChartElement = document.getElementById('certificate-expiration-chart');
    
    if (expirationChartElement && expirationChartElement.dataset.certificates) {
        // Get certificates data
        const certificates = JSON.parse(expirationChartElement.dataset.certificates);
        
        // Process data for chart - group by month
        const months = {};
        const currentDate = new Date();
        
        // Initialize next 12 months
        for (let i = 0; i < 12; i++) {
            const date = new Date(currentDate);
            date.setMonth(date.getMonth() + i);
            const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
            months[monthKey] = 0;
        }
        
        // Count certificates by expiration month
        certificates.forEach(cert => {
            const expirationDate = new Date(cert.expiration * 1000); // Convert from unix timestamp
            const monthKey = `${expirationDate.getFullYear()}-${String(expirationDate.getMonth() + 1).padStart(2, '0')}`;
            
            if (months[monthKey] !== undefined) {
                months[monthKey]++;
            }
        });
        
        const ctx = expirationChartElement.getContext('2d');
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(months).map(monthKey => {
                    const [year, month] = monthKey.split('-');
                    return `${month}/${year}`;
                }),
                datasets: [{
                    label: 'Certificados a vencer',
                    data: Object.values(months),
                    backgroundColor: '#3B82F6',
                    borderColor: '#2563EB',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    yAxes: [{
                        ticks: {
                            beginAtZero: true,
                            stepSize: 1
                        }
                    }]
                },
                legend: {
                    display: false
                },
                tooltips: {
                    callbacks: {
                        title: function(tooltipItems, data) {
                            return 'Mês: ' + data.labels[tooltipItems[0].index];
                        },
                        label: function(tooltipItem, data) {
                            return 'Certificados: ' + tooltipItem.value;
                        }
                    }
                }
            }
        });
    }
});
