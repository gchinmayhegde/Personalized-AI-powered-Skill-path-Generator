<template>
  <div class="container">
    <h1>🧭 SkillPath Generator</h1>
    <input v-model="goal" placeholder="Enter your goal..." />
    <button @click="generateRoadmap">Generate Plan</button>

    <div v-if="loading" class="loading">⚙️ Generating...</div>

    <!-- Actions at the top when roadmap is generated -->
    <div v-if="roadmap.length" class="actions-top">
      <button @click="copyToClipboard" class="action-btn copy-btn">
        📋 Copy
      </button>
      <button @click="exportPDF" class="action-btn pdf-btn">
        📄 Export as PDF
      </button>
      <button @click="exportMarkdown" class="action-btn md-btn">
        📥 Export as Markdown
      </button>
    </div>

    <div v-if="roadmap.length" class="roadmap-container">
      <h2>📘 Your Learning Roadmap</h2>
      
      <div class="steps">
        <div v-for="(item, index) in roadmap" :key="index" class="step-card">
          <div class="step-header">
            <span class="step-number">{{ index + 1 }}</span>
            <h3 class="step-title">{{ cleanStepTitle(item.step) }}</h3>
          </div>
          
          <div v-if="item.resources && hasResources(item.resources)" class="resources">
            <h4>📚 Resources:</h4>
            <div class="resource-grid">
              <div v-if="item.resources.youtube && item.resources.youtube.length" class="resource-item">
                <div class="resource-icon youtube">📺</div>
                <div class="resource-content">
                  <span class="resource-type">Video Tutorial</span>
                  <a :href="item.resources.youtube[0]" target="_blank" class="resource-link">
                    Watch on YouTube
                  </a>
                </div>
              </div>
              
              <div v-if="item.resources.blogs && item.resources.blogs.length" class="resource-item">
                <div class="resource-icon blog">📖</div>
                <div class="resource-content">
                  <span class="resource-type">Blog Article</span>
                  <a :href="item.resources.blogs[0]" target="_blank" class="resource-link">
                    Read Article
                  </a>
                </div>
              </div>
              
              <div v-if="item.resources.courses && item.resources.courses.length" class="resource-item">
                <div class="resource-icon course">📘</div>
                <div class="resource-content">
                  <span class="resource-type">Online Course</span>
                  <a :href="item.resources.courses[0]" target="_blank" class="resource-link">
                    Take Course
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import jsPDF from 'jspdf'

const goal = ref("")
const roadmap = ref([])
const loading = ref(false)

const generateRoadmap = async () => {
  loading.value = true
  roadmap.value = []
  try {
    const res = await fetch("http://localhost:5000/generate-roadmap", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ goal: goal.value })
    })
    const data = await res.json()
    roadmap.value = data.roadmap || []
  } catch (err) {
    roadmap.value = []
    alert("Error: " + err.message)
  }
  loading.value = false
}

// Helper function to clean step titles
const cleanStepTitle = (step) => {
  return step
    .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold markdown
    .replace(/^\d+\.\s*/, '') // Remove leading numbers
    .trim()
}

const hasResources = (resources) => {
  return (resources.youtube && resources.youtube.length) || 
         (resources.blogs && resources.blogs.length) || 
         (resources.courses && resources.courses.length)
}

const copyToClipboard = () => {
  if (roadmap.value.length === 0) return
  
  const text = roadmap.value.map((item, index) => {
    let stepText = `${index + 1}. ${cleanStepTitle(item.step)}`
    
    if (item.resources && hasResources(item.resources)) {
      stepText += '\nResources:'
      if (item.resources.youtube && item.resources.youtube.length) {
        stepText += `\n📺 Video: ${item.resources.youtube[0]}`
      }
      if (item.resources.blogs && item.resources.blogs.length) {
        stepText += `\n📖 Blog: ${item.resources.blogs[0]}`
      }
      if (item.resources.courses && item.resources.courses.length) {
        stepText += `\n📘 Course: ${item.resources.courses[0]}`
      }
    }
    
    return stepText
  }).join('\n\n')
  
  navigator.clipboard.writeText(text)
  alert("Roadmap copied to clipboard!")
}

