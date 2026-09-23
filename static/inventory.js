(function () {
  const tree = document.getElementById('fabric-tree');
  const categoryTemplate = document.getElementById('tree-category-template');
  const materialTemplate = document.getElementById('tree-material-template');

  function titleCase(word) {
    return (word || 'Other').replace(/\b\w/g, (c) => c.toUpperCase());
  }

  function groupByCategory(materials) {
    const groups = new Map();
    materials.forEach((material) => {
      const key = material.category || 'other';
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(material);
    });
    return groups;
  }

  function renderMaterial(material) {
    const node = materialTemplate.content.cloneNode(true);
    const row = node.querySelector('.tree-material-row');
    const detail = node.querySelector('.tree-material-detail');
    const swatch = node.querySelector('.tree-swatch');
    const img = node.querySelector('img');

    if (material.photo_url) {
      img.src = material.photo_url;
      img.hidden = false;
    } else if (material.color) {
      swatch.style.background = material.color.toLowerCase();
    }

    node.querySelector('.tree-material-label').textContent = material.color
      ? `${material.name} — ${material.color}`
      : material.name;
    node.querySelector('.tree-material-qty').textContent =
      `${material.available_qty} ${material.unit} available · ${material.physical_qty} total · ${material.reserved_qty} reserved`;

    row.addEventListener('click', () => {
      detail.hidden = !detail.hidden;
    });

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
    saveBtn.addEventListener('click', async (event) => {
      event.stopPropagation();
      const delta = parseFloat(qtyInput.value);
      if (Number.isNaN(delta) || delta === 0) return;
      await fetch(`/inventory/${encodeURIComponent(material.id)}/adjust`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ delta, note: 'Adjusted from the fabric tree' }),
      });
      qtyInput.value = '';
      loadInventory();
      if (window.refreshCalendar) window.refreshCalendar();
    });

    return node;
  }

  function renderCategory(name, materials) {
    const node = categoryTemplate.content.cloneNode(true);
    const header = node.querySelector('.tree-category-header');
    const chevron = node.querySelector('.tree-chevron');
    const children = node.querySelector('.tree-children');

    node.querySelector('.tree-category-name').textContent = titleCase(name);
    materials.forEach((material) => children.appendChild(renderMaterial(material)));

    header.addEventListener('click', () => {
      children.hidden = !children.hidden;
      chevron.classList.toggle('open', !children.hidden);
    });

    return node;
  }

  async function loadInventory() {
    try {
      const res = await fetch('/inventory/glance');
      const data = await res.json();
      tree.innerHTML = '';
      const groups = groupByCategory(data.materials || []);
      groups.forEach((materials, category) => {
        tree.appendChild(renderCategory(category, materials));
      });
    } catch (err) {
      console.error(err);
    }
  }

  loadInventory();
  window.refreshInventory = loadInventory;
})();
