const fs = require('fs');
const content = fs.readFileSync('full_data.js', 'utf8');

// Extract indices
const indices = content.match(/(\w+):\s*\{\s*title:/g);

if (indices) {
    console.log('📊 SECTIONS PER INDEX:\n');
    
    // Count sections per index
    const indexPattern = /(\w+):\s*\{\s*title:\s*"([^"]+)",\s*sections:\s*\[/g;
    let match;
    let indexNum = 0;
    
    while ((match = indexPattern.exec(content)) !== null) {
        const indexName = match[1];
        const title = match[2];
        
        // Count sections for this index
        const start = match.index + match[0].length;
        const end = content.indexOf('\n        ]\n    }', start);
        const sectionContent = content.substring(start, end);
        
        const sectionCount = (sectionContent.match(/icon:/g) || []).length;
        
        indexNum++;
        console.log(`${indexNum}. ${indexName.toUpperCase().padEnd(15)} - ${sectionCount.toString().padStart(2)} sections - ${title}`);
    }
    
    console.log(`\n✅ Total indices: ${indexNum}`);
}
