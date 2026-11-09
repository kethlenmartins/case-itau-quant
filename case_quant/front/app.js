"use strict";

const DATA_FILE = "./dados_interface.json";
const INITIAL_RISK_COUNT = 6;
const INITIAL_CRITICAL_COUNT = 5;

const numberFormatter = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 });
const integerFormatter = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });
const percentFormatter = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
});

const state = {
  data: null,
  showAllRisks: false,
};

function byId(id) {
  return document.getElementById(id);
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}

function isFiniteNumber(value) {
  return typeof value === "number" && Number.isFinite(value);
}

function formatNumber(value, fallback = "—") {
  return isFiniteNumber(value) ? numberFormatter.format(value) : fallback;
}

function formatInteger(value, fallback = "—") {
  return isFiniteNumber(value) ? integerFormatter.format(Math.round(value)) : fallback;
}

function formatPercent(value, fallback = "—") {
  return isFiniteNumber(value) ? `${percentFormatter.format(value)}%` : fallback;
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function safeText(value, fallback = "Não informado") {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

function formatTimestamp(value) {
  if (typeof value !== "string" || !value.trim()) return "Momento não informado";
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::\d{2})?/);
  if (!match) return value;
  return `${match[3]}/${match[2]}/${match[1]} · ${match[4]}:${match[5]}`;
}

function createHelpButton(label, helpText) {
  const button = element("button", "help-button", "?");
  button.type = "button";
  button.setAttribute("aria-label", label);
  button.dataset.tooltip = helpText;
  button.title = helpText;
  return button;
}

function renderContext(meta) {
  byId("snapshot-time").textContent = formatTimestamp(meta?.timestamp);
  byId("forecast-period").textContent = safeText(meta?.periodo_previsao, "Não informada");
}

function renderOverview(rede) {
  const grid = byId("metric-grid");
  grid.replaceChildren();

  const metrics = [
    {
      label: "Bicicletas disponíveis",
      value: formatInteger(rede?.bicicletas),
      detail: "na rede agora",
      help: "Soma das bicicletas disponíveis nas estações no momento do snapshot.",
    },
    {
      label: "Vagas disponíveis",
      value: formatInteger(rede?.vagas),
      detail: "para devoluções",
      help: "Soma das vagas livres nas estações no momento do snapshot.",
    },
    {
      label: "Ocupação da rede",
      value: formatPercent(rede?.ocupacao_pct),
      detail: isFiniteNumber(rede?.capacidade) && isFiniteNumber(rede?.bicicletas)
        ? `${formatInteger(rede.bicicletas)} de ${formatInteger(rede.capacidade)} espaços ocupados`
        : "capacidade não informada",
      help: "Parcela da capacidade total que está ocupada por bicicletas agora.",
    },
    {
      label: "Estações em operação",
      value: formatInteger(rede?.estacoes_ativas),
      detail: `${formatInteger(rede?.estacoes_indisponiveis, "0")} fora de operação`,
      help: "Estações ativas podem receber ou liberar bicicletas. As demais estão fora de operação.",
    },
    {
      label: "Estações críticas",
      value:
        isFiniteNumber(rede?.criticas_baixas) && isFiniteNumber(rede?.criticas_altas)
          ? formatInteger(rede.criticas_baixas + rede.criticas_altas)
          : "—",
      detail: `${formatInteger(rede?.criticas_baixas, "0")} quase sem bicicleta · ${formatInteger(rede?.criticas_altas, "0")} quase sem vaga`,
      help: "Estações ativas são críticas quando têm até 10% de ocupação, com risco de faltar bicicleta, ou ao menos 90%, com risco de faltar vaga.",
    },
  ];

  metrics.forEach((metric) => {
    const card = element("article", "metric-card");
    const top = element("div", "metric-top");
    top.append(element("span", "metric-label", metric.label));
    top.append(createHelpButton(`Explicar ${metric.label.toLowerCase()}`, metric.help));
    card.append(top, element("strong", "metric-value", metric.value));
    card.append(element("span", "metric-detail", metric.detail));
    grid.append(card);
  });

  const summaryParts = [];
  if (isFiniteNumber(rede?.estacoes_ativas)) {
    summaryParts.push(`${formatInteger(rede.estacoes_ativas)} estações ativas`);
  }
  if (isFiniteNumber(rede?.ocupacao_pct)) {
    summaryParts.push(`rede com ${formatPercent(rede.ocupacao_pct)} de ocupação`);
  }
  byId("overview-summary").textContent = summaryParts.length
    ? `${summaryParts.join(" · ")}.`
    : "Resumo do estado observado no snapshot.";
}

