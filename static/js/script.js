const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const fileInfo = document.getElementById("file-info");
const filenameSpan = document.getElementById("filename");
const convertBtn = document.getElementById("convert-btn");
const loader = document.getElementById("loader");
const result = document.getElementById("result");
const downloadLink = document.getElementById("download-link");
const restartBtn = document.getElementById("restart-btn");

let currentFile = null;

// Drag & Drop events
["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
  dropZone.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
  e.preventDefault();
  e.stopPropagation();
}

["dragenter", "dragover"].forEach((eventName) => {
  dropZone.addEventListener(
    eventName,
    () => dropZone.classList.add("dragover"),
    false,
  );
});

["dragleave", "drop"].forEach((eventName) => {
  dropZone.addEventListener(
    eventName,
    () => dropZone.classList.remove("dragover"),
    false,
  );
});

dropZone.addEventListener("drop", handleDrop, false);

function handleDrop(e) {
  const dt = e.dataTransfer;
  const files = dt.files;
  handleFiles(files);
}

dropZone.onclick = () => fileInput.click();

fileInput.onchange = (e) => handleFiles(e.target.files);

function handleFiles(files) {
  if (files.length > 0) {
    const file = files[0];
    if (file.type !== "application/pdf") {
      alert("Please upload a PDF file.");
      return;
    }
    currentFile = file;
    filenameSpan.textContent = file.name;

    dropZone.classList.add("hidden");
    fileInfo.classList.remove("hidden");
  }
}

convertBtn.onclick = async () => {
  if (!currentFile) return;

  const formData = new FormData();
  formData.append("file", currentFile);

  fileInfo.classList.add("hidden");
  loader.classList.remove("hidden");

  try {
    const response = await fetch("/upload", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (response.ok) {
      downloadLink.href = data.download_url;
      loader.classList.add("hidden");
      result.classList.remove("hidden");
    } else {
      throw new Error(data.error || "Conversion failed");
    }
  } catch (error) {
    alert(error.message);
    loader.classList.add("hidden");
    fileInfo.classList.remove("hidden");
  }
};

restartBtn.onclick = () => {
  currentFile = null;
  result.classList.add("hidden");
  dropZone.classList.remove("hidden");
  fileInput.value = "";
};
