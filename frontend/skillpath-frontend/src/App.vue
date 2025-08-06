<template>
  <div id="app">
    <!-- Animated Background -->
    <div class="background-animation">
      <div class="floating-shape shape-1"></div>
      <div class="floating-shape shape-2"></div>
      <div class="floating-shape shape-3"></div>
      <div class="floating-shape shape-4"></div>
    </div>

    <div class="container">
      <!-- Header Section -->
      <div class="header-section">
        <div class="logo-container">
          <div class="logo-icon">🧭</div>
          <h1 class="app-title">SkillPath Generator</h1>
        </div>
        <p class="subtitle">Create personalized learning roadmaps for any skill</p>
      </div>

      <!-- Input Section -->
      <div class="input-section">
        <div class="input-container">
          <div class="input-icon">🎯</div>
          <input 
            v-model="goal" 
            class="goal-input"
            placeholder="Enter your goal (e.g., Become a UI/UX Designer, Learn Figma, Become a Pilot)..."
            @keypress.enter="generateRoadmap"
          />
        </div>
        <button 
          @click="generateRoadmap" 
          :disabled="loading || !goal.trim()"
          class="generate-btn"
          :class="{ 'loading': loading, 'disabled': !goal.trim() }"
        >
          <span v-if="!loading" class="btn-content">
            <span class="btn-icon">✨</span>
            Generate Plan
          </span>
          <span v-else class="btn-content">
            <div class="btn-spinner"></div>
            Generating...
          </span>
        </button>
      </div>

      <!-- Loading Status -->
      <div v-if="loading" class="loading-status">
        <div class="pulse-animation">
          <div class="pulse-ring"></div>
          <div class="pulse-ring"></div>
          <div class="pulse-ring"></div>
        </div>
        <div class="status-message">{{ statusMessage }}</div>
      </div>

      <!-- Action Buttons -->
      <div v-if="roadmap.length" class="actions-section">
        <div class="actions-container">
          <button @click="copyToClipboard" class="action-btn copy-btn">
            <span class="action-icon">📋</span>
            Copy
          </button>
          <button @click="exportPDF" class="action-btn pdf-btn">
            <span class="action-icon">📄</span>
            PDF
          </button>
          <button @click="exportMarkdown" class="action-btn md-btn">
            <span class="action-icon">📥</span>
            Markdown
          </button>
        </div>
      </div>

      <!-- Roadmap Section -->
      <div v-if="roadmap.length" class="roadmap-section">
        <div class="roadmap-header">
          <h2 class="roadmap-title">
            <span class="title-icon">📘</span>
            Your Learning Roadmap
          </h2>
          <div class="roadmap-progress">
            <div class="progress-text">{{ completedSteps }}/{{ roadmap.length }} steps loaded</div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: progressPercentage + '%' }"></div>
            </div>
          </div>
        </div>
        
        <div class="steps-container">
          <div 
            v-for="(item, index) in roadmap" 
            :key="index" 
            class="step-card" 
            :class="{ 
              'loading-step': item.isLoading, 
              'completed-step': !item.isLoading,
              'fade-in': !item.isLoading 
            }"
          >
            <!-- Step Header -->
            <div class="step-header">
              <div class="step-number-container">
                <div class="step-number" :class="{ 'completed': !item.isLoading }">
                  <span v-if="!item.isLoading">{{ index + 1 }}</span>
                  <div v-else class="step-spinner"></div>
                </div>
                <div class="step-connector" v-if="index < roadmap.length - 1"></div>
              </div>
              
              <div class="step-content">
                <h3 class="step-title">{{ cleanStepTitle(item.step) }}</h3>
                
                <!-- Contextual Information -->
                <div v-if="item.contextualInfo" class="contextual-info">
                  <div class="info-badge">
                    <span class="info-icon">💡</span>
                    <span class="info-label">Important Note</span>
                  </div>
                  <div class="info-content">
                    <p class="info-message">{{ item.contextualInfo.message }}</p>
                    <p class="info-suggestion" v-if="item.contextualInfo.suggestion">
                      <strong>💡 Suggestion:</strong> {{ item.contextualInfo.suggestion }}
                    </p>
                  </div>
                </div>

                <!-- No Online Courses Message -->
                <div v-if="item.noOnlineCoursesMessage" class="no-courses-info">
                  <div class="info-badge warning">
                    <span class="info-icon">🎯</span>
                    <span class="info-label">Hands-on Required</span>
                  </div>
                  <div class="info-content">
                    <p class="info-message">{{ item.noOnlineCoursesMessage }}</p>
                  </div>
                </div>
                
                <!-- Resources Section -->
                <div v-if="item.resources && hasResources(item.resources)" class="resources-section">
                  <h4 class="resources-title">
                    <span class="resources-icon">📚</span>
                    Learning Resources
                  </h4>
                  
                  <div class="resource-grid">
                    <!-- YouTube Resources -->
                    <div v-if="item.resources.youtube && item.resources.youtube.length" class="resource-card youtube">
                      <div class="resource-header">
                        <div class="resource-icon-bg youtube-bg">
                          <span class="resource-icon">📺</span>
                        </div>
                        <div class="resource-info">
                          <span class="resource-type">{{ getResourceTypeLabel(item.youtubeMetadata, 0) }}</span>
                          <a :href="item.resources.youtube[0]" target="_blank" class="resource-link">
                            {{ getResourceTitle(item.youtubeMetadata, 0, 'Watch on YouTube') }}
                          </a>
                          <div v-if="item.youtubeMetadata && item.youtubeMetadata[0]" class="resource-meta">
                            📺 {{ item.youtubeMetadata[0].channel }}
                          </div>
                        </div>
                      </div>
                      <div v-if="item.resources.youtube.length > 1" class="additional-count">
                        +{{ item.resources.youtube.length - 1 }} more videos
                      </div>
                    </div>
                    
                    <!-- Blog Resources -->
                    <div v-if="item.resources.blogs && item.resources.blogs.length" class="resource-card blog">
                      <div class="resource-header">
                        <div class="resource-icon-bg blog-bg">
                          <span class="resource-icon">📖</span>
                        </div>
                        <div class="resource-info">
                          <span class="resource-type">Blog Article</span>
                          <a :href="item.resources.blogs[0]" target="_blank" class="resource-link">
                            {{ getResourceTitle(item.blogMetadata, 0, 'Read Article') }}
                          </a>
                          <div v-if="item.blogMetadata && item.blogMetadata[0] && item.blogMetadata[0].snippet" class="resource-snippet">
                            {{ truncateText(item.blogMetadata[0].snippet, 80) }}
                          </div>
                        </div>
                      </div>
                      <div v-if="item.resources.blogs.length > 1" class="additional-count">
                        +{{ item.resources.blogs.length - 1 }} more articles
                      </div>
                    </div>
                    
                    <!-- Course Resources -->
                    <div v-if="item.resources.courses && item.resources.courses.length" class="resource-card course">
                      <div class="resource-header">
                        <div class="resource-icon-bg course-bg">
                          <span class="resource-icon">📘</span>
                        </div>
                        <div class="resource-info">
                          <span class="resource-type">Online Course</span>
                          <a :href="item.resources.courses[0]" target="_blank" class="resource-link">
                            {{ getCoursePlatform(item.resources.courses[0]) }} Course
                          </a>
                          <div class="resource-meta">
                            {{ getCoursePlatformName(item.resources.courses[0]) }}
                          </div>
                        </div>
                      </div>
                      <div v-if="item.resources.courses.length > 1" class="additional-count">
                        +{{ item.resources.courses.length - 1 }} more courses
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Loading Placeholders -->
                <div v-if="item.isLoading" class="resources-loading">
                  <div class="loading-placeholder" v-for="n in 3" :key="n">
                    <div class="placeholder-icon shimmer"></div>
                    <div class="placeholder-content">
                      <div class="placeholder-text shimmer"></div>
                      <div class="placeholder-text-small shimmer"></div>
                    </div>
                  </div>
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
import { ref, computed } from 'vue'
import jsPDF from 'jspdf'

