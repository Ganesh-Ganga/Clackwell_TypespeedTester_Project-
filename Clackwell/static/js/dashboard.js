/* Charts. Every series comes from /api/analytics, which reads the signed-in
   user's own rows — there is no sample data anywhere in here. */

(function () {
  const INK = '#14161a';
  const MARK = '#ffd23f';
  const GO = '#11805b';
  const FAINT = '#8d929a';
  const RULE = '#e2e2dc';

  if (window.Chart) {
    Chart.defaults.font.family = "'Space Grotesk', system-ui, sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.color = FAINT;
    Chart.defaults.animation.duration = window.CWAnim?.calm ? 0 : 700;
  }

  const gridStyle = { color: RULE, drawTicks: false };
  const baseScales = {
    x: { grid: { display: false }, border: { color: RULE } },
    y: { grid: gridStyle, border: { display: false }, beginAtZero: true }
  };

  function legendOff() {
    return { legend: { display: false }, tooltip: tooltipStyle() };
  }

  function tooltipStyle() {
    return {
      backgroundColor: INK, padding: 10, cornerRadius: 6,
      titleFont: { weight: '600' }, displayColors: false
    };
  }

  function load() {
    return fetch('/api/analytics').then(r => r.json());
  }

  function hideLoader(id) {
    const node = document.getElementById(id);
    if (node) node.remove();
  }

  /* --- dashboard: one combined chart ------------------------------------ */

  function dashboard() {
    const canvas = document.getElementById('progressChart');
    if (!canvas) return;

    load().then(data => {
      hideLoader('loadProgress');
      new Chart(canvas, {
        data: {
          labels: data.progress.labels,
          datasets: [
            {
              type: 'line', label: 'WPM', data: data.progress.wpm,
              borderColor: INK, backgroundColor: 'rgba(20,22,26,.06)',
              borderWidth: 2.5, tension: .3, fill: true,
              pointBackgroundColor: MARK, pointBorderColor: INK,
              pointBorderWidth: 2, pointRadius: 4, yAxisID: 'y'
            },
            {
              type: 'line', label: 'Accuracy %', data: data.progress.accuracy,
              borderColor: GO, borderWidth: 1.5, borderDash: [4, 4],
              tension: .3, pointRadius: 0, yAxisID: 'y1'
            }
          ]
        },
        options: {
          maintainAspectRatio: false, responsive: true,
          interaction: { mode: 'index', intersect: false },
          plugins: { legend: { display: true, position: 'bottom', labels: { boxWidth: 12, boxHeight: 2 } }, tooltip: tooltipStyle() },
          scales: {
            x: baseScales.x,
            y: { ...baseScales.y, title: { display: true, text: 'wpm' } },
            y1: { position: 'right', min: 0, max: 100, grid: { display: false }, border: { display: false } }
          }
        }
      });
    });
  }

  /* --- analytics page: four charts --------------------------------------- */

  function analytics() {
    load().then(data => {
      hideLoader('loadAll');

      const progress = document.getElementById('wpmChart');
      if (progress) new Chart(progress, {
        type: 'line',
        data: {
          labels: data.progress.labels,
          datasets: [{
            data: data.progress.wpm, borderColor: INK, borderWidth: 2.5, tension: .3,
            fill: true, backgroundColor: 'rgba(255,210,63,.35)',
            pointBackgroundColor: MARK, pointBorderColor: INK, pointBorderWidth: 2, pointRadius: 3
          }]
        },
        options: { maintainAspectRatio: false, plugins: legendOff(), scales: baseScales }
      });

      const acc = document.getElementById('accChart');
      if (acc) new Chart(acc, {
        type: 'line',
        data: {
          labels: data.progress.labels,
          datasets: [{
            data: data.progress.accuracy, borderColor: GO, borderWidth: 2.5, tension: .3,
            pointBackgroundColor: '#fff', pointBorderColor: GO, pointBorderWidth: 2, pointRadius: 3
          }]
        },
        options: {
          maintainAspectRatio: false, plugins: legendOff(),
          scales: { x: baseScales.x, y: { ...baseScales.y, min: 50, max: 100 } }
        }
      });

      const weekday = document.getElementById('weekdayChart');
      if (weekday) new Chart(weekday, {
        type: 'bar',
        data: {
          labels: data.weekday.labels,
          datasets: [
            { label: 'Average WPM', data: data.weekday.wpm, backgroundColor: MARK, borderColor: INK, borderWidth: 2, borderRadius: 4 },
            { label: 'Runs', data: data.weekday.tests, backgroundColor: 'rgba(20,22,26,.85)', borderRadius: 4 }
          ]
        },
        options: {
          maintainAspectRatio: false,
          plugins: { legend: { position: 'bottom', labels: { boxWidth: 12 } }, tooltip: tooltipStyle() },
          scales: baseScales
        }
      });

      const levels = document.getElementById('levelChart');
      if (levels) new Chart(levels, {
        type: 'bar',
        data: {
          labels: data.levels.labels,
          datasets: [{ data: data.levels.wpm, backgroundColor: MARK, borderColor: INK, borderWidth: 2, borderRadius: 4 }]
        },
        options: {
          indexAxis: 'y', maintainAspectRatio: false, plugins: legendOff(),
          scales: { x: { ...baseScales.y }, y: { grid: { display: false }, border: { display: false } } }
        }
      });

      const modes = document.getElementById('modeChart');
      if (modes) new Chart(modes, {
        type: 'doughnut',
        data: {
          labels: data.modes.labels,
          datasets: [{
            data: data.modes.minutes,
            backgroundColor: [MARK, INK, GO, '#cf2f45', '#2331a8'],
            borderColor: '#fff', borderWidth: 3
          }]
        },
        options: {
          maintainAspectRatio: false, cutout: '62%',
          plugins: { legend: { position: 'right', labels: { boxWidth: 12 } }, tooltip: tooltipStyle() }
        }
      });
    });
  }

  window.CWCharts = { dashboard, analytics };
})();
