"""Graph 9 — Interactive TMDB genre co-occurrence network.
Run: python graph9_network.py
Requires: pandas, plotly, networkx. Input: tmdb_cleaned.csv in the same folder.
"""
from pathlib import Path
from collections import Counter
from itertools import combinations
import ast, json, math, html, zipfile
import pandas as pd
import networkx as nx
from plotly.offline import get_plotlyjs

ROOT=Path(__file__).resolve().parent
INPUT=ROOT/'tmdb_cleaned.csv'
OUTPUT=ROOT/'Grafik_9_Ag_Grafigi.html'
BG='#FAF7F2'; INK='#353535'; TEAL='#34877E'; GOLD='#D5A14A'; RED='#B5534B'

def parse_genres(row):
    if not isinstance(row,str) or not row.strip():return []
    try: a=json.loads(row)
    except (ValueError,TypeError):
        try:a=ast.literal_eval(row)
        except (ValueError,SyntaxError):return []
    if not isinstance(a,list):return []
    return sorted(set(str(z['name']).strip() for z in a if isinstance(z,dict) and z.get('name')))

def main(df=None):
    if df is None:
        df = pd.read_csv(INPUT)
    counts=Counter(); pairs=Counter(); examples={}
    for row in df.itertuples(index=False):
        gs=parse_genres(row.genres)
        for g in gs:counts[g]+=1
        for a,b in combinations(gs,2):
            pairs[(a,b)]+=1
            if len(examples.get((a,b),[]))<3:examples.setdefault((a,b),[]).append(str(row.title))
    G=nx.Graph()
    for g,n in counts.items():G.add_node(g,count=n)
    for (a,b),n in pairs.items():G.add_edge(a,b,weight=n)
    # Deterministic layout based on all edges; filtering does not rearrange the nodes.
    # Unweighted Kamada-Kawai spreads even weakly connected genres across the canvas.
    # A collision-relaxation pass reserves room for node circles and their labels.
    pos=nx.kamada_kawai_layout(G,weight=None,scale=1.0)
    import numpy as np
    names=list(G.nodes)
    xy_arr=np.array([pos[g] for g in names],dtype=float)
    radii=np.array([0.105+0.0022*math.sqrt(counts[g]) for g in names])
    for _ in range(420):
        movement=np.zeros_like(xy_arr)
        for i in range(len(names)):
            for j in range(i+1,len(names)):
                delta=xy_arr[i]-xy_arr[j]
                dist=float(np.linalg.norm(delta))
                min_dist=radii[i]+radii[j]+0.105
                if dist<min_dist:
                    direction=delta/dist if dist>1e-8 else np.array([math.cos(i+j),math.sin(i+j)])
                    push=(min_dist-dist)*0.22*direction
                    movement[i]+=push
                    movement[j]-=push
        xy_arr+=movement
        xy_arr-=xy_arr.mean(axis=0)
    pos={g:xy_arr[i] for i,g in enumerate(names)}
    xy={g:[float(pos[g][0]),float(pos[g][1])] for g in G.nodes}
    nodes=sorted(counts,key=lambda g:(-counts[g],g))
    edges=[{'a':a,'b':b,'n':n,'examples':examples.get((a,b),[])} for (a,b),n in sorted(pairs.items(),key=lambda p:-p[1])]
    payload=json.dumps({'nodes':[{'name':g,'count':counts[g],'xy':xy[g]} for g in nodes], 'edges':edges,'movies':len(df)},ensure_ascii=False)
    js=get_plotlyjs()
    page=r'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Movie Genre Connections — Graph 9</title>
