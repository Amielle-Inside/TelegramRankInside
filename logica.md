É um minigame para ranking de quem posta em supergrupos no telegram:

Todos os arquivos e tudo referente ao bot precisa ser gravado, salvo e gerenciado na pasta:
/var/home/Amielle/apps/telegramrankinside/

sendo assim a logica completa atual do bot:

Faça da seguinte forma:

Exemplos de pontuação

Uma mensagem de texto iniciando uma participação	+0,7

Uma resposta com texto à mensagem de outra pessoa, fora de sequência própria	+1,1

Três mensagens de texto consecutivas, sem bônus de resposta	+0,9 no total: 0,7 + 0,1 + 0,1

Uma quarta mensagem de texto nessa sequência	−0,1

Um vídeo com uma explicação própria, fora de sequência	+0,7

Um link sem comentário	−0,3

Três encaminhamentos consecutivos	−0,6 no total: 0 − 0,3 − 0,3

Dois cuidados para o ranking

    Mensagens idênticas repetidas pela mesma pessoa em um intervalo definido, por exemplo 10 minutos, não devem gerar novos pontos positivos nem bônus.

    pontos positivos concedidos e manter eventuais penalidades, deixando essa regra explícita para os participantes.

A principal mudança é esta: premiar a primeira contribuição, permitir pequenos complementos e reduzir o ganho de quem fragmenta mensagens. O bônus de resposta mantém o incentivo à interação, mas não transforma qualquer “reply” em pontos extras.

top 10 semanal com pódio rotativo
1. Pontuação reiniciada toda semana

    O ranking considera apenas os pontos daquela semana.

    No encerramento, o bot registra o resultado e começa uma nova rodada com zero pontos.

    As conquistas anteriores ficam no histórico, sem somar vantagem na rodada seguinte.

Reinícios periódicos são uma forma de evitar que a vantagem acumulada torne o ranking inacessível a quem entrou depois

Quem terminar no top 3 passa uma rodada fora do pódio

Minha regra inicial seria:

    Quem encerrar a semana no top 3 continua pontuando normalmente na semana seguinte, mas fica temporariamente inelegível às posições de 1º a 3º.

Na semana de intervalo:

    A pessoa pode aparecer do 4º ao 10º lugar.

    Não perde pontos nem recebe penalidade nas mensagens.

    O bot indica “pódio na rodada anterior”.

    Na rodada seguinte, volta a disputar o pódio normalmente.
    
    Isso exige deixar claro que a classificação considera pontuação e elegibilidade: alguém com mais pontos pode aparecer abaixo de alguém com menos pontos por estar no intervalo do pódio.
    
    Para todos terem vez, use ciclos de pódio

O intervalo de uma semana, sozinho, ainda permite que dois grupos de participantes se alternem e deixem os demais de fora. Se sua intenção é realmente dar uma oportunidade a todos, eu acrescentaria:

    Durante um ciclo, quem ainda não terminou nenhuma rodada no top 3 tem prioridade sobre quem já terminou.
    
    O funcionamento seria:

    Você define os participantes elegíveis do ciclo.

    A cada semana, as três vagas do pódio vão para os participantes com mais pontos entre aqueles que ainda não passaram pelo pódio naquele ciclo.

    Quem conquista uma vaga continua participando do top 10, mas deixa de disputar o pódio até a renovação do ciclo.

    Quando todos os participantes elegíveis tiverem passado pelo pódio, começa um novo ciclo.
    
    Se houver dez participantes fixos e todos mantiverem a participação exigida, serão necessárias quatro rodadas para todos passarem pelo pódio. Na quarta rodada, a pessoa restante recebe prioridade; as outras duas vagas podem ser preenchidas por pontuação entre os demais.

Eu escolheria esse sistema de ciclos no lugar do intervalo de uma semana se a passagem de todos pelo top 3 for uma exigência, não apenas um desejo.

Quem pode participar desse rodízio?