const exportPDF = () => {
  if (roadmap.value.length === 0) return
  
  const doc = new jsPDF()
  const pageWidth = doc.internal.pageSize.getWidth()
  const margin = 10
  let y = 20

  // Title
  doc.setFontSize(18)
  doc.setFont("helvetica", "bold")
  doc.text("SkillPath Roadmap", margin, y)
  y += 20

  // Helper function to clean text
  const cleanText = (text) => {
    return text
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/^\d+\.\s*/, '')
      .trim()
  }

  // Helper function to check if we need a new page
  const checkNewPage = (requiredHeight) => {
    if (y + requiredHeight > doc.internal.pageSize.getHeight() - 20) {
      doc.addPage()
      y = 20
    }
  }

  doc.setFontSize(12)
  doc.setFont("helvetica", "normal")

  roadmap.value.forEach((item, index) => {
    // Clean the step text
    const cleanedStep = cleanText(item.step)
    const stepText = `${index + 1}. ${cleanedStep}`
    
    // Split text to fit page width
    const wrappedText = doc.splitTextToSize(stepText, pageWidth - 2 * margin)
    
    // Check if we need a new page
    checkNewPage(wrappedText.length * 7 + 10)
    
    // Add step text with bold formatting
    doc.setFont("helvetica", "bold")
    doc.text(wrappedText, margin, y)
    y += wrappedText.length * 7 + 5
    
    // Add resources if they exist
    if (item.resources && hasResources(item.resources)) {
      doc.setFont("helvetica", "normal")
      
      // Resources header
      checkNewPage(10)
      doc.text("Resources:", margin + 5, y)
      y += 7
      
      // YouTube resources
      if (item.resources.youtube && item.resources.youtube.length > 0) {
        item.resources.youtube.forEach((link, linkIndex) => {
          checkNewPage(7)
          doc.setTextColor(0, 0, 255)
          doc.text(`📺 Video Tutorial ${linkIndex + 1}: ${link}`, margin + 10, y)
          doc.setTextColor(0, 0, 0)
          y += 7
        })
      }
      
      // Blog resources
      if (item.resources.blogs && item.resources.blogs.length > 0) {
        item.resources.blogs.forEach((link, linkIndex) => {
          checkNewPage(7)
          doc.setTextColor(0, 0, 255)
          doc.text(`📖 Blog Article ${linkIndex + 1}: ${link}`, margin + 10, y)
          doc.setTextColor(0, 0, 0)
          y += 7
        })
      }
      
      // Course resources
      if (item.resources.courses && item.resources.courses.length > 0) {
        item.resources.courses.forEach((link, linkIndex) => {
          checkNewPage(7)
          doc.setTextColor(0, 0, 255)
          doc.text(`📘 Online Course ${linkIndex + 1}: ${link}`, margin + 10, y)
          doc.setTextColor(0, 0, 0)
          y += 7
        })
      }
    }
    
    y += 10 // Extra spacing between steps
  })

  doc.save("skillpath-roadmap.pdf")
}

