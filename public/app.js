// TopClanker App Logic
// Modular, composable, no code smells

class RankingsApp {
    constructor() {
        this.data = null;
        this.currentFilter = 'all';
        this.currentPage = 1;
        this.itemsPerPage = 10;
        this.init();
    }

    async init() {
        await this.loadData();
        this.setupEventListeners();
        this.render();
    }

    async loadData() {
        try {
            const response = await fetch('data.json');
            this.data = await response.json();
        } catch (error) {
            console.error('Error loading data:', error);
            this.showError('Failed to load rankings data');
        }
    }

    setupEventListeners() {
        const filterButtons = document.querySelectorAll('.filter-btn');
        filterButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.handleFilterChange(e.target.dataset.category);
            });
        });
    }

    handleFilterChange(category) {
        this.currentFilter = category;
        this.currentPage = 1;
        
        // Update active button
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        event.target.classList.add('active');
        
        this.render();
    }

    getFilteredAgents() {
        if (!this.data || !this.data.agents) return [];
        
        if (this.currentFilter === 'all') {
            return this.data.agents;
        }
        
        return this.data.agents.filter(agent => 
            agent.category === this.currentFilter
        );
    }

    getTotalPages() {
        const agents = this.getFilteredAgents();
        return Math.ceil(agents.length / this.itemsPerPage);
    }

    getPaginatedAgents() {
        const agents = this.getFilteredAgents();
        const start = (this.currentPage - 1) * this.itemsPerPage;
        const end = start + this.itemsPerPage;
        return agents.slice(start, end);
    }

    render() {
        this.renderLastUpdated();
        this.renderTable();
        this.renderCards();
        this.renderPagination();
    }

    renderLastUpdated() {
        const element = document.getElementById('lastUpdated');
        if (element && this.data) {
            element.textContent = new Date(this.data.lastUpdated).toLocaleDateString();
        }
    }

    renderTable() {
        const tbody = document.getElementById('rankingsTableBody');
        if (!tbody) return;

        const agents = this.getPaginatedAgents();
        
        if (agents.length === 0) {
            tbody.innerHTML = this.getEmptyState();
            return;
        }

        tbody.innerHTML = agents.map(agent => this.createTableRow(agent)).join('');
    }

    renderCards() {
        const container = document.getElementById('rankingsCards');
        if (!container) return;

        const agents = this.getPaginatedAgents();
        
        if (agents.length === 0) {
            container.innerHTML = this.getEmptyState();
            return;
        }

        container.innerHTML = agents.map(agent => this.createCard(agent)).join('');
    }

    createCard(agent) {
        // Build benchmark chips if available
        let benchmarksHtml = '';
        if (agent.benchmarks) {
            const bm = agent.benchmarks;
            const chips = [];
            if (bm.swebench) chips.push(`<span class="text-xs bg-gray-100 px-2 py-1 rounded">SWE: ${bm.swebench}%</span>`);
            if (bm.mmlu) chips.push(`<span class="text-xs bg-gray-100 px-2 py-1 rounded">MMLU: ${bm.mmlu}%</span>`);
            if (bm.humaneval) chips.push(`<span class="text-xs bg-gray-100 px-2 py-1 rounded">HumanEval: ${bm.humaneval}%</span>`);
            if (bm.gsm8k) chips.push(`<span class="text-xs bg-gray-100 px-2 py-1 rounded">GSM8K: ${bm.gsm8k}%</span>`);
            if (chips.length > 0) {
                benchmarksHtml = `<div class="flex flex-wrap gap-1 mt-2">${chips.join('')}</div>`;
            }
        }

        const scoreDisplay = agent.benchmarkScore 
            ? `<div class="text-2xl font-bold text-blue-600">${agent.benchmarkScore}</div><div class="text-xs text-gray-500">Score</div>`
            : `<div class="text-2xl font-bold text-blue-600">${agent.score || 'N/A'}</div>`;

        return `
            <div class="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
                <div class="flex items-start justify-between mb-2">
                    <div class="flex items-center gap-2">
                        <span class="text-lg font-bold text-gray-400">#${agent.rank}</span>
                        <span class="font-bold text-gray-900">${agent.name}</span>
                    </div>
                    ${agent.url ? `<a href="${agent.url}" target="_blank" rel="noopener" class="text-blue-600 hover:text-blue-800 text-sm font-medium">Visit →</a>` : ''}
                </div>
                ${agent.description ? `<p class="text-sm text-gray-600 mb-3">${agent.description}</p>` : ''}
                <div class="flex flex-wrap gap-2 mb-3">
                    ${this.createCategoryBadge(agent.category)}
                    ${this.createTypeBadge(agent.type)}
                </div>
                ${benchmarksHtml}
                <div class="flex items-center justify-between pt-3 mt-3 border-t border-gray-100">
                    <div class="flex items-center gap-2">
                        <span class="text-sm text-gray-500">Privacy:</span>
                        ${this.createPrivacyRating(agent.privacy)}
                    </div>
                    <div class="text-right">
                        ${scoreDisplay}
                    </div>
                </div>
            </div>
        `;
    }

    renderPagination() {
        const paginationContainer = document.getElementById('pagination');
        if (!paginationContainer) return;

        const totalPages = this.getTotalPages();
        
        if (totalPages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }

        let paginationHTML = '<div class="flex items-center justify-center gap-2 mt-6">';
        
        // Previous button
        if (this.currentPage > 1) {
            paginationHTML += `<button onclick="app.goToPage(${this.currentPage - 1})" class="px-4 py-2 rounded-lg bg-gray-200 hover:bg-gray-300 text-gray-700">← Previous</button>`;
        }
        
        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= this.currentPage - 1 && i <= this.currentPage + 1)) {
                if (i === this.currentPage) {
                    paginationHTML += `<button class="px-4 py-2 rounded-lg bg-blue-600 text-white">${i}</button>`;
                } else {
                    paginationHTML += `<button onclick="app.goToPage(${i})" class="px-4 py-2 rounded-lg bg-gray-200 hover:bg-gray-300 text-gray-700">${i}</button>`;
                }
            } else if (i === this.currentPage - 2 || i === this.currentPage + 2) {
                paginationHTML += `<span class="px-2 text-gray-500">...</span>`;
            }
        }
        
        // Next button
        if (this.currentPage < totalPages) {
            paginationHTML += `<button onclick="app.goToPage(${this.currentPage + 1})" class="px-4 py-2 rounded-lg bg-gray-200 hover:bg-gray-300 text-gray-700">Next →</button>`;
        }
        
        paginationHTML += '</div>';
        
        // Add info
        const agents = this.getFilteredAgents();
        const start = (this.currentPage - 1) * this.itemsPerPage + 1;
        const end = Math.min(this.currentPage * this.itemsPerPage, agents.length);
        paginationHTML += `<p class="text-center text-gray-500 text-sm mt-2">Showing ${start}-${end} of ${agents.length} models</p>`;
        
        paginationContainer.innerHTML = paginationHTML;
    }

    goToPage(page) {
        this.currentPage = page;
        this.render();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    createTableRow(agent) {
        const benchmarkScoreDisplay = agent.benchmarkScore 
            ? `<div class="text-lg font-semibold text-gray-900">${agent.benchmarkScore}</div>
               <div class="text-xs text-gray-500">Benchmark</div>`
            : `<div class="text-lg font-semibold text-gray-900">${agent.score || 'N/A'}</div>`;

        return `
            <tr>
                <td class="px-6 py-4 whitespace-nowrap">
                    ${this.createRankBadge(agent.rank)}
                </td>
                <td class="px-6 py-4">
                    <div class="font-medium text-gray-900">${agent.name}</div>
                    ${agent.description ? `<div class="text-sm text-gray-500">${agent.description}</div>` : ''}
                    ${agent.benchmarks ? this.createBenchmarkTooltip(agent.benchmarks) : ''}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    ${this.createCategoryBadge(agent.category)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    ${this.createTypeBadge(agent.type)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    ${this.createPrivacyRating(agent.privacy)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    ${benchmarkScoreDisplay}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <a href="${agent.link}" target="_blank" rel="noopener noreferrer" class="external-link">
                        Visit →
                    </a>
                </td>
            </tr>
        `;
    }

    createRankBadge(rank) {
        let rankClass = 'rank-other';
        if (rank === 1) rankClass = 'rank-1';
        else if (rank === 2) rankClass = 'rank-2';
        else if (rank === 3) rankClass = 'rank-3';
        
        return `<span class="rank-badge ${rankClass}">${rank}</span>`;
    }

    createBenchmarkTooltip(benchmarks) {
        const benchmarkList = Object.entries(benchmarks)
            .map(([key, value]) => `${key.toUpperCase()}: ${value}${typeof value === 'number' && value < 100 ? '%' : ''}`)
            .join(' | ');
        
        return `<div class="text-xs text-gray-400 mt-1">${benchmarkList}</div>`;
    }

    createCategoryBadge(category) {
        const categoryNames = {
            'reasoning': 'Reasoning',
            'math': 'Math',
            'research': 'Research',
            'learning': 'Learning'
        };
        
        return `<span class="category-badge ${category}">${categoryNames[category] || category}</span>`;
    }

    createTypeBadge(type) {
        if (type === 'open-source') {
            return `
                <span class="type-icon open-source">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10 2a8 8 0 100 16 8 8 0 000-16zm1 11H9v-2h2v2zm0-4H9V5h2v4z"/>
                    </svg>
                    Open Source
                </span>
            `;
        } else {
            return `
                <span class="type-icon closed">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd"/>
                    </svg>
                    Closed
                </span>
            `;
        }
    }

    createPrivacyRating(privacy) {
        const ratings = {
            'high': { color: 'privacy-high', label: 'High' },
            'medium': { color: 'privacy-medium', label: 'Medium' },
            'low': { color: 'privacy-low', label: 'Low' }
        };
        
        const rating = ratings[privacy] || ratings.medium;
        
        return `
            <div class="privacy-rating">
                <span class="privacy-dot ${rating.color}"></span>
                <span class="text-sm text-gray-600">${rating.label}</span>
            </div>
        `;
    }

    getEmptyState() {
        return `
            <tr>
                <td colspan="7" class="px-6 py-12 text-center text-gray-500">
                    No agents found for this category.
                </td>
            </tr>
        `;
    }

    showError(message) {
        const tbody = document.getElementById('rankingsTableBody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="px-6 py-12 text-center text-red-600">
                        ${message}
                    </td>
                </tr>
            `;
        }
    }
}

// Initialize app when DOM is ready
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new RankingsApp();
});

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});