Eu não daria uma vaga garantida para qualquer conta que envie uma única mensagem. Como ponto de partida, proponho estes critérios:
Critério	Regra sugerida
Participação mínima	Ter mensagens que pontuem positivamente em pelo menos 3 dias da semana
Saldo	Terminar a semana com pontuação positiva
Entrada no ciclo	Participantes definidos no início; novos participantes entram no próximo
Inatividade	Quem não cumprir os critérios não bloqueia o encerramento do ciclo
Desempate	Menos pódios no histórico; depois, mais dias com participação positiva

Esses números são parâmetros sugeridos para o seu minigame, não uma regra universal. O requisito de dias diferentes serve para valorizar presença distribuída, em vez de uma rajada de mensagens em um único dia.

A garantia, portanto, seria: todos os inscritos no ciclo que continuarem cumprindo os critérios terão vez. Não seria uma garantia para contas inativas ou para quem só enviar conteúdo penalizado.

Separe pontuação de destaque

Para evitar a sensação de “fui bem e fui punido”, eu mostraria duas informações:

    Pódio da rodada: aplica o rodízio e distribui o destaque.

    Pontuação da semana: mostra os pontos reais de cada participante, inclusive de quem está fora da disputa pelo pódio.
    
    PÓDIO DA SEMANA
1. Ana — 24 pontos
2. Bruno — 21 pontos
3. Carla — 18 pontos

DEMAIS PARTICIPANTES
4. Diego — 35 pontos | Já conquistou pódio neste ciclo
5. Elisa — 30 pontos | Já conquistou pódio neste ciclo
6. Fábio — 16 pontos
...

Assim, Diego não perde os 35 pontos nem tem sua contribuição escondida; apenas não ocupa novamente uma vaga de destaque naquele ciclo.


Garanta que o bot mesmo que reiniciado possa garantir as pontuações após um reboot e use horario NTP como forma de validar o horario, tempo online, tempo offline, dia, semana, mês e ano, e guardar a mensagem de todo mundo em um sqlite para justamente
conseguir ter as mensagens comprovadas, Após reiniciar, o bot deve restaurar integralmente o estado persistido e processar os updates ainda disponíveis no Telegram, sem duplicação. Quando houver possibilidade de perda de eventos, deve registrar o intervalo como cobertura incompleta e informar a administração

Também não use “pulos” em message_id como prova de mensagens perdidas: registre uma suspeita de lacuna, não invente mensagens ou pontos.
Exclusões não são totalmente observáveis

A Bot API expõe eventos de edição de mensagens conhecidas, mas não oferece um update geral de exclusão de mensagens comuns de supergrupos; o evento deleted_business_messages pertence a conexões de contas comerciais.

Deixe o bot ser o mais leve possivel e que não haja acumulo de recursos da maquina

sempre grave em um json as colocações atuais, passadas e as que estão ocorrendo

o bot precisa ter comandos para checar algumas coisas, o comando sempre começara com !, por exemplo:
!rank exibe o rank atual, !rciclo exibibe o rank do ciclo atual, precisa ter os comandos de todos os
tipos de checagem, porem nao pode ser floodado, cada comando unico, por exemplo !rank so pode exibir uma
vez a cada 5minutos, mas administradores owner pode checar a qualquer momento.

precisa de ter comandos de apenas administradores:

!stop para o bot

!reboot reinicia o bot

!check reanalisa as mensagens, vê se algo for perdido, reconta e acaba dando/removendo pontos conformes as regras

o bot precisa ter uma pagina de acesso apenas adm, localhost, porta 2020 ou a que estiver livre localmente, assim havendo
o comando que apenas a owner pode ver, vai responder somente na pagina no bot e nao no grupo e o comando pode ser dado dentro
do bot tambem que é !web


comandos para adm e owner, somente adm e owners podem enxergas a existencia deles.

QLite oficial; JSON derivado

Eu evitaria que banco e JSON fossem duas fontes independentes de pontuação.

text
Updates recebidos
       ↓
SQLite: eventos persistidos
       ↓
Motor de regras
       ↓
Pontuações e classificação no SQLite
       ↓
Exportações JSON e comandos de consulta

