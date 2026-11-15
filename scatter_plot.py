"""Movie Data Visualization — Chart 7: Budget vs Box Office Revenue.
Run: python scatter_plot.py
Requires: pandas, numpy, plotly. Input: tmdb_cleaned.csv in same folder.
Other teammates can import create_scatter_plot(df) and embed its Plotly Figure.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go

BG = '#FAF7F2'
COLORS = {
    'Below budget': '#B5534B',
    '1–3× budget': '#D5A14A',
    'Above 3× budget': '#34877E',
}


def create_scatter_plot(df: pd.DataFrame) -> go.Figure:
    required = {'budget', 'revenue', 'title', 'vote_average'}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f'Missing columns: {sorted(missing)}')

    data = df.copy()
    for col in ('budget', 'revenue', 'vote_average'):
        data[col] = pd.to_numeric(data[col], errors='coerce')
    data = data.loc[(data['budget'] > 0) & (data['revenue'] > 0)].copy()
    data['budget_m'] = data['budget'] / 1_000_000
    data['revenue_m'] = data['revenue'] / 1_000_000
    data['ratio'] = data['revenue'] / data['budget']
    data['performance'] = np.select(
        [data['ratio'] < 1, data['ratio'] <= 3],
        ['Below budget', '1–3× budget'],
        default='Above 3× budget',
    )

    fig = go.Figure()
    for label, color in COLORS.items():
        part = data.loc[data['performance'] == label]
        custom = np.column_stack([
            part['title'].fillna('Untitled').astype(str).to_numpy(),
            part['vote_average'].to_numpy(),
            part['ratio'].to_numpy(),
        ])
        fig.add_trace(go.Scattergl(
            x=part['budget_m'], y=part['revenue_m'],
            mode='markers', name=f'{label} ({len(part):,})',
            showlegend=True, legendgroup=label,
            marker=dict(color=color, size=5, opacity=0.45),
            customdata=custom,
            hovertemplate=(
                '<b>%{customdata[0]}</b><br>'
                'Budget: $%{x:,.1f}M<br>'
                'Box office: $%{y:,.1f}M<br>'
                'Rating: %{customdata[1]} / 10<br>'
                'Revenue / budget: %{customdata[2]:.2f}×<extra></extra>'
            ),
        ))

    # Coordinate-anchored Plotly shapes remain on y=x and y=2x while panning.
    # Separate invisible markers provide hover targets without drawing polylines.
    max_b = float(data['budget_m'].max())
    reference_shapes = [
        dict(type='line', xref='x', yref='y', x0=0, y0=0,
             x1=max_b, y1=max_b,
             line=dict(color='#77736E', width=1.5, dash='dash'), layer='above',
             showlegend=True, name='1× budget'),
        dict(type='line', xref='x', yref='y', x0=0, y0=0,
             x1=max_b, y1=2 * max_b,
             line=dict(color='#A65349', width=1.5, dash='dot'), layer='above',
             showlegend=True, name='2× budget (approx. rule)'),
    ]
    for multiplier, color, label, tooltip, dash in [
        (1, '#77736E', '1× budget',
         '<b>1× Budget Reference</b><br>Box-office revenue equals production budget.<br>This does not necessarily mean the film broke even.<extra></extra>', 'dash'),
        (2, '#A65349', '2× budget (approx. rule)',
         '<b>2× Budget Rule</b><br>Industry rule of thumb for break-even<br>after marketing &amp; theater cuts<extra></extra>', 'dot'),
    ]:
        # Invisible hit targets along the coordinate-anchored shape.
        xs = np.linspace(0.001, max_b, 750)
        fig.add_trace(go.Scatter(
            x=xs, y=multiplier * xs, mode='markers',
            marker=dict(size=12, color='rgba(0,0,0,0.001)'),
            name=label, legendgroup=label, showlegend=False,
            hovertemplate=tooltip,
        ))

    low_count = int((data['budget_m'] <= 25).sum())
    medium_count = int((data['budget_m'] <= 100).sum())

    def subtitle(message):
        return [
            dict(x=0, y=1.24, xref='paper', yref='paper', showarrow=False,
                 text=message, font=dict(color='#706B66', size=12),
                 xanchor='left', yanchor='bottom'),
        ]

    # Reference lines appear as styled, clickable legend entries.
    # The 2× threshold is only a heuristic, not a measured profit boundary.
    # The initial viewport is chosen for readability; the 'All films' button
    # restores full axes without excluding any points from the dataset.
    fig.update_layout(
        template='none', paper_bgcolor=BG, plot_bgcolor='#FFFFFF',
        font=dict(family='Arial, sans-serif', color='#353535', size=13),
        title=dict(text='Budget vs. Box Office Revenue', x=0.077, y=0.97, xanchor='left', yanchor='top', font=dict(size=24)),
        width=1200, height=720,
        margin=dict(l=92, r=45, t=160, b=175),
        xaxis=dict(title='Production budget (USD millions)', range=[0, 400],
                   gridcolor='#E9E9E9', zeroline=False, tickformat=',.0f'),
        yaxis=dict(title='Box-office revenue (USD millions)', range=[0, 2900],
                   gridcolor='#E9E9E9', zeroline=False, tickformat=',.0f'),
        legend=dict(orientation='h', x=0.5, y=-0.25, xanchor='center', yanchor='top',
                    title=None, font=dict(size=13), bgcolor='rgba(255,255,255,0.9)',
                    itemclick='toggle', itemdoubleclick='toggleothers'),
        hovermode='closest', dragmode='pan',
        shapes=reference_shapes,
        annotations=subtitle(f'{len(data):,} movies with positive budget and revenue'),
        updatemenus=[dict(
            type='dropdown', direction='down', x=1, y=1.16,
            xanchor='right', yanchor='bottom', bgcolor='#FFFFFF',
            font=dict(size=12),
            buttons=[
                dict(label='Full dataset · linear', method='relayout', args=[{
                    'xaxis.type':'linear', 'yaxis.type':'linear',
                    'xaxis.range':[0,400], 'yaxis.range':[0,2900],
                    'annotations':subtitle(f'{len(data):,} movies with positive budget and revenue')}]),
                dict(label='Low budget · $0–25M', method='relayout', args=[{
                    'xaxis.type':'linear', 'yaxis.type':'linear',
                    'xaxis.range':[0,25], 'yaxis.range':[0,200],
                    'annotations':subtitle(f'{low_count:,} movies in $0–25M budget range')}]),
                dict(label='Medium budget · $0–100M', method='relayout', args=[{
                    'xaxis.type':'linear', 'yaxis.type':'linear',
                    'xaxis.range':[0,100], 'yaxis.range':[0,600],
                    'annotations':subtitle(f'{medium_count:,} movies in $0–100M budget range')}]),
                dict(label='Logarithmic · all films', method='relayout', args=[{
                    'xaxis.type':'log', 'yaxis.type':'log',
                    'xaxis.range':[-6,3], 'yaxis.range':[-6,4],
                    'annotations':subtitle(f'{len(data):,} movies · logarithmic axes')}]),
            ],
        ), dict(
            type='buttons', direction='right', x=0.77, y=1.16,
            xanchor='right', yanchor='bottom', bgcolor='#FFFFFF',
            font=dict(size=12),
            buttons=[dict(label='↺ Reset view', method='relayout', args=[{
                'xaxis.type':'linear', 'yaxis.type':'linear',
                'xaxis.range':[0,400], 'yaxis.range':[0,2900],
                'annotations':subtitle(f'{len(data):,} movies with positive budget and revenue'),
                'updatemenus[0].active':0,
            }])],
        )],
    )
    return fig


if __name__ == '__main__':
    source = Path(__file__).with_name('tmdb_cleaned.csv')
    df = pd.read_csv(source)
    fig = create_scatter_plot(df)
    target = Path(__file__).with_name('box_office_modern_cinema.html')
    # Plotly's built-in pan can reverse/collapse axes when repeatedly dragged
    # against minallowed/maxallowed. Use a bounded mouse pan instead.
    interaction_guard = r"""
