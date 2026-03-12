// TopClanker App Logic
// Modular, composable, no code smells

class RankingsApp {
    constructor() {
        console.log('[TopClanker] Initializing app...');
        this.data = null;
        this.currentFilter = 'all';
        this.currentLocalFilter = 'all';
        this.currentVramFilter = 'all';  // all, 8gb, 12gb, 16gb, 24gb, 32gb, api
        this.currentAppleFilter = 'all'; // all, 8gb, 16gb, 24gb, 32gb
        this.currentPage = 1;
        this.itemsPerPage = 10;
        
        // Local models that run on 8GB VRAM or less
        this.localModels = [
            'Qwen 3 4B', 'Qwen 2.5 4B', 'Qwen 2.5 Ultra',
            'Mistral 7B', 'Mistral Large 2', 'Mistral Small',
            'Phi-4 Mini', 'Phi-3 Mini', 'Phi-4',
            'Llama 3.2 3B', 'Llama 3.2 1B', 'Llama 3.3 70B', 'Llama 3 8B', 'Llama 4 Scout',
            'DeepSeek Coder 6.7B', 'DeepSeek Coder 7B', 'DeepSeek V3', 'DeepSeek R1',
            'Gemma 3 4B', 'Gemma 2 9B', 'Gemma 2B',
            'Command R7B', 'Command R',
            'Yi-Large', 'Yi-6B',
            'Mixtral 8x7B', 'Mixtral 8x22B',
            'Mathstral 7B',
            'Codestral 7B'
        ];
        
        this.init();
    }

    async init() {
        await this.loadData();
        await this.loadBlogPosts();
        await this.loadRecentBlogPosts();
        this.setupEventListeners();
        this.render();
    }

    async loadBlogPosts() {
        console.log('[TopClanker] Loading blog posts...');
        const container = document.getElementById('blog-posts');
        if (!container) {
            console.error('[TopClanker] Blog container not found');
            return;
        }
        
        try {
            console.log('[TopClanker] Fetching blog-index.json...');
            const response = await fetch('/blog/all-posts-2026.json?1772679399');
            console.log('[TopClanker] Response status:', response.status);
            const posts = await response.json();
            console.log('[TopClanker] Loaded posts:', posts.length);
            
            // Sort by date descending and take latest 3
            const latestPosts = posts
                .sort((a, b) => new Date(b.date) - new Date(a.date))
                .slice(0, 3);
            
            if (latestPosts.length === 0) {
                container.innerHTML = '<div class="text-center py-8 text-gray-500">No articles yet</div>';
                return;
            }
            
            const months = ['January', 'February', 'March', 'April', 'May', 'June', 
                           'July', 'August', 'September', 'October', 'November', 'December'];
            
            container.innerHTML = latestPosts.map(post => {
                const date = new Date(post.date + 'T00:00:00');
                const formattedDate = `${months[date.getMonth()]} ${date.getDate()}, ${date.getFullYear()}`;
                const shortTitle = post.title.length > 60 ? post.title.substring(0, 60) + '...' : post.title;
                
                return `
                    <article class="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
                        <p class="text-sm text-gray-500 mb-2">${formattedDate}</p>
                        <h4 class="text-xl font-bold mb-2">
                            <a href="/blog/${post.file}" class="text-gray-900 hover:text-blue-600">
                                ${shortTitle}
                            </a>
                        </h4>
                        <a href="/blog/${post.file}" class="text-blue-600 hover:underline text-sm font-medium">
                            Read more →
                        </a>
                    </article>
                `;
            }).join('');
        } catch (error) {
            console.error('Error loading blog posts:', error);
            container.innerHTML = '<div class="text-center py-8 text-gray-500">Unable to load articles</div>';
        }
    }