const goal = ref("")
const roadmap = ref([])
const loading = ref(false)
const statusMessage = ref("")

const completedSteps = computed(() => {
  return roadmap.value.filter(step => !step.isLoading).length
})

const progressPercentage = computed(() => {
  if (roadmap.value.length === 0) return 0
  return (completedSteps.value / roadmap.value.length) * 100
})

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
              youtubeMetadata: [],
              blogMetadata: [],
              isLoading: true,
              contextualInfo: null,
              noOnlineCoursesMessage: null
            }))
            statusMessage.value = "Loading resources..."
            break

          case 'step_start':
            statusMessage.value = `Loading resources for step ${data.index + 1}...`
            if (roadmap.value[data.index]) {
              roadmap.value[data.index].isLoading = true
            }
            break

          case 'contextual_info':
            if (roadmap.value[data.index]) {
              roadmap.value[data.index].contextualInfo = data.info
              roadmap.value = [...roadmap.value]
            }
            break

          case 'no_online_courses':
            if (roadmap.value[data.index]) {
              roadmap.value[data.index].noOnlineCoursesMessage = data.message
              roadmap.value = [...roadmap.value]
            }
            break

          case 'resources_update':
            if (roadmap.value[data.index]) {
              roadmap.value[data.index].resources[data.resource_type] = data.data
              
              // Store metadata for better display
              if (data.resource_type === 'youtube' && data.metadata) {
                roadmap.value[data.index].youtubeMetadata = data.metadata
              } else if (data.resource_type === 'blogs' && data.metadata) {
                roadmap.value[data.index].blogMetadata = data.metadata
              }
              
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

// Helper function to get resource type label for YouTube
const getResourceTypeLabel = (metadata, index) => {
  if (metadata && metadata[index]) {
    const type = metadata[index].type
    switch (type) {
      case 'course': return 'Video Course'
      case 'tutorial': return 'Video Tutorial'
      default: return 'Video Tutorial'
    }
  }
  return 'Video Tutorial'
}

// Helper function to get resource title
const getResourceTitle = (metadata, index, fallback) => {
  if (metadata && metadata[index] && metadata[index].title) {
    return truncateText(metadata[index].title, 60)
  }
  return fallback
}

// Helper function to get course platform
const getCoursePlatform = (url) => {
  if (url.includes('coursera.org')) return 'Coursera'
  if (url.includes('udemy.com')) return 'Udemy'
  if (url.includes('edx.org')) return 'edX'
  if (url.includes('khan')) return 'Khan Academy'
  return 'Online'
}

// Helper function to get course platform name
const getCoursePlatformName = (url) => {
  if (url.includes('coursera.org')) return '🎓 Coursera'
  if (url.includes('udemy.com')) return '💼 Udemy'
  if (url.includes('edx.org')) return '🏛️ edX'
  return '📚 Online Course'
}

// Helper function to truncate text
const truncateText = (text, maxLength) => {
  if (!text) return ''
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
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
    
    if (item.contextualInfo) {
      stepText += `\n💡 ${item.contextualInfo.message}`
      if (item.contextualInfo.suggestion) {
        stepText += `\n   ${item.contextualInfo.suggestion}`
      }
    }
    
    if (item.resources && hasResources(item.resources)) {
      stepText += '\nResources:'
      if (item.resources.youtube && item.resources.youtube.length) {
        item.resources.youtube.forEach((link, i) => {
          const title = getResourceTitle(item.youtubeMetadata, i, `Video Tutorial ${i + 1}`)
          stepText += `\n📺 ${title}: ${link}`
        })
      }
      if (item.resources.blogs && item.resources.blogs.length) {
        item.resources.blogs.forEach((link, i) => {
          const title = getResourceTitle(item.blogMetadata, i, `Blog Article ${i + 1}`)
          stepText += `\n📖 ${title}: ${link}`
        })
      }
      if (item.resources.courses && item.resources.courses.length) {
        item.resources.courses.forEach((link, i) => {
          const platform = getCoursePlatform(link)
          stepText += `\n📘 ${platform} Course: ${link}`
        })
      }
    }
    
    if (item.noOnlineCoursesMessage) {
      stepText += `\n${item.noOnlineCoursesMessage}`
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
  const pageHeight = doc.internal.pageSize.getHeight()
  const margin = 15
  let y = 25

  // Title
  doc.setFontSize(20)
  doc.setFont("helvetica", "bold")
  doc.text("🧭 SkillPath Roadmap", margin, y)
  y += 15

  // Goal
  doc.setFontSize(12)
  doc.setFont("helvetica", "normal")
  doc.setTextColor(100, 100, 100)
  doc.text(`Goal: ${goal.value}`, margin, y)
  doc.setTextColor(0, 0, 0)
  y += 20

  // Helper function to check if we need a new page
  const checkNewPage = (requiredHeight) => {
    if (y + requiredHeight > pageHeight - 25) {
      doc.addPage()
      y = 25
    }
  }

  // Helper function to add a clickable link
  const addClickableLink = (text, url, x, yPos, maxWidth) => {
    const textWidth = doc.getTextWidth(text)
    const actualWidth = Math.min(textWidth, maxWidth)
    
    // Add the text
    doc.setTextColor(0, 0, 255) // Blue color for links
    doc.text(text, x, yPos, { maxWidth: maxWidth })
    
    // Add the link annotation
    doc.link(x, yPos - 4, actualWidth, 6, { url: url })
    
    doc.setTextColor(0, 0, 0) // Reset to black
    return Math.ceil(textWidth / maxWidth) * 6 // Return height used
  }

  roadmap.value.forEach((item, index) => {
    // Clean the step text
    const cleanedStep = cleanStepTitle(item.step)
    const stepText = `${index + 1}. ${cleanedStep}`
    
    // Check if we need a new page for the step header
    checkNewPage(15)
    
    // Add step text with bold formatting
    doc.setFontSize(14)
    doc.setFont("helvetica", "bold")
    const wrappedStepText = doc.splitTextToSize(stepText, pageWidth - 2 * margin)
    doc.text(wrappedStepText, margin, y)
    y += wrappedStepText.length * 6 + 8
    
    // Add contextual information if exists
    if (item.contextualInfo) {
      checkNewPage(20)
      doc.setFontSize(11)
      doc.setFont("helvetica", "italic")
      doc.setTextColor(200, 100, 0) // Orange color
      
      const contextText = `💡 ${item.contextualInfo.message}`
      const wrappedContextText = doc.splitTextToSize(contextText, pageWidth - 2 * margin - 10)
      doc.text(wrappedContextText, margin + 5, y)
      y += wrappedContextText.length * 5 + 5
      
      if (item.contextualInfo.suggestion) {
        const suggestionText = `Suggestion: ${item.contextualInfo.suggestion}`
        const wrappedSuggestionText = doc.splitTextToSize(suggestionText, pageWidth - 2 * margin - 10)
        doc.text(wrappedSuggestionText, margin + 5, y)
        y += wrappedSuggestionText.length * 5 + 8
      }
      
      doc.setTextColor(0, 0, 0) // Reset color
    }
    
    // Add resources if they exist
    if (item.resources && hasResources(item.resources)) {
      checkNewPage(15)
      doc.setFontSize(12)
      doc.setFont("helvetica", "bold")
      doc.text("📚 Resources:", margin + 5, y)
      y += 10
      
      doc.setFont("helvetica", "normal")
      doc.setFontSize(10)
      
      // YouTube resources
      if (item.resources.youtube && item.resources.youtube.length > 0) {
        item.resources.youtube.forEach((link, linkIndex) => {
          checkNewPage(12)
          
          const title = getResourceTitle(item.youtubeMetadata, linkIndex, `Video Tutorial ${linkIndex + 1}`)
          const resourceText = `📺 ${title}`
          
          // Add title
          doc.text(resourceText, margin + 10, y)
          y += 6
          
          // Add clickable link
          const linkHeight = addClickableLink(link, link, margin + 15, y, pageWidth - margin - 20)
          y += linkHeight + 4
        })
      }
      
      // Blog resources
      if (item.resources.blogs && item.resources.blogs.length > 0) {
        item.resources.blogs.forEach((link, linkIndex) => {
          checkNewPage(12)
          
          const title = getResourceTitle(item.blogMetadata, linkIndex, `Blog Article ${linkIndex + 1}`)
          const resourceText = `📖 ${title}`
          
          // Add title
          doc.text(resourceText, margin + 10, y)
          y += 6
          
          // Add clickable link
          const linkHeight = addClickableLink(link, link, margin + 15, y, pageWidth - margin - 20)
          y += linkHeight + 4
        })
      }
      
      // Course resources
      if (item.resources.courses && item.resources.courses.length > 0) {
        item.resources.courses.forEach((link, linkIndex) => {
          checkNewPage(12)
          
          const platform = getCoursePlatform(link)
          const resourceText = `📘 ${platform} Course`
          
          // Add title
          doc.text(resourceText, margin + 10, y)
          y += 6
          
          // Add clickable link
          const linkHeight = addClickableLink(link, link, margin + 15, y, pageWidth - margin - 20)
          y += linkHeight + 4
        })
      }
    }
    
    // Add no online courses message if exists
    if (item.noOnlineCoursesMessage) {
      checkNewPage(10)
      doc.setFontSize(10)
      doc.setFont("helvetica", "italic")
      doc.setTextColor(150, 150, 150)
      
      const wrappedMessage = doc.splitTextToSize(item.noOnlineCoursesMessage, pageWidth - 2 * margin - 10)
      doc.text(wrappedMessage, margin + 5, y)
      y += wrappedMessage.length * 5 + 5
      
      doc.setTextColor(0, 0, 0)
    }
    
    y += 15 // Extra spacing between steps
  })

  // Add footer with generation date
  const totalPages = doc.internal.getNumberOfPages()
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i)
    doc.setFontSize(8)
    doc.setFont("helvetica", "normal")
    doc.setTextColor(150, 150, 150)
    doc.text(
      `Generated on ${new Date().toLocaleDateString()} | Page ${i} of ${totalPages}`,
      margin,
      pageHeight - 10
    )
  }

  doc.save("skillpath-roadmap.pdf")
}

