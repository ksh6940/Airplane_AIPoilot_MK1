const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".panel");
const sidebarToggle = document.getElementById("sidebar-toggle");
const sidebar = document.getElementById("sidebar");
const topbar = document.getElementById("topbar");
const iframe = document.getElementById("mapframe");
const deleteBtn = document.getElementById("delete-btn");
const btnFilter = document.getElementById("btn-filter");
const btnRoute = document.getElementById("btn-route");
const btnLoading = document.getElementById("btn-loading");
const btnRemoveRoute = document.getElementById("btn-remove-route");
const maptypeNormalBtn = document.getElementById("maptype-normal-btn");
const maptypeSatelliteBtn = document.getElementById("maptype-satellite-btn");

let zoomLevel; // 줌 레벨 변수

// 초기 줌 레벨 설정
document.addEventListener("DOMContentLoaded", () => {
  if (window.mapState && typeof window.mapState.zoom !== 'undefined') {
    zoomLevel = window.mapState.zoom;
    console.log(`초기 줌 레벨: ${zoomLevel}`);
  } else {
    zoomLevel = 8; // 기본값
    console.log(`기본 줌 레벨: ${zoomLevel}`);
  }
});

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((t) => t.classList.remove("active"));
    panels.forEach((p) => p.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(tab.dataset.tab).classList.add("active");
    sendSidebarState();
  });
});

sidebarToggle.addEventListener("click", () => {
  if (sidebar.classList.contains("hidden")) {
    sidebar.classList.remove("hidden");
    topbar.style.display = "none";
  } else {
    sidebar.classList.add("hidden");
    topbar.style.display = "flex";
  }
  sendSidebarState();
});

async function geocode(address) {
  const url = `/api/geocode?q=${encodeURIComponent(address)}`;
  const res = await fetch(url);
  if (!res.ok) {
    const errorData = await res.json();
    throw new Error(errorData.error || `HTTP 오류: ${res.status}`);
  }
  return res.json();
}

async function addLocationToServer(place_name, latitude, longitude) {
  try {
    const res = await fetch("/api/location", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ place_name, latitude, longitude }),
    });
    if (!res.ok) throw new Error("서버 응답 오류");
    const result = await res.json();
    console.log("서버 응답:", result);

    if (result.success && result.reloadMap) {
      iframe.src = iframe.src;
      console.log("🗺 지도 새로고침 완료");
      deleteBtn.style.display = "flex";
    } else if (!result.success) {
      console.log(`❌ 서버 응답 오류: ${result.message}`);
    }
  } catch (e) {
    console.error("서버 전송 오류:", e);
    console.log("❌ 서버 전송 오류: " + e.message);
  }
}

function sendToMap(data) {
  iframe.contentWindow.postMessage(data, "*");
}

document.getElementById("btn-location").addEventListener("click", async () => {
  const place = document.getElementById("search").value.trim();
  if (!place) return alert("장소를 입력하세요.");
  console.log("주소 변환 중...");

  try {
    const loc = await geocode(place);
    sendToMap({ type: "markLocation", location: [loc.lat, loc.lon] });
    console.log(`📍 ${loc.display_name}`);
    await addLocationToServer(place, loc.lat, loc.lon);
  } catch (e) {
    console.log("❌ 에러: " + e.message);
    console.error(e);
  }
});

btnRoute.addEventListener("click", async () => {
  btnRoute.style.display = "none";
  btnLoading.style.display = "inline-block";

  const start = document.getElementById("start").value.trim();
  const end = document.getElementById("end").value.trim();

  if (!start || !end) {
    alert("출발지와 도착지를 모두 입력하세요.");
    btnRoute.style.display = "block";
    btnLoading.style.display = "none";
    return;
  }

  alert("✈️ 경로 탐색을 시작합니다. 시간이 걸릴 수 있습니다.");
  console.log("주소 변환 중...");

  const delayTimeout = setTimeout(() => {
    alert("🛰 현재 응답이 지연되고 있습니다. 잠시만 기다려 주세요.");
  }, 5000);

  try {
    const startLoc = await geocode(start);
    const endLoc = await geocode(end);

    const routeResponse = await fetch("/api/route", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        startLocation: { name: start, latitude: startLoc.lat, longitude: startLoc.lon },
        endLocation: { name: end, latitude: endLoc.lat, longitude: endLoc.lon },
      }),
    });

    const result = await routeResponse.json();
    if (!routeResponse.ok || !result.success) {
      throw new Error(result.message || "경로 데이터 전송 실패");
    }

    clearTimeout(delayTimeout);
    
    // 경로 정보 표시
    const summary = result.summary;
    document.getElementById("summary-start").textContent = summary.start_point;
    document.getElementById("summary-end").textContent = summary.end_point;
    document.getElementById("summary-time").textContent = summary.estimated_time;
    document.getElementById("summary-distance").textContent = summary.total_distance;

    // 경로 분석 결과 표시
    const analysis = result.analysis;
    const warningDiv = document.getElementById("summary-warning");
    const analysisRow = document.getElementById("summary-analysis");

    if (analysis && analysis.warnings && analysis.warnings.length > 0) {
      warningDiv.innerHTML = analysis.warnings.join('<br>');
      analysisRow.style.display = 'flex';
    } else {
      analysisRow.style.display = 'none';
    }

    document.getElementById("route-summary").style.display = "block";
    btnRemoveRoute.style.display = "block";
    deleteBtn.style.display = "flex";

    document.getElementById("route-summary").addEventListener("click", () => {
        document.getElementById("route-summary").style.display = "block";
    });

    document.getElementById("route-summary").addEventListener("click", () => {
        document.getElementById("route-summary").style.display = "block";
    });

    iframe.src = iframe.src; // 지도 새로고침
    
    alert("✅ 경로 탐색이 완료되었습니다.");

  } catch (e) {
    clearTimeout(delayTimeout);
    alert(`❌ 경로 탐색 중 오류가 발생했습니다: ${e.message}`);
    console.error(e);
  } finally {
    btnRoute.style.display = "block";
    btnLoading.style.display = "none";
  }
});