O que persistir
Conjunto	Dados essenciais
Eventos recebidos	update_id, tipo, conteúdo recebido, data de recebimento e estado de processamento
Mensagens	Grupo, tópico, mensagem, autor, texto/legenda, timestamps, resposta, encaminhamento e metadados de mídia
Revisões	Versões recebidas de cada mensagem editada
Lançamentos de pontos	Mensagem de origem, regra, valor, versão das regras e eventual ajuste
Rodadas e ciclos	Início, fim, participantes, elegibilidade, pódios e estado de fechamento
Estado operacional	Cursor de updates, cooldowns, tarefas em andamento e exportação pendente
Auditoria	Quem executou uma ação, quando, parâmetros e resultado

Use user_id como identidade, não @username. Para mensagens, a chave deve incluir chat_id e message_id, porque o identificador da mensagem é único dentro do chat.
Evitar duplicação após uma queda

Exija este comportamento:

    Receber o mesmo evento novamente não pode gerar novos pontos.

No long polling, grave duravelmente os updates antes de avançar o offset que os confirma no Telegram. A API considera um update confirmado quando recebe um offset maior que seu update_id.

Uma arquitetura simples é persistir primeiro o evento e deixar um processador consumir os eventos pendentes. Se cair entre essas etapas, ele continua depois.
Configuração do banco

Para priorizar durabilidade, eu começaria com:

PRAGMA journal_mode = WAL;
PRAGMA synchronous = FULL;
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 5000;

WAL permite leitura e escrita concorrentes, mas continua havendo apenas um escritor por vez. synchronous=FULL sincroniza o WAL a cada commit; com NORMAL, commits recentes podem ser revertidos após falta de energia ou reinicialização brusca. Use armazenamento local e uma versão do SQLite com as correções de WAL aplicadas.

Isso não substitui backup nem protege contra defeito físico do armazenamento.
Como manter os JSONs

Sugestão:

    Snapshot atual: atualizado com um pequeno atraso configurável, por exemplo até 5 segundos após mudanças.

    Snapshot de rodada encerrada: gerado no fechamento.

    Snapshot de ciclo encerrado: gerado no fechamento.

    Cada exportação contém schema_version, rules_version, horário e revisão do estado.

    Gravação em arquivo temporário e substituição atômica do arquivo final.

    Se a exportação falhar, registrar pendência e tentar novamente.

    Na inicialização, regenerar exportações ausentes ou desatualizadas a partir do SQLite.

Não regrave todo o histórico a cada mensagem. E não use o JSON para “corrigir” o banco automaticamente.

 Horário: separar calendário, duração e disponibilidade

Eu mudaria “usar horário NTP para tudo” para:

    O sistema operacional deve manter o relógio sincronizado por NTP. O bot deve usar timestamps UTC para persistência, um fuso configurado para calendário e um relógio monotônico para medir durações durante a execução.
    
    proponho:
Finalidade	Regra
Armazenamento	UTC
Calendário do ranking	America/Sao_Paulo
Semana	Segunda-feira, 00:00, até a segunda seguinte
Mês e ano	Limites reais do calendário
Data da mensagem	Timestamp enviado pelo Telegram
Data de recebimento	Relógio local sincronizado
Duração de tarefas e cooldown na execução	Relógio monotônico
Cooldown após reboot	Prazo persistido, validado com relógio sincronizado


O Telegram fornece date em Unix time nas mensagens; preserve esse horário separadamente da hora em que o bot recebeu o evento.

O Telegram fornece date em Unix time nas mensagens; preserve esse horário separadamente da hora em que o bot recebeu o evento.

Defina ainda:

    Se o relógio estiver claramente incorreto, continuar recebendo e armazenando eventos, mas adiar fechamentos automáticos.

    Após voltar de uma queda, verificar quais rodadas venceram; não depender apenas de um timer que pode não ter executado.

    Separar “processo ligado” de “conexão com Telegram funcionando”.

    Persistir um heartbeat, por exemplo a cada 60 segundos.

    Em queda abrupta, apresentar o início da indisponibilidade como estimado entre o último heartbeat e a detecção, não como horário exato.