const exportMarkdown = () => {
  if (roadmap.value.length === 0) return
  
  let md = "# 🧭 SkillPath Roadmap\n\n"
  md += `**Goal:** ${goal.value}\n\n`
  md += `**Generated on:** ${new Date().toLocaleDateString()}\n\n`
  md += "---\n\n"
  
  roadmap.value.forEach((item, index) => {
    const cleanedStep = cleanStepTitle(item.step)
    md += `## ${index + 1}. ${cleanedStep}\n\n`
    
    // Add contextual information
    if (item.contextualInfo) {
      md += `> 💡 **${item.contextualInfo.message}**\n>\n`
      if (item.contextualInfo.suggestion) {
        md += `> **Suggestion:** ${item.contextualInfo.suggestion}\n\n`
      } else {
        md += `\n`
      }
    }
    
    if (item.resources && hasResources(item.resources)) {
      md += "### 📚 Resources\n\n"
      
      if (item.resources.youtube && item.resources.youtube.length) {
        item.resources.youtube.forEach((link, linkIndex) => {
          const title = getResourceTitle(item.youtubeMetadata, linkIndex, `Video Tutorial ${linkIndex + 1}`)
          const type = getResourceTypeLabel(item.youtubeMetadata, linkIndex)
          md += `- 📺 **${type}:** [${title}](${link})\n`
          if (item.youtubeMetadata && item.youtubeMetadata[linkIndex] && item.youtubeMetadata[linkIndex].channel) {
            md += `  - *Channel: ${item.youtubeMetadata[linkIndex].channel}*\n`
          }
        })
        md += "\n"
      }
      
      if (item.resources.blogs && item.resources.blogs.length) {
        item.resources.blogs.forEach((link, linkIndex) => {
          const title = getResourceTitle(item.blogMetadata, linkIndex, `Blog Article ${linkIndex + 1}`)
          md += `- 📖 **Blog Article:** [${title}](${link})\n`
          if (item.blogMetadata && item.blogMetadata[linkIndex] && item.blogMetadata[linkIndex].snippet) {
            md += `  - *${truncateText(item.blogMetadata[linkIndex].snippet, 150)}*\n`
          }
        })
        md += "\n"
      }
      
      if (item.resources.courses && item.resources.courses.length) {
        item.resources.courses.forEach((link, linkIndex) => {
          const platform = getCoursePlatform(link)
          const platformName = getCoursePlatformName(link)
          md += `- 📘 **${platform} Course:** [${platformName} Course](${link})\n`
        })
        md += "\n"
      }
    }
    
    // Add no online courses message
    if (item.noOnlineCoursesMessage) {
      md += `> ${item.noOnlineCoursesMessage}\n\n`
    }
    
    md += "---\n\n"
  })
  
  md += "*Generated by SkillPath Generator*\n"
  
  const blob = new Blob([md], { type: "text/markdown" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = "skillpath-roadmap.md"
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
/* ===== GLOBAL STYLES ===== */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  position: relative;
  overflow-x: hidden;
}

/* ===== ANIMATED BACKGROUND ===== */
.background-animation {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}

.floating-shape {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  animation: float 20s infinite linear;
}

.shape-1 {
  width: 80px;
  height: 80px;
  top: 10%;
  left: 10%;
  animation-delay: 0s;
}

.shape-2 {
  width: 120px;
  height: 120px;
  top: 60%;
  right: 15%;
  animation-delay: -5s;
}

.shape-3 {
  width: 60px;
  height: 60px;
  bottom: 20%;
  left: 20%;
  animation-delay: -10s;
}

.shape-4 {
  width: 100px;
  height: 100px;
  top: 30%;
  right: 30%;
  animation-delay: -15s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
    opacity: 0.5;
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
    opacity: 0.8;
  }
}

/* ===== CONTAINER ===== */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
  position: relative;
  z-index: 1;
}

