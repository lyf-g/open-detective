<template>
  <div class="dossier-container">
    <div class="stamp">TOP SECRET</div>
    <div class="dossier-header">
      <div class="photo-frame">
        <div class="unknown-user">?</div>
      </div>
      <div class="header-info">
        <h1>SUBJECT: {{ profile.username }}</h1>
        <div class="codename">CODENAME: {{ profile.codename }}</div>
        <div class="threat">THREAT LEVEL: <span :class="getThreatClass(profile.threat_level)">{{ profile.threat_level }}</span></div>
      </div>
    </div>
    
    <div class="dossier-body">
      <div class="section">
        <h3>PSYCHOLOGICAL PROFILE</h3>
        <p class="typewriter">{{ profile.psych_profile }}</p>
      </div>
      
      <div class="section">
        <h3>SKILL MATRIX</h3>
        <div class="skills">
          <div v-for="skill in profile.skills" :key="skill.name" class="skill-bar">
            <span class="skill-name">{{ skill.name }}</span>
            <div class="bar-container">
              <div class="bar-fill" :style="{ width: skill.value + '%' }"></div>
            </div>
            <span class="skill-val">{{ skill.value }}%</span>
          </div>
        </div>
      </div>
      
      <div class="status-footer">
        STATUS: <span class="blink">{{ profile.status }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  profile: any;
}>();

const getThreatClass = (level: string) => {
  if (level.includes('5')) return 'text-red';
  if (level.includes('4')) return 'text-orange';
  return 'text-yellow';
};
</script>

<style scoped>
.dossier-container {
  background: #0a0a0a;
  border: 1px solid #333;
  padding: 30px;
  position: relative;
  font-family: 'Courier New', monospace;
  color: #ccc;
  width: 100%;
  max-width: 600px;
  margin: 0 auto;
  box-shadow: 0 0 30px rgba(0,0,0,0.8);
}
.stamp {
  position: absolute;
  top: 20px;
  right: 20px;
  border: 3px solid rgba(255, 0, 0, 0.4);
  color: rgba(255, 0, 0, 0.4);
  font-size: 2rem;
  font-weight: bold;
  padding: 5px 10px;
  transform: rotate(-15deg);
  pointer-events: none;
}
.dossier-header {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
  border-bottom: 1px dashed #444;
  padding-bottom: 20px;
}
.photo-frame {
  width: 100px;
  height: 120px;
  border: 1px solid #555;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #111;
}
.unknown-user {
  font-size: 3rem;
  color: #333;
}
.header-info h1 {
  margin: 0 0 10px 0;
  font-size: 1.5rem;
  color: #fff;
}
.codename {
  font-size: 1rem;
  color: #00bcd4;
  margin-bottom: 5px;
}
.threat {
  font-size: 0.9rem;
}
.text-red { color: #ff4d4f; font-weight: bold; }
.text-orange { color: #faad14; font-weight: bold; }
.text-yellow { color: #fadb14; font-weight: bold; }

.section { margin-bottom: 25px; }
.section h3 {
  border-left: 3px solid #00bcd4;
  padding-left: 10px;
  color: #888;
  font-size: 0.9rem;
  margin-bottom: 10px;
}
.typewriter {
  color: #00bcd4;
  line-height: 1.4;
}
.skill-bar {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 0.8rem;
}
.skill-name { width: 100px; }
.bar-container {
  flex-grow: 1;
  height: 6px;
  background: #222;
  margin: 0 10px;
}
.bar-fill {
  height: 100%;
  background: #00bcd4;
}
.status-footer {
  text-align: center;
  margin-top: 30px;
  font-size: 1.2rem;
  border-top: 1px double #444;
  padding-top: 10px;
}
.blink {
  color: #ff4d4f;
  animation: blink 1s infinite;
}
@keyframes blink { 50% { opacity: 0; } }
</style>