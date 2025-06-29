let logInterval, alertInterval, allLogInterval, liveFrameInterval
let zones = []
let drawingZone = false
let currentZone = {}
let videoCanvas = document.getElementById('videoCanvas')
let ctx = videoCanvas.getContext('2d')
let previousMonitoringStatus = null

function toggleInfo() {
  const modal = document.getElementById('infoModal')
  if (modal.style.display === 'flex') {
    modal.style.opacity = '0'
    setTimeout(() => {
      modal.style.display = 'none'
    }, 200)
  } else {
    modal.style.display = 'flex'
    setTimeout(() => {
      modal.style.opacity = '1'
    }, 10)
  }
}

function updateIntervals(running) {
  if (running) {
    if (!liveFrameInterval) {
      liveFrameInterval = setInterval(refreshLiveFeed, 1000)
    }
  } else {
    if (liveFrameInterval) {
      clearInterval(liveFrameInterval)
      liveFrameInterval = null
    }
  }
}

function setupModalOutsideClicks() {
  const modal = document.getElementById('infoModal')
  const confirmModal = document.getElementById('confirmModal')

  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      toggleInfo()
    }
  })

  confirmModal.addEventListener('click', (e) => {
    if (e.target === confirmModal) {
      confirmReset(false)
    }
  })
}

function toggleEmailField(enabled) {
  document.getElementById('emailField').style.display = enabled
    ? 'block'
    : 'none'
}

function handleVideoPreview() {
  const filename = document.getElementById('filename').value
  const previewEnabled =
    document.querySelector('input[name="previewToggle"]:checked').value ===
    'yes'
  const viewer = document.getElementById('videoViewer')
  const player = document.getElementById('videoPlayer')

  if (filename && previewEnabled) {
    player.src = `/static/videos/${filename}`
    viewer.style.display = 'block'

    player.onloadedmetadata = function () {
      videoCanvas.width = player.videoWidth
      videoCanvas.height = player.videoHeight
      drawVideoFrame()
    }
  } else {
    viewer.style.display = 'none'
    player.src = ''
  }
}

function startDrawingZone() {
  drawingZone = true
  videoCanvas.classList.add('drawing-active')
  document.getElementById('startDrawingBtn').disabled = true
}

function clearZones() {
  zones = []
  drawVideoFrame()
  showToast('Monitoring zones cleared', 'info')
}

function drawVideoFrame() {
  const player = document.getElementById('videoPlayer')

  if (player.src) {
    ctx.drawImage(player, 0, 0, videoCanvas.width, videoCanvas.height)
  } else {
    ctx.fillStyle = '#000'
    ctx.fillRect(0, 0, videoCanvas.width, videoCanvas.height)
  }

  zones.forEach((zone) => {
    ctx.strokeStyle = 'red'
    ctx.lineWidth = 2
    ctx.fillStyle = 'rgba(255, 0, 0, 0.2)'
    ctx.fillRect(zone.x, zone.y, zone.width, zone.height)
    ctx.strokeRect(zone.x, zone.y, zone.width, zone.height)
  })
}

videoCanvas.addEventListener('mousedown', (e) => {
  if (!drawingZone) return

  const rect = videoCanvas.getBoundingClientRect()
  const scaleX = videoCanvas.width / rect.width
  const scaleY = videoCanvas.height / rect.height

  currentZone.x = (e.clientX - rect.left) * scaleX
  currentZone.y = (e.clientY - rect.top) * scaleY
  currentZone.startX = currentZone.x
  currentZone.startY = currentZone.y
})

