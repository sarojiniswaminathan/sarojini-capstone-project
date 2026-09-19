(function () {
  const calendarEl = document.getElementById('calendar');
  const calendarBanner = document.getElementById('calendar-banner');
  const dayPanel = document.getElementById('day-panel');
  const dayPanelContent = document.getElementById('day-panel-content');
  const dayPanelClose = document.getElementById('day-panel-close');

  function colorFor(type) {
    switch (type) {
      case 'deadline':
        return '#c0392b';
      case 'college':
        return '#2980b9';
      case 'google':
        return '#8e44ad';
      default:
        return '#27ae60';
    }
  }

  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    headerToolbar: { left: 'prev,next today', center: 'title', right: 'dayGridMonth,timeGridWeek' },
    height: 'auto',
    events: async function (fetchInfo, successCallback, failureCallback) {
      try {
        const url = `/calendar/events?start=${encodeURIComponent(fetchInfo.startStr)}&end=${encodeURIComponent(fetchInfo.endStr)}`;
        const res = await fetch(url);
        const data = await res.json();
        calendarBanner.hidden = !!data.connected;
        successCallback(
          (data.events || []).map((e) => ({
            id: e.id,
            title: e.title,
            start: e.start,
            end: e.end,
            allDay: e.type === 'deadline',
            backgroundColor: colorFor(e.type),
            borderColor: colorFor(e.type),
            extendedProps: { shortage: !!e.shortage },
          }))
        );
      } catch (err) {
        console.error(err);
        failureCallback(err);
      }
    },
    // A shortage-blocked order shows a warning right on its deadline day.
    eventContent: function (arg) {
      const prefix = arg.event.extendedProps.shortage ? '⚠ ' : '';
      const span = document.createElement('span');
      span.className = 'fc-event-title';
      span.textContent = prefix + arg.event.title;
      return { domNodes: [span] };
    },
    dateClick: function (info) {
      openDayPanel(info.dateStr);
    },
    eventClick: function (info) {
      const start = info.event.startStr || '';
      openDayPanel(start.slice(0, 10));
    },
  });

  calendar.render();

  function renderDay(data) {
    const plan = data.plan || {};
    const recs =
      (plan.recommendations || [])
        .map((r) => `<li>${r.order_id} — ${r.customer}: ${r.suggested_hours}h (${r.garment || ''})</li>`)
        .join('') || '<li>No recommendations.</li>';
    const noCommitmentsMessage = data.connected
      ? '<li>None.</li>'
      : '<li>Connect Google Calendar (top of the page) to see commitments here.</li>';
    const commitments =
      (data.commitments || [])
        .map((c) => `<li>${c.title} (${c.start_datetime.slice(11, 16)}–${c.end_datetime.slice(11, 16)})</li>`)
        .join('') || noCommitmentsMessage;
    const due =
      (data.due_orders || [])
        .map((o) => {
          const shortageText =
            o.shortages && o.shortages.length
              ? `<span class="shortage-text">Short: ${o.shortages
                  .map((s) => `${s.material} ${s.total_shortage}${s.unit}`)
                  .join(', ')}</span>`
              : '<span class="ready-text">Materials ready</span>';
          return `<li>${o.order_id} — ${o.customer} (${o.garment || ''}) ${shortageText}</li>`;
        })
        .join('') || '<li>None due.</li>';

    return `
      <h2>${data.date}</h2>
      <h3>Free time</h3>
      <p>${plan.available_hours_today != null ? plan.available_hours_today + 'h free' : 'N/A'}</p>
      <h3>Recommended work</h3>
      <ul>${recs}</ul>
      <h3>Commitments</h3>
      <ul>${commitments}</ul>
      <h3>Orders due</h3>
      <ul>${due}</ul>
      <h3>Add a commitment</h3>
      <form id="quick-commitment-form">
        <input name="title" placeholder="Title" required />
        <input name="start_time" type="time" required />
        <input name="end_time" type="time" required />
        <button type="submit">Add</button>
      </form>
    `;
  }

  function wireQuickForm(dateStr) {
    const form = document.getElementById('quick-commitment-form');
    if (!form) return;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const fd = new FormData(form);
      const title = fd.get('title');
      const start = `${dateStr}T${fd.get('start_time')}:00`;
      const end = `${dateStr}T${fd.get('end_time')}:00`;
      const res = await fetch('/commitments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, start_datetime: start, end_datetime: end, type: 'personal' }),
      });
      const result = await res.json();
      if (result.status === 'not_connected') {
        alert('Connect Google Calendar first (see the link at the top of the page).');
        return;
      }
      calendar.refetchEvents();
      openDayPanel(dateStr);
    });
  }

  async function openDayPanel(dateStr) {
    dayPanelContent.innerHTML = 'Loading…';
    dayPanel.hidden = false;
    try {
      const res = await fetch(`/calendar/day?date=${encodeURIComponent(dateStr)}`);
      const data = await res.json();
      dayPanelContent.innerHTML = renderDay(data);
      wireQuickForm(dateStr);
    } catch (err) {
      dayPanelContent.textContent = 'Could not load this day.';
      console.error(err);
    }
  }

  dayPanelClose.addEventListener('click', () => {
    dayPanel.hidden = true;
  });

  window.refreshCalendar = function () {
    calendar.refetchEvents();
  };

  async function loadGoogleStatus() {
    const el = document.getElementById('google-status');
    try {
      const res = await fetch('/auth/google/status');
      const data = await res.json();
      el.innerHTML = data.connected
        ? '<span class="connected">✓ Google Calendar connected</span>'
        : '<a href="/auth/google/login">Connect Google Calendar</a>';
    } catch (err) {
      el.textContent = '';
    }
  }

  async function loadPendingBadge() {
    const badge = document.getElementById('pending-badge');
    try {
      const res = await fetch('/orders/pending');
      const data = await res.json();
      const count = (data.orders || []).length;
      badge.hidden = count === 0;
      badge.textContent = count === 1 ? '1 order awaiting your response' : `${count} orders awaiting your response`;
    } catch (err) {
      badge.hidden = true;
    }
  }

  loadGoogleStatus();
  loadPendingBadge();
  window.refreshPendingBadge = loadPendingBadge;
})();