function renderMovements(movements) {
  const grid = byId("movement-grid");
  const emptyNote = byId("movement-empty-note");
  grid.replaceChildren();

  const prioritized = [...asArray(movements)]
    .filter((item) => item && typeof item === "object")
    .sort((a, b) => (a.ordem ?? 999) - (b.ordem ?? 999))
    .slice(0, 3);

  prioritized.forEach((movement, index) => {
    const origin = movement.origem || {};
    const destination = movement.destino || {};
    const originDelta = movement.variacao_risco_origem;
    const card = element("article", "movement-card");
    const order = element("div", "movement-order");
    order.append(
      element("span", "order-label", `${index + 1}º movimento`),
      element("span", "gain-badge", `Ganho previsto +${formatNumber(movement.ganho_liquido)}`),
    );

    const relievesOrigin = isFiniteNumber(originDelta) && originDelta < 0;
    const priorityName = relievesOrigin
      ? safeText(origin.nome, "Origem não informada")
      : safeText(destination.nome, "Destino não informado");
    const priorityRole = relievesOrigin
      ? "Estação prioritária · aliviar lotação"
      : "Estação prioritária · abastecer";

    const route = element("div", "route");
    route.setAttribute(
      "aria-label",
      `Rota de ${safeText(origin.nome)} para ${safeText(destination.nome)}`,
    );
    route.append(
      createRoutePoint(origin, "Origem"),
      element("span", "route-arrow", "→"),
      createRoutePoint(destination, "Destino", true),
    );

    const impact = element("div", "movement-impact");
    impact.append(
      element("strong", "bike-quantity", formatInteger(movement.quantidade)),
      element(
        "span",
        "bike-unit",
        Math.round(movement.quantidade) === 1 ? "bicicleta" : "bicicletas",
      ),
    );

    const details = element("details", "movement-details");
    details.append(element("summary", "", "Ver efeito nas duas estações"));
    const effects = element("div", "effects");
    const originEffect = relievesOrigin
      ? `Efeito na origem: esta retirada também reduz em ${formatNumber(Math.abs(originDelta))} o risco previsto de falta de vagas.`
      : isFiniteNumber(originDelta) && originDelta > 0
        ? `Trade-off na origem: aumento previsto de ${formatNumber(originDelta)} no risco.`
        : "Efeito na origem: não informado.";
    const destinationEffect = isFiniteNumber(movement.beneficio_destino)
      ? `Efeito no destino: redução prevista de ${formatNumber(movement.beneficio_destino)} no risco.`
      : "Efeito no destino: não informado.";
    effects.append(element("p", "", originEffect), element("p", "", destinationEffect));
    details.append(effects);

    card.append(
      order,
      element("h3", "priority-station", priorityName),
      element("p", "priority-note", priorityRole),
      route,
      impact,
      element(
        "p",
        "justification",
        safeText(
          movement.justificativa,
          "Esta movimentação apresenta ganho líquido previsto para a rede no horizonte analisado.",
        ),
      ),
      details,
    );
    grid.append(card);
  });

  if (prioritized.length === 0) {
    emptyNote.textContent = "Não há movimentação com ganho previsto positivo neste snapshot.";
    emptyNote.hidden = false;
  } else if (prioritized.length < 3) {
    emptyNote.textContent = "Não há outra movimentação com ganho previsto positivo.";
    emptyNote.hidden = false;
  } else {
    emptyNote.hidden = true;
  }
}

function createRoutePoint(point, role, destination = false) {
  const wrapper = element("div", `route-point${destination ? " destination" : ""}`);
  wrapper.append(
    element("span", "route-name", safeText(point?.nome)),
    element(
      "span",
      "route-meta",
      `${role} · ${safeText(point?.id, "ID —")} · ${safeText(point?.zona, "zona não informada")}`,
    ),
  );
  return wrapper;
}