videoCanvas.addEventListener('mousemove', (e) => {
  if (!drawingZone || !currentZone.hasOwnProperty('startX')) return

  const rect = videoCanvas.getBoundingClientRect()
  const scaleX = videoCanvas.width / rect.width
  const scaleY = videoCanvas.height / rect.height
  const currX = (e.clientX - rect.left) * scaleX
  const currY = (e.clientY - rect.top) * scaleY

  currentZone.width = currX - currentZone.startX
  currentZone.height = currY - currentZone.startY

  drawVideoFrame()

  ctx.strokeStyle = 'yellow'
  ctx.lineWidth = 2
  ctx.fillStyle = 'rgba(255, 255, 0, 0.2)'
  ctx.fillRect(
    currentZone.x,
    currentZone.y,
    currentZone.width,
    currentZone.height
  )
  ctx.strokeRect(
    currentZone.x,
    currentZone.y,
    currentZone.width,
    currentZone.height
  )
})

videoCanvas.addEventListener('mouseup', (e) => {
  if (!drawingZone || !currentZone.hasOwnProperty('startX')) return

  const rect = videoCanvas.getBoundingClientRect()
  const scaleX = videoCanvas.width / rect.width
  const scaleY = videoCanvas.height / rect.height

  if (currentZone.width < 0) {
    currentZone.x += currentZone.width
    currentZone.width = Math.abs(currentZone.width)
  }

  if (currentZone.height < 0) {
    currentZone.y += currentZone.height
    currentZone.height = Math.abs(currentZone.height)
  }

  zones.push({
    x: currentZone.x,
    y: currentZone.y,
    width: currentZone.width,
    height: currentZone.height,
  })

  drawingZone = false
  videoCanvas.classList.remove('drawing-active')
  document.getElementById('startDrawingBtn').disabled = false
  currentZone = {}

  drawVideoFrame()
  showToast(`Zone ${zones.length} added`, 'success')
})

function saveZones() {
  fetch('/save-zones', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ zones }),
  })
}

function showToast(message, type = 'info') {
  const toast = document.getElementById('toast')
  const toastMessage = document.getElementById('toastMessage')
  const toastIcon = document.getElementById('toastIcon')

  toastMessage.textContent = message

  let iconSvg = ''
  if (type === 'success') {
    iconSvg =
      '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>'
  } else if (type === 'error') {
    iconSvg =
      '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>'
  } else if (type === 'warning') {
    iconSvg =
      '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>'
  } else {
    iconSvg =
      '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x="12" y="16" x2="12" y2="12"></line><line x="12" y="8" x2="12.01" y2="8"></line></svg>'
  }

  toastIcon.innerHTML = iconSvg

  toast.classList.add('show')

  setTimeout(() => {
    toast.classList.remove('show')
  }, 3000)
}

function showConfirmModal() {
  const modal = document.getElementById('confirmModal')
  modal.style.display = 'flex'
  setTimeout(() => (modal.style.opacity = 1), 10)
}

async function confirmReset(yes) {
  const modal = document.getElementById('confirmModal')
  modal.style.opacity = 0
  setTimeout(() => (modal.style.display = 'none'), 200)

  if (!yes) return

  clearInterval(alertInterval)
  clearInterval(allLogInterval)

  const res = await fetch('/reset', { method: 'POST' })
  await res.json()

  showToast('Logs and screenshots deleted.', 'warning')
  document.getElementById('criticalList').innerHTML = ''
  document.getElementById('allLogsList').innerHTML = ''

  alertInterval = setInterval(fetchCriticalAlerts, 500)
  allLogInterval = setInterval(fetchAllLogs, 500)
}

async function fetchStatus() {
  try {
    const res = await fetch('/status')
    const data = await res.json()
    const running = data.running

    if (previousMonitoringStatus === true && running === false) {
      showToast('Monitoring has ended', 'info')
    }

    previousMonitoringStatus = running

    updateMonitoringStatus(running)

    return running
  } catch (error) {
    console.error('Error fetching status:', error)
    resetLiveFeed()
    return false
  }
}

document.getElementById('startDrawingBtn').onclick = startDrawingZone
document.getElementById('clearZonesBtn').onclick = clearZones