Uma rodada também deve ter estado aberta, em fechamento ou fechada, para um reboot não produzir dois pódios.

O !check precisa ter escopo e resultado previsível

Eu definiria:

    O !check reprocessa os eventos persistidos usando a versão de regras aplicável ao período, compara o resultado com os saldos existentes e registra as diferenças encontradas.

Fluxo recomendado:

    Selecionar grupo e período.

    Fixar uma revisão dos dados para a auditoria.

    Recalcular em estruturas separadas, sem apagar o ranking atual.

    Mostrar diferenças e limitações de cobertura.

    Aplicar os ajustes em transação após confirmação administrativa.

    Regenerar os JSONs.

Exemplo:

!check semana
!check ciclo
!check periodo 2026-11-01 2026-11-07
!check status
!check aplicar <id>

Requisitos importantes:

    Só uma recontagem ativa por grupo.

    Recepção de novas mensagens continua funcionando.

    O cálculo respeita ordem, sequências, duplicações e edições.

    Alterar uma mensagem pode exigir recalcular outras relacionadas, não só aquela mensagem.

    Rodadas antigas usam suas regras antigas por padrão.

    Corrigir uma rodada encerrada cria uma revisão auditada; não reescreve silenciosamente os vencedores.

E mantenha as duas coisas separadas: receber updates pendentes é sincronização; recalcular o que foi armazenado é auditoria.


Comandos e controle de flood
Consultas públicas

Eu começaria com este conjunto, sem criar comandos demais:
Comando	Resultado
!rank	Top 10 da rodada atual
!rciclo	Situação do ciclo, pódios conquistados e elegibilidade
!pontos	Pontuação do próprio usuário
!posicao	Posição e situação no rodízio
!historico	Rodadas e pódios anteriores
!regras	Regras vigentes
!ajuda	Comandos públicos

Cooldown

Sua regra deve ser por grupo e por comando, não apenas por usuário:

text
(chave do grupo, comando canônico) → próxima execução pública permitida

Assim, se alguém usar !rank, outra pessoa não consegue repetir o mesmo resultado imediatamente.

Eu acrescentaria:

    Aliases compartilham cooldown.

    Trocar argumentos não pode contornar o limite.

    Registrar o cooldown após envio bem-sucedido.

    Bloquear pedidos concorrentes do mesmo comando.

    Durante o cooldown, ignorar silenciosamente no grupo.

    Persistir cooldowns para reboot não liberar flood.

    Aplicar também um limite agregado configurável, evitando alternância entre vários comandos.
    
    Administradores e owner podem consultar sem cooldown de usuário, mas preferencialmente recebem o resultado no privado. “Sem cooldown” não deve significar fila ilimitada de trabalho ou ignorar limites da API.

Comandos não pontuam e não interrompem nem reiniciam as sequências usadas pelo minigame.

Permissões e comandos administrativos

Separe três papéis:

    Owner do bot: IDs definidos na configuração, com controle global.

    Administrador do grupo: controle apenas dos grupos em que tem autorização.

    Participante: consultas públicas.

Não trate automaticamente o dono de um grupo como owner global do bot.

| Comando          | Permissão sugerida | Comportamento                                      |
| ---------------- | ------------------ | -------------------------------------------------- |
| !status          | Admin/owner        | Saúde, sincronização, fila e disponibilidade       |
| !check           | Admin/owner        | Auditoria limitada ao grupo autorizado             |
| !export          | Admin/owner        | Exportação do grupo autorizado                     |
| !pause / !resume | Admin/owner        | Pausar/retomar pontuação do grupo, mantendo coleta |
| !stop            | Owner por padrão   | Parar o processo inteiro                           |
| !reboot          | Owner por padrão   | Reiniciar o processo inteiro                       |
| !backup          | Owner              | Backup operacional                                 |
| !web             | Owner              | Informações de acesso ao painel                    |

Se o bot atender vários grupos, dar !stop a qualquer administrador permite que uma pessoa derrube o serviço de todos. Se você quiser manter essa permissão para admins, torne-a uma autorização explícita na configuração.
Esconder não é proteger

