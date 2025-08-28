const form = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const dropzone = document.getElementById('dropzone');
const statusDiv = document.getElementById('status');
const results = document.getElementById('results');

dropzone.addEventListener('click', () => fileInput.click());
dropzone.addEventListener('dragover', (e)=>{ e.preventDefault(); dropzone.style.borderColor='#00ffe1'; });
dropzone.addEventListener('dragleave', (e)=>{ e.preventDefault(); dropzone.style.borderColor='rgba(38,255,124,0.6)'; });
dropzone.addEventListener('drop', (e)=>{
  e.preventDefault();
  dropzone.style.borderColor='rgba(38,255,124,0.6)';
  if(e.dataTransfer.files.length){
    fileInput.files = e.dataTransfer.files;
  }
});

form.addEventListener('submit', async (e)=>{
  e.preventDefault();
  if(!fileInput.files.length){
    statusDiv.textContent = "Please select an image.";
    return;
  }
  statusDiv.textContent = "Analyzing...";
  const fd = new FormData();
  fd.append('file', fileInput.files[0]);

  try{
    const res = await fetch('/analyze', { method:'POST', body:fd });
    const data = await res.json();
    if(!res.ok){ throw new Error(data.error || 'Server error'); }

    // Update metrics
    document.getElementById('seagrass_pct').textContent = data.seagrass_pct + '%';
    document.getElementById('white_pct').textContent = data.white_pct + '%';
    document.getElementById('blue_carbon').textContent = data.blue_carbon_g.toFixed(2);

    // Overlays
    document.getElementById('overlay_seagrass').src = 'data:image/png;base64,' + data.overlay_seagrass_b64;
    document.getElementById('overlay_white').src = 'data:image/png;base64,' + data.overlay_white_b64;

    // Chart
    const ctx = document.getElementById('pieChart').getContext('2d');
    if(window._pie) window._pie.destroy();
    window._pie = new Chart(ctx, {
      type: 'pie',
      data: {
        labels: ['Seagrass','White Sand','Other'],
        datasets: [{
          data: [data.seagrass_pct, data.white_pct, Math.max(0, 100 - data.seagrass_pct - data.white_pct)]
        }]
      },
      options: {
        plugins: { legend: { labels: { color: '#e6ffff' } } }
      }
    });

    results.style.display = '';
    statusDiv.textContent = "Done.";
  }catch(err){
    console.error(err);
    statusDiv.textContent = 'Error: ' + err.message;
  }
});