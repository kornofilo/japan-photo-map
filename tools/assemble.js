const fs=require("fs");
const css=fs.readFileSync("node_modules/leaflet/dist/leaflet.css","utf8").replace(/[^{}]*\{[^{}]*url\([^{}]*\}/g,"");
let t=fs.readFileSync("template2.html","utf8");
for (const [a,b] of [["/*LEAFLET_CSS*/",css],["__DATA__",fs.readFileSync("data.json","utf8")]]) { if(!t.includes(a)) throw new Error("missing "+a); t=t.split(a).join(b); }
fs.mkdirSync("site2",{recursive:true}); fs.writeFileSync("site2/index.html",t);
fs.writeFileSync("test2.html",t.replace(/<script src="https:\/\/cdnjs[^"]+"><\/script>/,()=>"<script>"+fs.readFileSync("node_modules/leaflet/dist/leaflet.js","utf8")+"</script>"));
console.log((t.length/1024).toFixed(0)+" KB");
