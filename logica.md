É um minigame para ranking de quem posta em supergrupos no telegram:

Todos os arquivos e tudo referente ao bot precisa ser gravado, salvo e gerenciado na pasta:
/var/home/Amielle/apps/telegramrankinside/

sendo assim a logica completa atual do bot:

Versão atual: 1.1.0 (arquivo VERSION na raiz do projeto)
Branch de desenvolvimento: beta
Repositório: https://github.com/Amielle-Inside/TelegramRankInside
Página pública: https://amielle-inside.github.io/TelegramRankInside/
Repositório privado de backups (snapshots): https://github.com/Amielle-Inside/snapshot-backups.git

-------------------------------------------------------------------------------
1. Exemplos de pontuação
-------------------------------------------------------------------------------

Uma mensagem de texto iniciando uma participação          +0,7
Uma resposta com texto à mensagem de outra pessoa, fora de sequência própria  +1,1
Três mensagens de texto consecutivas, sem bônus de resposta  +0,9 no total: 0,7 + 0,1 + 0,1
Uma quarta mensagem de texto nessa sequência                 −0,1
Um vídeo com uma explicação própria, fora de sequência       +0,7
Um link sem comentário                                       −0,3
Três encaminhamentos consecutivos                            −0,6 no total: 0 − 0,3 − 0,3

-------------------------------------------------------------------------------
2. Dois cuidados para o ranking
-------------------------------------------------------------------------------

Mensagens idênticas repetidas pela mesma pessoa em um intervalo definido, por exemplo 10 minutos, não devem gerar novos pontos positivos nem bônus.

Pontos positivos concedidos e manter eventuais penalidades, deixando essa regra explícita para os participantes.

A principal mudança é esta: premiar a primeira contribuição, permitir pequenos complementos e reduzir o ganho de quem fragmenta mensagens. O bônus de resposta mantém o incentivo à interação, mas não transforma qualquer “reply” em pontos extras.

-------------------------------------------------------------------------------
3. Top 10 semanal com pódio rotativo
-------------------------------------------------------------------------------

1. Pontuação reiniciada toda semana
   O ranking considera apenas os pontos daquela semana.
   No encerramento, o bot registra o resultado e começa uma nova rodada com zero pontos.
   As conquistas anteriores ficam no histórico, sem somar vantagem na rodada seguinte.

Reinícios periódicos são uma forma de evitar que a vantagem acumulada torne o ranking inacessível a quem entrou depois.

2. Quem terminar no top 3 passa uma rodada fora do pódio
   Quem encerrar a semana no top 3 continua pontuando normalmente na semana seguinte, mas fica temporariamente inelegível às posições de 1º a 3º.
   Na semana de intervalo: a pessoa pode aparecer do 4º ao 10º lugar, não perde pontos nem recebe penalidade, o bot indica “pódio na rodada anterior”, e na rodada seguinte volta a disputar o pódio normalmente.

3. Ciclos de pódio (prioridade para quem ainda não passou pelo top 3)
   Durante um ciclo, quem ainda não terminou nenhuma rodada no top 3 tem prioridade sobre quem já terminou.
   A cada semana, as três vagas do pódio vão para os participantes com mais pontos entre aqueles que ainda não passaram pelo pódio naquele ciclo.
   Quando todos os participantes elegíveis tiverem passado pelo pódio, começa um novo ciclo.

4. Critérios de participação no rodízio
   Participação mínima: ter mensagens que pontuem positivamente em pelo menos 3 dias da semana.
   Saldo: terminar a semana com pontuação positiva.
   Entrada no ciclo: participantes definidos no início; novos entram no próximo.
   Inatividade: quem não cumprir os critérios não bloqueia o encerramento do ciclo.
   Desempate: menos pódios no histórico; depois, mais dias com participação positiva.

5. Separe pontuação de destaque
   Pódio da rodada: aplica o rodízio e distribui o destaque.
   Pontuação da semana: mostra os pontos reais de cada participante, inclusive de quem está fora da disputa pelo pódio.

-------------------------------------------------------------------------------
4. Persistência e recuperação após reboot
-------------------------------------------------------------------------------

O bot deve restaurar integralmente o estado persistido e processar os updates ainda disponíveis no Telegram, sem duplicação.
Quando houver possibilidade de perda de eventos, deve registrar o intervalo como cobertura incompleta e informar a administração.

Não use “pulos” em message_id como prova de mensagens perdidas: registre uma suspeita de lacuna, não invente mensagens ou pontos.

