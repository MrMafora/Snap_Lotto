/**
 * AI-Powered Lottery Pattern Analysis
 * JavaScript frontend for Google Gemini AI pattern analysis
 */

class AIPatternAnalyzer {
    constructor() {
        this.isAnalyzing = false;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Main pattern analysis button
        const analyzeBtn = document.getElementById('analyze-patterns-btn');
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => this.analyzePatterns());
        }

        // Game-specific insights
        const gameInsightsBtn = document.getElementById('get-game-insights-btn');
        const gameInsightsSelect = document.getElementById('game-insights-type');
        
        if (gameInsightsBtn && gameInsightsSelect) {
            gameInsightsSelect.addEventListener('change', (e) => {
                gameInsightsBtn.disabled = !e.target.value;
            });
            
            gameInsightsBtn.addEventListener('click', () => this.getGameInsights());
        }
    }

    async analyzePatterns() {
        if (this.isAnalyzing) return;
        
        const lotteryType = document.getElementById('ai-lottery-type').value;
        const button = document.getElementById('analyze-patterns-btn');
        
        try {
            this.isAnalyzing = true;
            this.showLoadingState();
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Analyzing...';
            
            const response = await fetch(`/api/lottery-analysis/ai-patterns?lottery_type=${lotteryType}&days=180`);
            const data = await response.json();
            
            if (data.error) {
                this.showError(data.error);
                return;
            }
            
            this.displayAnalysisResults(data);
            
        } catch (error) {
            console.error('Pattern analysis error:', error);
            this.showError('Failed to analyze patterns. Please try again.');
        } finally {
            this.isAnalyzing = false;
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-brain me-1"></i>Analyze Patterns';
            this.hideLoadingState();
        }
    }

    async getGameInsights() {
        const lotteryType = document.getElementById('game-insights-type').value;
        const button = document.getElementById('get-game-insights-btn');
        
        if (!lotteryType) return;
        
        try {
            this.showGameInsightsLoading();
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Analyzing...';
            
            const response = await fetch(`/api/lottery-analysis/game-insights?lottery_type=${lotteryType}&days=90`);
            const data = await response.json();
            
            if (data.error) {
                this.showGameInsightsError(data.error);
                return;
            }
            
            this.displayGameInsights(data);
            
        } catch (error) {
            console.error('Game insights error:', error);
            this.showGameInsightsError('Failed to get game insights. Please try again.');
        } finally {
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-lightbulb me-1"></i>Get Insights';
            this.hideGameInsightsLoading();
        }
    }

    showLoadingState() {
        document.getElementById('ai-loading').classList.remove('d-none');
        document.getElementById('ai-initial-state').classList.add('d-none');
        document.getElementById('ai-error').classList.add('d-none');
        document.getElementById('pattern-results').classList.add('d-none');
        document.getElementById('ai-summary-section').classList.add('d-none');
    }

    hideLoadingState() {
        document.getElementById('ai-loading').classList.add('d-none');
    }

    showError(message) {
        document.getElementById('ai-error-message').textContent = message;
        document.getElementById('ai-error').classList.remove('d-none');
        document.getElementById('ai-initial-state').classList.add('d-none');
        document.getElementById('pattern-results').classList.add('d-none');
        document.getElementById('ai-summary-section').classList.add('d-none');
    }

    displayAnalysisResults(data) {
        // Hide other states
        document.getElementById('ai-initial-state').classList.add('d-none');
        document.getElementById('ai-error').classList.add('d-none');
        
        // Show AI summary
        if (data.ai_summary) {
            const summaryContent = document.getElementById('ai-summary-content');
            summaryContent.innerHTML = `<p class="mb-0">${data.ai_summary}</p>`;
            document.getElementById('ai-summary-section').classList.remove('d-none');
        }
        
        // Display pattern analyses
        const patternsContainer = document.getElementById('number-patterns-list');
        patternsContainer.innerHTML = '';
        
        if (data.pattern_analyses && data.pattern_analyses.length > 0) {
            data.pattern_analyses.forEach(pattern => {
                const patternCard = this.createPatternCard(pattern);
                patternsContainer.appendChild(patternCard);
            });
        } else {
            patternsContainer.innerHTML = '<p class="text-muted">No specific number patterns detected in recent data.</p>';
        }
        
        // Display game analyses
        const gameContainer = document.getElementById('game-analysis-list');
        gameContainer.innerHTML = '';
        
        if (data.game_analyses && data.game_analyses.length > 0) {
            data.game_analyses.forEach(analysis => {
                const gameCard = this.createGameAnalysisCard(analysis);
                gameContainer.appendChild(gameCard);
            });
        } else {
            gameContainer.innerHTML = '<p class="text-muted">No game-specific patterns detected.</p>';
        }
        
        // Show results
        document.getElementById('pattern-results').classList.remove('d-none');
    }

    createPatternCard(pattern) {
        const card = document.createElement('div');
        card.className = 'card mb-3 border-warning';
        
        const confidence = (pattern.confidence * 100).toFixed(0);
        const confidenceColor = confidence > 70 ? 'success' : confidence > 40 ? 'warning' : 'danger';
        
        card.innerHTML = `
            <div class="card-body">
                <h6 class="card-title d-flex justify-content-between">
                    ${pattern.pattern_type}
                    <span class="badge bg-${confidenceColor}">${confidence}% confidence</span>
                </h6>
                <p class="card-text">${pattern.description}</p>
                ${pattern.evidence && pattern.evidence.length > 0 ? `
                    <div class="mb-2">
                        <strong>Evidence:</strong>
                        <ul class="mb-2">
                            ${pattern.evidence.map(e => `<li class="small">${e}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                ${pattern.recommendation ? `
                    <div class="alert alert-info py-2 mb-0">
                        <strong>Recommendation:</strong> ${pattern.recommendation}
                    </div>
                ` : ''}
            </div>
        `;
        
        return card;
    }

    createGameAnalysisCard(analysis) {
        const card = document.createElement('div');
        card.className = 'card mb-3 border-info';
        
        card.innerHTML = `
            <div class="card-body">
                <h6 class="card-title">${analysis.game_type}</h6>
                <div class="row">
                    <div class="col-6">
                        <small class="text-muted">Total Draws:</small>
                        <div class="fw-bold">${analysis.total_draws}</div>
                    </div>
                    <div class="col-6">
                        <small class="text-muted">Unique Patterns:</small>
                        <div class="fw-bold">${analysis.unique_patterns || 'N/A'}</div>
                    </div>
                </div>
                ${analysis.hot_sequences && analysis.hot_sequences.length > 0 ? `
                    <div class="mt-2">
                        <strong class="text-danger">Hot Sequences:</strong>
                        <div class="d-flex flex-wrap gap-1 mt-1">
                            ${analysis.hot_sequences.slice(0, 3).map(seq => 
                                `<span class="badge bg-danger">${seq.join('-')}</span>`
                            ).join('')}
                        </div>
                    </div>
                ` : ''}
                ${analysis.cold_sequences && analysis.cold_sequences.length > 0 ? `
                    <div class="mt-2">
                        <strong class="text-info">Cold Sequences:</strong>
                        <div class="d-flex flex-wrap gap-1 mt-1">
                            ${analysis.cold_sequences.slice(0, 3).map(seq => 
                                `<span class="badge bg-info">${seq.join('-')}</span>`
                            ).join('')}
                        </div>
                    </div>
                ` : ''}
                ${analysis.ai_insights ? `
                    <div class="mt-2">
                        <small class="text-muted">${analysis.ai_insights}</small>
                    </div>
                ` : ''}
            </div>
        `;
        
        return card;
    }

    showGameInsightsLoading() {
        document.getElementById('game-insights-loading').classList.remove('d-none');
        document.getElementById('game-insights-initial').classList.add('d-none');
        document.getElementById('game-insights-content').classList.add('d-none');
    }

    hideGameInsightsLoading() {
        document.getElementById('game-insights-loading').classList.add('d-none');
    }

    showGameInsightsError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger';
        errorDiv.innerHTML = `<i class="fas fa-exclamation-triangle me-2"></i>${message}`;
        
        const container = document.getElementById('game-insights-content');
        container.innerHTML = '';
        container.appendChild(errorDiv);
        container.classList.remove('d-none');
    }

    displayGameInsights(data) {
        document.getElementById('game-insights-initial').classList.add('d-none');
        
        const container = document.getElementById('game-insights-content');
        container.innerHTML = '';
        
        if (data.game_analyses && data.game_analyses.length > 0) {
            data.game_analyses.forEach(analysis => {
                const card = this.createDetailedGameCard(analysis);
                container.appendChild(card);
            });
        } else {
            container.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    No specific insights available for ${data.lottery_type} at this time.
                </div>
            `;
        }
        
        container.classList.remove('d-none');
    }

    createDetailedGameCard(analysis) {
        const card = document.createElement('div');
        card.className = 'card border-warning';
        
        card.innerHTML = `
            <div class="card-header bg-warning bg-opacity-10">
                <h6 class="mb-0">🎯 ${analysis.game_type} Analysis</h6>
            </div>
            <div class="card-body">
                <div class="row mb-3">
                    <div class="col-md-4">
                        <div class="text-center p-2 bg-light rounded">
                            <div class="h5 text-primary mb-1">${analysis.total_draws}</div>
                            <small class="text-muted">Total Draws Analyzed</small>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="text-center p-2 bg-light rounded">
                            <div class="h5 text-warning mb-1">${analysis.unique_patterns || 'N/A'}</div>
                            <small class="text-muted">Unique Patterns</small>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="text-center p-2 bg-light rounded">
                            <div class="h5 text-success mb-1">${(analysis.hot_sequences || []).length}</div>
                            <small class="text-muted">Hot Sequences</small>
                        </div>
                    </div>
                </div>
                
                ${analysis.ai_insights ? `
                    <div class="alert alert-info">
                        <strong>AI Analysis:</strong><br>
                        ${analysis.ai_insights}
                    </div>
                ` : ''}
                
                <div class="row">
                    ${analysis.hot_sequences && analysis.hot_sequences.length > 0 ? `
                        <div class="col-md-6">
                            <h6 class="text-danger">🔥 Hot Number Sequences</h6>
                            <div class="d-flex flex-wrap gap-1">
                                ${analysis.hot_sequences.slice(0, 5).map(seq => 
                                    `<span class="badge bg-danger">${seq.join(' - ')}</span>`
                                ).join('')}
                            </div>
                        </div>
                    ` : ''}
                    
                    ${analysis.cold_sequences && analysis.cold_sequences.length > 0 ? `
                        <div class="col-md-6">
                            <h6 class="text-info">❄️ Cold Number Sequences</h6>
                            <div class="d-flex flex-wrap gap-1">
                                ${analysis.cold_sequences.slice(0, 5).map(seq => 
                                    `<span class="badge bg-info">${seq.join(' - ')}</span>`
                                ).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        return card;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new AIPatternAnalyzer();
});