    async loadRecentBlogPosts() {
        console.log('[TopClanker] Loading recent blog posts...');
        const container = document.getElementById('recent-blog-posts');
        if (!container) {
            console.error('[TopClanker] Recent blog container not found');
            return;
        }
        
        try {
            const response = await fetch('/blog/all-posts-2026.json?1772679399');
            const posts = await response.json();
            
            // Sort by date descending and take latest 3
            const latestPosts = posts
                .sort((a, b) => new Date(b.date) - new Date(a.date))
                .slice(0, 3);
            
            if (latestPosts.length === 0) {
                container.innerHTML = '<div class="text-center py-8 text-gray-500">No articles yet</div>';
                return;
            }
            
            const months = ['January', 'February', 'March', 'April', 'May', 'June', 
                           'July', 'August', 'September', 'October', 'November', 'December'];
            
            // Extract clean title (remove " - TopClanker Blog" suffix)
            const cleanTitle = (title) => {
                return title.replace(/ - TopClanker( Blog)?$/, '');
            };
            
            container.innerHTML = latestPosts.map(post => {
                const date = new Date(post.date + 'T00:00:00');
                const formattedDate = `${months[date.getMonth()]} ${date.getDate()}, ${date.getFullYear()}`;
                const title = cleanTitle(post.title);
                const shortTitle = title.length > 55 ? title.substring(0, 55) + '...' : title;
                
                return `
                    <article class="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
                        <p class="text-sm text-gray-500 mb-2">${formattedDate}</p>
                        <h4 class="text-xl font-bold mb-2">
                            <a href="/blog/${post.file}" class="text-gray-900 hover:text-blue-600">
                                ${shortTitle}
                            </a>
                        </h4>
                        <a href="/blog/${post.file}" class="text-blue-600 hover:underline text-sm font-medium">
                            Read more →
                        </a>
                    </article>
                `;
            }).join('');
        } catch (error) {
            console.error('Error loading recent blog posts:', error);
            container.innerHTML = '<div class="text-center py-8 text-gray-500">Unable to load articles</div>';
        }
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
                const category = e.target.dataset.category;
                const local = e.target.dataset.local;
                
                if (category !== undefined) {
                    this.handleFilterChange(category);
                } else if (local !== undefined) {
                    this.handleLocalFilterChange(local);
                }
            });
        });

        // VRAM filter dropdown
        const vramSelect = document.getElementById('vramSelect');
        if (vramSelect) {
            vramSelect.addEventListener('change', (e) => {
                this.handleVramFilterChange(e.target.value);
            });
        }

        // Apple memory filter dropdown
        const appleSelect = document.getElementById('appleSelect');
        if (appleSelect) {
            appleSelect.addEventListener('change', (e) => {
                this.handleAppleFilterChange(e.target.value);
            });
        }
    }

    handleVramFilterChange(vramFilter) {
        this.currentVramFilter = vramFilter;
        this.currentPage = 1;
        this.render();
    }

    handleAppleFilterChange(appleFilter) {
        this.currentAppleFilter = appleFilter;
        this.currentPage = 1;
        this.render();
    }

    handleLocalFilterChange(localFilter) {
        this.currentLocalFilter = localFilter;
        this.currentPage = 1;
        
        // Update active button
        document.querySelectorAll('#localFilter .filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        const activeBtn = document.querySelector(`#localFilter .filter-btn[data-local="${localFilter}"]`);
        if (activeBtn) activeBtn.classList.add('active');
        
        this.render();
    }

    isLocalModel(agent) {
        // Check if model has vram requirement (not API-only)
        const vram = agent.vram || 'api';
        if (vram !== 'api') {
            return true;
        }
        // Fallback to name matching for legacy data
        const name = agent.name || '';
        return this.localModels.some(local => 
            name.toLowerCase().includes(local.toLowerCase())
        );
    }

    handleFilterChange(category) {
        this.currentFilter = category;
        this.currentPage = 1;
        
        // Update active button
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        const activeBtn = document.querySelector(`.filter-btn[data-category="${category}"]`);
        if (activeBtn) activeBtn.classList.add('active');
        
        this.render();
    }

    getFilteredAgents() {
        if (!this.data || !this.data.agents) return [];
        
        let agents = this.data.agents;
        
        // Filter by category
        if (this.currentFilter !== 'all') {
            agents = agents.filter(agent => 
                agent.category === this.currentFilter
            );
        }
        
        // Filter by local models
        if (this.currentLocalFilter === 'local') {
            agents = agents.filter(agent => 
                this.isLocalModel(agent)
            );
        }

        // Filter by VRAM requirement
        if (this.currentVramFilter !== 'all') {
            agents = agents.filter(agent => {
                const vram = agent.vram || 'api';
                if (this.currentVramFilter === 'api') {
                    return vram === 'api';
                } else if (this.currentVramFilter === '32gb') {
                    // 32GB+ shows models that need 32GB or are API-only
                    return vram === 'api' || vram === '32gb';
                } else {
                    // For specific GB values, show API models + models that fit
                    return vram === 'api' || vram === this.currentVramFilter;
                }
            });
        }

        // Filter by Apple unified memory (simplified - shows local models as compatible)
        if (this.currentAppleFilter !== 'all') {
            agents = agents.filter(agent => {
                // Apple unified memory can run local models efficiently
                // Show local models + API models
                const vram = agent.vram || 'api';
                return vram === 'api' || vram !== 'api';
            });
        }
        
        return agents;
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

        if (!this.data) {
            container.innerHTML = '<div class="text-center py-8 text-gray-500"><p>Loading rankings...</p></div>';
            return;
        }

        const agents = this.getPaginatedAgents();
        
        if (agents.length === 0) {
            container.innerHTML = '<div class="text-center py-8 text-gray-500">No agents found</div>';
            return;
        }

        try {
            container.innerHTML = agents.map(agent => this.createCard(agent)).join('');
        } catch (e) {
            console.error('Error rendering cards:', e);
            container.innerHTML = '<div class="text-center py-8 text-red-500">Error loading rankings</div>';
        }
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