# LGPD — mapa de dados e decisões do Spectra

> Documento de estudo e engenharia, não parecer jurídico. Antes de vender para empresas, revise com o DPO/jurídico.

## 1. O que o app faz com dados

| Dado | Origem | Para onde vai | Retenção |
|---|---|---|---|
| Screenshot do monitor ativo | Tela do usuário | Endpoint do provedor escolhido | Não é salvo pelo Spectra |
| Prompt do sistema + histórico curto | App | Mesmo endpoint | Sessão local de 1 h |
| Chave de API | Usuário | System keyring | Até o usuário remover |
| Configuração | Usuário | `~/.config/spectra-hud/config.yaml` (600; JSON de compatibilidade) | Até o usuário remover |
| Log de eventos | App | `~/.local/state/spectra-hud/spectra.log` | Rotação 1 MB × 3 |
| Cache de sessão | App | `~/.local/state/spectra-hud/session.json` (600) | 1 h de inatividade |

O Spectra **não opera servidor**. O screenshot sai da máquina apenas para o endpoint configurado pelo usuário.

## 2. Papéis

- **Usuário/empresa:** controlador dos dados que aparecem na tela.
- **Spectra (app local):** operador técnico, sem acesso remoto aos dados.
- **Provedor do modelo:** subprocessador/controlador independente, conforme os termos dele.
- **Fabricante do modelo local (Ollama):** nada sai da máquina; o usuário continua controlador.

## 3. Base legal

- **Consentimento** (art. 7º, I) para o envio do screenshot. O app exige consentimento explícito antes do primeiro scan e registra `consent_at`.
- **Legítimo interesse** pode ser discutido para uso interno, mas não substitui o consentimento em telas com dados pessoais de terceiros.
- Dados sensíveis (saúde, biometria, financeiro) não são o alvo do produto. Se aparecerem na tela, o risco é do usuário; por isso existem pausa e blocklist.

## 4. Riscos

1. **Tela sensível:** senha, banco, prontuário, conversa privada.
2. **Transferência internacional:** o provedor pode processar fora do Brasil.
3. **Retenção do provedor:** o screenshot pode ficar retido conforme os termos dele.
4. **Prompt injection:** texto na tela pode manipular a resposta do modelo.
5. **Acesso local:** qualquer processo do mesmo usuário pode ler o cache/log.
6. **Multiusuário:** a chave no keyring é por usuário; o cache também.

## 5. Controles já implementados

- Consentimento explícito e registrado.
- **Private mode** (`Ctrl+Alt+P`): nenhum scan é capturado.
- **Blocklist por título de janela** (1Password, bancos, etc.): o scan é recusado antes da captura.
- Chave no **system keyring**; fallback em arquivo 600.
- Cache e config com permissão 600.
- Logs sem screenshots e sem chaves.
- Nenhuma telemetria, analytics ou conta.
- Modelo local (Ollama) disponível para quem não quer sair da máquina.
- Teste de visão explícito antes de salvar.

## 6. Lacunas antes de um produto pago

- **Redaction por região** e seleção de área (não implementado).
- **DPA** com cada provedor e definição de retenção/subprocessadores.
- **Política de privacidade e termos de uso** publicados.
- **Fluxo de direitos do titular:** exportar/apagar config, cache e chave (parcial: botão “limpar cache”).
- **Registro de consentimento** com versão do texto e timestamp (hoje só timestamp).
- **Avaliação de impacto (RIPD)** para clientes enterprise.
- **Resposta a incidentes** e canal de segurança.
- **Região de processamento** e opção “somente local” como padrão para setores regulados.

## 7. Checklist de lançamento

- [x] Consentimento antes do primeiro scan
- [x] Pausa e blocklist
- [x] Keyring e arquivos 600
- [x] Sem telemetria
- [x] Log sanitizado
- [ ] Política de privacidade/termos publicados
- [ ] DPA com provedores
- [ ] Redaction/região
- [ ] Direitos do titular documentados
- [ ] RIPD para enterprise

## 8. Decisões recomendadas

1. **Padrão seguro:** começar pausado em instalações enterprise.
2. **Local-first:** oferecer Ollama como caminho de menor risco.
3. **Blocklist editável** e mantida pelo usuário, não como garantia.
4. **Nunca** enviar screenshot para um endpoint sem consentimento registrado.
5. **Transparência:** mostrar o provedor e o modelo no centro de comando e no status.
