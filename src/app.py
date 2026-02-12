from shiny import App, ui, render
import matplotlib.pyplot as plt


# Page level CSS 
page_style = ui.tags.style(
    """
    html, body, .container-fluid { height: 100%; margin: 0; }
    .shiny-page { min-height: 100vh; overflow: hidden; }
    .full-height { height: 100vh; }
    .sidebar-card { height: 100vh; display: flex; flex-direction: column; }
    .sidebar-card .card-body { flex: 1 1 auto; display:flex; flex-direction:column; justify-content:space-between; }
    .kpi-row { display: flex; gap: 12px; height: 66px; align-items: center; }
    .main-content { padding-top: 32px; height: 100vh; box-sizing: border-box; }
    .kpi-card { flex: 1 1 0; }
    .kpi-card .card-body { padding: 8px 10px; }
    .kpi-card h5, .kpi-card .card-title { font-size: 11px; margin-bottom: 2px; }
    .kpi-card h2 { font-size: 14px; margin: 0; font-weight: 600; line-height: 1; }
    .kpi-row { margin-bottom: 12px; position: relative; z-index: 2; }
    .kpi-row .card { height: 100%; display: flex; align-items: center; justify-content: center; box-sizing: border-box; }
    .kpi-row .card .card-body { width: 100%; display:flex; flex-direction:column; align-items:center; justify-content:center; padding: 4px 6px; }
    .charts-area { display: flex; flex-direction: column; height: calc(100vh - 110px); gap: 12px; }
        .top-charts { display:flex; gap:12px; align-items: stretch; flex: 0 0 12.5%; }
    .top-charts .card { flex: 1 1 0; height: 240px; min-height:240px; max-height:240px; overflow:hidden; }
    .top-charts .card .card-body { height: 100%; }
        .bottom-chart { flex: 1 1 12.5%; }
        .bottom-chart .card { height: 240px; min-height:240px; max-height:240px; overflow:hidden; }
        .bottom-chart .card .card-body { height: 100%; }
    """
)

