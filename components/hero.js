/**
 * hero.js — Componente de renderização da seção Hero
 *
 * Popula os elementos da seção #hero e #pipeline com dados do config.json.
 * Requirements: 5.1, 5.2, 5.3
 */

/**
 * Renderiza a seção hero com os dados de configuração.
 *
 * @param {import('../configLoader.js').AppConfig} config
 */
export function renderHero(config) {
  // Atualiza o título principal
  const heroTitle = document.getElementById('hero-title');
  if (heroTitle) {
    heroTitle.textContent = config.projectName;
  }

  // Atualiza o tagline
  const heroTagline = document.querySelector('.hero-tagline');
  if (heroTagline) {
    heroTagline.textContent = config.tagline;
  }

  // Popula a lista de problemas
  const problemsList = document.getElementById('problems-list');
  if (problemsList && Array.isArray(config.problems)) {
    problemsList.innerHTML = '';
    for (const problem of config.problems) {
      const li = document.createElement('li');
      li.textContent = problem;
      problemsList.appendChild(li);
    }
  }

  // Popula o pipeline como sequência visual com setas
  const pipelineContainer = document.getElementById('pipeline-container');
  if (pipelineContainer && Array.isArray(config.pipeline)) {
    pipelineContainer.innerHTML = '';
    const steps = config.pipeline;
    const middleIndex = Math.floor(steps.length / 2);

    steps.forEach((step, index) => {
      // Cria o elemento do passo
      const div = document.createElement('div');
      div.className = 'pipeline-step';
      if (index === middleIndex) {
        div.className += ' pipeline-step--highlight';
      }
      div.textContent = step;
      pipelineContainer.appendChild(div);

      // Adiciona seta entre os passos (não após o último)
      if (index < steps.length - 1) {
        const arrow = document.createElement('span');
        arrow.className = 'pipeline-arrow';
        arrow.setAttribute('aria-hidden', 'true');
        arrow.textContent = '→';
        pipelineContainer.appendChild(arrow);
      }
    });
  }
}
