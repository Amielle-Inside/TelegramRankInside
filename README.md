# TelegramRankInside

Bot de ranking semanal para grupos do Telegram com painel administrativo web, SQLite com WAL mode, e persistência durável de updates. Desenvolvido em Python puro (stdlib apenas — zero dependências externas).

## Sobre

O **TelegramRankInside** é um minijogo de participação para grupos do Telegram. Os usuários ganham pontos por enviar mensagens no grupo, e um ranking semanal (top 10) é atualizado automaticamente. Há pódio semanal com 🥇🥈🥉, rodízio de ciclos, cooldown de comandos, e um painel administrativo web (somente localhost) para consultar rankings, participantes, exportar dados e gerenciar grupos.

Principais características:
- **Ranking semanal** com top 10 por grupo, pódio com medalhas
- **Ciclos de pódio** com rodízio (quem ficou no top 3 não pode repetir no ciclo seguinte)
- **Comandos públicos** no grupo com cooldown (ex.: `!rank`, `!pontos`, `!posicao`)
- **Comandos administrativos** para owner/admin (ex.: `!status`, `!stop`, `!reboot`)
- **Painel web** em localhost com login, sessão, CSRF e seletor de grupos
- **Persistência durável**: todo update é gravado no SQLite *antes* de confirmar o offset ao Telegram (sem duplicar mensagens após reinício)
- **Deduplicação** de `update_id` para evitar processamento repetido
- **SQLite WAL mode**, `synchronous=FULL`, `foreign_keys=ON`, `busy_timeout=5000`
- **Zero dependências externas** — apenas Python stdlib (`urllib`, `json`, `sqlite3`, `http.server`, etc.)

## Estrutura do repositório

```
TelegramRankInside/
├── .env.example              # Modelo de configuracao (copie para config/config.env)
├ .gitignore                  # Ignora dados sensíveis, banco, cache, venv
├── README.md                 # Este arquivo
├── run.py                    # Ponto de entrada (orquestra core + modulos + painel)
├── config/
│   └── config.env            # Configuracao real (NO COMMIT — dados sensiveis)
├── bot/
│   ├── core/
│   │   ├── app.py            # Orquestrador principal (run_loop, process_update, cooldowns)
│   │   ├── storage.py        # Camada SQLite (WAL, tabelas core, transacoes)
│   │   ├── telegram.py       # Cliente Telegram (long polling, getUpdates, sendMessage)
│   │   ├── commands.py       # Registro e parsing de comandos (!xxx)
│   │   ├── cooldowns.py      # Gerenciador de cooldown por chat/comando
│   │   ├── modules.py        # Gerenciador de modulos e manifests
│   │   ├── permissions.py    # Checagem de owner/admin
│   │   └── __init__.py
│   ├── modules/
│   │   └── ranking/
│   │       ├── __init__.py   # Manifest, on_enable, create_handler
│   │       ├── commands.py   # Handlers dos comandos de ranking (!rank, !pontos, etc.)
│   │       ├── handlers.py   # Processamento de eventos de mensagem (pontuacao)
│   │       ├── rules.py      # Regras de pontuacao (valores +0.7, +1.1, etc.)
│   │       └── storage.py    # Tabelas especifica do ranking (mensagens, pontos, ciclos)
│   └── __init__.py
├── web/
│   ├── __init__.py
│   └── panel.py              # Painel administrativo web (HTTP server, login, sessao, CSRF)
├── backfill_ranking.py       # Script para reprocessar updates armazenados no ranking
└── data/                     # Banco SQLite e exports (NO COMMIT)
```

## Como funciona (visao geral)

1. **Long polling**: o bot chama `getUpdates` da Telegram Bot API a cada ciclo (timeout de 5s).
2. **Persistencia primeiro**: cada `update_id` é gravado no SQLite *antes* de ser processado. O offset só é confirmado ao Telegram depois da persistencia. Isso garante que, em caso de reinicio, nenhuma mensagem seja processada duas vezes.
3. **Deduplicacao**: o `run_loop` verifica se o `update_id` ja foi processado antes de despachar.
4. **Comandos**: mensagens que comecam com `!` sao tratadas como comandos. Comandos nao pontuam no ranking.
5. **Ranking**: mensagens comuns sao processadas pelo `RankingHandler`, que aplica regras de pontuacao e grava em `ranking_messages` e `ranking_points`.
6. **Painel web**: servidor HTTP em `127.0.0.1:2020` com login (form HTML + cookie de sessao), CSRF, dashboard, rankings, ciclos, participantes, exportacao e configuracao.

## Parte tecnica ponto a ponto

