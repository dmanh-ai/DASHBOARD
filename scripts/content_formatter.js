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

            // Section markers
            conclusion: /^kết luận:/gmi,
            evidence: /^dẫn chứng|^ý nghĩa/gi,
            conditions: /^điều kiện/gmi
        };
    }

    // Format content với visual elements
    format(content) {
        if (!content) return '';

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

        // Format sections
        formatted = this.formatSections(formatted);

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

            // Regular paragraph
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

    formatSections(text) {
        const lines = text.split('\n');

        return lines.map(line => {
            const trimmedLine = line.trim();

            // Section headers - Enhanced with icons and backgrounds
            if (this.patterns.conclusion.test(trimmedLine)) {
                return `<div class="conclusion-box">
                    <span class="conclusion-icon">📌</span>
                    <span class="conclusion-text">${trimmedLine.replace(/^Kết luận:\s*/i, '')}</span>
                </div>`;
            }
            if (this.patterns.evidence.test(trimmedLine)) {
                return `<div class="evidence-box">
                    <span class="evidence-icon">📊</span>
                    <span class="evidence-text">${trimmedLine}</span>
                </div>`;
            }
            if (this.patterns.conditions.test(trimmedLine)) {
                return `<div class="conditions-box">
                    <span class="conditions-icon">⚠️</span>
                    <span class="conditions-text">${trimmedLine}</span>
                </div>`;
            }

            return line;
        }).join('\n');
    }
}

// Export để dùng trong DASHBOARD
window.ContentFormatter = ContentFormatter;
