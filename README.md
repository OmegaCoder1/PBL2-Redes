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
  Escreva o contexto aqui.
</p>

<h3>Principais Problemas Identificados:</h3>

<ul>
  <li>Problemas identi.</li>
</ul>

<hr/>

<h2>🎯 Objetivos da Solução</h2>

<ul>
  <li>Escreva o objetivo aqui.</li>
  
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

<p>Passo 1 da execução:</p>

<pre>
Descrição do passo 1.
</pre>

<h2>📈 Fluxo do Sistema</h2>

<p>Fluxo geral do funcionamento do sistema:</p>

<pre>
Exemplo de fluxo -> Exemplo de fluxo
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