Ajustaria seu requisito para:

    Comandos administrativos não aparecem na ajuda pública. Sua execução exige autorização em todas as interfaces. Consultas e respostas administrativas devem ocorrer em conversa privada ou no painel.
    
    Se alguém digitar literalmente !stop no grupo como mensagem comum, o próprio texto já estará visível aos membros. Portanto, não prometa invisibilidade para comandos comuns enviados no grupo.

O prefixo ! deve ser tratado pelo parser do seu aplicativo; não dependa apenas do menu de comandos nativos do Telegram.

Também rejeite comandos privilegiados cuja autoria individual não possa ser validada, como mensagens enviadas em nome de um chat por um administrador anônimo. A Bot API distingue esses casos por sender_chat

Eu resolveria a ambiguidade de “responder somente na página no bot” assim:

    !web só é aceito em conversa privada com o bot, por um owner autorizado. O bot informa o endereço local e as instruções de acesso. Nada é publicado no grupo. O painel exige autenticação própria.
    
    Requisitos sugeridos:

    Bind exclusivamente em 127.0.0.1.

    Porta preferencial 2020.

    Se ocupada, tentar uma faixa pequena e configurada, registrando a porta efetivamente aberta.

    Nunca mudar automaticamente para 0.0.0.0.

    Login obrigatório, sessões com expiração e proteção contra tentativas repetidas.

    Proteção CSRF nas ações de alteração.

    Escape do conteúdo de mensagens exibidas, sem renderizar HTML fornecido pelos usuários.

    Token do Telegram e segredos nunca aparecem no painel ou nos logs.

    Ações destrutivas exigem confirmação e entram na auditoria.

Se o bot estiver em um servidor, localhost no seu computador não aponta para esse servidor. Uma forma de manter o painel local é acessá-lo por túnel SSH:

ssh -N -L 2020:127.0.0.1:2020 usuario@servidor

O comando precisa usar a porta real caso ela tenha sido alterada.
8. !stop e !reboot precisam de supervisão externa

Defina o comportamento antes de implementar:

    !stop: encerrar de forma limpa e permanecer parado.

    !reboot: encerrar de forma limpa e ser iniciado novamente pelo supervisor.

    Reboot da máquina: serviço inicia automaticamente.

    Falha inesperada: reinício com atraso e limite contra loop.

Eu usaria systemd para supervisionar o processo, sem executar o bot como root.

No desligamento:

    Parar de aceitar novas tarefas administrativas.

    Finalizar transações em andamento.

    Manter eventos ainda não processados persistidos.

    Tentar atualizar exportações pendentes.

    Registrar motivo da parada e fechar conexões.

Um detalhe operacional: depois de um !stop verdadeiro, o próprio bot não estará disponível para receber um comando de ligar. A retomada precisa ocorrer pelo supervisor ou por outro mecanismo independente. O mesmo vale para o painel se ele estiver no mesmo processo.
9. Leveza, crescimento e comprovação

“Não acumular recursos” precisa virar limites verificáveis:

    Fila com tamanho máximo e política de pressão.

    Cache com tamanho máximo e expiração.

    Pool pequeno de conexões e escrita serializada.

    Consultas indexadas e paginadas.

    Logs com rotação.

    Retentativas com atraso progressivo.

    Monitoramento de espaço em disco.

    Política de retenção de mensagens, revisões, JSONs e backups.

    Testes periódicos de restauração.

No WAL, transações de leitura muito longas podem impedir a conclusão de checkpoints e favorecer crescimento do arquivo. Evite deixar consultas do painel abertas indefinidamente. Não apague arquivos -wal manualmente.

Para mídia, eu armazenaria metadados e identificadores por padrão, sem baixar todos os arquivos. Mas deixe a consequência clara: identificadores não equivalem a um arquivo de mídia preservado localmente.

Também reformularia “mensagens comprovadas”:

    O banco fornece evidências operacionais do que o bot recebeu e de como calculou os pontos. Não é, por si só, uma prova independente contra alterações feitas por quem controla o servidor.

