<h1 align="center">🚗⚡ Sistema Distrbuído e Inteligente de Gerenciamento de Pontos de Recarga para Veículos Elétricos</h1>

<h2>📚 Descrição do Projeto</h2>

<p>
  Este projeto foi desenvolvido como parte da disciplina de <b>TEC 502 - MI Concorrência e Conectividade</b>, com o objetivo de simular um sistema distrbuído e inteligente de gerenciamento de pontos de recarga de veículos elétricos (EV - Electric Vehicle).
</p>

<p>
  A solução foi desenvolvida utilizando o protocolo <b><i>Machine-to-Machine<i> (M2M)</b> e comunicação via <b>MQTT (<i>Message Queue Telemetry Transport<i>)</b>, através do uso de <b>API <i>Rest<i></b> e testado com o <b><i>Portainer<i></b>.
</p>

<p>
  O sistema tem como principal objetivo fornecer aos motoristas informações em tempo real sobre pontos de recarga, realizar reservas remotas e distribuir de maneira eficiente a demanda entre os postos.
</p>

<hr/>

<h2>📝 Contexto do Problema</h2>

<p>
Segundo a Associação Brasileira do Veículo Elétrico, o número de veículos elétricos no Brasil cresce a cada ano, mas a infraestrutura de carregamento não acompanha essa evolução.
</p>

<h3>Principais Problemas Identificados:</h3>

<ul>
  <li>Baixa quantidade de pontos de recarga.</li>
  <li>Filas e longos tempos de espera.</li>
  <li>Falta de informações em tempo real.</li>
  <li>Dificuldade no planejamento de viagens com veículos elétricos.</li>
</ul>

<hr/>

<h2>🎯 Objetivos da Solução</h2>

<ul>
  <li>Localizar o ponto de recarga mais próximo e disponível.</li>
  <li>Realizar reserva antecipada do ponto.</li>
  <li>Liberar o ponto automaticamente após carregamento.</li>
  <li>Distribuir a demanda entre os postos, otimizando o tempo de espera.</li>
  <li>Registrar os valores das recargas realizadas.</li>
  <li>Possibilitar o pagamento posterior via PIX ou outro meio eletrônico.</li>
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

<h4>Servidor Central</h4>
<ul>
  <li>Gerencia os pontos de recarga.</li>
  <li>Controla o status de cada posto (livre/ocupado).</li>
  <li>Realiza distribuição inteligente da demanda.</li>
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
    <td>TCP/IP Sockets</td>
    <td>Comunicação Cliente-Servidor</td>
  </tr>
  <tr>
    <td>UDP/IP Sockets</td>
    <td>Comunicação Postos-Servidor</td>
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
git clone https://github.com/luanbsc/PBL1-Redes.git
cd PBL1-Redes
</pre>

<p>Criar imagem do nosso servidor:</p>

<pre>
docker build -f DockerfileAPISERVIDOR -t imagem_servidor .
</pre>

<p>Criar e rodar um container que mapeia a porta 8015:</p>

<pre>
docker run -d -p 8015:8015 --name servidor_dockerrun imagem_servidor
</pre>

<p>Alterar no arquivo >container_postos>controllers>station_server_controller.py o IP pela máquina que está rodando o servidor</p>

<p>Criar a imagem do posto:</p>

<pre>
docker build -f DockerfilePOSTOS -t imagem_posto .
</pre>

<p>Rodar o container do posto na porta que você desejar passando ela no env:</p>

<pre>
docker run -it -p 9001:9001 -e STATION_TCP_PORT=9001 --name posto_1 imagem_posto
</pre>

<p>Iniciar o arquivo do cliente com testes automáticos:</p>

<pre>
docker build -f DockerfileCLIENTE -t imagem_cliente .
</pre>

<p>Rodar o container do cliente com terminal interativo:</p>

<pre>
docker run -it --rm --name cliente_interativo imagem_cliente
</pre>

<hr/>

<p>Dessa forma você conseguiu inicializar o servidor, um cliente e apenas um posto.</p>

<p>Caso queira fazer um teste de estresse, autorize os scripts de criação de containers para execução:</p>

<pre>
chmod +x start_postos.sh
chmod +x stop_postos.sh
</pre>

<p>Agora, execute o script para iniciar a criação de 100 postos:</p>

<pre>
./start_postos.sh
</pre>

<p>Caso queira apagar todos os containers dos postos, basta rodar:</p>

<pre>
./stop_postos.sh
</pre>

<hr/>

<h2>📈 Fluxo do Sistema</h2>

<p>Fluxo geral do funcionamento do sistema:</p>

<pre>
Cliente -> Servidor: Solicita ponto de recarga mais próximo
Postos -> Servidor: Envia status dos postos para o servidor
Servidor -> Cliente: Informa ponto disponível
Cliente -> Servidor: Realiza reserva do ponto
Cliente -> Posto: Inicia carregamento
Posto -> Servidor: Atualiza status
Cliente -> Servidor: Finaliza carregamento
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
Este projeto foi desenvolvido exclusivamente para fins acadêmicos na disciplina de Redes de Computadores.
</p>