(function () {
  const gd = document.getElementById('{plot_id}');
  const limits = {linear: {x: [0, 400], y: [0, 2900]},
                  log: {x: [-6, 3], y: [-6, 4]}};
  const minSpan = {linear: {x: 1, y: 5},
                   log: {x: 0.02, y: 0.02}};
  let updating = false;
  let dragging = null;
  let pending = null;
  let rendering = false;

  function clampRange(range, bounds, smallest) {
    const [min, max] = bounds;
    let lo = Number(range[0]), hi = Number(range[1]);
    if (!Number.isFinite(lo) || !Number.isFinite(hi) || hi <= lo) {
      return [min, max];
    }
    const span = Math.max(smallest, Math.min(max - min, hi - lo));
    lo = Math.max(min, Math.min(lo, max - span));
    return [lo, lo + span];
  }

  function currentMode() {
    return gd._fullLayout.xaxis.type === 'log' ? 'log' : 'linear';
  }

  // Queue viewport updates; avoid competing Plotly.relayout calls on fast input.
  function applyViewport(xr, yr) {
    const currentX = gd._fullLayout.xaxis.range;
    const currentY = gd._fullLayout.yaxis.range;
    const same = (a,b) => Math.abs(a[0]-b[0]) < 1e-8 && Math.abs(a[1]-b[1]) < 1e-8;
    if (same(xr,currentX) && same(yr,currentY) && !pending) return;
    pending = {'xaxis.range': xr, 'yaxis.range': yr};
    if (rendering) return;
    const run = () => {
      if (!pending) { rendering = false; return; }
      rendering = true;
      const next = pending;
      pending = null;
      updating = true;
      Plotly.relayout(gd, next).finally(() => {
        updating = false;
        run();
      });
    };
    run();
  }

  // Clamp menu-driven axis changes. Never allow a reversed axis.
  function checkAxes() {
    if (updating || !gd._fullLayout) return;
    const mode = currentMode();
    const change = {};
    for (const name of ['x', 'y']) {
      const old = gd._fullLayout[name + 'axis'].range;
      const next = clampRange(old, limits[mode][name], minSpan[mode][name]);
      if (Math.abs(next[0] - old[0]) > 1e-8 ||
          Math.abs(next[1] - old[1]) > 1e-8) {
        change[name + 'axis.range'] = next;
      }
    }
    if (Object.keys(change).length) {
      updating = true;
      Plotly.relayout(gd, change).finally(() => { updating = false; });
    }
  }
  gd.on('plotly_relayout', checkAxes);

  // Intercept Plotly's built-in mouse panning BEFORE it starts. We calculate
  // bounded displacement from the mouse-down viewport, so dragging past zero
  // simply stops rather than stretching, reversing, or shrinking the axes.
  gd.addEventListener('mousedown', function (event) {
    if (event.button !== 0) {
      event.preventDefault();
      event.stopImmediatePropagation();
      return;
    }
    const dragSurface = event.target.closest('.nsewdrag');
    if (!dragSurface || !gd._fullLayout) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    const layout = gd._fullLayout;
    dragging = {
      x: event.clientX, y: event.clientY,
      mode: currentMode(),
      xr: layout.xaxis.range.slice(), yr: layout.yaxis.range.slice(),
      width: layout.xaxis._length, height: layout.yaxis._length
    };
    document.body.style.cursor = 'grabbing';
  }, true);

  gd.addEventListener('contextmenu', e => e.preventDefault(), true);

  // Replace Plotly's native wheel zoom, which can overshoot limits and invert
  // axes during repeated zoom-out. Zoom about the cursor with bounded spans.
  gd.addEventListener('wheel', function (event) {
    if (!gd._fullLayout || event.target.closest('.updatemenu') || event.target.closest('.legend')) return;
    // Capture wheel before Plotly and the browser can perform a temporary
    // overshoot. Even at maximum zoom-out, consume the event without relayout.
    event.preventDefault();
    event.stopImmediatePropagation();
    const surface = gd.querySelector('.nsewdrag');
    if (!surface) return;
    const layout = gd._fullLayout;
    const mode = currentMode();
    const box = surface.getBoundingClientRect();
    const fx = Math.max(0, Math.min(1, (event.clientX - box.left) / box.width));
    const fy = 1 - Math.max(0, Math.min(1, (event.clientY - box.top) / box.height));
    const factor = Math.exp(Math.max(-100, Math.min(100, event.deltaY)) * 0.0018);
    if (event.deltaY > 0 && ['x','y'].every(name => {
      const r = layout[name + 'axis'].range, b = limits[mode][name];
      return Math.abs(r[0] - b[0]) < 1e-7 && Math.abs(r[1] - b[1]) < 1e-7;
    })) return;
    const next = {};
    for (const name of ['x', 'y']) {
      const old = layout[name + 'axis'].range;
      const f = name === 'x' ? fx : fy;
      const span = (old[1] - old[0]) * factor;
      const anchor = old[0] + f * (old[1] - old[0]);
      next[name] = clampRange([anchor - f * span, anchor + (1 - f) * span],
                               limits[mode][name], minSpan[mode][name]);
    }
    applyViewport(next.x, next.y);
  }, {capture: true, passive: false});

  document.addEventListener('mousemove', function (event) {
    if (!dragging || updating) return;
    const d = dragging;
    const dx = event.clientX - d.x, dy = event.clientY - d.y;
    const sx = d.xr[1] - d.xr[0], sy = d.yr[1] - d.yr[0];
    const x0 = d.xr[0] - dx * sx / d.width;
    const y0 = d.yr[0] + dy * sy / d.height;
    const xr = clampRange([x0, x0 + sx], limits[d.mode].x, minSpan[d.mode].x);
    const yr = clampRange([y0, y0 + sy], limits[d.mode].y, minSpan[d.mode].y);
    applyViewport(xr, yr);
  }, true);

  document.addEventListener('mouseup', function () {
    if (dragging) { dragging = null; document.body.style.cursor = ''; }
  }, true);
  window.addEventListener('blur', function () {
    dragging = null; document.body.style.cursor = '';
  });
})();
"""
    fig.write_html(str(target), include_plotlyjs=True, full_html=True,
                   post_script=interaction_guard,
                   config={'responsive':True, 'displaylogo':False, 'scrollZoom':False, 'displayModeBar':False, 'doubleClick':False})
    print(f'Created {target} | {sum((df.budget > 0) & (df.revenue > 0)):,} movies')


def create_scatter_html(df: pd.DataFrame) -> str:
    """Render the original interactive chart, including bounded mouse controls."""
    fig = create_scatter_plot(df)
    interaction_guard = r"""
