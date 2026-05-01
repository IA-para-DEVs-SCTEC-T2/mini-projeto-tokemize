/**
 * techStack.js — Componente de renderização da seção Tech Stack
 *
 * Popula o elemento #tech-stack-list com os itens de config.techStack.
 * Requirements: 5.4
 */

/**
 * @typedef {Object} TechItem
 * @property {string} name - Nome da tecnologia
 * @property {string} url  - URL da documentação
 */

/**
 * Renderiza a lista de tecnologias com links externos.
 *
 * @param {import('../configLoader.js').AppConfig} config
 */
export function renderTechStack(config) {
  const techList = document.getElementById('tech-stack-list');
  if (!techList || !Array.isArray(config.techStack)) {
    return;
  }

  techList.innerHTML = '';

  for (const tech of config.techStack) {
    const li = document.createElement('li');
    li.className = 'tech-item';

    const a = document.createElement('a');
    a.href = tech.url;
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    a.textContent = tech.name;

    li.appendChild(a);
    techList.appendChild(li);
  }
}
