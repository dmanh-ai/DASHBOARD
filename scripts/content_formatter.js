// Content Formatter - Transform plain text to visual data

class ContentFormatter {
    constructor() {
        this.patterns = {
            // Numbers: prices, percentages, ratios
            price: /(\d{1,3}(?:,\d{3})*(?:\.\d+)?)/g,
            percentage: /([+-]?\d+\.?\d*)%/g,
            number: /\b(\d+\.?\d*)\b/g,

            // Technical indicators - Enhanced patterns
            rsi: /RSI[ -]?(\d+)[\s=:]*(-?\d+\.?\d*)?/gi,
            atr: /ATR[ -]?(\d+)[\s=:]*(-?\d+\.?\d*)?/gi,
            ma: /MA[ -]?(\d+)[\s\(=:]*(-?[\d,]+\.?\d*)?/gi,
            momentum: /Mom[ -]?(\d+)[\s\(=:]*([+-]?\d+\.?\d*)?/gi,
            adx: /ADX[ -]?(\d+)[\s=:]*(-?[\d,]+\.?\d*)?/gi,
            vwma: /VWAP[ -]?(\d+)[\s\(=:]*(-?[\d,]+\.?\d*)?/gi,

            // Keywords - Enhanced to avoid false positives
            bullish: /\btăng\b|bullish|positive|kháng cự|sức mạnh|hồi phục|phục hồi|đột biến|phòng thủ|ổn định/gi,
            bearish: /\bgiảm\b|bearish|negative|áp lực|\bbán\b|tháo chạy|\bđiều chỉnh\b|yếu(?!\s*tố)|xấu/gi,
            warning: /\bcảnh báo\b|rủi ro|thận trọng|canh giác|nguy hiểm/gi,

            // Section markers (non-global to avoid RegExp.lastIndex bugs)
            conclusion: /^kết\s+luận\s*:/mi,
            conclusionShort: /^kết\s+luận\s+ngắn\s*:/mi,
            evidence: /^dẫn\s+chứng\b/mi,
            action: /^(ý\s+nghĩa(?:\/hành\s+động)?|hành\s+động\s+đề\s+xuất)\s*:/mi,
            invalidation: /^điều\s+kiện\s+(khiến\s+kết\s+luận\s+sai|sai)\s*:/mi,
            risk: /^(rủi\s+ro|cảnh\s+báo\s+rủi\s+ro)\s*:/mi,
            levels: /^(hỗ\s+trợ|kháng\s+cự|hỗ\s+trợ\s+then\s+chốt|mức\s+quan\s+trọng\s+cần\s+theo\s+dõi)\s*:/mi,
            scenario: /^kịch\s+bản\b/mi,
            confidence: /^(mức\s+độ\s+tự\s+tin|độ\s+tin\s+cậy)\s*:/mi,
            metrics: /^độ\s+rộng\s*:/mi
        };

        // Safety: cap number of callouts per formatted section (prevents UI flooding/slowness).
        // Reset for each `format()` call.
        this.calloutLimits = {
            total: 10,
            hero: 1,
            conclusion: 2,
            action: 2,
            risk: 2,
            invalidation: 1,
            levels: 2,
            scenario: 3,
            confidence: 1,
            metrics: 1,
            evidence: 1,
        };
    }

    resetCalloutState() {
        this._calloutTotal = 0;
        this._calloutByType = Object.create(null);
    }

    canEmitCallout(type) {
        if (!this._calloutByType) this.resetCalloutState();

        const limitTotal = this.calloutLimits.total ?? 0;
        if (limitTotal > 0 && this._calloutTotal >= limitTotal) return false;

        const limitType = this.calloutLimits[type];
        if (typeof limitType === 'number' && limitType >= 0) {
            const current = this._calloutByType[type] || 0;
            if (current >= limitType) return false;
        }

        this._calloutTotal += 1;
        this._calloutByType[type] = (this._calloutByType[type] || 0) + 1;
        return true;
    }

    stripTagsUnsafe(html) {
        return String(html || '').replace(/<[^>]*>/g, '');
    }

    escapeRegExp(str) {
        return String(str).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    stripPrefix(htmlText, prefix) {
        const re = new RegExp(`^\\s*${this.escapeRegExp(prefix)}\\s*`, 'i');
        return htmlText.replace(re, '');
    }

    isAllCapsHeadline(rawLine) {
        const line = (rawLine || '').trim();
        if (line.length < 10 || line.length > 120) return false;
        if (/^PHẦN\s+[IVX]+\b/i.test(line)) return false;

        // Browser-safe all-caps detection without Unicode property escapes.
        const letters = Array.from(line).filter(ch => ch.toLowerCase() !== ch.toUpperCase());
        if (letters.length < 6) return false;
        return letters.every(ch => ch === ch.toUpperCase());
    }

    renderCallout({ boxClass, icon, iconClass, textClass }, htmlText) {
        return `<div class="${boxClass}">
            <span class="${iconClass}">${icon}</span>
            <span class="${textClass}">${htmlText}</span>
        </div>`;
    }

    tryRenderCalloutParagraph(htmlParagraph) {
        const raw = this.stripTagsUnsafe(htmlParagraph).trim();
        if (!raw) return null;

        // HERO: quoted headline or all-caps headline.
        if ((raw.startsWith('"') && raw.endsWith('"') && raw.length <= 140) || this.isAllCapsHeadline(raw)) {
            const cleaned = raw.startsWith('"') && raw.endsWith('"') ? raw.slice(1, -1).trim() : htmlParagraph;
            if (!this.canEmitCallout('hero')) return null;
            return this.renderCallout(
                { boxClass: 'hero-box', icon: '✨', iconClass: 'hero-icon', textClass: 'hero-text' },
                cleaned
            );
        }

        if (this.patterns.conclusionShort.test(raw)) {
            const body = this.stripPrefix(htmlParagraph, 'Kết luận ngắn:');
            if (!this.canEmitCallout('conclusion')) return null;
            return this.renderCallout(
                { boxClass: 'conclusion-box', icon: '📌', iconClass: 'conclusion-icon', textClass: 'conclusion-text' },
                body
            );
        }

        if (this.patterns.conclusion.test(raw)) {
            const body = this.stripPrefix(htmlParagraph, 'Kết luận:');
            if (!this.canEmitCallout('conclusion')) return null;
            return this.renderCallout(
                { boxClass: 'conclusion-box', icon: '📌', iconClass: 'conclusion-icon', textClass: 'conclusion-text' },
                body
            );
        }

        if (this.patterns.action.test(raw)) {
            // Prefer the more specific prefix first.
            let body = htmlParagraph;
            body = this.stripPrefix(body, 'Ý nghĩa/Hành động:');
            body = this.stripPrefix(body, 'Ý nghĩa:');
            body = this.stripPrefix(body, 'Hành động đề xuất:');
            if (!this.canEmitCallout('action')) return null;
            return this.renderCallout(
                { boxClass: 'action-box', icon: '🎯', iconClass: 'action-icon', textClass: 'action-text' },
                body
            );
        }

        if (this.patterns.risk.test(raw) || /\b(Black\s+Swan|RỦI\s+RO\s+LỚN|Tuyệt\s+đối|cắt\s+lỗ|stop-?loss)\b/i.test(raw)) {
            let body = htmlParagraph;
            body = this.stripPrefix(body, 'Rủi ro:');
            body = this.stripPrefix(body, 'Cảnh báo rủi ro:');
            if (!this.canEmitCallout('risk')) return null;
            return this.renderCallout(
                { boxClass: 'risk-box', icon: '⛔', iconClass: 'risk-icon', textClass: 'risk-text' },
                body
            );
        }

        if (this.patterns.invalidation.test(raw) || /^3\s+điều\s+kiện\b/i.test(raw)) {
            let body = htmlParagraph;
            body = this.stripPrefix(body, 'Điều kiện khiến kết luận sai:');
            body = this.stripPrefix(body, 'Điều kiện sai:');
            if (!this.canEmitCallout('invalidation')) return null;
            return this.renderCallout(
                { boxClass: 'conditions-box', icon: '⚠️', iconClass: 'conditions-icon', textClass: 'conditions-text' },
                body
            );
        }

        // Levels: prefer explicit support/resistance / H1/R1 style markers to avoid over-highlighting MA/RSI lines.
        if (this.patterns.levels.test(raw) || /^(H\d|R\d)\b/i.test(raw) || /\b(H[1-9]|R[1-9])\b/i.test(raw)) {
            if (!this.canEmitCallout('levels')) return null;
            return this.renderCallout(
                { boxClass: 'levels-box', icon: '🎯', iconClass: 'levels-icon', textClass: 'levels-text' },
                htmlParagraph
            );
        }

        if (this.patterns.scenario.test(raw) || /\bXác\s+suất\b/i.test(raw)) {
            if (!this.canEmitCallout('scenario')) return null;
            return this.renderCallout(
                { boxClass: 'scenario-box', icon: '🎲', iconClass: 'scenario-icon', textClass: 'scenario-text' },
                htmlParagraph
            );
        }

        // Confidence: avoid catching every % change line; require explicit wording or x/10 score.
        if (this.patterns.confidence.test(raw) || /\b\d+\s*\/\s*10\b/.test(raw) || /\b(tự\s+tin|tin\s+cậy)\b/i.test(raw)) {
            if (!this.canEmitCallout('confidence')) return null;
            return this.renderCallout(
                { boxClass: 'confidence-box', icon: '✅', iconClass: 'confidence-icon', textClass: 'confidence-text' },
                htmlParagraph
            );
        }

        if (this.patterns.metrics.test(raw) || /\b(TRIN|A\/D|Volume\s+Ratio|52W)\b/i.test(raw)) {
            if (!this.canEmitCallout('metrics')) return null;
            return this.renderCallout(
                { boxClass: 'metrics-box', icon: '📊', iconClass: 'metrics-icon', textClass: 'metrics-text' },
                htmlParagraph
            );
        }

        if (this.patterns.evidence.test(raw)) {
            const body = this.stripPrefix(htmlParagraph, 'Dẫn chứng:');
            if (!this.canEmitCallout('evidence')) return null;
            return this.renderCallout(
                { boxClass: 'evidence-box', icon: '📊', iconClass: 'evidence-icon', textClass: 'evidence-text' },
                body
            );
        }

        return null;
    }

    // Format content với visual elements
    format(content) {
        if (!content) return '';

        this.resetCalloutState();

        // Strip existing HTML tags to get plain text
        let plainText = this.stripHtml(content);

        let formatted = plainText;

        // Remove backticks from title
        formatted = formatted.replace(/`([^`]+)`/g, '$1');

        // Format numbers
        formatted = this.formatNumbers(formatted);

        // Format percentages
        formatted = this.formatPercentages(formatted);

        // Format technical indicators
        formatted = this.formatIndicators(formatted);

        // Format lists
        formatted = this.formatLists(formatted);

        // Add color coding
        formatted = this.colorCode(formatted);

        return formatted;
    }

    // Strip HTML tags to get plain text, but preserve structure
    stripHtml(html) {
        // Remove the outer info-box div but keep inner content
        let cleaned = html.replace(/<div class=['"]info-box['"]>/gi, '');
        cleaned = cleaned.replace(/<\/div>\s*$/gi, ''); // Remove closing div at end

        // Convert <p> tags to newlines
        cleaned = cleaned.replace(/<p>/gi, '');
        cleaned = cleaned.replace(/<\/p>/gi, '\n\n');

        // Remove any remaining HTML tags
        const tmp = document.createElement('div');
        tmp.innerHTML = cleaned;
        return tmp.textContent || tmp.innerText || '';
    }

    formatNumbers(text) {
        return text.replace(this.patterns.price, (match, number) => {
            const num = parseFloat(number.replace(/,/g, ''));
            if (isNaN(num)) return match;

            // Format based on magnitude
            // CHỈ convert số cực lớn (>= 1M) thành M/K format
            // Giá chỉ số (1,000-10,000) giữ nguyên dấu phẩy
            if (num >= 1000000) {
                return `<span class="metric-number">${(num/1000000).toFixed(2)}M</span>`;
            } else if (num >= 10000) {
                // Số 5 chữ số trở lên: format with K
                return `<span class="metric-number">${(num/1000).toFixed(1)}K</span>`;
            } else if (num >= 1000) {
                // Số 4 chữ số (giá chỉ số): GIỮ NGUYÊN dấu phẩy
                // Nếu match có dấu phẩy, giữ nguyên, ngược lại add dấu phẩy
                if (match.includes(',')) {
                    return `<span class="metric-number">${match}</span>`;
                }
                return `<span class="metric-number">${num.toLocaleString('en-US')}</span>`;
            } else if (num >= 1) {
                return `<span class="metric-number">${num.toLocaleString('en-US')}</span>`;
            }
            return match;
        });
    }

    formatPercentages(text) {
        return text.replace(this.patterns.percentage, (match, pct) => {
            const num = parseFloat(pct);
            if (isNaN(num)) return match;

            const className = num > 0 ? 'bullish' : num < 0 ? 'bearish' : 'neutral';
            const icon = num > 0 ? '📈' : num < 0 ? '📉' : '➡️';

            return `<span class="percentage ${className}" title="${pct}">${icon} ${pct}</span>`;
        });
    }

    formatIndicators(text) {
        // Format RSI with progress bar - pattern: /RSI[ -]?(\d+)[\s=:]*(-?\d+\.?\d*)?/gi
        text = text.replace(this.patterns.rsi, (match, period, value) => {
            if (!value) return match; // No value provided
            const num = parseFloat(value);
            if (isNaN(num)) return match;

            const level = num > 70 ? 'overbought' : num < 30 ? 'oversold' : 'neutral';
            const color = num > 70 ? 'var(--danger)' : num < 30 ? 'var(--success)' : 'var(--warning)';
            const label = num > 70 ? 'Quá mua' : num < 30 ? 'Quá bán' : 'Trung tính';

            return `
                <div class="indicator-container">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div class="indicator-label">RSI${period}</div>
                        <div class="indicator-value" style="font-size: 1.2rem;">${num.toFixed(2)}</div>
                    </div>
                    <div class="progress-bar">
                        <div class="fill ${level}" style="width: ${Math.min(100, num)}%; background: ${color};"></div>
                    </div>
                    <div style="text-align: center; font-size: 0.75rem; margin-top: 4px; color: var(--text-secondary);">${label}</div>
                </div>
            `;
        });

        // Format MA with level
        text = text.replace(this.patterns.ma, (match, period, value) => {
            if (!value) return `<span class="ma-indicator"><strong>MA${period}</strong></span>`;
            const num = parseFloat(value.replace(/,/g, ''));
            if (isNaN(num)) return match;

            return `<span class="ma-indicator"><strong>MA${period}:</strong> <span class="ma-value">${num.toLocaleString('en-US')}</span></span>`;
        });

        // Format Momentum
        text = text.replace(this.patterns.momentum, (match, period, value) => {
            if (!value) return `<span class="momentum">Mom${period}</span>`;
            const num = parseFloat(value);
            if (isNaN(num)) return match;

            const className = num > 0 ? 'bullish' : num < 0 ? 'bearish' : 'neutral';
            const icon = num > 0 ? '📈' : num < 0 ? '📉' : '➡️';

            return `<span class="momentum ${className}">${icon} Mom${period}: ${value}</span>`;
        });

        // Format ADX
        text = text.replace(this.patterns.adx, (match, period, value) => {
            if (!value) return `<span class="ma-indicator"><strong>ADX${period}</strong></span>`;
            const num = parseFloat(value.replace(/,/g, ''));
            if (isNaN(num)) return match;

            const strength = num > 25 ? 'Mạnh' : num > 20 ? 'Trung bình' : 'Yếu';
            const color = num > 25 ? 'var(--success)' : num > 20 ? 'var(--warning)' : 'var(--text-secondary)';

            return `<span class="ma-indicator"><strong>ADX${period}:</strong> <span class="ma-value" style="color: ${color};">${num.toFixed(2)} (${strength})</span></span>`;
        });

        // Format ATR
        text = text.replace(this.patterns.atr, (match, period, value) => {
            if (!value) return `<span class="ma-indicator"><strong>ATR${period}</strong></span>`;
            const num = parseFloat(value);
            if (isNaN(num)) return match;

            return `<span class="ma-indicator"><strong>ATR${period}:</strong> <span class="ma-value">${num.toFixed(2)}</span></span>`;
        });

        // Format VWAP
        text = text.replace(this.patterns.vwma, (match, period, value) => {
            if (!value) return `<span class="ma-indicator"><strong>VWAP${period}</strong></span>`;
            const num = parseFloat(value.replace(/,/g, ''));
            if (isNaN(num)) return match;

            return `<span class="ma-indicator"><strong>VWAP${period}:</strong> <span class="ma-value">${num.toLocaleString('en-US')}</span></span>`;
        });

        return text;
    }

    formatLists(text) {
        // Split by paragraphs first
        const paragraphs = text.split('\n\n');

        return paragraphs.map(para => {
            // Check if it's a numbered list
            const lines = para.split('\n');
            const nonEmptyLines = lines.map(l => l.trim()).filter(Boolean);

            // Check for numbered items
            if (lines.some(line => /^\d+\.\s/.test(line))) {
                return `<div class="formatted-list numbered">${lines.map(line => {
                    const match = line.match(/^(\d+)\.\s+(.*)/);
                    if (match) {
                        // Check if content has a header like "Ngắn hạn:", "Trung hạn:"
                        const content = match[2];
                        const headerMatch = content.match(/^([^:]+):\s*(.*)/);

                        if (headerMatch) {
                            const header = headerMatch[1];
                            const body = headerMatch[2];
                            return `<div class="list-item numbered">
                                <span class="list-number">${match[1]}</span>
                                <span class="list-content">
                                    <span class="list-header">${header}</span>
                                    <span class="list-body">${this.formatInline(body)}</span>
                                </span>
                            </div>`;
                        }

                        return `<div class="list-item numbered"><span class="list-number">${match[1]}</span><span class="list-content">${this.formatInline(content)}</span></div>`;
                    }
                    return `<div class="list-item">${line}</div>`;
                }).join('')}</div>`;
            }

            // Check for bullet points
            if (lines.some(line => /^[\-\•]\s/.test(line))) {
                return `<div class="formatted-list bulleted">${lines.map(line => {
                    const match = line.match(/^[\-\•]\s+(.*)/);
                    if (match) {
                        // Check if content has a header
                        const content = match[1];
                        const headerMatch = content.match(/^([^:]+):\s*(.*)/);

                        if (headerMatch) {
                            const header = headerMatch[1];
                            const body = headerMatch[2];
                            return `<div class="list-item bulleted">
                                <span class="list-bullet">•</span>
                                <span class="list-content">
                                    <span class="list-header">${header}</span>
                                    <span class="list-body">${this.formatInline(body)}</span>
                                </span>
                            </div>`;
                        }

                        return `<div class="list-item bulleted"><span class="list-bullet">•</span><span class="list-content">${this.formatInline(content)}</span></div>`;
                    }
                    return `<div class="list-item">${line}</div>`;
                }).join('')}</div>`;
            }

            // Regular paragraph (single-line callouts)
            if (nonEmptyLines.length === 1) {
                const callout = this.tryRenderCalloutParagraph(this.formatInline(nonEmptyLines[0]));
                if (callout) return callout;
            }

            return `<p class="content-paragraph">${this.formatInline(para)}</p>`;
        }).join('\n\n');
    }

    formatInline(text) {
        // Bold key terms
        text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

        // NOTE: Disabled keyword highlighting due to false positives
        // Vietnamese has many context-dependent words that don't work well
        // with simple pattern matching. Kept code for reference only.

        // Highlight keywords - DISABLED
        // text = text.replace(this.patterns.bullish, '<span class="text-success">$&</span>');
        // text = text.replace(this.patterns.bearish, '<span class="text-danger">$&</span>');
        // text = text.replace(this.patterns.warning, '<span class="text-warning">$&</span>');

        return text;
    }

    colorCode(text) {
        return text;
    }

    // Kept for backward compatibility; callouts are now handled in `formatLists()`.
    formatSections(text) { return text; }
}

// Export để dùng trong DASHBOARD
window.ContentFormatter = ContentFormatter;
