const fs = require('fs');

// Read the file
const content = fs.readFileSync('/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/UI GLM/baocao_full.txt', 'utf8');
const lines = content.split('\n');

// Read vnindex data
const vnindexContent = fs.readFileSync('/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/UI GLM/vnindex_data.js', 'utf8');

// Extract VNINDEX data from vnindex_data.js
const vnindexMatch = vnindexContent.match(/vnindex:\s*\{[\s\S]*?\n    \}/);
const vnindexData = vnindexMatch ? vnindexMatch[0].replace('vnindex:', '').trim() : '';

// Section mapping with icons
const sectionIcons = {
    'THÔNG TIN CHUNG': '📊',
    'XU HƯỚNG GIÁ': '📈',
    'XU HƯỚNG KHỐI LƯỢNG': '📊',
    'KẾT HỢP XU HƯỚNG GIÁ & KHỐI LƯỢNG': '💹',
    'CUNG - CẦU': '⚖️',
    'MỨC GIÁ QUAN TRỌNG': '🎯',
    'BIẾN ĐỘNG GIÁ': '📉',
    'MÔ HÌNH GIÁ - MÔ HÌNH NẾN': '🕯️',
    'MARKET BREADTH & TÂM LÝ THỊ TRƯỜNG': '👥',
    'LỊCH SỬ & XU HƯỚNG BREADTH': '📜',
    'RỦI RO': '⚠️',
    'KHUYẾN NGHỊ VỊ THẾ': '🎯',
    'GIÁ MỤC TIÊU': '🎯',
    'KỊCH BẢN WHAT-IF': '🎲'
};

// Function to find sections in a range
function extractSections(startLine, endLine, indexName) {
    const sections = [];
    let currentSection = null;
    let contentLines = [];
    let inSection = false;

    for (let i = startLine - 1; i < Math.min(endLine, lines.length); i++) {
        const line = lines[i].trim();

        // Detect section headers (all caps, followed by colon)
        if (/^[A-ZÀ-Ỹ\s&\-]+$/.test(line) && line.length > 3 && line.length < 60 && !line.includes('PHẦN') && !line.includes('PHÂN TÍCH CHỈ SỐ') && !line.startsWith('Giá hiện tại') && !line.startsWith('Thay đổi')) {
            // Save previous section
            if (currentSection && contentLines.length > 0) {
                sections.push({
                    icon: sectionIcons[currentSection] || '📊',
                    title: currentSection,
                    content: contentLines.join('\n')
                });
            }

            currentSection = line;
            contentLines = [];
            inSection = true;
        } else if (inSection && line) {
            contentLines.push(line);
        }
    }

    // Save last section
    if (currentSection && contentLines.length > 0) {
        sections.push({
            icon: sectionIcons[currentSection] || '📊',
            title: currentSection,
            content: contentLines.join('\n')
        });
    }

    return sections;
}

// Index definitions with line ranges
const indices = [
    { name: 'vn30', title: 'VN30 - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 222, end: 395 },
    { name: 'vn100', title: 'VN100 - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 396, end: 544 },
    { name: 'vnmidcap', title: 'VNMIDCAP - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 547, end: 700 },
    { name: 'vnreal', title: 'VNREAL - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 704, end: 847 },
    { name: 'vnit', title: 'VNIT - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 848, end: 981 },
    { name: 'vnheal', title: 'VNHEAL - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 982, end: 1163 },
    { name: 'vnfin', title: 'VNFIN - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 1164, end: 1323 },
    { name: 'vnene', title: 'VNENE - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 1324, end: 1464 },
    { name: 'vncons', title: 'VNCONS - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 1465, end: 1606 },
    { name: 'vnmat', title: 'VNMAT - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 1607, end: 1755 },
    { name: 'vncond', title: 'VNCOND - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 1756, end: 1900 },
    { name: 'vnsml', title: 'VNSML - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 1928, end: 2075 },
    { name: 'vnfinselect', title: 'VNFINSELECT - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 2076, end: 2221 },
    { name: 'vndiamond', title: 'VNDIAMOND - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 2222, end: 2372 }
];

// Build output
let output = `// DỮ LIỆU ĐẦY ĐỦ CHO TẤT CẢ CÁC CHỈ SỐ - 100% TỪ FILE GỐC
// Tự động tạo từ baocao_full.txt

const FULL_DATA = {
    vnindex: ${vnindexData},
`;

// Process each index
indices.forEach((index, idx) => {
    console.log(`Processing ${index.name}...`);
    const sections = extractSections(index.start, index.end, index.name);
    console.log(`  Found ${sections.length} sections`);

    output += `    ${index.name}: {\n`;
    output += `        title: "${index.title}",\n`;
    output += `        sections: [\n`;

    sections.forEach((section, sidx) => {
        // Convert content to HTML-like format
        let htmlContent = section.content
            .replace(/^Kết luận ngắn:/gm, '<strong>Kết luận:</strong>')
            .replace(/^Dẫn chứng từ dữ liệu:/gm, '<strong>Dẫn chứng:</strong>')
            .replace(/^Ý nghĩa\/Hành động:/gm, '<strong>Ý nghĩa:</strong>')
            .replace(/^Điều kiện khiến kết luận sai:/gm, '<strong>Điều kiện sai:</strong>')
            .replace(/^- /gm, '• ')
            .replace(/^\d+\. /gm, '<strong>$&</strong>');

        output += `            {\n`;
        output += `                icon: "${section.icon}",\n`;
        output += `                title: "${section.title}",\n`;
        output += `                content: \`${htmlContent.trim()}\`\n`;
        output += `            }${sidx < sections.length - 1 ? ',' : ''}\n`;
    });

    output += `        ]\n`;
    output += `    }${idx < indices.length - 1 ? ',' : ''}\n`;
});

output += `};\n\nmodule.exports = FULL_DATA;\n`;

// Write output
fs.writeFileSync('/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/UI GLM/full_data.js', output, 'utf8');
console.log('\n✅ Successfully created full_data.js');
console.log(`📊 Parsed ${indices.length} indices`);