function renderZones(zones) {
  const list = byId("zones-list");
  list.replaceChildren();
  const items = asArray(zones);

  if (!items.length) {
    list.append(element("div", "empty-state", "Não há dados por zona neste snapshot."));
    return;
  }

  items.forEach((zone) => {
    const row = element("div", "zone-row");
    const track = element("div", "bar-track");
    const fill = element("div", "bar-fill");
    const percentage = isFiniteNumber(zone?.ocupacao_pct)
      ? Math.max(0, Math.min(100, zone.ocupacao_pct))
      : 0;
    fill.style.width = `${percentage}%`;
    track.setAttribute("aria-hidden", "true");
    track.append(fill);
    row.append(
      element("span", "zone-name", safeText(zone?.nome)),
      track,
      element("span", "zone-value", formatPercent(zone?.ocupacao_pct)),
      element(
        "span",
        "zone-detail",
        `${formatInteger(zone?.ativas, "0")} ativas · ${formatInteger(zone?.criticas, "0")} críticas`,
      ),
    );
    list.append(row);
  });
}

function renderCriticalStations(critical, unavailable) {
  const container = byId("critical-groups");
  container.replaceChildren();
  const criticalItems = asArray(critical);
  const groups = [
    {
      title: "Quase sem bicicletas",
      items: criticalItems.filter((item) => item?.tipo === "baixa"),
      unavailable: false,
      rule: "Abaixo de 10% de ocupação",
    },
    {
      title: "Quase sem vagas",
      items: criticalItems.filter((item) => item?.tipo === "alta"),
      unavailable: false,
      rule: "Acima de 90% de ocupação",
    },
    {
      title: "Fora de operação",
      items: asArray(unavailable),
      unavailable: true,
      rule: "Não entra nas movimentações",
    },
  ];

  groups.forEach((group, groupIndex) => {
    const wrapper = element("details", "critical-group");
    const heading = element("summary", "critical-group-head");
    const title = element("div", "critical-title-copy");
    title.append(element("h3", "", group.title), element("p", "critical-rule", group.rule));
    heading.append(title, element("span", "count-badge", formatInteger(group.items.length)));
    wrapper.append(heading);

    if (!group.items.length) {
      wrapper.append(element("p", "metric-detail", "Nenhuma estação nesta categoria."));
      container.append(wrapper);
      return;
    }

    const list = element("ul", "station-list");
    const groupId = `critical-list-${groupIndex}`;
    list.id = groupId;
    group.items.forEach((station, index) => {
      const item = element("li", "station-item");
      if (index >= INITIAL_CRITICAL_COUNT) item.hidden = true;
      const identity = element("span", "");
      identity.append(
        element("span", "station-id", safeText(station?.station_id, "ID —")),
        document.createTextNode(safeText(station?.name)),
      );
      const statusText = group.unavailable
        ? station?.status === "maintenance"
          ? "em manutenção"
          : "fora de operação"
        : isFiniteNumber(station?.ocupacao_pct)
          ? `${formatPercent(station.ocupacao_pct)} ocupada · ${station.tipo === "baixa" ? "abaixo de 10%" : "acima de 90%"}`
          : safeText(station?.zone, "zona não informada");
      item.append(
        identity,
        element("span", group.unavailable ? "station-status" : "station-zone", statusText),
      );
      list.append(item);
    });
    wrapper.append(list);

    if (group.items.length > INITIAL_CRITICAL_COUNT) {
      const button = element("button", "small-toggle", `Ver todas (${group.items.length})`);
      button.type = "button";
      button.dataset.listToggle = groupId;
      button.dataset.expanded = "false";
      wrapper.append(button);
    }
    container.append(wrapper);
  });
}