Avise os participantes sobre o armazenamento e defina quem pode consultar o conteúdo. Guardar todas as mensagens para sempre conflita com a ideia de crescimento controlado.
10. Testes que eu exigiria antes de colocar em produção
Teste	Resultado esperado
Teste	Resultado esperado
Mesmo update entregue duas vezes	Pontua uma única vez
Queda depois de persistir o evento, antes de pontuar	Retoma o processamento
Queda depois de pontuar, antes de exportar	Regenera o JSON
Reboot durante fechamento semanal	Não duplica rodada ou pódio
Edição de mensagem antiga	Aplica a política de revisão correta
Dois !rank simultâneos	Uma única publicação
!check enquanto chegam mensagens	Mantém coleta e resultado consistente
Relógio local incorreto	Não fecha períodos indevidamente
Offline além da retenção do Telegram	Sinaliza cobertura incompleta
Disco cheio	Alerta; não confirma eventos que não conseguiu persistir
Usuário comum chama comando administrativo	Não executa e não expõe informações
Restauração de backup	Reconstrói ranking, ciclo e exportações

O requisito central que eu adicionaria ao seu documento é:

    Todo ponto deve ser rastreável até sua origem e versão de regra; todo evento persistido deve poder ser reprocessado sem duplicação; toda limitação de cobertura deve ficar explícita para a administração.
    
    Texto curto para !ajuda:

text
O ranking premia participação com conteúdo e interação. Texto próprio vale +0,7; resposta a outra pessoa pode ganhar +0,4 extra. Mídia/link sem contexto perde 0,3. Mensagens consecutivas têm ganho reduzido e podem perder pontos; encaminhamentos não pontuam e, quando repetidos na sequência, perdem pontos.

A pontuação reinicia semanalmente. O top 3 tem rodízio por ciclo: quem ainda não conquistou pódio tem prioridade, desde que cumpra os critérios de participação.

Comandos:
!rank — Top 10 da semana.
!rciclo — Ciclo atual e elegibilidade ao pódio.
!pontos — Seus pontos.
!posicao — Sua posição e situação no rodízio.
!historico — Resultados anteriores.
!regras — Regras completas.
!ajuda <comando> — Explicação de um comando.

Consultas públicas: uma execução por comando a cada 5 minutos no grupo.

Lógica da ajuda

    !ajuda → mostra o texto acima.

    !ajuda rank ou !ajuda !rank → explica somente o comando solicitado.

    Comando desconhecido → responde: Comando não encontrado. Use !ajuda para consultar a lista.

    Ajuda pública não lista comandos administrativos; ajuda específica deles só responde em ambiente privado e após autorização.

    A ajuda também respeita cooldown para não gerar flood.
    
    Exemplo de resposta para !ajuda rciclo:
    
    !rciclo mostra o ciclo atual, quem já conquistou pódio e quem ainda tem prioridade para o top 3. Quem já passou pelo pódio continua pontuando, mas cede prioridade aos demais participantes elegíveis.
    
O bot deve ter arquitetura modular, permitindo adicionar novas funcionalidades sem modificar a lógica interna do ranking.

O núcleo deve cuidar apenas dos serviços compartilhados: conexão com o Telegram, recebimento e distribuição de eventos, registro de comandos, permissões, cooldowns, configuração, logs e acesso à persistência.

O ranking deve ser um módulo independente, contendo suas próprias regras, pontuações, ciclos, comandos e estruturas de armazenamento. Novos módulos devem seguir o mesmo padrão e poder ser habilitados ou desabilitados individualmente por configuração, inclusive por grupo.

Cada módulo deve declarar um identificador único, versão, comandos, eventos utilizados e configurações. O núcleo deve detectar conflitos de comandos e impedir a ativação de configurações incompatíveis.

Os módulos não devem acessar diretamente as tabelas ou funções internas uns dos outros. Quando precisarem interagir, devem usar interfaces ou eventos definidos pelo núcleo.

