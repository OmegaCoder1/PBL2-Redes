<h1 align="center">🚗⚡ Sistema Distrbuído e Inteligente de Gerenciamento de Pontos de Recarga para Veículos Elétricos</h1>

<h2>📚 Descrição do Projeto</h2>

<p>
  Este projeto foi desenvolvido como parte da disciplina de <b>TEC 502 - MI Concorrência e Conectividade</b>, com o objetivo de simular um sistema distrbuído e inteligente de gerenciamento de pontos de recarga de veículos elétricos (EV - Electric Vehicle).
</p>

<p>
  A solução foi desenvolvida utilizando o protocolo <b><i>Machine-to-Machine<i> (M2M)</b> e comunicação via <b>MQTT (<i>Message Queue Telemetry Transport<i>)</b>, através do uso de <b>API <i>Rest<i></b> e testado com o <b><i>Portainer<i></b>.
</p>

<p>
  O sistema tem como principal objetivo fornecer aos motoristas informações em tempo real sobre pontos de recarga, realizar reservas remotas e atômicas e distribuir de maneira eficiente a demanda entre diferentes postos sediados por diferentes servidores.
</p>

<hr/>

<h2>📝 Contexto do Problema</h2>

<p>
🚗⚡ No projeto anterior, desenvolvemos um sistema inteligente de carregamento para veículos elétricos, focado em pontos de recarga urbanos.

🌍 Agora, o desafio é outro: viabilizar viagens de longa distância (entre cidades e estados) com paradas planejadas e seguras para recarga. Usuários enfrentam dificuldades em garantir que haverá carregadores disponíveis ao longo de toda a rota.

🎯 O objetivo é permitir que o cliente possa:
<ul>
  <li>🔍 Consultar a disponibilidade de vários pontos de recarga em sequência</li>
  <li>📆 Realizar reservas antecipadas com horários definidos</li>
  <li>⚙️ Enviar uma única requisição atômica para garantir todas as reservas de uma vez</li>
</ul>

🧠 Para isso, a comunicação entre servidores de diferentes empresas conveniadas deve ser padronizada, utilizando uma API REST desenvolvida pela equipe.

📦 Exemplo prático:
Um cliente quer viajar de <strong>João Pessoa</strong> até <strong>Feira de Santana</strong>. Ele inicia a requisição pelo servidor da empresa A e:
<ul>
  <li>Reserva um ponto entre João Pessoa e Maceió (empresa A)</li>
  <li>Outro entre Maceió e Sergipe (empresa B)</li>
  <li>Outro entre Sergipe e Feira de Santana (empresa C)</li>
</ul>

🔐 A reserva é sequencial e priorizada: o cliente que inicia o processo deve manter sua prioridade nos pontos seguintes. Isso garante uma viagem sem interrupções por falta de energia, evitando atrasos e falhas no trajeto.
</p>


<h3>Principais Problemas Identificados:</h3>

<ul>
  <li>Problemas identi.</li>
</ul>

<hr/>

<h2>🎯 Objetivos da Solução</h2>

<ul>
  <li>✅ Desenvolver um sistema de reserva antecipada de múltiplos pontos de recarga para veículos elétricos em rotas intermunicipais e interestaduais</li>
  
  <li>🔄 Garantir que todas as reservas sejam feitas de forma atômica — ou todas são confirmadas ou nenhuma é mantida — evitando paradas inesperadas</li>
  
  <li>🌐 Padronizar a comunicação entre servidores de diferentes empresas por meio de MQTT e  API REST </li>
  
  <li>🧠 Permitir que o sistema calcule a rota ideal do cliente, identifique os pontos necessários e realize as reservas automaticamente</li>
  
  <li>🔒 Implementar mecanismos de concorrência e controle de acesso (locks) para evitar conflitos e garantir integridade nas reservas simultâneas</li>
  
  <li>📊 Realizar testes automatizados e de stress para validar a consistência do sistema sob diferentes cenários de uso</li>
</ul>


<hr/>

<h2>🖥️ Arquitetura do Sistema</h2>

<h3>Componentes Principais:</h3>

<h4>Cliente (Veículo)</h4>
<ul>
  <li>Monitora o nível de bateria.</li>
  <li>Solicita ao servidor o ponto de recarga mais próximo.</li>
  <li>Realiza reserva e inicia o carregamento.</li>
  <li>Libera o ponto após finalização da recarga.</li>
  <li>Consulta histórico e valores das recargas.</li>
</ul>

<h4>Posto de Recarga</h4>
<ul>
  <li>Informa seu status ao servidor.</li>
  <li>Controla o processo de carregamento.</li>
</ul>

<hr/>