async function fetchLogs() {
  const res = await fetch('/logs/live')
  const data = await res.json()
  document.getElementById('logbox').textContent = data.join('\n')
}

async function fetchCriticalAlerts() {
  const res = await fetch('/logs/action-required')
  const data = await res.json()
  const list = document.getElementById('criticalList')
  list.innerHTML = ''
  if (data.length === 0) {
    list.innerHTML = '<li>No critical alerts.</li>'
  } else {
    data.forEach((entry) => {
      const dangerClass =
        entry.analysis.danger === 'CRITICAL'
          ? 'danger-critical'
          : entry.analysis.danger === 'HIGH'
          ? 'danger-high'
          : entry.analysis.danger === 'MEDIUM'
          ? 'danger-medium'
          : 'danger-low'

      const li = document.createElement('li')
      li.innerHTML = `
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 500;">${entry.timestamp}</span>
                <span class="${dangerClass}" style="font-weight: 600;">
                  ${entry.analysis.danger}
                </span>
              </div>
              <div style="margin-top: 0.5rem;">
                <strong>Action: </strong>${entry.analysis.recommended_response}
              </div>
              <div style="margin-top: 0.5rem;">
                <strong>Summary: </strong>${
                  entry.analysis.summary || 'No summary available.'
                }
              </div>
              <div style="margin-top: 0.5rem;">
                <a href="/images/${
                  entry.image
                }" target="_blank" class="btn btn-secondary" style="font-size: 0.8rem; padding: 0.3rem 0.6rem;">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                    <circle cx="8.5" cy="8.5" r="1.5"></circle>
                    <polyline points="21 15 16 10 5 21"></polyline>
                  </svg>
                  View Image
                </a>
                <a href="/images/${
                  entry.timestamp
                }.json" target="_blank" class="btn btn-secondary" style="font-size: 0.8rem; padding: 0.3rem 0.6rem; margin-left: 0.5rem;">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                    <line x1="16" y1="13" x2="8" y2="13"></line>
                    <line x1="16" y1="17" x2="8" y2="17"></line>
                    <polyline points="10 9 9 9 8 9"></polyline>
                  </svg>
                  View Log
                </a>
              </div>
            `
      list.appendChild(li)
    })
  }
}

async function fetchAllLogs() {
  const res = await fetch('/logs')
  const data = await res.json()
  const list = document.getElementById('allLogsList')
  list.innerHTML = ''
  if (data.length === 0) {
    list.innerHTML = '<li>No logs available.</li>'
  } else {
    data.forEach((entry) => {
      const dangerClass =
        entry.analysis.danger === 'CRITICAL'
          ? 'danger-critical'
          : entry.analysis.danger === 'HIGH'
          ? 'danger-high'
          : entry.analysis.danger === 'MEDIUM'
          ? 'danger-medium'
          : 'danger-low'

      const li = document.createElement('li')
      li.innerHTML = `
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 500;">${entry.timestamp}</span>
                <span class="${dangerClass}" style="font-weight: 600;">
                  ${entry.analysis.danger}
                </span>
              </div>
              <div style="margin-top: 0.5rem;">
                <a href="/images/${entry.image}" target="_blank" class="btn btn-secondary" style="font-size: 0.8rem; padding: 0.3rem 0.6rem;">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                    <circle cx="8.5" cy="8.5" r="1.5"></circle>
                    <polyline points="21 15 16 10 5 21"></polyline>
                  </svg>
                  View Image
                </a>
                <a href="/images/${entry.timestamp}.json" target="_blank" class="btn btn-secondary" style="font-size: 0.8rem; padding: 0.3rem 0.6rem; margin-left: 0.5rem;">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                    <line x1="16" y1="13" x2="8" y2="13"></line>
                    <line x1="16" y1="17" x2="8" y2="17"></line>
                    <polyline points="10 9 9 9 8 9"></polyline>
                  </svg>
                  View Log
                </a>
              </div>
            `
      list.appendChild(li)
    })
  }
}