const exportMarkdown = () => {
  if (roadmap.value.length === 0) return
  
  let md = "# SkillPath Roadmap\n\n"
  
  roadmap.value.forEach((item, index) => {
    const cleanedStep = cleanStepTitle(item.step)
    md += `## ${index + 1}. ${cleanedStep}\n\n`
    
    if (item.resources && hasResources(item.resources)) {
      md += "### Resources:\n\n"
      
      if (item.resources.youtube && item.resources.youtube.length) {
        item.resources.youtube.forEach((link, linkIndex) => {
          md += `- 📺 [Video Tutorial ${linkIndex + 1}](${link})\n`
        })
      }
      
      if (item.resources.blogs && item.resources.blogs.length) {
        item.resources.blogs.forEach((link, linkIndex) => {
          md += `- 📖 [Blog Article ${linkIndex + 1}](${link})\n`
        })
      }
      
      if (item.resources.courses && item.resources.courses.length) {
        item.resources.courses.forEach((link, linkIndex) => {
          md += `- 📘 [Online Course ${linkIndex + 1}](${link})\n`
        })
      }
    }
    
    md += "\n"
  })
  
  const blob = new Blob([md], { type: "text/markdown" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = "skillpath-roadmap.md"
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style>
.container {
  max-width: 900px;
  margin: 50px auto;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  text-align: center;
  color: #fff;
  padding: 0 20px;
}

body {
  background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
  min-height: 100vh;
  margin: 0;
}

h1 {
  font-size: 2.5rem;
  margin-bottom: 30px;
  background: linear-gradient(45deg, #f39c12, #e74c3c);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

input {
  width: 70%;
  max-width: 500px;
  padding: 15px;
  font-size: 1.1rem;
  margin-bottom: 15px;
  background: #2a2a2a;
  border: 2px solid #444;
  color: #fff;
  border-radius: 10px;
  transition: border-color 0.3s ease;
}

input:focus {
  outline: none;
  border-color: #f39c12;
}

button {
  padding: 12px 24px;
  margin: 8px;
  font-size: 1rem;
  cursor: pointer;
  border: none;
  border-radius: 8px;
  background: linear-gradient(45deg, #f39c12, #e67e22);
  color: #fff;
  font-weight: bold;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(243, 156, 18, 0.3);
}

button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(243, 156, 18, 0.4);
}

.actions-top {
  margin: 20px 0;
  display: flex;
  justify-content: center;
  gap: 15px;
  flex-wrap: wrap;
}

.action-btn {
  font-size: 0.95rem;
  padding: 10px 20px;
}

.copy-btn {
  background: linear-gradient(45deg, #3498db, #2980b9);
  box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
}

.pdf-btn {
  background: linear-gradient(45deg, #e74c3c, #c0392b);
  box-shadow: 0 4px 15px rgba(231, 76, 60, 0.3);
}

.md-btn {
  background: linear-gradient(45deg, #2ecc71, #27ae60);
  box-shadow: 0 4px 15px rgba(46, 204, 113, 0.3);
}

.loading {
  margin: 30px 0;
  font-size: 1.2rem;
  color: #f39c12;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.roadmap-container {
  margin-top: 30px;
  background: rgba(30, 30, 30, 0.8);
  padding: 25px;
  border-radius: 15px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
}

.roadmap-container h2 {
  text-align: center;
  margin-bottom: 25px;
  color: #f39c12;
  font-size: 1.8rem;
}

.steps {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.step-card {
  background: linear-gradient(135deg, #2c2c2c 0%, #3a3a3a 100%);
  padding: 25px;
  border-radius: 12px;
  text-align: left;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
  border: 1px solid #444;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.step-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 35px rgba(0, 0, 0, 0.3);
}

.step-header {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 35px;
  height: 35px;
  background: linear-gradient(45deg, #f39c12, #e67e22);
  color: white;
  border-radius: 50%;
  font-weight: bold;
  font-size: 1.1rem;
  margin-right: 15px;
  flex-shrink: 0;
}

.step-title {
  margin: 0;
  color: #fff;
  font-size: 1.2rem;
  line-height: 1.3;
}

.resources {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #555;
}

.resources h4 {
  margin: 0 0 15px 0;
  color: #f39c12;
  font-size: 1rem;
}

.resource-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
}

.resource-item {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.05);
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #555;
  transition: all 0.3s ease;
}

.resource-item:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: #f39c12;
}

.resource-icon {
  font-size: 1.5rem;
  margin-right: 12px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  flex-shrink: 0;
}

.resource-icon.youtube {
  background: rgba(255, 0, 0, 0.1);
}

.resource-icon.blog {
  background: rgba(52, 152, 219, 0.1);
}

.resource-icon.course {
  background: rgba(155, 89, 182, 0.1);
}

.resource-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.resource-type {
  font-size: 0.85rem;
  color: #bbb;
  font-weight: 500;
}

.resource-link {
  color: #4fc3f7;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;
}

.resource-link:hover {
  color: #29b6f6;
  text-decoration: underline;
}

@media (max-width: 768px) {
  .container {
    padding: 0 15px;
  }
  
  .actions-top {
    flex-direction: column;
    align-items: center;
  }
  
  .action-btn {
    width: 200px;
  }
  
  .resource-grid {
    grid-template-columns: 1fr;
  }
  
  .step-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .step-number {
    margin-right: 0;
  }
}
</style>