<style>
:root{--bg:#FAF7F2;--ink:#353535;--teal:#34877E;--gold:#D5A14A;--red:#B5534B}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px Arial,sans-serif}.wrap{max-width:1390px;margin:auto;padding:32px 34px}h1{font-size:28px;margin:0 0 9px}h2{font-size:16px;margin:0 0 10px}.subtitle{color:#77716b;margin:0 0 22px}.toolbar{display:flex;align-items:center;gap:15px;flex-wrap:wrap;margin-bottom:16px;padding:14px 18px;border:1px solid #e5ded5;border-radius:12px;background:white}.toolbar input{accent-color:var(--teal);width:180px}.toolbar select,.toolbar button{border:1px solid #d9d0c6;background:#FAF7F2;border-radius:6px;padding:8px 10px;color:var(--ink)}button{cursor:pointer}.layout{display:grid;grid-template-columns:minmax(0,1fr) 295px;gap:18px}.card{border:1px solid #e5ded5;background:white;border-radius:14px;padding:18px;min-width:0}#network{height:700px;cursor:grab;touch-action:none}.help,.foot{font-size:12px;color:#817c75;line-height:1.6}.stat{font-size:25px;font-weight:bold;color:var(--teal)}.muted{color:#77716b;font-size:12px}.connection{border-bottom:1px solid #eee8e1;padding:10px 0;display:flex;justify-content:space-between;gap:8px}.connection b{color:var(--teal)}.pill{display:inline-block;border-radius:12px;padding:5px 9px;background:#e5f0ed;color:#27685f;font-size:12px}.legend{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-top:8px;color:#6e6962;font-size:12px}.swatch{width:12px;height:12px;border-radius:50%;background:var(--teal);display:inline-block}.swatch2{width:24px;height:4px;background:#828986;display:inline-block}.foot{margin-top:20px}@media(max-width:900px){.layout{grid-template-columns:1fr}#network{height:570px}.wrap{padding:20px 12px}}
/* Soft white SVG halo keeps labels legible over crossing edges at every zoom level. */
#network .textlayer .textpoint text{paint-order:stroke fill;stroke:rgba(255,255,255,.94);stroke-width:3.5px;stroke-linejoin:round;stroke-linecap:round;}
</style><script>__PLOTLY__</script></head><body><main class="wrap"><h1>Movie Genre Connections</h1><p class="subtitle">Explore which movie genres appear together · TMDB dataset · Each film is counted once per genre and genre pair</p>
<div class="toolbar"><label for="minEdge"><b>Minimum shared movies:</b> <span id="minLabel">25</span></label><input type="range" id="minEdge" min="1" max="250" value="25" step="1"><label for="genreSelect"><b>Highlight genre:</b></label><select id="genreSelect"><option value="">All genres</option></select><button id="reset">↺ Reset view</button><span class="muted" id="shown"></span></div>
<div class="layout"><section class="card"><h2>Genre relationship map</h2><p class="help">Scroll to zoom; hold the right mouse button and drag to pan within the network bounds. Left-click a genre to highlight its connections.</p><div id="network"></div><div class="legend"><span class="swatch"></span> Genre (size = movie count) <span class="swatch2"></span> Shared movies (thicker = more)</div></section>
<aside class="card"><h2 id="panelTitle">All movie genres</h2><p class="muted" id="panelHint">Select a genre to explore its strongest connections.</p><div class="stat" id="panelCount"></div><p class="muted" id="panelUnit"></p><h2 style="margin-top:24px">Strongest connections</h2><div id="connections"></div></aside></div>
<p class="foot">Data: TMDB movie dataset. Genres are multi-label: a movie may connect several genres. Connections show co-occurrence, not similarity or causation. The network layout is a visualization aid; distances are not precise similarity scores. All genre labels are available on hover, including smaller nodes. Labels for major genres are placed above their nodes.</p></main>
<script>
const DATA=__DATA__, nodes=DATA.nodes, edges=DATA.edges, graph=document.getElementById('network');
const select=document.getElementById('genreSelect'), slider=document.getElementById('minEdge');let selected='',threshold=25;
for(const n of [...nodes].sort((a,b)=>a.name.localeCompare(b.name))){const opt=document.createElement('option');opt.value=n.name;opt.textContent=n.name;select.appendChild(opt)}
const nodeIndex=Object.fromEntries(nodes.map((n,i)=>[n.name,i]));
const xs=nodes.map(n=>n.xy[0]),ys=nodes.map(n=>n.xy[1]);
const xMin=Math.min(...xs),xMax=Math.max(...xs),yMin=Math.min(...ys),yMax=Math.max(...ys);
const xPad=(xMax-xMin)*0.035+0.09,yPad=(yMax-yMin)*0.045+0.09;
const xRange=[xMin-xPad,xMax+xPad],yRange=[yMin-yPad,yMax+yPad];
const fullX=xRange.slice(),fullY=yRange.slice();let viewX=xRange.slice(),viewY=yRange.slice();
const maxZoom=4.0;
function clampRange(range,full){
 const fullWidth=full[1]-full[0],minWidth=fullWidth/maxZoom;
 let width=Math.min(fullWidth,Math.max(minWidth,range[1]-range[0]));
 let center=(range[0]+range[1])/2;
 let low=Math.max(full[0],Math.min(full[1]-width,center-width/2));
 return [low,low+width];
}
function labelFontSize(){
 const zoom=(fullX[1]-fullX[0])/(viewX[1]-viewX[0]);
 return Math.min(20,Math.round((12+4.5*(zoom-1))*10)/10);
}
function applyView(){
 Plotly.relayout(graph,{'xaxis.range':viewX,'yaxis.range':viewY});
 // Keep labels readable as the camera zooms in (markers stay unchanged).
 if(graph.data && graph.data.length){
  const nodeTrace=graph.data.length-1;
  Plotly.restyle(graph,{'textfont.size':labelFontSize()},[nodeTrace]);
 }
}
function resetCamera(){viewX=fullX.slice();viewY=fullY.slice();applyView();}
function zoomAt(clientX,clientY,factor){
 const rect=graph.getBoundingClientRect(),px=Math.max(0,Math.min(1,(clientX-rect.left)/rect.width)),py=Math.max(0,Math.min(1,(clientY-rect.top)/rect.height));
 const zoom=(r,t)=>{let v=r[0]+(r[1]-r[0])*t;return [v+(r[0]-v)*factor,v+(r[1]-v)*factor]};
 viewX=clampRange(zoom(viewX,px),fullX);viewY=clampRange(zoom(viewY,1-py),fullY);applyView();
}
// Right button pans; left click is reserved exclusively for genre selection.
// Track the drag on window so releasing the button outside the chart always ends it.
let panStart=null;
graph.addEventListener('contextmenu',e=>e.preventDefault());
// Defer blank-area clearing until Plotly has had time to dispatch plotly_click.
// Plotly's click target may be an overlay rather than a .point element.
let lastGenreClick=0;
graph.addEventListener('click',e=>{
 if(e.button!==0)return;
 const clickTime=Date.now();
 window.setTimeout(()=>{
  if(lastGenreClick>=clickTime-50 || !selected)return;
  selected='';select.value='';makePlot();updatePanel();
 },110);
});
graph.addEventListener('wheel',e=>{e.preventDefault();zoomAt(e.clientX,e.clientY,e.deltaY<0?0.88:1/0.88)},{passive:false});
graph.addEventListener('pointerdown',e=>{
 if(e.button!==2)return;
 e.preventDefault();
 panStart={x:e.clientX,y:e.clientY,xr:viewX.slice(),yr:viewY.slice(),id:e.pointerId};
 graph.style.cursor='grabbing';
});
window.addEventListener('pointermove',e=>{
 if(!panStart||e.pointerId!==panStart.id)return;
 // Recover from a missed pointerup, e.g. when focus changes.
 if(!(e.buttons&2)){panStart=null;graph.style.cursor='default';return;}
 e.preventDefault();
 const r=graph.getBoundingClientRect();
 const dx=(e.clientX-panStart.x)/r.width,dy=(e.clientY-panStart.y)/r.height;
 const wx=panStart.xr[1]-panStart.xr[0],wy=panStart.yr[1]-panStart.yr[0];
 viewX=clampRange([panStart.xr[0]-dx*wx,panStart.xr[1]-dx*wx],fullX);
 viewY=clampRange([panStart.yr[0]+dy*wy,panStart.yr[1]+dy*wy],fullY);
 applyView();
});
function endPan(e){if(panStart && (e.pointerId===panStart.id||e.type==='blur')){panStart=null;graph.style.cursor='default';}}
window.addEventListener('pointerup',endPan);
window.addEventListener('pointercancel',endPan);
window.addEventListener('blur',endPan);

function makePlot(){
 const active=edges.filter(e=>e.n>=threshold && (!selected||e.a===selected||e.b===selected));
 const edgeTraces=active.map(e=>{const a=nodes[nodeIndex[e.a]],b=nodes[nodeIndex[e.b]];return {type:'scatter',mode:'lines',x:[a.xy[0],b.xy[0]],y:[a.xy[1],b.xy[1]],line:{width:Math.max(1,Math.min(9,1+Math.sqrt(e.n)/3)),color:selected?'rgba(213,161,74,0.78)':'rgba(130,137,134,0.30)'},hoverinfo:'skip',showlegend:false}});
 const connected=new Set();for(const e of active){connected.add(e.a);connected.add(e.b)}
 const visibleNodes=nodes.filter(n=>connected.has(n.name));
 const ns={type:'scatter',mode:'markers+text',x:visibleNodes.map(n=>n.xy[0]),y:visibleNodes.map(n=>n.xy[1]),text:visibleNodes.map(n=>n.count>=100||n.name===selected?n.name:''),textposition:'top center',textfont:{size:labelFontSize(),color:'#353535'},customdata:visibleNodes.map(n=>[n.name,n.count]),hovertemplate:'<b>%{customdata[0]}</b><br>%{customdata[1]:,} movies<extra></extra>',marker:{size:visibleNodes.map(n=>10+Math.sqrt(n.count)*1.45),color:visibleNodes.map(n=>n.name===selected?'#D5A14A':selected&&!connected.has(n.name)?'#C9C8C3':'#34877E'),opacity:visibleNodes.map(n=>selected&&!connected.has(n.name)?.32:.9),line:{color:'#FFFFFF',width:1.6}},showlegend:false};
 const layout={paper_bgcolor:'#FFFFFF',plot_bgcolor:'#FFFFFF',font:{family:'Arial,sans-serif',color:'#353535'},margin:{l:25,r:25,t:30,b:20},xaxis:{visible:false,scaleanchor:'y',scaleratio:1,range:[...viewX],fixedrange:true},yaxis:{visible:false,range:[...viewY],fixedrange:true},dragmode:false,hovermode:'closest',showlegend:false};
 Plotly.react(graph,[...edgeTraces,ns],layout,{responsive:true,scrollZoom:false,displaylogo:false,modeBarButtonsToRemove:['lasso2d','select2d']}).then(()=>{
  graph.removeAllListeners('plotly_click');graph.on('plotly_click',ev=>{const p=ev.points?.[0];if(p?.customdata?.[0]){lastGenreClick=Date.now();selected=p.customdata[0];select.value=selected;makePlot();updatePanel()}})
 });
 document.getElementById('shown').textContent=`${active.length} connections shown · ${visibleNodes.length} genres`;
}
function updatePanel(){const box=document.getElementById('connections');box.replaceChildren();const arr=edges.filter(e=>!selected||e.a===selected||e.b===selected).sort((a,b)=>b.n-a.n).slice(0,9);
 document.getElementById('panelTitle').textContent=selected||'All movie genres';document.getElementById('panelHint').textContent=selected?'Movies tagged with this genre and its strongest co-occurring genres.':'Top genre combinations across the dataset.';
 document.getElementById('panelCount').textContent=selected?nodes[nodeIndex[selected]].count.toLocaleString('en-US'):DATA.movies.toLocaleString('en-US');document.getElementById('panelUnit').textContent=selected?'movies tagged '+selected:'movies in dataset';
 for(const e of arr){const row=document.createElement('div');row.className='connection';const name=document.createElement('span');name.textContent=selected?(e.a===selected?e.b:e.a):e.a+' + '+e.b;const count=document.createElement('b');count.textContent=e.n.toLocaleString();row.append(name,count);box.appendChild(row)}
}
slider.addEventListener('input',()=>{threshold=+slider.value;document.getElementById('minLabel').textContent=threshold;makePlot()});select.addEventListener('change',()=>{selected=select.value;makePlot();updatePanel()});document.getElementById('reset').addEventListener('click',()=>{selected='';select.value='';threshold=25;slider.value=25;viewX=fullX.slice();viewY=fullY.slice();document.getElementById('minLabel').textContent='25';makePlot();updatePanel()});
makePlot();updatePanel();
</script></body></html>'''
    page=page.replace('__PLOTLY__',js).replace('__DATA__',payload)
    return page
    if __name__=='__main__':main()