Exclusões não são totalmente observáveis: a Bot API expõe eventos de edição, mas não oferece um update geral de exclusão de mensagens comuns de supergrupos.

O bot deve ser o mais leve possível e não acumular recursos da máquina.

Sempre grave em JSON as colocações atuais, passadas e as que estão ocorrendo.

-------------------------------------------------------------------------------
5. Comandos (prefixo !)
-------------------------------------------------------------------------------

Comandos públicos (todos os participantes):
!rank      — Top 10 da semana (cooldown: 5 min por grupo)
!rciclo    — Situação do ciclo, pódios conquistados e elegibilidade
!pontos    — Pontuação do próprio usuário
!posicao   — Posição e situação no rodízio
!historico — Rodadas e pódios anteriores
!regras    — Regras vigentes
!ajuda     — Comandos públicos / ajuda de um comando específico

Comandos administrativos (apenas adm/owner):
!status    — Saúde, sincronização, fila e disponibilidade
!check     — Auditoria limitada ao grupo autorizado
!export    — Exportação do grupo autorizado
!pause/!resume — Pausar/retomar pontuação do grupo, mantendo coleta

Comandos exclusivos do owner:
!stop      — Para o processo inteiro (precisa de supervisão externa para retomar)
!reboot    — Reinicia o processo inteiro
!backup    — Backup operacional
!web       — Informações de acesso ao painel (apenas em conversa privada)

Regras de cooldown:
- Por grupo e por comando canônico, não apenas por usuário.
- Aliases compartilham cooldown; trocar argumentos não contorna o limite.
- Registrar cooldown após envio bem-sucedido; bloquear pedidos concorrentes do mesmo comando.
- Durante o cooldown, ignorar silenciosamente no grupo; persistir cooldowns para reboot não liberar flood.
- Aplicar limite agregado configurável, evitando alternância entre vários comandos.
- Administradores e owner podem consultar sem cooldown de usuário, mas preferencialmente recebem o resultado no privado.

Comandos não pontuam e não interrompem nem reiniciam as sequências usadas pelo minigame.

-------------------------------------------------------------------------------
6. Painel web administrativo
-------------------------------------------------------------------------------

Acesso apenas admin, localhost apenas, porta 2020 (ou a que estiver livre localmente).
Bind exclusivamente em 127.0.0.1; nunca mudar automaticamente para 0.0.0.0.
Login obrigatório com sessão e expiração; proteção CSRF nas ações de alteração.
Escape do conteúdo de mensagens exibidas; sem renderizar HTML fornecido pelos usuários.
Token do Telegram e segredos nunca aparecem no painel ou nos logs.

Páginas do painel:
- Visão geral (estatísticas, ciclo atual, grupos monitorados, módulos)
- Rankings (Top 10, filtro por semana, filtros avançados, pódio)
- Ciclos e rodadas (término estimado, participantes, pódios, filtros avançados)
- Participantes (lista com mensagens pontuadas, pontos totais, nome/@, ID, filtros avançados)
- Pontuação e regras (regras vigentes, valores de pontuação)
- Comandos e cooldowns (comandos registrados, cooldowns ativos)
- Módulos (lista com versão, estado, comandos — versionamento dinâmico via arquivo VERSION)
- Operação e diagnósticos (saúde, sincronização, fila, disponibilidade)
- Backups e exportações (JSONs gerados, importar backup com feedback de sucesso)
- Auditoria (log de !check, quem auditou, o que foi auditado, quem ganhou/perdeu pontos)
- Configurações e acesso (usuários, senhas, WEB_SECRET, portas, variáveis de ambiente)

Login persistente:
- Checkbox “Lembrar-me” no formulário de login.
- Se marcado: cookie com Max-Age de 30 dias.
- Se não marcado: cookie de sessão (1 hora / expira ao fechar o navegador).
- Credenciais sincronizadas do .env para a tabela web_users no SQLite.

Seletor de grupos integrado ao nav:
- Aparece em todas as páginas do painel (rankings, ciclos, participantes, operação, exportar, auditoria, config).
- Form com <select name="chat_id"> + onchange submit ao lado dos links de navegação.
- Não é mais um card separado; integrado ao layout da barra de navegação.

Filtros avançados:
- Rankings: posição (exata / ≥ / ≤), usuário (contém), ID (exato), pontos (≥ / ≤).
- Ciclos: estado, início de/até, participantes (≥ / ≤), pódios (≥).
- Participantes: usuário (contém), ID (exato), mensagens pontuadas (≥ / ≤), pontos totais (≥ / ≤).