Falhas em um módulo devem ser tratadas e registradas sem interromper desnecessariamente os demais. Ao desabilitar um módulo, seus comandos e tarefas devem parar, mas seus dados devem ser preservados.

A instalação de módulos poderá exigir reiniciar o bot; não é necessário implementar carregamento dinâmico nesta etapa.

Estrutura ilustrativa

bot/
├── core/
│   ├── telegram
│   ├── events
│   ├── commands
│   ├── permissions
│   ├── cooldowns
│   ├── storage
│   └── modules
├── modules/
│   └── ranking/
│       ├── manifest
│       ├── handlers
│       ├── commands
│       ├── rules
│       ├── storage
│       └── migrations
└── config/

Deve ser possível adicionar um módulo de exemplo com um comando próprio, habilitá-lo e desabilitá-lo sem alterar os arquivos do módulo de ranking. O ranking deve continuar funcionando normalmente, mantendo seus dados, permissões e resultados.

O bot e todos os seus módulos devem priorizar baixo consumo de CPU, RAM, disco e rede, sem uso de GPU no funcionamento padrão.

A persistência não pode depender de manter dados em memória: estados necessários à recuperação devem ser gravados no SQLite. Reiniciar, desabilitar ou atualizar um módulo não deve apagar seus dados nem duplicar operações já concluídas.

O núcleo deve compartilhar conexão com o Telegram, agendamento, acesso ao banco, logs e controle de tarefas. Cada módulo deve utilizar esses serviços, evitando criar conexões, threads, processos ou temporizadores próprios sem necessidade.

O processamento deve ocorrer por eventos ou tarefas agendadas, sem loops de consulta contínua. Módulos desabilitados não devem manter tarefas, filas ou processamento em segundo plano.

Caches, filas, tarefas concorrentes, conexões, logs e arquivos temporários devem possuir limites configuráveis. Recursos devem ser liberados ao concluir tarefas, cancelar operações ou desativar módulos.

Consultas e reprocessamentos devem trabalhar em lotes limitados, sem carregar todo o histórico em memória. Rankings devem ser atualizados incrementalmente; recontagens completas devem ocorrer apenas quando necessárias.

Os JSONs devem ser exportações do banco, atualizados apenas quando houver alterações e com agrupamento de mudanças, evitando regravações repetidas do mesmo conteúdo.

A redução de consumo não pode comprometer a durabilidade: eventos recebidos devem ser persistidos antes de serem confirmados, e tarefas interrompidas devem poder continuar após reinicialização.

O armazenamento deve ter políticas configuráveis de retenção, backup e manutenção. Dados necessários à auditoria não podem ser apagados silenciosamente para liberar espaço.

O sistema deve registrar métricas leves de consumo e detectar crescimento contínuo de memória, filas, tarefas ou arquivos, emitindo alertas quando os limites forem atingidos.

Comportamento quando faltar recurso

Eu acrescentaria uma ordem de prioridade explícita:

    Preservar o recebimento e a gravação dos eventos.

    Manter o processamento essencial.

    Adiar exportações, relatórios e manutenção.

    Impedir novas tarefas pesadas enquanto houver sobrecarga.

    Se não conseguir persistir, registrar a falha e não confirmar o evento como salvo.
    
    Nenhum módulo deve descartar silenciosamente dados para “ficar leve”.

No SQLite, também é necessário acompanhar checkpoints e o tamanho do WAL: leituras prolongadas podem impedir sua reciclagem e provocar crescimento contínuo do arquivo. Não basta limitar apenas o tamanho do banco principal.


Em testes prolongados com carga estável, memória, quantidade de tarefas, conexões e filas devem permanecer dentro de limites definidos, sem crescimento contínuo injustificado. Ao encerrar uma tarefa ou desabilitar um módulo, os recursos associados devem ser liberados. Após reinicialização, todos os módulos devem recuperar seu estado persistido sem perda ou duplicação.

Os limites numéricos devem ser definidos após medir uma versão funcional. Evite exigir um valor arbitrariamente baixo antes de conhecer a linguagem, as bibliotecas e o volume de mensagens.