### 1. Armazenamento (`bot/core/storage.py`)
- SQLite com **WAL mode** (melhor concorrencia leitura/escrita)
- `synchronous = FULL` (durabilidade maxima)
- `foreign_keys = ON` (integridade referencial)
- `busy_timeout = 5000` (espera 5s em caso de lock)
- Tabelas core: `core_meta`, `updates_received`, `core_state`, `cooldowns`, `audit_log`, `heartbeat`, `web_users`, `web_sessions`, `web_config`, `web_csrf_tokens`
- Transacoes serializadas com commit/rollback automatico
- Metodo `transaction()` como context manager

### 2. Cliente Telegram (`bot/core/telegram.py`)
- Usa apenas `urllib` da stdlib (sem `requests` ou dependências externas)
- `getUpdates` com `timeout=5`, `allowed_updates = ["message", "edited_message", "chat_member"]`
- `persist_update()` grava o update no SQLite **antes** de `save_offset()` avançar o offset
- `send_message()`, `send_private()`, `get_chat()`, `get_chat_administrators()`, `get_chat_member_count()`, `get_me()`
- Timeout configuravel (padrão 30s, reduzido para 5s no loop de updates)

### 3. Aplicacao principal (`bot/core/app.py`)
- `RankingApp` orquestra storage, telegram client, comandos, modulos, permissoes e cooldowns
- `run_loop()`: loop principal de long polling com dedup de `update_id`
- `process_update()`: despacha comandos (`!xxx`) ou modulos (ranking)
- Cooldown por escopo `chat:{chat_id}` + comando, com mensagem de espera explicita
- Sinais `SIGINT`/`SIGTERM` para parada limpa (fecha storage e painel web)

### 4. Modulo Ranking (`bot/modules/ranking/`)
- **`handlers.py`**: processa eventos de mensagem (texto, resposta, vídeo, link, encaminhamento, repetição) e aplica pontuacao
- **`rules.py`**: valores de pontuacao (ex.: texto proprio +0.7, resposta +1.1, link sem comentario -0.3, etc.)
- **`commands.py`**: `!rank`, `!rciclo`, `!pontos`, `!posicao`, `!historico`, `!regras`, `!ajuda`, `!status`, `!check`, `!stop`, `!reboot`
- **`storage.py`**: tabelas `ranking_messages`, `ranking_points`, `ranking_rounds`, `ranking_cycles`, `ranking_podiums`
- Semana começa segunda-feira 00:00 (America/Sao_Paulo)

### 5. Painel web (`web/panel.py`)
- Servidor HTTP nativo da stdlib (`http.server`)
- Apenas `127.0.0.1` (nunca exposto externamente)
- Login via form HTML + cookie de sessao (HttpOnly, SameSite=Lax, Max-Age=1h)
- CSRF token em forms (validado em POST)
- Páginas: visão geral, rankings, ciclos, participantes, regras, comandos, módulos, operação, exportar, auditoria, configurações
- Seletor de grupos abaixo do título com nome e quantidade de membros
- Rankings mostram `@username`/nome no grupo; ID apenas no painel admin
- Pódio semanal (🥇🥈🥉) na prévia e na página de rankings

### 6. Segurança
- Token do bot, senhas e IDs nunca sao commitados (veja `.gitignore` e `.env.example`)
- Painel web so escuta em `127.0.0.1`
- Senhas armazenadas como hash SHA-256 no SQLite
- CSRF token validado em todas as mutacoes via POST
- Sessao expira apos 1 hora

## Dependencias

**Zero dependências externas.** Apenas Python 3 stdlib:

| Modulo | Uso |
|--------|-----|
| `urllib.request`, `urllib.parse`, `urllib.error` | Cliente HTTP para Telegram Bot API |
| `json` | Serializacao de payloads e respostas |
| `sqlite3` | Banco de dados local (WAL) |
| `http.server` | Painel administrativo web |
| `threading` | Painel web em thread separada |
| `signal` | Sinais de parada limpa |
| `time`, `calendar` | Timestamps, calculo de semana |
| `hashlib` | Hash de senhas |
| `pathlib`, `os` | Manipulacao de caminhos |

Python >= 3.10 recomendado (usado `str | Path` union type, `list[tuple]` generics).

## Como instalar

```bash
# 1. Clone o repositorio
git clone https://github.com/Amielle-Inside/TelegramRankInside.git
cd TelegramRankInside

# 2. Crie o arquivo de configuracao a partir do modelo
cp .env.example config/config.env

# 3. Edite config/config.env com seus valores reais
#    (TELEGRAM_BOT_TOKEN, OWNER_IDS, ADMIN_IDS, WEB_USER, WEB_PASSWORD, etc.)

# 4. Execute o bot
python3 run.py
```

## Como configurar