(function () {
  const gd = document.getElementById('{plot_id}');
  const limits = {linear: {x: [0, 400], y: [0, 2900]},
                  log: {x: [-6, 3], y: [-6, 4]}};
  const minSpan = {linear: {x: 1, y: 5},
                   log: {x: 0.02, y: 0.02}};
  let updating = false;
  let dragging = null;
  let pending = null;
  let rendering = false;

  function clampRange(range, bounds, smallest) {
    const [min, max] = bounds;
    let lo = Number(range[0]), hi = Number(range[1]);
    if (!Number.isFinite(lo) || !Number.isFinite(hi) || hi <= lo) {
      return [min, max];
    }
    const span = Math.max(smallest, Math.min(max - min, hi - lo));
    lo = Math.max(min, Math.min(lo, max - span));
    return [lo, lo + span];
  }

  function currentMode() {
    return gd._fullLayout.xaxis.type === 'log' ? 'log' : 'linear';
  }

  // Queue viewport updates; avoid competing Plotly.relayout calls on fast input.
  function applyViewport(xr, yr) {
    const currentX = gd._fullLayout.xaxis.range;
    const currentY = gd._fullLayout.yaxis.range;
    const same = (a,b) => Math.abs(a[0]-b[0]) < 1e-8 && Math.abs(a[1]-b[1]) < 1e-8;
    if (same(xr,currentX) && same(yr,currentY) && !pending) return;
    pending = {'xaxis.range': xr, 'yaxis.range': yr};
    if (rendering) return;
    const run = () => {
      if (!pending) { rendering = false; return; }
      rendering = true;
      const next = pending;
      pending = null;
      updating = true;
      Plotly.relayout(gd, next).finally(() => {
        updating = false;
        run();
      });
    };
    run();
  }

  // Clamp menu-driven axis changes. Never allow a reversed axis.
  function checkAxes() {
    if (updating || !gd._fullLayout) return;
    const mode = currentMode();
    const change = {};
    for (const name of ['x', 'y']) {
      const old = gd._fullLayout[name + 'axis'].range;
      const next = clampRange(old, limits[mode][name], minSpan[mode][name]);
      if (Math.abs(next[0] - old[0]) > 1e-8 ||
          Math.abs(next[1] - old[1]) > 1e-8) {
        change[name + 'axis.range'] = next;
      }
    }
    if (Object.keys(change).length) {
      updating = true;
      Plotly.relayout(gd, change).finally(() => { updating = false; });
    }
  }
  gd.on('plotly_relayout', checkAxes);

  // Intercept Plotly's built-in mouse panning BEFORE it starts. We calculate
  // bounded displacement from the mouse-down viewport, so dragging past zero
  // simply stops rather than stretching, reversing, or shrinking the axes.
  gd.addEventListener('mousedown', function (event) {
    if (event.button !== 0) {
      event.preventDefault();
      event.stopImmediatePropagation();
      return;
    }
    const dragSurface = event.target.closest('.nsewdrag');
    if (!dragSurface || !gd._fullLayout) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    const layout = gd._fullLayout;
    dragging = {
      x: event.clientX, y: event.clientY,
      mode: currentMode(),
      xr: layout.xaxis.range.slice(), yr: layout.yaxis.range.slice(),
      width: layout.xaxis._length, height: layout.yaxis._length
    };
    document.body.style.cursor = 'grabbing';
  }, true);

  gd.addEventListener('contextmenu', e => e.preventDefault(), true);

  // Replace Plotly's native wheel zoom, which can overshoot limits and invert
  // axes during repeated zoom-out. Zoom about the cursor with bounded spans.
  gd.addEventListener('wheel', function (event) {
    if (!gd._fullLayout || event.target.closest('.updatemenu') || event.target.closest('.legend')) return;
    // Capture wheel before Plotly and the browser can perform a temporary
    // overshoot. Even at maximum zoom-out, consume the event without relayout.
    event.preventDefault();
    event.stopImmediatePropagation();
    const surface = gd.querySelector('.nsewdrag');
    if (!surface) return;
    const layout = gd._fullLayout;
    const mode = currentMode();
    const box = surface.getBoundingClientRect();
    const fx = Math.max(0, Math.min(1, (event.clientX - box.left) / box.width));
    const fy = 1 - Math.max(0, Math.min(1, (event.clientY - box.top) / box.height));
    const factor = Math.exp(Math.max(-100, Math.min(100, event.deltaY)) * 0.0018);
    if (event.deltaY > 0 && ['x','y'].every(name => {
      const r = layout[name + 'axis'].range, b = limits[mode][name];
      return Math.abs(r[0] - b[0]) < 1e-7 && Math.abs(r[1] - b[1]) < 1e-7;
    })) return;
    const next = {};
    for (const name of ['x', 'y']) {
      const old = layout[name + 'axis'].range;
      const f = name === 'x' ? fx : fy;
      const span = (old[1] - old[0]) * factor;
      const anchor = old[0] + f * (old[1] - old[0]);
      next[name] = clampRange([anchor - f * span, anchor + (1 - f) * span],
                               limits[mode][name], minSpan[mode][name]);
    }
    applyViewport(next.x, next.y);
  }, {capture: true, passive: false});

  document.addEventListener('mousemove', function (event) {
    if (!dragging || updating) return;
    const d = dragging;
    const dx = event.clientX - d.x, dy = event.clientY - d.y;
    const sx = d.xr[1] - d.xr[0], sy = d.yr[1] - d.yr[0];
    const x0 = d.xr[0] - dx * sx / d.width;
    const y0 = d.yr[0] + dy * sy / d.height;
    const xr = clampRange([x0, x0 + sx], limits[d.mode].x, minSpan[d.mode].x);
    const yr = clampRange([y0, y0 + sy], limits[d.mode].y, minSpan[d.mode].y);
    applyViewport(xr, yr);
  }, true);

  document.addEventListener('mouseup', function () {
    if (dragging) { dragging = null; document.body.style.cursor = ''; }
  }, true);
  window.addEventListener('blur', function () {
    dragging = null; document.body.style.cursor = '';
  });
})();
"""
    return fig.to_html(
        full_html=False, include_plotlyjs=True, post_script=interaction_guard,
        config={'responsive': True, 'displaylogo': False, 'scrollZoom': False,
                'displayModeBar': False, 'doubleClick': False}
    )
