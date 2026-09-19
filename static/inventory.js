(function () {
  const strip = document.getElementById('glance-strip');
  const template = document.getElementById('material-card-template');

  function statusClass(summary) {
    if (summary.available_qty <= 0) return 'status-red';
    if (summary.physical_qty > 0 && summary.available_qty / summary.physical_qty < 0.2) return 'status-amber';
    return 'status-green';
  }

  function renderCard(material) {
    const node = template.content.cloneNode(true);
    const card = node.querySelector('.material-card');
    card.classList.add(statusClass(material));

    const img = node.querySelector('img');
    const placeholder = node.querySelector('.material-photo-placeholder');
    if (material.photo_url) {
      img.src = material.photo_url;
      img.hidden = false;
      placeholder.hidden = true;
    }

    node.querySelector('.material-name').textContent = material.color
      ? `${material.name} (${material.color})`
      : material.name;
    node.querySelector('.material-qty').textContent =
      `${material.available_qty} ${material.unit} available · ${material.physical_qty} total · ${material.reserved_qty} reserved`;

    const fileInput = node.querySelector('.photo-upload input');
    fileInput.addEventListener('change', async () => {
      if (!fileInput.files.length) return;
      const formData = new FormData();
      formData.append('file', fileInput.files[0]);
      await fetch(`/inventory/${encodeURIComponent(material.id)}/photo`, {
        method: 'POST',
        body: formData,
      });
      loadInventory();
    });

    const qtyInput = node.querySelector('.material-adjust input');
    const saveBtn = node.querySelector('.material-adjust button');
    saveBtn.addEventListener('click', async () => {
      const delta = parseFloat(qtyInput.value);
      if (Number.isNaN(delta) || delta === 0) return;
      await fetch(`/inventory/${encodeURIComponent(material.id)}/adjust`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ delta, note: 'Adjusted from the calendar glance strip' }),
      });
      qtyInput.value = '';
      loadInventory();
      if (window.refreshCalendar) window.refreshCalendar();
    });

    strip.appendChild(node);
  }

  async function loadInventory() {
    try {
      const res = await fetch('/inventory/glance');
      const data = await res.json();
      strip.innerHTML = '';
      (data.materials || []).forEach(renderCard);
    } catch (err) {
      console.error(err);
    }
  }

  loadInventory();
  window.refreshInventory = loadInventory;
})();
