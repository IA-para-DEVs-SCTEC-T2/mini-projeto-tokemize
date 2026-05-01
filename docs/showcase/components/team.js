/**
 * team.js — Componente de renderização da seção de Equipe
 *
 * Renderiza os membros da equipe com avatar, nome e link para o GitHub.
 * Requirements: 6.1, 6.2, 6.3
 */

/** Caminho para o avatar padrão quando o username não está no mapa de avatares. */
const DEFAULT_AVATAR = './assets/default-avatar.svg';

/**
 * Renderiza a lista de membros da equipe no elemento #team-list.
 *
 * Para cada membro:
 * - Usa a URL do avatar fornecida no mapa `avatars` se disponível
 * - Usa `DEFAULT_AVATAR` como fallback quando o username não está no mapa
 *
 * @typedef {Object} TeamMember
 * @property {string} name   - Nome completo do membro
 * @property {string} github - Username do GitHub
 *
 * @param {TeamMember[]} members - Array de membros da equipe
 * @param {Map<string, string>} avatars - Mapa de username → URL do avatar
 */
export function renderTeam(members, avatars) {
  const list = document.getElementById('team-list');
  if (!list) return;

  list.innerHTML = '';

  for (const member of members) {
    const avatarUrl = avatars.has(member.github)
      ? avatars.get(member.github)
      : DEFAULT_AVATAR;

    const li = document.createElement('li');
    li.className = 'team-member';

    // Avatar
    const img = document.createElement('img');
    img.className = 'team-avatar';
    img.src = avatarUrl;
    img.alt = `Avatar de ${member.name}`;

    // Nome
    const nameSpan = document.createElement('span');
    nameSpan.className = 'team-name';
    nameSpan.textContent = member.name;

    // Link GitHub
    const githubLink = document.createElement('a');
    githubLink.className = 'team-github-link';
    githubLink.href = `https://github.com/${member.github}`;
    githubLink.target = '_blank';
    githubLink.rel = 'noopener noreferrer';
    githubLink.textContent = `@${member.github}`;

    li.appendChild(img);
    li.appendChild(nameSpan);
    li.appendChild(githubLink);
    list.appendChild(li);
  }
}