E mantenha esta distinção no documento: CPU representa trabalho executado; RAM representa memória ocupada; disco representa histórico armazenado. Guardar mensagens indefinidamente inevitavelmente aumenta o uso de disco — para controlar isso, será necessário definir retenção ou arquivamento, não apenas otimizar os scripts.


Após o login, o sistema deve apresentar uma interface web completa de gerenciamento, com navegação, tabelas, filtros, formulários e botões de ação. Não deve exibir respostas JSON como interface principal.

As rotas de páginas devem apresentar conteúdo visual; endpoints JSON devem ser separados e utilizados internamente pela interface.

O painel deve permitir acompanhar e configurar o bot sem editar manualmente arquivos ou executar comandos no terminal, exceto em procedimentos de recuperação ou manutenção externa.

A interface deve informar claramente quando uma operação foi concluída, falhou, está aguardando processamento ou exige reinicialização.

Visão geral
Rankings
Ciclos e rodadas
Participantes
Pontuação e regras
Comandos e cooldowns
Módulos
Operação e diagnósticos
Backups e exportações
Auditoria
Configurações e acesso


 Auditoria
 Configurações e acesso
 
+A página inicial deve mostrar:
+
+    Estado: funcionando, pausado, reconectando ou com falha.
+
+    Tempo desde a inicialização.
+
+    Último evento recebido e último evento processado.
+
+    Quantidade de eventos pendentes.
+
+    Grupos monitorados e módulos ativos.
+
+    Rodada e ciclo atuais.
+
+    Estado da sincronização do relógio.
+
+    Intervalos com possível perda de cobertura.
+
+    Uso de memória, CPU e armazenamento.
+
+    Tamanho do banco, WAL, logs e backups.
+
+    Alertas recentes e tarefas em execução.
+
+Inclua um seletor de grupo no topo. Uma configuração de um grupo não deve afetar outro sem uma ação explícita.


O login não basta: cada endpoint de consulta ou alteração deve validar a autorização do usuário. A OWASP recomenda verificar privilégios em cada requisição e restringir funções administrativas aos usuários autorizados.


Inclua:

    Perfis separados de consulta, administração do grupo e owner.

    Expiração de sessão e logout com invalidação no servidor.

    Renovação da sessão após autenticação.

    Reautenticação para operações críticas.

    Proteção CSRF nas ações de alteração.

    Segredos mascarados e nunca incluídos em exportações comuns.

    Histórico de alterações com autor, data, escopo e valores anteriores/novos.
    
    As medidas de sessão, reautenticação e proteção de operações sensíveis seguem as orientações da OWASP para aplicações autenticadas.
    
    Mantenha o acesso local definido anteriormente; exposição externa deve ser uma decisão explícita, não um efeito colateral da configuração.
    
    Para manter seu requisito de economia:
    
    A interface deve usar tabelas paginadas, filtros processados no servidor e atualização apenas das informações necessárias. Não deve carregar todo o histórico, recalcular rankings a cada abertura ou manter consultas contínuas quando a aba estiver inativa.

Atualizações automáticas devem ter intervalo configurável e poder ser pausadas. Operações pesadas devem executar em segundo plano com fila limitada e progresso visível.

A interface pode ser simples, renderizada no servidor e com JavaScript mínimo; não é obrigatório utilizar um framework pesado para oferecer um painel completo.

O portal deve ser um painel administrativo visual completo, não uma exibição de JSON. Deve permitir consultar rankings e evidências de pontuação, gerenciar ciclos, participantes, comandos e módulos, ajustar regras e acompanhar a saúde do bot.

Todas as configurações operacionais suportadas devem ser editáveis pela interface, com validação, escopo global ou por grupo, persistência, versionamento e auditoria. Alterações devem indicar quando passam a valer e se exigem reinicialização.

Restaurar valores padrão não pode apagar dados ou alterar resultados históricos. Recontagens e mudanças retroativas devem ser operações separadas, precedidas de simulação e confirmação.

O painel deve permanecer leve, seguro e integrado aos serviços do núcleo, sem duplicar a lógica do ranking ou criar uma segunda fonte de dados.


