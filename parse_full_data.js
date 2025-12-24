const fs = require('fs');

// Read the file
const content = fs.readFileSync('/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/UI GLM/baocao_full.txt', 'utf8');
const lines = content.split('\n');

// Read vnindex data
const vnindexContent = fs.readFileSync('/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/UI GLM/vnindex_data.js', 'utf8');

// Extract VNINDEX data - get the sections array
const vnindexSectionsMatch = vnindexContent.match(/sections:\s*\[[\s\S]*?\s+\]/);
const vnindexSectionData = vnindexSectionsMatch ? vnindexSectionsMatch[0].replace('sections:', '').trim() : '';

// Known section patterns with icons
const sectionPatterns = [
    { pattern: /Xu Hướng Giá/, icon: '📈', title: 'XU HƯỚNG GIÁ' },
    { pattern: /Xu Hướng Khối Lượng/, icon: '📊', title: 'XU HƯỚNG KHỐI LƯỢNG' },
    { pattern: /Kết Hợp Xu Hướng Giá và Khối Lượng/, icon: '💹', title: 'KẾT HỢP XU HƯỚNG GIÁ & KHỐI LƯỢNG' },
    { pattern: /Cung-Cầu/, icon: '⚖️', title: 'CUNG - CẦU' },
    { pattern: /Mức Giá Quan Trọng/, icon: '🎯', title: 'MỨC GIÁ QUAN TRỌNG' },
    { pattern: /Biến Động Giá/, icon: '📉', title: 'BIẾN ĐỘNG GIÁ' },
    { pattern: /Mô hình giá - Mô hình nến/, icon: '🕯️', title: 'MÔ HÌNH GIÁ - MÔ HÌNH NẾN' },
    { pattern: /Market Breadth & Tâm Lý Thị Trường/, icon: '👥', title: 'MARKET BREADTH & TÂM LÝ THỊ TRƯỜNG' },
    { pattern: /Lịch Sử & Xu Hướng Breadth/, icon: '📜', title: 'LỊCH SỬ & XU HƯỚNG BREADTH' },
    { pattern: /^Rủi Ro$/, icon: '⚠️', title: 'RỦI RO' },
    { pattern: /Khuyến Nghị Vị Thế/, icon: '🎯', title: 'KHUYẾN NGHỊ VỊ THẾ', alert: true },
    { pattern: /Giá Mục Tiêu/, icon: '🎯', title: 'GIÁ MỤC TIÊU' },
    { pattern: /Kịch Bản "What-if"/, icon: '🎲', title: 'KỊCH BẢN WHAT-IF (Phiên tiếp theo & 1-5 phiên)' }
];

// Function to extract sections from a line range
function extractSections(startLine, endLine, indexName, currentPrice) {
    const sections = [];
    let currentSection = null;
    let contentLines = [];
    let currentIcon = '📊';
    let isAlert = false;

    for (let i = startLine - 1; i < Math.min(endLine, lines.length); i++) {
        const line = lines[i];
        const trimmedLine = line.trim();

        // Skip separator lines
        if (trimmedLine.match(/^─+$/)) continue;

        // Check if this line matches a known section pattern
        let matchedSection = null;
        for (const section of sectionPatterns) {
            if (trimmedLine.match(section.pattern)) {
                matchedSection = section;
                break;
            }
        }

        if (matchedSection) {
            // Save previous section
            if (currentSection && contentLines.length > 0) {
                const content = contentLines.join('\n').trim();
                if (content.length > 0) {
                    sections.push({
                        icon: currentIcon,
                        title: currentSection,
                        content: content,
                        alert: isAlert
                    });
                }
            }

            currentSection = matchedSection.title;
            currentIcon = matchedSection.icon;
            isAlert = matchedSection.alert || false;
            contentLines = [];
        } else if (currentSection && trimmedLine && !trimmedLine.startsWith('Giá hiện tại') &&
                   !trimmedLine.startsWith('Thay đổi') && !trimmedLine.startsWith('Khối lượng') &&
                   !trimmedLine.startsWith('Tương quan') && !trimmedLine.startsWith('Phân tích chi tiết')) {
            // Add content to current section
            contentLines.push(line);
        }
    }

    // Save last section
    if (currentSection && contentLines.length > 0) {
        const content = contentLines.join('\n').trim();
        if (content.length > 0) {
            sections.push({
                icon: currentIcon,
                title: currentSection,
                content: content,
                alert: isAlert
            });
        }
    }

    return sections;
}

// Index definitions with line ranges
const indices = [
    { name: 'vn30', title: 'VN30 - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 229, end: 392 },
    { name: 'vn100', title: 'VN100 - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 400, end: 543 },
    { name: 'vnmidcap', title: 'VNMIDCAP - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 551, end: 699 },
    { name: 'vnreal', title: 'VNREAL - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 708, end: 846 },
    { name: 'vnit', title: 'VNIT - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 852, end: 980 },
    { name: 'vnheal', title: 'VNHEAL - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 986, end: 1162 },
    { name: 'vnfin', title: 'VNFIN - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 1168, end: 1322 },
    { name: 'vnene', title: 'VNENE - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 1328, end: 1463 },
    { name: 'vncons', title: 'VNCONS - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 1469, end: 1605 },
    { name: 'vnmat', title: 'VNMAT - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 1611, end: 1754 },
    { name: 'vncond', title: 'VNCOND - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 1760, end: 1899 },
    { name: 'vnsml', title: 'VNSML - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 1932, end: 2074 },
    { name: 'vnfinselect', title: 'VNFINSELECT - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 2080, end: 2220 },
    { name: 'vndiamond', title: 'VNDIAMOND - PHÂN TÍCH ĐẦY ĐỦ 100%', start: 2226, end: 2372 }
];

// Build output
let output = `// DỮ LIỆU ĐẦY ĐỦ CHO TẤT CẢ CÁC CHỈ SỐ - 100% TỪ FILE GỐC
// Tự động tạo từ baocao_full.txt

const FULL_DATA = {
    vnindex: {
        title: "VNINDEX - PHÂN TÍCH ĐẦY ĐỦ 100%",
        sections: ${vnindexSectionData}
    },
`;

// Process each index
indices.forEach((index, idx) => {
    console.log(`Processing ${index.name} (lines ${index.start}-${index.end})...`);
    const sections = extractSections(index.start, index.end, index.name);
    console.log(`  Found ${sections.length} sections`);

    output += `    ${index.name}: {\n`;
    output += `        title: "${index.title}",\n`;
    output += `        sections: [\n`;

    sections.forEach((section, sidx) => {
        // Clean and format content
        let cleanContent = section.content
            .replace(/`/g, '\\`')  // Escape backticks
            .replace(/\${/g, '\\\\${')  // Escape template literals
            .trim();

        output += `            {\n`;
        output += `                icon: "${section.icon}",\n`;
        output += `                title: "${section.title}",\n`;
        if (section.alert) {
            output += `                alert: true,\n`;
        }
        output += `                content: \`\n${cleanContent}\n\`\n`;
        output += `            }${sidx < sections.length - 1 ? ',' : ''}\n`;
    });

    output += `        ]\n`;
    output += `    }${idx < indices.length - 1 ? ',' : ''}\n`;
    console.log(`  ✅ Parsed ${sections.length} sections for ${index.name}`);
});

output += `};\n\nmodule.exports = FULL_DATA;\n`;

// Write output
fs.writeFileSync('/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/UI GLM/full_data.js', output, 'utf8');
console.log('\n✅ Successfully created full_data.js');
console.log(`📊 Total indices parsed: ${indices.length + 1} (including VNINDEX)`);
