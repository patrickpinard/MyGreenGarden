/**
 * MyGreenGarden V7.0 — Utilitaires graphiques ApexCharts.
 * Configuration par défaut + thème vert.
 */

'use strict';

const CHART_COLORS = {
  tempIn:   '#f97316',  // orange
  tempOut:  '#3b82f6',  // bleu
  moist1:   '#16a34a',  // vert
  moist2:   '#0d9488',  // teal
  wind:     '#0ea5e9',  // sky
  fan:      '#6366f1',  // indigo
};

/**
 * Options par défaut partagées par tous les graphiques.
 */
function defaultChartOptions(overrides = {}) {
  return {
    chart: {
      fontFamily: 'Inter, system-ui, sans-serif',
      toolbar: { show: false },
      animations: { enabled: false },
      background: 'transparent',
      ...overrides.chart,
    },
    grid: {
      borderColor: '#f3f4f6',
      strokeDashArray: 4,
      xaxis: { lines: { show: false } },
    },
    xaxis: {
      labels: {
        style: { fontSize: '10px', colors: '#9ca3af' },
        rotate: -30,
      },
      axisBorder: { show: false },
      axisTicks:  { show: false },
      tickAmount: 8,
    },
    yaxis: {
      labels: { style: { fontSize: '11px', colors: '#9ca3af' } },
    },
    stroke: { curve: 'smooth', width: 2 },
    markers: { size: 0 },
    tooltip: { shared: true, intersect: false },
    legend: { position: 'top', fontSize: '12px' },
    ...overrides,
  };
}