<h2>🛠️ Tecnologias Utilizadas</h2>

<table>
  <tr>
    <th>Tecnologia</th>
    <th>Finalidade</th>
  </tr>
  <tr>
    <td>Python</td>
    <td>Implementação dos componentes</td>
  </tr>
  <tr>
    <td>MQTT</td>
    <td>Comunicação Servidor-Servidor</td>
  </tr>
  <tr>
    <td>Docker</td>
    <td>Containerização dos componentes</td>
  </tr>
</table>

<hr/>

<h2>⚙️ Execução do Projeto</h2>

<p>Clone o repositório:</p>

<pre>
git clone https://github.com/OmegaCoder1/PBL2-Redes.git
cd PBL2-Redes
</pre>

<p><strong>Passo 1 da execução:</strong></p>

<pre>
Rode o comando:
docker-compose run -it teste_multiplos_clientes_diferentes

Com isso todos os containers necessários serão gerados automaticamente.
Após isso, abra os arquivos HTML localizados na pasta "interface".

Após abrir os HTMLs, volte ao terminal e digite a quantidade de usuários que deseja simular fazendo solicitações de reserva de postos.

⚠️ Se preferir testar unitariamente, basta abrir o arquivo "simulador_reserva.html".
</pre>

<p><strong>Testes disponíveis:</strong></p>

<ul>
  <li>
    <strong>Teste 1 – Concorrência com mesma origem e destino:</strong><br>
    Execute: <code>teste_multiplos_clientes_concorrentes_MESMA_ORIGEM_E_DESTINO_FINAL copy.py</code><br>
    Esse teste simula vários usuários tentando reservar os mesmos postos no mesmo horário. Apenas um usuário deverá conseguir a reserva (caso exista rota possível), e os demais receberão erro informando que já existe uma reserva para aquele posto e horário.
  </li><br>
  <li>
    <strong>Teste 2 – Concorrência com origens e destinos diferentes (stress test):</strong><br>
    Execute: <code>teste_multiplos_clientes_concorrentes_ORIGENS_EFINAL_DIFERENTES.py</code><br>
    Você pode definir a quantidade de usuários, e cada um fará requisições com origem e destino aleatórios para testar a robustez do sistema.
  </li><br>
  <li>
    <strong>Teste 3 – Teste de lock de escrita e leitura:</strong><br>
    Execute: <code>testes/teste_lock_geral_f.py</code><br>
    Esse teste verifica o mecanismo de travamento (lock) de escrita/leitura. Enquanto um processo estiver alterando um posto (escrita), nenhuma outra requisição poderá ser processada. Quando não houver escrita ativa, múltiplas leituras poderão ocorrer simultaneamente.
  </li>
</ul>


<h2>📈 Fluxo do Sistema</h2>

<p>Entenda abaixo o funcionamento geral do sistema de reserva:</p>

<pre>
1️⃣ O cliente solicita a reserva de uma lista de postos através de um dos servidores MQTT.

2️⃣ O servidor MQTT entra em contato com os dois servidores de posto via API REST
    🔁 para obter um dicionário com todos os postos disponíveis no sistema.

3️⃣ Com base nos dados recebidos, o servidor:
    🧭 Calcula a rota que o usuário irá percorrer
    📌 Identifica os postos que precisarão ser reservados

4️⃣ O servidor inicia o processo de reserva:
    🔐 Envia requisições de reserva para cada posto da rota via API REST

5️⃣ A cada reserva bem-sucedida:
    ✅ O posto reservado é salvo em um dicionário de confirmações

6️⃣ Se ocorrer qualquer erro durante o processo de reserva:
    ⚠️ O sistema desfaz todas as reservas anteriores
    🔁 Enviando requisições de cancelamento via API REST para os postos já reservados

📦 Resultado: O sistema garante que o usuário só terá uma reserva válida se todos os postos da rota forem reservados com sucesso. Caso contrário, nenhuma reserva é mantida.
</pre>


<hr/>

<hr/>

<h2>👥 Equipe de Desenvolvimento</h2>

<table>
  <tr>
    <th>Nome</th>
    <th>Função</th>
  </tr>
  <tr>
    <td>Luan Barbosa</td>
    <td>Cliente, Postos</td>
  </tr>
  <tr>
    <td>Henrique Zeu</td>
    <td>Cliente, Servidor, Postos</td>
  </tr>
  <tr>
    <td>Robson Jones</td>
    <td>Cliente, Documentação</td>
  </tr>
</table>

<hr/>

<h2>📝 Licença</h2>

<p>
Este projeto foi desenvolvido exclusivamente para fins acadêmicos na disciplina de TEC 502 - MI Concorrência e Conectividade.
</p>