Cache de HTML (navegação rápida entre abas):
- Páginas estáticas (regras, comandos, módulos, config) são cacheadas em memória (_STATIC_CACHE) com TTL de 300 segundos.
- Chave de cache inclui o chat_id selecionado (seletor de grupos).
- Cache invalidado ao salvar ou resetar configurações.

Cards e layout centralizado:
- Todos os cards do painel ocupam a mesma largura (sem max-width fixo diferente entre filtros e pódio).
- Container centralizado com max-width: 1200px e margin: 0 auto.
- Grid de stats da visão geral envolto em card “Visão geral”.

Importar backup:
- Página /painel/exportar permite importar arquivo JSON de snapshot gerado anteriormente.
- Após a importação, o bot redireciona com parâmetro ?imported=N e exibe alert de sucesso.
- Os dados são inseridos no ranking_messages e ranking_points com reason 'importado_backup'.
- A operação é registrada no audit_log com actor_id, parâmetros e resultado.

-------------------------------------------------------------------------------
7. Snapshot semanal e upload para repositório privado
-------------------------------------------------------------------------------

Thread de snapshot semanal executada em run.py:
- Gera arquivos JSON de snapshot para todos os grupos monitorados.
- Cada snapshot contém: chat_id, week_start, records, top10, dados dos participantes.
- Arquivo salvo em data/snapshots/ com nome snapshot_<chat_id>_<week_start>.json.
- Log gravado na tabela snapshot_log (id, chat_id, week_start, file_name, records, uploaded, upload_error, uploaded_at, created_at).

Upload automático para repositório privado:
- Configurado em config/config.env (NUNCA commitado):
    SNAPSHOT_REPO_URL=https://github.com/Amielle-Inside/snapshot-backups.git
    SNAPSHOT_REPO_BRANCH=main
    SNAPSHOT_REPO_USER=<usuario>
    SNAPSHOT_REPO_TOKEN=<PAT com acesso ao repositório privado>
- O bot inicializa o repositório local em data/snapshot_repo/, faz git add/commit/push para o remoto privado.
- Status do repositório exibido no painel (/painel/snapshots): “Configurado” ou “Não configurado”.
- Coluna de upload no log de snapshots mostra se foi enviado ou houve erro.
- O upload ocorre automaticamente ao gerar snapshots e também pode ser disparado manualmente pelo painel.

-------------------------------------------------------------------------------
8. Estrutura de pastas e arquivos
-------------------------------------------------------------------------------

