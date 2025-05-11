
document.addEventListener('DOMContentLoaded', function() {
    try {
        // Parse data safely
        const normal = parseInt('{{ normal_count|default:"0" }}') || 0;
        const vip = parseInt('{{ vip_count|default:"0" }}') || 0;
        const vvip = parseInt('{{ vvip_count|default:"0" }}') || 0;
        const eventData = JSON.parse('{{ event_revenue_json|escapejs }}' || '[]');

        console.log('Chart data loaded:', {
            tickets: {normal, vip, vvip},
            events: eventData
        });

        // 1. Ticket Type Chart
        const typeCtx = document.getElementById('ticketTypeChart');
        if (typeCtx) {
            new Chart(typeCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Normal', 'VIP', 'VVIP'],
                    datasets: [{
                        data: [normal, vip, vvip],
                        backgroundColor: [
                            'rgba(40, 167, 69, 0.8)',
                            'rgba(0, 123, 255, 0.8)',
                            'rgba(255, 193, 7, 0.8)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }

        // 2. Revenue Chart
        const revCtx = document.getElementById('revenueChart');
        if (revCtx && eventData.length > 0) {
            new Chart(revCtx, {
                type: 'bar',
                data: {
                    labels: eventData.map(e => e.name),
                    datasets: [{
                        label: 'Revenue (GHS)',
                        data: eventData.map(e => e.revenue),
                        backgroundColor: 'rgba(40, 167, 69, 0.6)',
                        borderColor: 'rgba(40, 167, 69, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return 'GHS ' + value;
                                }
                            }
                        },
                        x: {
                            ticks: {
                                autoSkip: false,
                                maxRotation: 45,
                                minRotation: 45
                            }
                        }
                    }
                }
            });
        }

    } catch (error) {
        console.error('Chart initialization error:', error);
        document.getElementById('errorMessage').textContent = 
            'Failed to load charts: ' + error.message;
        document.getElementById('chartError').classList.remove('d-none');
    }
});
