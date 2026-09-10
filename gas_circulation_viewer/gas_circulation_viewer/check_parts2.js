const fs = require('fs');
const b = fs.readFileSync('C:/Users/Administrator/Desktop/Tesla_Control_UI/gas_circulation_process_modifier.glb');
const jsonLen = b.readUInt32LE(12);
const json = JSON.parse(b.toString('utf8', 20, 20 + jsonLen));
const names = [];
json.nodes.forEach((n, i) => {
    if (n.name && /nut_m01[12]|bolt_short_m00[23]/.test(n.name)) {
        names.push({ i, name: n.name, mesh: n.mesh !== undefined, children: n.children ? n.children.length : 0 });
    }
});
console.log(`total nodes: ${json.nodes.length}`);
names.forEach(x => console.log(`[${x.i}] ${x.name} mesh=${x.mesh} children=${x.children}`));
console.log('count:', names.length);