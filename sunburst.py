"""Chart 8: static-depth Sunburst plus interactive cross-era rating comparison.
Run: python grafik8_kaynak_kod.py (requires pandas, plotly and tmdb_cleaned.csv).
"""
from pathlib import Path
import json
import pandas as pd
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs

BG='#FAF7F2'
PERIODS=['Pre-1980s','1980s','1990s','2000s','2010s','Unknown year']
PERIOD_COLORS=['#7897A6','#B98B82','#C2A36E','#77A59B','#A094B6','#AAA7A1']
RATINGS=['0–3.9','4.0–5.9','6.0–7.9','8.0–10','Unrated']
RATING_COLORS={'0–3.9':'#B5534B','4.0–5.9':'#D5A14A','6.0–7.9':'#9BBCA9','8.0–10':'#34877E','Unrated':'#B7B4AE'}
GENRE_COLORS=['#F0ECE5','#E8E3DA','#F5F1EB','#EDE8DF','#E4DED5','#F2EEE8','#DDD8D0']

def prepare_data(df):
    required={'release_year','primary_genre','vote_average','vote_count'}
    if missing:=required-set(df.columns):
        raise ValueError(f'Missing columns: {sorted(missing)}')
    d=df.copy()
    year=pd.to_numeric(d['release_year'],errors='coerce')
    d=d.loc[year.notna()].copy()
    year=year.loc[d.index]
    d['period']='Unknown year'
    d.loc[year<1980,'period']='Pre-1980s'
    for start in (1980,1990,2000,2010):
        d.loc[(year>=start)&(year<start+10),'period']=f'{start}s'
    future=year>=2020
    d.loc[future,'period']=((year.loc[future]//10)*10).astype(int).astype(str)+'s'
    d['primary_genre']=d['primary_genre'].fillna('').astype(str).str.strip()
    d.loc[d['primary_genre'].isin(['','Unknown','nan','None']),'primary_genre']='Unclassified'
    v=pd.to_numeric(d['vote_average'],errors='coerce')
    counts=pd.to_numeric(d['vote_count'],errors='coerce').fillna(0)
    d['rating_band']='Unrated'
    valid=(counts>0)&v.notna()&(v>0)
    d.loc[valid&(v<4),'rating_band']='0–3.9'
    d.loc[valid&(v>=4)&(v<6),'rating_band']='4.0–5.9'
    d.loc[valid&(v>=6)&(v<8),'rating_band']='6.0–7.9'
    d.loc[valid&(v>=8),'rating_band']='8.0–10'
    genre_sizes=d.groupby(['period','primary_genre'])['primary_genre'].transform('size')
    era_sizes=d.groupby('period')['period'].transform('size')
    d['display_genre']=d['primary_genre'].where(genre_sizes / era_sizes >= 0.025,'Other')
    return d

def create_sunburst_plot(df):
    d=prepare_data(df)
    periods=[p for p in PERIODS if p in set(d.period)]+sorted(set(d.period)-set(PERIODS))
    ids=[];labels=[];parents=[];values=[];colors=[];custom=[];texts=[]
    for pi,period in enumerate(periods):
        pd_=d[d.period==period];pid=f'period:{period}'
        ids.append(pid);labels.append(period);parents.append('');values.append(len(pd_));colors.append(PERIOD_COLORS[pi%len(PERIOD_COLORS)]);custom.append('Era');texts.append(period)
        for i,(genre,n) in enumerate(pd_['display_genre'].value_counts().items()):
            gd=pd_[pd_.display_genre==genre];gid=f'{pid}/genre:{genre}'
            ids.append(gid);labels.append(genre);parents.append(pid);values.append(int(n));colors.append(GENRE_COLORS[i%len(GENRE_COLORS)]);custom.append('First-listed genre');texts.append(genre if n>=25 else '')
            rc=gd.rating_band.value_counts()
            for rating in RATINGS:
                count=int(rc.get(rating,0))
                if not count:continue
                ids.append(f'{gid}/rating:{rating}');labels.append(rating);parents.append(gid);values.append(count);colors.append(RATING_COLORS[rating]);custom.append('TMDB rating band');texts.append(rating if count>=28 else '')
    fig=go.Figure(go.Sunburst(ids=ids,labels=labels,parents=parents,values=values,branchvalues='total',sort=False,maxdepth=3,
        marker=dict(colors=colors,line=dict(color=BG,width=1.25)),customdata=custom,text=texts,textinfo='text',
        hovertemplate='<b>%{label}</b><br>%{customdata}<br>Movies: %{value:,}<br>Share of parent: %{percentParent:.1%}<extra></extra>',
        insidetextorientation='auto',textfont=dict(size=11)))
    fig.update_layout(template='none',paper_bgcolor=BG,font=dict(family='Arial, sans-serif',color='#353535'),
        margin=dict(l=10,r=10,t=15,b=15),uniformtext=dict(minsize=9,mode='hide'),height=620)
    return fig

def build_comparison_data(d):
    periods=[p for p in PERIODS if p in set(d.period)]+sorted(set(d.period)-set(PERIODS))
    # Comparison uses original genres, never the Sunburst-only Other grouping.
    genres=['All genres']+sorted(d['primary_genre'].unique().tolist())
    result={}
    for genre in genres:
        subset=d if genre=='All genres' else d[d.primary_genre==genre]
        result[genre]={}
        for period in periods:
            piece=subset[subset.period==period]
            vc=piece.rating_band.value_counts()
            result[genre][period]=[int(vc.get(b,0)) for b in RATINGS]
    return result,periods,genres

def create_dashboard(df):
    d=prepare_data(df)
    fig=create_sunburst_plot(df)
    compare,periods,genres=build_comparison_data(d)
    payload=json.dumps({'counts':compare,'periods':periods,'genres':genres,'bands':RATINGS,'colors':[RATING_COLORS[x] for x in RATINGS]},ensure_ascii=False)
    sunburst_json=fig.to_json()
    options=''.join(f'<option value="{i}">{g}</option>' for i,g in enumerate(genres))
    html='''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Movie Eras, Genres & Ratings — Modern Cinema</title><style>
:root{--bg:#FAF7F2;--ink:#353535;--muted:#706B66;--line:#E6E0D8}*{box-sizing:border-box}
body{margin:0;background:var(--bg);font-family:Arial,Helvetica,sans-serif;color:var(--ink)}
.shell{max-width:1600px;margin:auto;padding:34px 36px 30px}h1{font-size:28px;margin:0 0 10px;letter-spacing:-.5px}
.subtitle{color:var(--muted);font-size:13px;margin:0 0 22px;line-height:1.6}
.panels{display:grid;grid-template-columns:minmax(0,1.06fr) minmax(0,1fr);gap:20px;align-items:stretch}
.panel{background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px;min-width:0}
h2{font-size:18px;margin:0 0 8px}.hint{font-size:12px;color:var(--muted);line-height:1.5;margin:0 0 10px}
#sunburstViewport{height:620px;width:100%;overflow:hidden;position:relative;touch-action:none;cursor:grab}#sunburstViewport.dragging{cursor:grabbing}#sunburst{height:620px;width:100%;position:absolute;top:0;left:0;transform:none;will-change:left,top}#comparison{height:465px;width:100%}
.zoom-controls{display:flex;align-items:center;gap:7px;margin:8px 0}.zoom-controls button{border:1px solid #D8D1C8;background:#FAF7F2;color:#353535;border-radius:7px;padding:7px 12px;cursor:pointer;font-size:13px}.zoom-controls button:hover{background:#ECE6DD}.zoom-level{font-size:12px;color:#706B66;min-width:43px;text-align:center}.control{display:flex;align-items:center;gap:12px;margin:16px 0 10px;flex-wrap:wrap}
.control label{font-size:13px;font-weight:600}select{background:#FAF7F2;border:1px solid #D8D1C8;border-radius:7px;padding:10px 12px;color:var(--ink);font-size:13px;min-width:170px;max-width:100%}
.legend{display:flex;gap:10px 16px;flex-wrap:wrap;margin:12px 0 6px;font-size:12px;color:#56524F}.shared-legend{margin:0 0 20px;gap:12px 22px}.key{display:inline-flex;align-items:center;gap:6px}.swatch{width:12px;height:12px;border-radius:3px;display:inline-block}
#stats{color:var(--muted);font-size:12px;margin:4px 0 8px}.foot{color:var(--muted);font-size:12px;line-height:1.6;margin-top:20px}
@media(max-width:1020px){.panels{grid-template-columns:1fr}.shell{padding:22px 14px}#sunburstViewport,#sunburst{height:570px}#comparison{height:440px}}
</style></head><body><main class="shell">
<h1>Movie Eras, Genres & Audience Ratings</h1>
<p class="subtitle">__TOTAL__ movies · Era → first-listed genre → TMDB rating band · Genres below 2.5% of their era grouped as Other</p>
<div id="legend" class="legend shared-legend"></div>
<div class="panels"><section class="panel"><h2>Genre landscape</h2><p class="hint">All eras and rating bands remain visible. Scroll to zoom and reveal smaller genre and rating labels; drag to move. Clicking sectors does not navigate.</p><div class="zoom-controls"><button id="zoomOut" type="button" aria-label="Zoom out">−</button><span id="zoomLevel" class="zoom-level">100%</span><button id="zoomIn" type="button" aria-label="Zoom in">+</button><button id="zoomReset" type="button">↺ Reset</button></div><div id="sunburstViewport"><div id="sunburst"></div></div></section>
<section class="panel"><h2>Compare eras side by side</h2><p class="hint">Choose a genre to compare movie counts and rating distributions across eras. Bar lengths represent movie counts; colors show rating bands.</p>
<div class="control"><label for="genre">Movie genre</label><select id="genre">__OPTIONS__</select></div>
<div id="stats"></div><div id="comparison"></div>
<p class="hint" style="margin-top:16px">Hover over a bar segment to see its movie count. Larger bars represent more movies. Eras with no films in the selected genre are shown as empty.</p></section></div>
<p class="foot">Data: TMDB movie dataset. Each movie is counted once, using its first-listed genre. A 0.0 rating or zero votes is treated as Unrated. The charts compare dataset composition, not all films ever released. Only the Sunburst groups genres representing less than 2.5% of their era as “Other”; the comparison uses original genre labels. __EXCLUDED__ movie(s) with missing release year excluded.</p>
</main><script>__PLOTLY__</script><script>
const DATA=__DATA__;const SUN=__SUN__;
// Crisp zoom: resize and re-render Plotly's SVG, never scale a rasterized layer.
const sun=document.getElementById('sunburst');
// Preserve every genre and rating node; reveal labels as zoom increases.
const LABELS=SUN.data[0].labels;
const VALUES=SUN.data[0].values;
const PARENTS=SUN.data[0].parents;
let lastLabelSignature='';
function labelsForZoom(z){
 const genreMin=Math.max(1,Math.ceil(25/Math.pow(z,1.8)));
 const ratingMin=Math.max(1,Math.ceil(28/Math.pow(z,1.8)));
 return LABELS.map((label,i)=>{
   const parent=PARENTS[i]||'';
   if(!parent)return label;
   const rating=parent.includes('/genre:');
   return VALUES[i]>=(rating?ratingMin:genreMin)?label:'';
 });
}
function updateZoomLabels(){
 const sig=`${Math.ceil(25/Math.pow(zoom,1.8))}:${Math.ceil(28/Math.pow(zoom,1.8))}`;
 if(sig===lastLabelSignature)return;
 lastLabelSignature=sig;
 Plotly.restyle(sun,{text:[labelsForZoom(zoom)]},[0]);
}
const viewport=document.getElementById('sunburstViewport');
let zoom=1, offsetX=0, offsetY=0, drag=null, renderQueued=false, ready=false;
const clamp=(v,lo,hi)=>Math.max(lo,Math.min(hi,v));
function constrain(){
 const w=viewport.clientWidth,h=viewport.clientHeight;
 offsetX=clamp(offsetX,w*(1-zoom),0);
 offsetY=clamp(offsetY,h*(1-zoom),0);
}
function renderZoom(){
 constrain();
 sun.style.left=`${offsetX}px`;
 sun.style.top=`${offsetY}px`;
 document.getElementById('zoomLevel').textContent=`${Math.round(zoom*100)}%`;
 if(!ready||renderQueued)return;
 renderQueued=true;
 requestAnimationFrame(()=>{
  renderQueued=false;
  const w=Math.round(viewport.clientWidth*zoom);
  const h=Math.round(viewport.clientHeight*zoom);
  sun.style.width=`${w}px`;
  sun.style.height=`${h}px`;
  // Plotly re-renders SVG paths and text at their real pixel dimensions.
  Plotly.relayout(sun,{width:w,height:h}).then(updateZoomLabels);
 });
}
function zoomAt(factor,clientX,clientY){
 const rect=viewport.getBoundingClientRect();
 const px=clientX-rect.left,py=clientY-rect.top;
 const next=clamp(zoom*factor,1,4);
 const ratio=next/zoom;
 offsetX=px-(px-offsetX)*ratio;
 offsetY=py-(py-offsetY)*ratio;
 zoom=next;
 if(zoom===1){offsetX=0;offsetY=0;}
 renderZoom();
}
Plotly.newPlot(sun,SUN.data,{...SUN.layout,width:viewport.clientWidth,height:viewport.clientHeight},
 {responsive:false,displaylogo:false,displayModeBar:false}).then(()=>{
 ready=true;
 updateZoomLabels();
 sun.on('plotly_sunburstclick',()=>false);
 renderZoom();
});
viewport.addEventListener('wheel',e=>{e.preventDefault();zoomAt(Math.exp(-e.deltaY*0.0015),e.clientX,e.clientY);},{passive:false,capture:true});
viewport.addEventListener('pointerdown',e=>{if(e.button!==0||zoom<=1)return;drag={x:e.clientX,y:e.clientY,ox:offsetX,oy:offsetY};viewport.classList.add('dragging');viewport.setPointerCapture(e.pointerId);e.preventDefault();},true);
viewport.addEventListener('pointermove',e=>{if(!drag)return;offsetX=drag.ox+e.clientX-drag.x;offsetY=drag.oy+e.clientY-drag.y;renderZoom();e.preventDefault();},true);
function stopDrag(){drag=null;viewport.classList.remove('dragging');}
viewport.addEventListener('pointerup',stopDrag,true);viewport.addEventListener('pointercancel',stopDrag,true);
document.getElementById('zoomIn').addEventListener('click',()=>{const r=viewport.getBoundingClientRect();zoomAt(1.3,r.left+r.width/2,r.top+r.height/2);});
document.getElementById('zoomOut').addEventListener('click',()=>{const r=viewport.getBoundingClientRect();zoomAt(1/1.3,r.left+r.width/2,r.top+r.height/2);});
document.getElementById('zoomReset').addEventListener('click',()=>{zoom=1;offsetX=0;offsetY=0;renderZoom();});
window.addEventListener('resize',renderZoom);

const select=document.getElementById('genre');select.innerHTML=DATA.genres.map((g,i)=>`<option value="${i}">${g}</option>`).join('');
document.getElementById('legend').className='legend';
document.getElementById('legend').innerHTML=DATA.bands.map((b,i)=>`<span class="key"><i class="swatch" style="background:${DATA.colors[i]}"></i>${b}</span>`).join('');
function draw(){const genre=DATA.genres[Number(select.value)];const counts=DATA.counts[genre];
 const totals=DATA.periods.map(p=>counts[p].reduce((a,b)=>a+b,0));
 const traces=DATA.bands.map((band,i)=>({type:'bar',orientation:'h',name:band,y:DATA.periods,
 x:DATA.periods.map(p=>counts[p][i]),
 customdata:DATA.periods.map((p,j)=>[totals[j]?100*counts[p][i]/totals[j]:0,totals[j]]),marker:{color:DATA.colors[i]},
 hovertemplate:`<b>${band}</b><br>%{y}<br>%{x:,} movies<br>%{customdata[0]:.1f}% of %{customdata[1]:,} movies<extra></extra>`}));
 const sum=totals.reduce((a,b)=>a+b,0);document.getElementById('stats').textContent=`${sum.toLocaleString()} movies across ${totals.filter(x=>x>0).length} eras · ${genre}`;
 const layout={barmode:'stack',showlegend:false,paper_bgcolor:'#fff',plot_bgcolor:'#fff',
 margin:{l:104,r:22,t:20,b:50},height:465,font:{family:'Arial, sans-serif',color:'#353535',size:12},
 xaxis:{rangemode:'tozero',tickformat:',d',title:{text:'Number of movies',font:{size:12}},gridcolor:'#EDEAE5',zeroline:false},
 yaxis:{categoryorder:'array',categoryarray:[...DATA.periods].reverse(),automargin:true},
 bargap:0.28,hovermode:'closest'};
 Plotly.react('comparison',traces,layout,{responsive:true,displayModeBar:false,displaylogo:false});}
select.addEventListener('change',draw);draw();
</script></body></html>'''
    excluded=len(df)-len(d)
    return html.replace('__EXCLUDED__',str(excluded)).replace('__TOTAL__',f'{len(d):,}').replace('__OPTIONS__',options).replace('__PLOTLY__',get_plotlyjs()).replace('__DATA__',payload).replace('__SUN__',sunburst_json)

if __name__=='__main__':
    folder=Path(__file__).parent
    df=pd.read_csv(folder/'tmdb_cleaned.csv')
    html=create_dashboard(df)
    target=folder/'movie_genres_sunburst.html'
    target.write_text(html,encoding='utf-8')
    d=prepare_data(df)
    print(f'Created {target} ({len(d)} movies, {len(html):,} characters)')