function refreshLiveFeed() {
  const img = document.getElementById('liveFeed')
  const timestamp = new Date().getTime()
  fetch('/status')
    .then((response) => response.json())
    .then((data) => {
      if (data.running) {
        img.src = `/current_frame?t=${timestamp}`
      } else {
        resetLiveFeed()
      }
    })
    .catch((error) => {
      console.error('Error checking status:', error)
    })
}

function resetLiveFeed() {
  const img = document.getElementById('liveFeed')
  img.src =
    'data:image/svg+xml;charset=utf-8,' +
    encodeURIComponent(`
      <svg width="640" height="360" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#111113"/>
        <text x="50%" y="50%" font-family="Inter, sans-serif" font-size="14" 
          fill="#a1a1aa" text-anchor="middle" dominant-baseline="middle">
          Current frame isn't available. Start monitoring to view.
        </text>
      </svg>
    `)
}

logInterval = setInterval(fetchLogs, 500)
alertInterval = setInterval(fetchCriticalAlerts, 500)
allLogInterval = setInterval(fetchAllLogs, 500)
document.addEventListener('DOMContentLoaded', () => {
  setupModalOutsideClicks()
  drawVideoFrame()
  fetchStatus()
  resetLiveFeed()
})
setInterval(fetchStatus, 500)

fetchLogs()
fetchCriticalAlerts()
fetchAllLogs()
fetchStatus()

// Add event listeners for live camera functionality
document.addEventListener('DOMContentLoaded', function() {
    // Test camera button
    const testCameraBtn = document.getElementById('testCameraBtn')
    if (testCameraBtn) {
        testCameraBtn.addEventListener('click', testCamera)
    }

    // Start live monitoring button
    const startLiveBtn = document.getElementById('startLiveBtn')
    if (startLiveBtn) {
        startLiveBtn.addEventListener('click', startLiveMonitoring)
    }

    // Test call button
    const testCallBtn = document.getElementById('testCallBtn')
    if (testCallBtn) {
        testCallBtn.addEventListener('click', testCallService)
    }

    // Existing event listeners
    setupModalOutsideClicks()
    
    // Start monitoring button
    const startBtn = document.getElementById('startBtn')
    if (startBtn) {
        startBtn.addEventListener('click', startMonitoring)
    }
    
    // Stop monitoring button
    const stopBtn = document.getElementById('stopBtn')
    if (stopBtn) {
        stopBtn.addEventListener('click', stopMonitoring)
    }
    
    // Reset button
    const resetBtn = document.getElementById('resetBtn')
    if (resetBtn) {
        resetBtn.addEventListener('click', showConfirmModal)
    }
    
    // Initial status check
    fetchStatus()
    
    // Start intervals
    logInterval = setInterval(fetchLogs, 2000)
    alertInterval = setInterval(fetchCriticalAlerts, 3000)
    allLogInterval = setInterval(fetchAllLogs, 5000)
})

async function testCamera() {
    const cameraSelect = document.getElementById('cameraSelect')
    const cameraIndex = parseInt(cameraSelect.value)
    
    try {
        const response = await fetch('/camera-test')
        const data = await response.json()
        
        if (data.available_cameras.includes(cameraIndex)) {
            showToast(`Camera ${cameraIndex} is available and working!`, 'success')
        } else {
            showToast(`Camera ${cameraIndex} is not available. Try a different camera.`, 'error')
        }
    } catch (error) {
        showToast('Failed to test camera. Please check your connection.', 'error')
        console.error('Camera test error:', error)
    }
}