btnRemoveRoute.addEventListener("click", async () => {
    try {
        const res = await fetch("/api/delete-route", { method: "POST" });
        const result = await res.json();
        if (result.success) {
            document.getElementById("route-summary").style.display = "none";
            btnRemoveRoute.style.display = "none";
            deleteBtn.style.display = "none";
            iframe.src = iframe.src;
            console.log("🧹 경로가 삭제되었습니다.");
        } else {
            throw new Error(result.message || "경로 삭제 실패");
        }
    } catch (e) {
        alert(`❌ 경로 삭제 중 오류: ${e.message}`);
        console.error(e);
    }
});


document.getElementById("global-search-btn").addEventListener("click", async () => {
    const place = document.getElementById("global-search").value.trim();
    if (!place) return alert("검색어를 입력하세요.");
    console.log("주소 변환 중...");

    try {
      const loc = await geocode(place);
      sendToMap({ type: "markLocation", location: [loc.lat, loc.lon] });
      console.log(`🌐 ${loc.display_name}`);
      await addLocationToServer(place, loc.lat, loc.lon);
    } catch (e) {
      console.log("❌ 에러: " + e.message);
      console.error(e);
    }
  });

async function changeMapType(type) {
    mapType = type;
    if (type === "satellite") {
        maptypeSatelliteBtn.classList.add("active");
        maptypeNormalBtn.classList.remove("active");
    } else {
        maptypeNormalBtn.classList.add("active");
        maptypeSatelliteBtn.classList.remove("active");
    }
    
    try {
      const res = await fetch("/api/map-action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: "changeMapType", mapType: type }),
      });
      const data = await res.json();
      if (data.success) {
        iframe.src = iframe.src;
        console.log(`🗺 지도 모드 변경 완료: ${type}`);
      }
    } catch (err) {
      console.error("❌ 지도 모드 변경 중 오류:", err);
    }
}

maptypeNormalBtn.addEventListener("click", () => changeMapType("normal"));
maptypeSatelliteBtn.addEventListener("click", () => changeMapType("satellite"));


const MIN_ZOOM = 7;
const MAX_ZOOM = 16;

async function setZoom(level) {
    zoomLevel = Math.max(MIN_ZOOM, Math.min(level, MAX_ZOOM));
    console.log("현재 확대 레벨:", zoomLevel);
    
    try {
        const res = await fetch("/api/map-action", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ type: "setZoom", zoomLevel }),
        });
        const data = await res.json();
        if (data.success) {
            iframe.src = iframe.src;
            console.log("🗺 지도 줌 조정 완료");
        }
    } catch (e) {
        console.error("줌 변경 오류:", e);
    }
}

document.getElementById("btn-zoom-in").addEventListener("click", () => setZoom(zoomLevel + 1));
document.getElementById("btn-zoom-out").addEventListener("click", () => setZoom(zoomLevel - 1));


const legendTypes = [
  { name: "비행 가능", info: "드론 등 초경량 비행장치 운용 가능" },
  { name: "비행 금지", info: "비행이 법적으로 금지된 구역" },
  { name: "비행 제한", info: "특정 조건에서만 비행 가능" },
  { name: "비행 경고", info: "비행 전 특별 주의 필요" },
  { name: "비행 위험", info: "비행 시 위험 요소 존재" },
  { name: "군 작전", info: "군 작전이 이루어지는 공역" },
];
let selectedTypes = legendTypes.map((t) => t.name);