function renderRisks(risks) {
  const body = byId("risk-table-body");
  const empty = byId("risk-empty");
  const toggle = byId("toggle-risks");
  body.replaceChildren();

  const sorted = [...asArray(risks)]
    .filter((item) => item && typeof item === "object")
    .sort((a, b) => (b.total_2h ?? -Infinity) - (a.total_2h ?? -Infinity));

  if (!sorted.length) {
    empty.hidden = false;
    toggle.hidden = true;
    return;
  }

  empty.hidden = true;
  const visible = state.showAllRisks ? sorted : sorted.slice(0, INITIAL_RISK_COUNT);
  visible.forEach((risk) => {
    const row = document.createElement("tr");
    const stationCell = document.createElement("td");
    stationCell.append(
      element("span", "table-station", safeText(risk.name)),
      element(
        "span",
        "table-zone",
        `${safeText(risk.station_id, "ID —")} · ${safeText(risk.zone, "zona não informada")}`,
      ),
    );
    row.append(
      stationCell,
      createCell(
        `${formatInteger(risk.bikes, "0")} bicicleta${risk.bikes === 1 ? "" : "s"} · ${formatInteger(risk.docks, "0")} vaga${risk.docks === 1 ? "" : "s"}`,
      ),
      createCell(riskValueLabel(risk.retirada_1h)),
      createCell(riskValueLabel(risk.devolucao_1h)),
      createRiskTotalCell(risk),
    );
    body.append(row);
  });

  toggle.hidden = sorted.length <= INITIAL_RISK_COUNT;
  toggle.textContent = state.showAllRisks
    ? "Mostrar apenas prioridades"
    : `Ver detalhes (${sorted.length} estações)`;
  toggle.setAttribute("aria-expanded", String(state.showAllRisks));
}

function createCell(text) {
  return element("td", "", text);
}

function riskValueLabel(value) {
  if (!isFiniteNumber(value) || value === 0) return "nenhum previsto";
  const unidade = Math.abs(value - 1) < 0.001 ? "viagem" : "viagens";
  return `≈ ${formatNumber(value)} ${unidade}`;
}

function createRiskTotalCell(risk) {
  const cell = element("td", "risk-total");
  const label = riskValueLabel(risk.total_2h);
  cell.append(element("strong", "", label));
  if (isFiniteNumber(risk.total_2h) && risk.total_2h > 0) {
    cell.append(element("span", "risk-caption", "podem falhar neste horizonte"));
  }
  const category = risk.categoria ?? risk.nivel ?? risk.classificacao;
  if (typeof category === "string" && category.trim()) {
    const normalized = category.toLowerCase();
    const classMap = {
      alto: "high",
      alta: "high",
      médio: "medium",
      medio: "medium",
      média: "medium",
      media: "medium",
      baixo: "low",
      baixa: "low",
    };
    const badge = element("span", `risk-category ${classMap[normalized] || ""}`, category);
    cell.append(badge);
  }
  return cell;
}

function renderValidation(validation) {
  const periods = byId("validation-periods");
  if (validation?.periodo_treino || validation?.periodo_validacao) {
    periods.textContent = `Comparamos a previsão com o que aconteceu de fato. Treino: ${safeText(validation.periodo_treino, "não informado")} · validação: ${safeText(validation.periodo_validacao, "não informada")}.`;
  }

  const container = byId("validation-metrics");
  container.replaceChildren();
  [
    ["Retiradas", validation?.retiradas, "Viagens que começam nesta estação: pessoas buscando uma bicicleta."],
    ["Devoluções", validation?.devolucoes, "Viagens que terminam nesta estação: pessoas precisando de uma vaga."],
  ].forEach(([label, metrics, explanation]) => {
    const group = element("section", "validation-group");
    const heading = element("div", "validation-heading");
    heading.append(element("h3", "", label), createHelpButton(`Explicar ${label.toLowerCase()}`, explanation));
    group.append(heading);
    const mae = formatNumber(metrics?.mae);
    group.append(element("strong", "validation-main", `Erro médio: ${mae} viagem`));
    group.append(element("p", "validation-copy", "por estação e por hora. Quanto menor, mais próxima a previsão ficou do realizado."));
    const details = element("details", "validation-details");
    details.append(element("summary", "", "Ver métricas técnicas"));
    details.append(
      element(
        "p",
        "",
        `MAE: ${mae} · RMSE: ${formatNumber(metrics?.rmse)} · Viés: ${formatNumber(metrics?.vies)}.`,
      ),
    );
    group.append(details);
    container.append(group);
  });
}