/* ===== HEADER SECTION ===== */
.header-section {
  text-align: center;
  margin-bottom: 50px;
}

.logo-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin-bottom: 20px;
}

.logo-icon {
  font-size: 4rem;
  background: linear-gradient(45deg, #FFD700, #FFA500);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 4px 8px rgba(255, 215, 0, 0.3));
  animation: pulse 2s infinite ease-in-out;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

.app-title {
  font-size: 3.5rem;
  font-weight: 700;
  background: linear-gradient(45deg, #ffffff, #e0e7ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 4px 20px rgba(255, 255, 255, 0.3);
  letter-spacing: -2px;
}

.subtitle {
  font-size: 1.2rem;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 400;
  margin-top: 10px;
}

/* ===== INPUT SECTION ===== */
.input-section {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  padding: 40px;
  margin-bottom: 40px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.input-container {
  position: relative;
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 8px;
  margin-bottom: 25px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.input-container:focus-within {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

.input-icon {
  font-size: 1.5rem;
  margin: 0 15px;
  color: #667eea;
}

.goal-input {
  flex: 1;
  border: none;
  outline: none;
  padding: 16px 20px 16px 0;
  font-size: 1.1rem;
  background: transparent;
  color: #2d3748;
  font-weight: 500;
}

.goal-input::placeholder {
  color: #a0aec0;
  font-weight: 400;
}

.generate-btn {
  width: 100%;
  padding: 18px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 16px;
  color: white;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.4);
  position: relative;
  overflow: hidden;
}

.generate-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.generate-btn:hover::before {
  left: 100%;
}

.generate-btn:hover:not(.disabled):not(.loading) {
  transform: translateY(-3px);
  box-shadow: 0 12px 40px rgba(102, 126, 234, 0.6);
}

.generate-btn.disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.generate-btn.loading {
  cursor: not-allowed;
}

.btn-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.btn-icon {
  font-size: 1.2rem;
}

.btn-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* ===== LOADING STATUS ===== */
.loading-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 25px;
  margin: 60px 0;
}

.pulse-animation {
  position: relative;
  width: 120px;
  height: 120px;
}

.pulse-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  animation: pulse-ring 2s linear infinite;
}

.pulse-ring:nth-child(2) {
  animation-delay: 0.7s;
}

.pulse-ring:nth-child(3) {
  animation-delay: 1.4s;
}

@keyframes pulse-ring {
  0% {
    transform: scale(0.8);
    opacity: 1;
  }
  100% {
    transform: scale(2);
    opacity: 0;
  }
}

.status-message {
  color: white;
  font-size: 1.2rem;
  font-weight: 500;
  text-align: center;
  background: rgba(255, 255, 255, 0.1);
  padding: 15px 30px;
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

/* ===== ACTIONS SECTION ===== */
.actions-section {
  margin-bottom: 40px;
}

.actions-container {
  display: flex;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: none;
  border-radius: 12px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.9);
  color: #2d3748;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
}

.copy-btn:hover {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.pdf-btn:hover {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  color: white;
}

.md-btn:hover {
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
  color: #2d3748;
}

/* ===== ROADMAP SECTION ===== */
.roadmap-section {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 24px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(20px);
}

.roadmap-header {
  margin-bottom: 40px;
  text-align: center;
}

.roadmap-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
  font-size: 2.2rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 20px;
}

.title-icon {
  font-size: 2.5rem;
}

.roadmap-progress {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.progress-text {
  font-size: 0.95rem;
  color: #718096;
  font-weight: 500;
}

.progress-bar {
  width: 300px;
  height: 6px;
  background: #e2e8f0;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 3px;
  transition: width 0.5s ease;
}

/* ===== STEPS CONTAINER ===== */
.steps-container {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.step-card {
  background: white;
  border-radius: 20px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  border: 1px solid #e2e8f0;
  transition: all 0.5s ease;
  position: relative;
  overflow: hidden;
}

.step-card.loading-step {
  border-left: 4px solid #fbbf24;
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
}

.step-card.completed-step {
  border-left: 4px solid #10b981;
}

.fade-in {
  animation: fadeIn 0.8s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.step-header {
  display: flex;
  gap: 25px;
  align-items: flex-start;
}

.step-number-container {
  position: relative;
  flex-shrink: 0;
}

.step-number {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.2rem;
  background: #e2e8f0;
  color: #718096;
  transition: all 0.3s ease;
}

.step-number.completed {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  box-shadow: 0 4px 20px rgba(16, 185, 129, 0.4);
}

.step-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #e2e8f0;
  border-top: 2px solid #fbbf24;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.step-connector {
  position: absolute;
  top: 60px;
  left: 50%;
  transform: translateX(-50%);
  width: 2px;
  height: 40px;
  background: #e2e8f0;
}

.step-content {
  flex: 1;
}

.step-title {
  font-size: 1.4rem;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 20px;
  line-height: 1.4;
}

/* ===== CONTEXTUAL INFO ===== */
.contextual-info,
.no-courses-info {
  background: linear-gradient(135deg, #fff7ed 0%, #fed7aa 100%);
  border: 1px solid #fdba74;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 25px;
}

.no-courses-info {
  background: linear-gradient(135deg, #fef2f2 0%, #fecaca 100%);
  border: 1px solid #f87171;
}

.info-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.info-badge.warning .info-icon {
  color: #dc2626;
}

.info-icon {
  font-size: 1.1rem;
}

.info-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #92400e;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-badge.warning .info-label {
  color: #dc2626;
}

.info-message {
  color: #92400e;
  font-weight: 500;
  line-height: 1.5;
  margin-bottom: 8px;
}

.no-courses-info .info-message {
  color: #dc2626;
}

.info-suggestion {
  color: #92400e;
  font-size: 0.95rem;
  line-height: 1.5;
}

/* ===== RESOURCES SECTION ===== */
.resources-section {
  margin-top: 25px;
}

.resources-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1.2rem;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 20px;
}

.resources-icon {
  font-size: 1.3rem;
}

.resource-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.resource-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.resource-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: #e2e8f0;
  transition: all 0.3s ease;
}

.resource-card.youtube::before {
  background: linear-gradient(135deg, #ff0000, #ff4500);
}

.resource-card.blog::before {
  background: linear-gradient(135deg, #00d084, #00b574);
}

.resource-card.course::before {
  background: linear-gradient(135deg, #4285f4, #34a853);
}

.resource-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.resource-card:hover::before {
  width: 6px;
}

.resource-header {
  display: flex;
  gap: 15px;
  align-items: flex-start;
}

.resource-icon-bg {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.youtube-bg {
  background: linear-gradient(135deg, #ff0000, #ff4500);
}

.blog-bg {
  background: linear-gradient(135deg, #00d084, #00b574);
}

.course-bg {
  background: linear-gradient(135deg, #4285f4, #34a853);
}

.resource-icon {
  font-size: 1.2rem;
  filter: grayscale(100%) brightness(0) invert(1);
}

.resource-info {
  flex: 1;
}

.resource-type {
  font-size: 0.8rem;
  font-weight: 600;
  color: #718096;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 5px;
  display: block;
}

.resource-link {
  color: #2d3748;
  text-decoration: none;
  font-weight: 600;
  font-size: 1rem;
  line-height: 1.4;
  display: block;
  margin-bottom: 8px;
  transition: color 0.3s ease;
}

.resource-link:hover {
  color: #667eea;
}

.resource-meta,
.resource-snippet {
  font-size: 0.9rem;
  color: #718096;
  line-height: 1.4;
}

.resource-snippet {
  margin-top: 8px;
}

.additional-count {
  margin-top: 12px;
  font-size: 0.85rem;
  color: #718096;
  font-style: italic;
}

/* ===== LOADING PLACEHOLDERS ===== */
.resources-loading {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-top: 25px;
}

.loading-placeholder {
  display: flex;
  gap: 15px;
  align-items: center;
  padding: 15px;
  background: #f7fafc;
  border-radius: 8px;
}

.placeholder-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: #e2e8f0;
}

.placeholder-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.placeholder-text {
  height: 12px;
  background: #e2e8f0;
  border-radius: 6px;
  width: 70%;
}

.placeholder-text-small {
  height: 10px;
  background: #e2e8f0;
  border-radius: 5px;
  width: 50%;
}

.shimmer {
  background: linear-gradient(90deg, #e2e8f0 25%, #f7fafc 50%, #e2e8f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

/* ===== RESPONSIVE DESIGN ===== */
@media (max-width: 768px) {
  .container {
    padding: 20px 15px;
  }
  
  .app-title {
    font-size: 2.5rem;
  }
  
  .logo-container {
    flex-direction: column;
    gap: 10px;
  }
  
  .input-section {
    padding: 25px;
  }
  
  .goal-input {
    font-size: 1rem;
    padding: 14px 15px 14px 0;
  }
  
  .generate-btn {
    padding: 16px 24px;
    font-size: 1rem;
  }
  
  .roadmap-section {
    padding: 25px;
  }
  
  .step-card {
    padding: 20px;
  }
  
  .step-header {
    gap: 15px;
  }
  
  .resource-grid {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  
  .actions-container {
    flex-direction: column;
    align-items: center;
  }
  
  .action-btn {
    width: 200px;
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .app-title {
    font-size: 2rem;
  }
  
  .logo-icon {
    font-size: 3rem;
  }
  
  .subtitle {
    font-size: 1rem;
  }
  
  .input-section {
    padding: 20px;
  }
  
  .roadmap-title {
    font-size: 1.8rem;
    flex-direction: column;
    gap: 10px;
  }
  
  .progress-bar {
    width: 200px;
  }
}
</style>