Edite `config/config.env` (baseado em `.env.example`):

| Variavel | Descricao | Exemplo |
|----------|-----------|---------|
| `TELEGRAM_BOT_TOKEN` | Token do bot obtido em @BotFather | `123456789:ABCdef...` |
| `OWNER_IDS` | IDs do owner (controle global), separados por virgula | `237007859` |
| `ADMIN_IDS` | IDs de admins autorizados | `237007859` |
| `TZ` | Fuso horario para calendário do ranking | `America/Sao_Paulo` |
| `DB_PATH` | Caminho do banco SQLite | `data/ranking.db` |
| `JSON_DIR` | Diretorio de exports JSON | `data/json` |
| `WEB_HOST` | Host do painel web (sempre localhost) | `127.0.0.1` |
| `WEB_PORT` | Porta do painel web | `2020` |
| `WEB_SECRET` | Secreto para sessao/CSRF | `sua_senha_forte` |
| `WEB_USER` | Usuario do painel web | `Amielle` |
| `WEB_PASSWORD` | Senha do painel web | `sua_senha_forte` |
| `COOLDOWN_PUBLIC_SEC` | Cooldown de comandos publicos (segundos) | `300` |

**Como obter o token do bot:**
1. Converse com @BotFather no Telegram
2. Use `/newbot` para criar um bot
3. Copie o token fornecido
4. Desative o modo de privacidade do bot (@BotFather → /setprivacy → disable) para que ele veja mensagens no grupo
5. Adicione o bot como administrador nos grupos alvo

**Como obter IDs de usuario:**
Use @userinfobot ou encaminhe uma mensagem do usuario para o bot para capturar o `user_id`.

## Como buildar

Nao e necessario build. O projeto e Python puro — execute diretamente com `python3 run.py`.

Se precisar empacotar para distribuicao:
```bash
# Criar um executavel standalone com PyInstaller (opcional, dependencia externa)
pip install pyinstaller
pyinstaller --onefile run.py
```

## Como usar os comandos

### Comandos publicos (cooldown 5 min no grupo)

| Comando | Descricao |
|---------|-----------|
| `!rank` | Top 10 da semana com nomes e pontos |
| `!rciclo` | Ciclo atual e elegibilidade ao pódio |
| `!pontos` | Sua pontuacao nesta semana |
| `!posicao` | Sua posicao no rodizio de pódio |
| `!historico` | Rodadas anteriores encerradas |
| `!regras` | Regras de pontuacao |
| `!ajuda` | Lista de comandos publicos |

### Comandos administrativos (owner/admin)

| Comando | Descricao | Restricao |
|---------|-----------|-----------|
| `!status` | Status do bot e estatisticas | Admin |
| `!check` | Auditoria/recontagem | Admin |
| `!stop` | Para o bot | Owner |
| `!reboot` | Reinicia o bot | Owner |

## Painel administrativo web

Acesse `http://127.0.0.1:2020/painel/` apos iniciar o bot.

- **Login**: usuario e senha definidos em `WEB_USER` / `WEB_PASSWORD`
- **Sessao**: cookie HttpOnly, expira em 1 hora
- **Seletor de grupos**: abaixo do título `TelegramRankInside`, escolha entre os grupos monitorados para ver ranking, participantes e exportacoes de cada um
- **Paginas**:
  - Visão geral: estatisticas e estado do bot
  - Rankings: top 10 semanal com pódio (🥇🥈🥉) e tabela completa
  - Ciclos e rodadas: ciclos ativos, rodadas fechadas
  - Participantes: lista de usuarios pontuados por grupo
  - Regras: tabela de pontuacao
  - Comandos: lista de comandos e cooldowns
  - Modulos: modulos carregados e status
  - Operacao: diagnosticos, heartbeat, logs
  - Exportar: backup JSON do banco
  - Auditoria: log de acoes administrativas
  - Configuracoes: ajustes do painel

## Backfill (reprocessar mensagens antigas)

Se ja houver updates armazenados antes do modulo de ranking estar ativo, use o script de backfill:

```bash
python3 backfill_ranking.py
```

Isso reprocessa todas as mensagens em `updates_received` para as tabelas de ranking (`ranking_messages`, `ranking_points`).

## Seguranca — dados sensiveis

O seguinte **NUNCA** deve ser commitado no repositorio:

- `config/config.env` — contem token do bot, senhas e IDs
- `data/ranking.db` — banco com dados de usuarios e pontuacao
- `__pycache__/` — cache de bytecode Python
- `.env` e variantes — arquivos de ambiente locais

O arquivo `.gitignore` ja ignora todos esses itens. O `.env.example` serve apenas como modelo com valores fictícios.

## Licença

MIT.
