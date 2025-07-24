<template>
  <div class="container">
    <h1>🧭 SkillPath Generator</h1>
    <input v-model="goal" placeholder="Enter your goal..." />
    <button @click="generateRoadmap" :disabled="loading">
      {{ loading ? 'Generating...' : 'Generate Plan' }}
    </button>

    <!-- Real-time status updates -->
    <div v-if="loading" class="loading">
      <div class="loading-spinner"></div>
      <div class="status-message">{{ statusMessage }}</div>
    </div>

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
        <div v-for="(item, index) in roadmap" :key="index" class="step-card" :class="{ 'loading-step': item.isLoading }">
          <div class="step-header">
            <span class="step-number">{{ index + 1 }}</span>
            <h3 class="step-title">{{ cleanStepTitle(item.step) }}</h3>
            <div v-if="item.isLoading" class="step-loading-indicator">
              <div class="mini-spinner"></div>
            </div>
          </div>
          
          <div v-if="item.resources && hasResources(item.resources)" class="resources">
            <h4>📚 Resources:</h4>
            <div class="resource-grid">
              <!-- YouTube Resources -->
              <div v-if="item.resources.youtube && item.resources.youtube.length" class="resource-item">
                <div class="resource-icon youtube">📺</div>
                <div class="resource-content">
                  <span class="resource-type">Video Tutorial</span>
                  <a :href="item.resources.youtube[0]" target="_blank" class="resource-link">
                    Watch on YouTube
                  </a>
                  <div v-if="item.resources.youtube.length > 1" class="additional-resources">
                    +{{ item.resources.youtube.length - 1 }} more
                  </div>
                </div>
              </div>
              
              <!-- Blog Resources -->
              <div v-if="item.resources.blogs && item.resources.blogs.length" class="resource-item">
                <div class="resource-icon blog">📖</div>
                <div class="resource-content">
                  <span class="resource-type">Blog Article</span>
                  <a :href="item.resources.blogs[0]" target="_blank" class="resource-link">
                    Read Article
                  </a>
                  <div v-if="item.resources.blogs.length > 1" class="additional-resources">
                    +{{ item.resources.blogs.length - 1 }} more
                  </div>
                </div>
              </div>
              
              <!-- Course Resources -->
              <div v-if="item.resources.courses && item.resources.courses.length" class="resource-item">
                <div class="resource-icon course">📘</div>
                <div class="resource-content">
                  <span class="resource-type">Online Course</span>
                  <a :href="item.resources.courses[0]" target="_blank" class="resource-link">
                    Take Course
                  </a>
                  <div v-if="item.resources.courses.length > 1" class="additional-resources">
                    +{{ item.resources.courses.length - 1 }} more
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Loading placeholders for resources -->
          <div v-if="item.isLoading" class="resources-loading">
            <div class="loading-placeholder">
              <div class="placeholder-icon"></div>
              <div class="placeholder-text"></div>
            </div>
            <div class="loading-placeholder">
              <div class="placeholder-icon"></div>
              <div class="placeholder-text"></div>
            </div>
            <div class="loading-placeholder">
              <div class="placeholder-icon"></div>
              <div class="placeholder-text"></div>
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
const statusMessage = ref("")

const generateRoadmap = async () => {
  loading.value = true
  roadmap.value = []
  statusMessage.value = "Initializing..."

  try {
    const eventSource = new EventSource(`http://localhost:5000/generate-roadmap?goal=${encodeURIComponent(goal.value)}`)
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        console.log('Received:', data)

        switch (data.type) {
          case 'status':
            statusMessage.value = data.message
            break

          case 'roadmap_generated':
            // Initialize roadmap with steps
            roadmap.value = data.steps.map(step => ({
              step: step,
              resources: { youtube: [], blogs: [], courses: [] },
              isLoading: true
            }))
            statusMessage.value = "Loading resources..."
            break

          case 'step_start':
            statusMessage.value = `Loading resources for step ${data.index + 1}...`
            if (roadmap.value[data.index]) {
              roadmap.value[data.index].isLoading = true
            }
            break

          case 'resources_update':
            if (roadmap.value[data.index]) {
              roadmap.value[data.index].resources[data.resource_type] = data.data
              // Trigger reactivity
              roadmap.value = [...roadmap.value]
            }
            break

          case 'step_complete':
            if (roadmap.value[data.index]) {
              roadmap.value[data.index].isLoading = false
              // Trigger reactivity
              roadmap.value = [...roadmap.value]
            }
            break

          case 'complete':
            loading.value = false
            statusMessage.value = "Roadmap generated successfully!"
            eventSource.close()
            break

          case 'error':
            loading.value = false
            statusMessage.value = "Error: " + data.message
            alert("Error: " + data.message)
            eventSource.close()
            break
        }
      } catch (e) {
        console.error('Error parsing event data:', e)
      }
    }

    eventSource.onerror = (error) => {
      console.error('EventSource error:', error)
      loading.value = false
      statusMessage.value = "Connection error"
      eventSource.close()
      
      // Fallback to regular POST request
      fallbackGenerate()
    }

  } catch (err) {
    loading.value = false
    roadmap.value = []
    alert("Error: " + err.message)
  }
}

// Fallback function for when streaming fails
const fallbackGenerate = async () => {
  try {
    const res = await fetch("http://localhost:5000/generate-roadmap", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ goal: goal.value })
    })
    const data = await res.json()
    roadmap.value = data.roadmap || []
    loading.value = false
  } catch (err) {
    roadmap.value = []
    alert("Error: " + err.message)
    loading.value = false
  }
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
        item.resources.youtube.forEach((link, i) => {
          stepText += `\n📺 Video ${i + 1}: ${link}`
        })
      }
      if (item.resources.blogs && item.resources.blogs.length) {
        item.resources.blogs.forEach((link, i) => {
          stepText += `\n📖 Blog ${i + 1}: ${link}`
        })
      }
      if (item.resources.courses && item.resources.courses.length) {
        item.resources.courses.forEach((link, i) => {
          stepText += `\n📘 Course ${i + 1}: ${link}`
        })
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

button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(243, 156, 18, 0.4);
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.loading {
  margin: 30px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #333;
  border-top: 4px solid #f39c12;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.status-message {
  font-size: 1.1rem;
  color: #f39c12;
  font-weight: 500;
}

.mini-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #333;
  border-top: 2px solid #f39c12;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.step-loading-indicator {
  margin-left: auto;
  display: flex;
  align-items: center;
}

.loading-step {
  opacity: 0.7;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.7; }
  50% { opacity: 1; }
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
  flex-grow: 1;
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
  flex-grow: 1;
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

.additional-resources {
  font-size: 0.75rem;
  color: #999;
  font-style: italic;
}

.resources-loading {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #555;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
}

.loading-placeholder {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.03);
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #444;
  animation: shimmer 1.5s infinite linear;
}

@keyframes shimmer {
  0% {
    background-position: -468px 0;
  }
  100% {
    background-position: 468px 0;
  }
}

.loading-placeholder {
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.03) 0px,
    rgba(255, 255, 255, 0.08) 40px,
    rgba(255, 255, 255, 0.03) 80px
  );
  background-size: 600px;
}

.placeholder-icon {
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  margin-right: 12px;
  flex-shrink: 0;
}

.placeholder-text {
  flex-grow: 1;
  height: 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
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
  
  .resources-loading {
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
  
  .step-loading-indicator {
    margin-left: 0;
    margin-top: 10px;
  }
}
</style>