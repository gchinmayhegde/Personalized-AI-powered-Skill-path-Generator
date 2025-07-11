<template>
  <div class="container">
    <h1>🧭 SkillPath Generator</h1>
    <input v-model="goal" placeholder="Enter your goal..." />
    <button @click="generateRoadmap">Generate Plan</button>

    <div v-if="loading">Generating...</div>

    <div v-if="roadmap">
      <pre class="response-box">{{ roadmap }}</pre>
      <button @click="copyToClipboard">📋 Copy</button>
      <button @click="exportAsMarkdown">📄 Export as Markdown</button>
      <button @click="exportAsPDF">🧾 Export as PDF</button>
    </div>
  </div>
</template>


<script setup>
import { ref } from 'vue'

const goal = ref("")
const roadmap = ref("")
const loading = ref(false)

const generateRoadmap = async () => {
  loading.value = true
  roadmap.value = ""
  try {
    const res = await fetch("http://localhost:5000/generate-roadmap", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ goal: goal.value })
    })
    const data = await res.json()
    roadmap.value = data.roadmap
  } catch (err) {
    roadmap.value = "Error: " + err.message
  }
  loading.value = false
}

// ✅ Copy to Clipboard
const copyToClipboard = () => {
  navigator.clipboard.writeText(roadmap.value)
    .then(() => alert("✅ Copied to clipboard!"))
    .catch(() => alert("❌ Failed to copy!"))
}

// ✅ Export as Markdown (.md)
const exportAsMarkdown = () => {
  const blob = new Blob([roadmap.value], { type: "text/markdown" })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = "roadmap.md"
  link.click()
  URL.revokeObjectURL(url)
}

// ✅ Export as PDF (using print)
const exportAsPDF = () => {
  const printWindow = window.open('', '', 'width=800,height=600')
  printWindow.document.write(`
    <html><head><title>Roadmap PDF</title></head><body>
    <pre style="font-family:Courier New; white-space:pre-wrap;">${roadmap.value}</pre>
    </body></html>
  `)
  printWindow.document.close()
  printWindow.print()
}

</script>

<style>
.container {
  max-width: 700px;
  margin: 50px auto;
  font-family: sans-serif;
  text-align: center;
}
input {
  width: 80%;
  padding: 10px;
  font-size: 1rem;
  margin-bottom: 10px;
}
button {
  padding: 10px 20px;
  font-size: 1rem;
  cursor: pointer;
}

.response-box {
  background-color: #1e1e1e; /* Dark background */
  color: #f1f1f1;            /* Light text for readability */
  padding: 1rem;
  border-radius: 8px;
  margin-top: 1rem;
  white-space: pre-wrap;
  font-family: 'Courier New', monospace;
  line-height: 1.6;
  text-align: left;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
}

button {
  padding: 8px 16px;
  font-size: 0.95rem;
  cursor: pointer;
  margin: 0.5rem 0.25rem;
  border: none;
  border-radius: 6px;
  background-color: #333;
  color: white;
  transition: 0.3s ease;
}
button:hover {
  background-color: #555;
}

</style>