/var/home/Amielle/apps/telegramrankinside/
├── VERSION                          # Versão atual (ex: 1.1.0)
├── config/config.env                # Token, owner IDs, web user/pass, port, TZ, SNAPSHOT_* (NUNCA commitar)
├── .env.example                     # Template com placeholders apenas
├── .gitignore                       # Exclui config.env, data/, __pycache__, logs, etc.
├── logica.md                        # Este documento
├── README.md                        # Documentação PT-BR completa
├── run.py                           # Ponto de entrada, orquestração, thread de snapshot, upload para repo privado
├── backfill_ranking.py              # Script de backfill de updates armazenados
├── bot/
│   ├── core/
│   │   ├── app.py                   # run_loop com dedup de update_id, process_update, cooldowns
│   │   ├── storage.py               # SQLite WAL, todas as tabelas core + web + snapshot_log
│   │   └── telegram.py              # Telegram API client, timeout 10s
│   └── modules/
│       └── ranking/
│           ├── __init__.py          # manifest, on_enable, create_handler
│           ├── manifest.py          # Lê versão dinamicamente do arquivo VERSION
│           ├── rules.py             # Valores de pontuação (+0.7, +1.1, -0.3, etc.)
│           ├── handlers.py          # Processamento de eventos de mensagem e scoring
│           ├── commands.py          # !rank, !rciclo, !pontos, !posicao, !historico, !regras, !ajuda, !status, !check, !stop, !reboot
│           └── storage.py           # Tabelas específicas do ranking
├── web/
│   └── panel.py                     # Painel HTML + sessão + CSRF + endpoints + filtros avançados + cache + snapshots
├── data/
│   ├── ranking.db                   # SQLite WAL (synchronous=FULL, foreign_keys=ON, busy_timeout=5000)
│   ├── snapshots/                   # Arquivos JSON de snapshot gerados
│   └── snapshot_repo/               # Repositório git local para upload de backups
├── docs/                            # GitHub Page (publicado em /docs do branch beta)
│   ├── index.html                   # Landing page completa
│   ├── assets/style.css             # CSS escuro moderno + lightbox
│   └── assets/prints/*.svg          # 8 prints representativos da interface (dados desidentificados)
└── .github/workflows/release.yml    # Auto-release em tags v* a partir da main

-------------------------------------------------------------------------------
9. Tabelas SQLite principais
-------------------------------------------------------------------------------

ranking_messages: mensagem, autor, grupo, tópico, texto, timestamps, resposta, encaminhamento, metadados de mídia
ranking_points: mensagem de origem, regra, valor, versão das regras, ajuste eventual
ranking_rounds: semana, início, fim, estado (aberta/em fechamento/fechada)
ranking_cycles: ciclo, início, fim estimado, participantes, elegibilidade, pódios, estado
audit_log: quem executou, quando, parâmetros, resultado
web_users: usuários do painel web (sincronizado do .env)
web_config: configurações editáveis pelo painel (chave, valor, escopo, versão)
snapshot_log: id, chat_id, week_start, file_name, records, uploaded, upload_error, uploaded_at, created_at

PRAGMA configurados:
journal_mode = WAL
synchronous = FULL
foreign_keys = ON
busy_timeout = 5000

-------------------------------------------------------------------------------
10. Arquitetura modular
-------------------------------------------------------------------------------

Núcleo (bot/core): conexão com Telegram, recebimento e distribuição de eventos, registro de comandos, permissões, cooldowns, configuração, logs, acesso à persistência.

Módulo ranking (bot/modules/ranking): regras, pontuações, ciclos, comandos e armazenamento próprios. Cada módulo declara identificador único, versão, comandos, eventos utilizados e configurações.

Módulos não acessam diretamente tabelas/funções internas uns dos outros; usam interfaces ou eventos definidos pelo núcleo. Falhas em um módulo são tratadas e registradas sem interromper os demais. Ao desabilitar, comandos e tarefas param, mas dados são preservados.

Caches, filas, tarefas concorrentes, conexões, logs e arquivos temporários possuem limites configuráveis. Recursos são liberados ao concluir tarefas ou desativar módulos.

-------------------------------------------------------------------------------
11. Testes exigidos antes de produção
-------------------------------------------------------------------------------

Mesmo update entregue duas vezes → pontua uma única vez.
Queda depois de persistir o evento, antes de pontuar → retoma o processamento.
Queda depois de pontuar, antes de exportar → regenera o JSON.
Reboot durante fechamento semanal → não duplica rodada ou pódio.
Edição de mensagem antiga → aplica a política de revisão correta.
Dois !rank simultâneos → uma única publicação.
!check enquanto chegam mensagens → mantém coleta e resultado consistente.
Relógio local incorreto → não fecha períodos indevidamente.
Offline além da retenção do Telegram → sinaliza cobertura incompleta.
Disco cheio → alerta; não confirma eventos que não conseguiu persistir.
Usuário comum chama comando administrativo → não executa e não expõe informações.
Restauração de backup → reconstrói ranking, ciclo e exportações.

Requisito central: todo ponto deve ser rastreável até sua origem e versão de regra; todo evento persistido deve poder ser reprocessado sem duplicação; toda limitação de cobertura deve ficar explícita para a administração.

-------------------------------------------------------------------------------
12. GitHub Page
-------------------------------------------------------------------------------

Publicada em: https://amielle-inside.github.io/TelegramRankInside/
Fonte: branch beta, pasta /docs
Conteúdo: sobre o projeto, funcionalidades, prints da interface (com lightbox para ampliar), tecnologia, como usar.
Dados sensíveis desidentificados com ████████ nos prints.
Token e senhas nunca são versionados.

-------------------------------------------------------------------------------
13. Supervisão e reinicialização
-------------------------------------------------------------------------------

systemd supervisiona o processo (sem executar como root).
!stop: encerrar de forma limpa e permanecer parado (retomada só pelo supervisor).
!reboot: encerrar de forma limpa e ser iniciado novamente pelo supervisor.
Reboot da máquina: serviço inicia automaticamente.
Falha inesperada: reinício com atraso e limite contra loop.

Após um !stop verdadeiro, o bot não está disponível para receber comando de ligar; a retomada ocorre pelo supervisor ou mecanismo independente.