const FULL_DATA = require('./full_data.js');

console.log('📊 VERIFICATION REPORT\n');
console.log('='.repeat(60));

Object.keys(FULL_DATA).forEach((key, index) => {
    const data = FULL_DATA[key];
    const sectionCount = data.sections ? data.sections.length : 0;
    
    console.log(`\n${index + 1}. ${key.toUpperCase().padEnd(15)} - ${sectionCount} sections`);
    console.log(`   Title: ${data.title}`);
    
    if (sectionCount > 0) {
        console.log(`   Sections:`);
        data.sections.forEach((section, sidx) => {
            const contentPreview = section.content.substring(0, 50).replace(/\n/g, ' ');
            console.log(`     ${sidx + 1}. ${section.icon} ${section.title} (${contentPreview}...)`);
        });
    }
});

console.log('\n' + '='.repeat(60));
const totalIndices = Object.keys(FULL_DATA).length;
const totalSections = Object.values(FULL_DATA).reduce((sum, idx) => sum + (idx.sections ? idx.sections.length : 0), 0);
console.log(`\n✅ Total indices: ${totalIndices}`);
console.log(`✅ Total sections: ${totalSections}`);
console.log(`✅ Average sections per index: ${(totalSections / totalIndices).toFixed(1)}`);