function renderLimitations(limitations, details) {
  const defaultLimits = [
    "Viagens históricas incluem apenas trajetos realizados.",
    "A demanda futura é estimada, não observada.",
    "Indisponibilidades futuras de estação são incertas.",
  ];
  const received = asArray(limitations).filter((item) => typeof item === "string" && item.trim());
  const visibleLimits = defaultLimits.map((fallback, index) => received[index] || fallback);
  const list = byId("limits-list");
  list.replaceChildren();
  visibleLimits.forEach((text) => list.append(element("li", "", text)));

  const detailItems = asArray(details).filter((item) => typeof item === "string" && item.trim());
  const button = byId("toggle-limits");
  const detailContainer = byId("model-details");
  detailContainer.replaceChildren();
  detailItems.forEach((text) => detailContainer.append(element("p", "", text)));
  button.hidden = detailItems.length === 0;
  detailContainer.hidden = true;
  button.setAttribute("aria-expanded", "false");
  button.textContent = "Entender os limites";
}

function renderDashboard(data) {
  renderContext(data.meta || {});
  renderOverview(data.rede || {});
  renderMovements(data.movimentacoes);
  renderZones(data.zonas);
  renderCriticalStations(data.criticas, data.indisponiveis);
  renderRisks(data.riscos);
  renderValidation(data.validacao || {});
  renderLimitations(data.limitacoes, data.detalhes_modelo);
}

function showError(error) {
  byId("loading-state").hidden = true;
  byId("dashboard").hidden = true;
  byId("error-state").hidden = false;
  byId("snapshot-time").textContent = "Dados indisponíveis";
  byId("forecast-period").textContent = "—";
  if (error instanceof SyntaxError) {
    byId("error-message").textContent =
      "O arquivo dados_interface.json foi encontrado, mas não contém JSON válido. Revise o arquivo e recarregue a página.";
  }
}

async function loadData() {
  try {
    const response = await fetch(DATA_FILE, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Falha ao carregar os dados: HTTP ${response.status}`);
    }
    const data = await response.json();
    if (!data || typeof data !== "object" || Array.isArray(data)) {
      throw new SyntaxError("Estrutura de dados inválida");
    }
    state.data = data;
    renderDashboard(data);
    byId("loading-state").hidden = true;
    byId("error-state").hidden = true;
    byId("dashboard").hidden = false;
  } catch (error) {
    showError(error);
  }
}

document.addEventListener("click", (event) => {
  const listToggle = event.target.closest("[data-list-toggle]");
  if (listToggle) {
    const list = byId(listToggle.dataset.listToggle);
    const expanded = listToggle.dataset.expanded === "true";
    if (list) {
      [...list.children].forEach((item, index) => {
        if (index >= INITIAL_CRITICAL_COUNT) item.hidden = expanded;
      });
      listToggle.dataset.expanded = String(!expanded);
      listToggle.textContent = expanded ? `Ver todas (${list.children.length})` : "Mostrar menos";
    }
  }

  const openButton = event.target.closest("[data-open-dialog]");
  if (openButton) {
    const dialog = byId(openButton.dataset.openDialog);
    if (dialog?.showModal) dialog.showModal();
  }

  if (event.target.closest("[data-close-dialog]")) {
    event.target.closest("dialog")?.close();
  }
});

byId("method-dialog").addEventListener("click", (event) => {
  if (event.target === event.currentTarget) event.currentTarget.close();
});

byId("toggle-risks").addEventListener("click", () => {
  state.showAllRisks = !state.showAllRisks;
  renderRisks(state.data?.riscos);
});

byId("toggle-limits").addEventListener("click", (event) => {
  const details = byId("model-details");
  const willOpen = details.hidden;
  details.hidden = !willOpen;
  event.currentTarget.setAttribute("aria-expanded", String(willOpen));
  event.currentTarget.textContent = willOpen ? "Recolher explicação" : "Entender os limites";
});

loadData();