function showFilterPopup() {
  const popup = document.getElementById("filter-popup");
  const rect = btnFilter.getBoundingClientRect();
  popup.style.display = "block";
  popup.style.position = "fixed";
  let left = rect.left;
  let top = rect.bottom + 8;
  const maxRight = window.innerWidth - 20;
  if (left + 160 > maxRight) left = maxRight - 160;
  popup.style.left = left + "px";
  popup.style.top = top + "px";
  popup.style.width = "160px";
  popup.style.right = "";
  popup.style.borderRadius = "10px";
  popup.style.zIndex = "101";
  renderFilterBtns();
  updateFilterAllBtn();
}

function hideFilterPopup() {
  const popup = document.getElementById("filter-popup");
  popup.style.display = "none";
  btnFilter.classList.remove("active");
}

function renderFilterBtns() {
  const btnsDiv = document.getElementById("filter-btns");
  btnsDiv.innerHTML = "";
  btnsDiv.style.display = "flex";
  btnsDiv.style.flexDirection = "column";
  legendTypes.forEach((typeObj) => {
    const btn = document.createElement("button");
    btn.className = "filter-btn";
    btn.textContent = typeObj.name;
    btn.style.background = selectedTypes.includes(typeObj.name) ? "#000" : "#eee";
    btn.style.color = selectedTypes.includes(typeObj.name) ? "#fff" : "#555";
    btn.style.margin = "2px 0";
    btn.onclick = () => {
      if (selectedTypes.includes(typeObj.name)) {
        selectedTypes = selectedTypes.filter((t) => t !== typeObj.name);
      } else {
        selectedTypes.push(typeObj.name);
      }
      renderFilterBtns();
      updateFilterAllBtn();
    };
    btnsDiv.appendChild(btn);
  });
  updateFilterAllBtn();
}

function updateFilterAllBtn() {
  const allBtn = document.getElementById("filter-all-btn");
  if (selectedTypes.length === legendTypes.length) {
    allBtn.textContent = "모두 취소";
    allBtn.style.background = "#eee";
    allBtn.style.color = "#000";
  } else {
    allBtn.textContent = "모두 선택";
    allBtn.style.background = "#000";
    allBtn.style.color = "#fff";
  }
}

document.getElementById("filter-all-btn").onclick = () => {
  if (selectedTypes.length === legendTypes.length) {
    selectedTypes = [];
  } else {
    selectedTypes = legendTypes.map((t) => t.name);
  }
  renderFilterBtns();
};

window.addEventListener("mousedown", (e) => {
  const popup = document.getElementById("filter-popup");
  if (popup.style.display === "block" && !popup.contains(e.target) && e.target.id !== "btn-filter") {
    hideFilterPopup();
  }
});

document.getElementById("filter-confirm-btn").onclick = () => {
  hideFilterPopup();

  fetch("/api/map-action", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      type: "filterConfirm",
      selectedFilters: selectedTypes,
    }),
  })
    .then((res) => res.json())
    .then((data) => {
      console.log("🎯 필터 값 전송 완료:", data);
      if (data.success && data.reloadMap) {
        iframe.src = iframe.src;
        console.log("🗺 필터 적용 및 지도 새로고침 완료");
      } else if (!data.success) {
        console.log(`❌ 필터 적용 실패: ${data.message}`);
      }
    })
    .catch((error) => {
      console.log(`❌ 필터 전송 오류: ${error.message}`);
    });
};

function sendSidebarState() {
  const isSidebarOpen = !sidebar.classList.contains("hidden");
  const activeTab = document.querySelector(".tab.active")?.dataset.tab || "unknown";

  fetch("/api/map-action", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      type: "uiState",
      sidebarOpen: isSidebarOpen,
      activeMode: activeTab,
    }),
  })
    .then((res) => res.json())
    .then((data) => {
      console.log("📡 UI 상태 전송 완료:", data);
    })
    .catch((error) => {
      console.error("UI 상태 전송 오류:", error);
    });
}

window.addEventListener("message", async (event) => {
  if (event.data && event.data.type === "addMarkerFromMapClick") {
    const location = event.data.location;
    if (location) {
      await addLocationToServer(null, location[0], location[1]);
    } else {
      console.warn("⚠ addMarkerFromMapClick에 대한 위치 데이터가 수신되지 않았습니다.");
    }
  }
});

document.getElementById("delete-btn").addEventListener("click", async () => {
  deleteBtn.disabled = true;
  deleteBtn.style.opacity = 0.5;

  try {
    const res = await fetch("/api/deleteMarker", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: "deleteMarker" }),
    });

    const result = await res.json();
    if (result.success) {
      console.log("🧹 마커 제거 성공");
      deleteBtn.style.display = "none";
      iframe.src = iframe.src;
    } else {
      console.log("❌ 마커 제거 실패");
      console.error("마커 제거 실패:", result.message);
    }
  } catch (err) {
    console.log("❌ 서버 오류");
    console.error("마커 제거 중 서버 오류:", err);
  } finally {
    deleteBtn.disabled = false;
    deleteBtn.style.opacity = 1;
  }
});