async function startLiveMonitoring() {
    const cameraSelect = document.getElementById('cameraSelect')
    const livePrivacyBlur = document.getElementById('livePrivacyBlur')
    const emailField = document.getElementById('email')
    const enableEmail = document.getElementById('enableEmail')
    
    const cameraIndex = parseInt(cameraSelect.value)
    const privacyBlur = livePrivacyBlur.checked
    const email = enableEmail.checked ? emailField.value : null
    
    if (enableEmail.checked && !email) {
        showToast('Please enter an email address for alerts', 'error')
        return
    }
    
    try {
        const response = await fetch('/start-live', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                camera_index: cameraIndex,
                privacy_blur: privacyBlur,
                zones: zones
            })
        })
        
        const data = await response.json()
        
        if (data.status === 'started') {
            showToast('Live camera monitoring started!', 'success')
            updateMonitoringStatus(true)
            updateIntervals(true)
        } else {
            showToast(data.message || 'Failed to start live monitoring', 'error')
        }
    } catch (error) {
        showToast('Failed to start live monitoring. Please check your connection.', 'error')
        console.error('Start live monitoring error:', error)
    }
}

async function startMonitoring() {
    const enableEmail = document.getElementById('enableEmail').checked
    const email = enableEmail ? document.getElementById('email').value : null
    const filename = document.getElementById('filename').value
    const privacyBlur = document.getElementById('privacyBlur').checked

    if (!filename) {
        return showToast('Please select a video file.', 'error')
    }

    saveZones()

    const res = await fetch('/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            email,
            filename,
            privacy_blur: privacyBlur,
            use_live_camera: false
        }),
    })
    const data = await res.json()
    showToast(`Monitoring started${email ? ' for ' + email : ''}`, 'success')
    fetchStatus()
}

async function stopMonitoring() {
    const res = await fetch('/stop', { method: 'POST' })
    await res.json()
    showToast('Monitoring stopped.', 'warning')
    fetchStatus()
    resetLiveFeed()
}

function updateMonitoringStatus(running) {
    document.getElementById('monitoringStatus').innerHTML = running
        ? '<div class="status-badge status-running"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12c0 5.5-4.5 10-10 10S2 17.5 2 12 6.5 2 12 2s10 4.5 10 10z"></path><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>Monitoring is active</div>'
        : '<div class="status-badge status-stopped"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12c0 5.5-4.5 10-10 10S2 17.5 2 12 6.5 2 12 2s10 4.5 10 10z"></path><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>Monitoring is inactive</div>'

    // Update button states
    const startBtn = document.getElementById('startBtn')
    const stopBtn = document.getElementById('stopBtn')
    const startLiveBtn = document.getElementById('startLiveBtn')
    const filename = document.getElementById('filename')
    const email = document.getElementById('email')
    const enableEmail = document.getElementById('enableEmail')
    const privacyBlur = document.getElementById('privacyBlur')
    const livePrivacyBlur = document.getElementById('livePrivacyBlur')
    const cameraSelect = document.getElementById('cameraSelect')
    const testCameraBtn = document.getElementById('testCameraBtn')

    if (startBtn) startBtn.disabled = running
    if (stopBtn) stopBtn.disabled = !running
    if (startLiveBtn) startLiveBtn.disabled = running
    if (filename) filename.disabled = running
    if (email) email.disabled = running
    if (enableEmail) enableEmail.disabled = running
    if (privacyBlur) privacyBlur.disabled = running
    if (livePrivacyBlur) livePrivacyBlur.disabled = running
    if (cameraSelect) cameraSelect.disabled = running
    if (testCameraBtn) testCameraBtn.disabled = running

    updateIntervals(running)

    if (!running) {
        resetLiveFeed()
    }
}

async function testCallService() {
    try {
        showToast('Testing call service...', 'info')
        
        const response = await fetch('/test-call', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        
        const data = await response.json()
        
        if (data.status === 'success') {
            showToast('Test call initiated! You should receive a call shortly.', 'success')
        } else {
            showToast(data.message || 'Failed to make test call', 'error')
        }
    } catch (error) {
        showToast('Failed to test call service. Please check your connection.', 'error')
        console.error('Test call error:', error)
    }
}
