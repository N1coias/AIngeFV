:root{
  font-family:Segoe UI,Arial,sans-serif;
  color:#17324a;
  background:#f4f8fb;
}
*{box-sizing:border-box}
body{margin:0}
main{max-width:1320px;margin:auto;padding:24px}
header{display:flex;align-items:center;gap:14px;margin-bottom:20px}
header button{margin-left:auto}
.logo{font-size:40px;color:#0b5c96}
h1,h2{color:#0b5c96}
h1{margin:0}
header p{margin:3px 0;color:#6b7e8d}
.two{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.card,.kpis>div{
  background:white;
  border:1px solid #d8e5ee;
  border-radius:16px;
  padding:18px;
  box-shadow:0 8px 24px rgba(28,77,112,.05);
  margin-bottom:16px;
}
.grid{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(155px,1fr));
  gap:12px;
}
label{font-size:13px;font-weight:700}
input,select{
  display:block;
  width:100%;
  margin-top:5px;
  padding:10px;
  border:1px solid #c9d9e5;
  border-radius:9px;
  background:white;
}
button{
  border:0;
  border-radius:9px;
  padding:10px 13px;
  margin-top:12px;
  font-weight:700;
  cursor:pointer;
  background:#1680c0;
  color:white;
}
button.secondary{background:#e7f2f9;color:#0b5c96}
.status{
  display:inline-block;
  margin:12px 0 0 10px;
  font-size:12px;
  color:#607588;
}
.reader{
  margin:12px 0;
  padding:12px;
  border-radius:10px;
  background:#f3f8fb;
}
.kpis{
  display:grid;
  grid-template-columns:repeat(4,1fr);
  gap:12px;
}
.kpis.compact{margin:0}
.kpis span{
  display:block;
  font-size:12px;
  color:#6b7e8d;
}
.kpis strong{
  display:block;
  font-size:22px;
  color:#0b5c96;
  margin-top:6px;
}
.error,.warning{
  padding:12px;
  border-radius:10px;
  margin-bottom:16px;
}
.error{background:#fdebea;color:#98251f}
.warning{background:#fff3d9;color:#795800}
.title-row{
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:12px;
}
.title-row h2{margin:0}
.table{overflow:auto}
table{width:100%;border-collapse:collapse}
th,td{
  padding:9px;
  border-bottom:1px solid #e1eaf0;
  text-align:center;
  font-size:13px;
}
th{background:#eaf4fb}
tr.best{background:#e8f8f0}
@media(max-width:900px){
  .two,.kpis{grid-template-columns:1fr 1fr}
}
@media(max-width:620px){
  .two,.kpis{grid-template-columns:1fr}
  header{align-items:flex-start;flex-wrap:wrap}
  header button{margin-left:0}
  .title-row{align-items:stretch;flex-direction:column}
}


.optimizer-rules{
  margin-top:16px;
  padding:14px;
  border-radius:12px;
  background:#eef8f2;
  border:1px solid #cce9d6;
}
.optimizer-rules h3{margin:0 0 8px;color:#17623a}
.optimizer-rules p{margin:5px 0}
.inverter-grid{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
  gap:14px;
}
.inverter-card{
  border:1px solid #d8e5ee;
  border-radius:14px;
  padding:14px;
  background:#f9fcfe;
}
.inverter-card h3{margin-top:0;color:#0b5c96}
.mppt-list{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(105px,1fr));
  gap:8px;
}
.mppt-item{
  padding:9px;
  border-radius:10px;
  background:white;
  border:1px solid #dce8ef;
  text-align:center;
}
.mppt-item span,.mppt-item small{display:block;color:#6b7e8d}
.mppt-item strong{display:block;font-size:18px;color:#0b5c96;margin:3px 0}
.tags{display:flex;flex-wrap:wrap;gap:4px;min-width:170px}
.tags span{
  display:inline-block;
  padding:4px 7px;
  border-radius:999px;
  background:#e7f2f9;
  color:#0b5c96;
  font-size:11px;
  white-space:nowrap;
}
