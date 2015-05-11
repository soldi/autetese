# AUTETESE
**AUTETESE** (AUTomação da Execução de TEstes de Software Embarcado) é um ambiente que visa a automação da execução dos testes de software embarcado utilizando o sistema operacional EPOS. Em AUTETESE o conjunto de testes é executado automaticamente para cada mudança realizada no sistema.
Dentre as suas principais características estão a simplicidade para a configuração do ambiente, a execução dos testes de forma transparente e a legibilidade nos resultados obtidos.

# Instruções
Para utilizar o ambiente AUTETESE é necessário um sistema operacional Linux e que possua todas as dependências instaladas. 

## Dependências
 * [EPOS](http://epos.lisha.ufsc.br/HomePage)
 * [QEMU](http://wiki.qemu.org/Main_Page)
 * [GDB - versão >= 7.9](http://www.gnu.org/software/gdb/)
 * [Python](https://www.python.org/)

## Como usar
Antes de utilizar o ambiente, é necessária uma configuração dos testes que serão executados automaticamente. A configuração possui um comando help que exibe as seguintes opções de uso: 
```
$ python configure.py --help
usage: configure.py [-h] --filename FILENAME --epospath EPOSPATH [--execute]

Process XML file and outputs TAP scripts.

optional arguments:
  -h, --help           show this help message and exit
  --filename FILENAME  The XML configuration filename (with the .xml extension).
  --epospath EPOSPATH  The absolute path for EPOS.
  --execute            Execute TAP scripts after configuration.
```

Na pasta raiz deste projeto existe um exemplo demonstrativo, no qual o ambiente é configurado para gerar os scripts de automação de teste, executar os testes e, na sequência, gerar o relatório da execução deste testes. 

Para executar este exemplo deve-se primeiro baixar este projeto em sua máquina através do comando 

`git clone https://github.com/soldi/autetese.git`

Uma vez dentro da pasta autetese, executar o seguinte comando abaixo, onde `[caminho para EPOS]` deve ser substituído pelo caminho completo (partindo do diretório raiz) onde encontra-se a sua instalação do EPOS:

`python configure.py --epospath=[caminho para EPOS] --filename=demo.xml --execute`

A configuração do ambiente produz um arquivo de configuração para cada teste que será automatizado. Cada configuração possui um repositório identificado pelo nome do XML (neste caso, demo) e que dentro possui todos os scripts de troca de parâmetros (identificados pelo nome da aplicação de teste). O usuário pode optar por executar o ambiente logo após a configuração adicionando o parâmetro `--execute`. 

Caso o usuário deseje apenas configurar o ambiente e executar os testes manualmente em outro momento, basta suprimir esta opção. Para executar os testes posteriormente, deve-se entrar na pasta do repositório que deseja utilizar, identificar a aplicação de teste e executá-la através do comando **sh**. Como resultado da execução dos scripts de troca de parâmetros, AUTETESE gera uma pasta de logs da execução, contida na pasta `[caminho para EPOS]/log`.

No arquivo **demo.xml** encontram-se as configurações para os testes **task_test** e **semaphore_test**, conforme descrito abaixo:
```
<test>
  <application name="task_test">
    <configuration>
      <trait id="CPUS">
   			<min>-1</min>
   			<max>1</max>
      </trait>
 			<debug>
        <path>debugForTaskTest.gdb</path>
 			</debug>
    </configuration>
  </application>
  <application name="semaphore_test">
    <configuration>
      <trait id="QUANTUM" scope="Thread">
   			<value>10000</value>
   			<value>20000</value>
      </trait>
 			<debug>
 			</debug>
    </configuration>
  </application>
</test>
```
Neste XML, o teste **task_test** está configurado para trocar o trait **CPUS** por valores entre -1 e 1 (inclusive) e, caso a aplicação apresente um resultado diferente do esperado, o ambiente deve utilizar o arquivo **debugForTaskTest.gdb** para depurar o sistema. No caso da automação de **semaphore_test**, o trait modificado será o **QUANTUM** que encontra-se no escopo **Thread**, que pode apenas conter os valores **10000** e **20000**. Este último teste possui a tag **debug**, mas sem um arquivo, identificando que o usuário deseja realizar a depuração manualmente.

Além das tags contidas no exemplo, AUTETESE possui outras opções de configuração. Abaixo encontram-se mais detalhes de como preencher o arquivo XML de configuração do ambiente.

# Configuração do arquivo XML
A configuração de AUTETESE deve iniciar com a tag `<test>`, que identifica que um novo caso de teste será especificado. A partir desta tag raiz, é possível acrescentar as opções de ajustes na execução do teste. Elas são:
 * `<application>` que juntamente com o descritor 'name', deve ser preenchida com a aplicação teste que será executada. É possível apontar mais de um teste no arquivo de configuração, mas cada um deve possuir seus próprios parâmetros de execução. Ou seja, todas as definições `<application>` devem ser filhas de um `<test>`.
 * `<configuration>` é uma tag agrupadora para todas as configurações de um caso de teste. Com esta separação estrutural é possível especificar vários casos de teste para uma mesma aplicação.
 * `<trait>` é onde são definidos os parâmetros que serão analisados nos casos de teste. Esta tag possui o descritor 'id' para armazenar o nome da configuração e o descritor 'scope' para os casos em que o parâmetro deve ser verificado dentro de um escopo específico da aplicação.
 * `<min>` e `<max>` são utilizadas para a definição de valores mínimo e máximo que determinada configuração pode atingir. Estas tags devem ser preenchidas em conjunto e qualquer valor inteiro presente neste intervalo é considerado válido.
 * `<value>` define um valor específico de configuração e deve ser utilizada para discriminar todos os possíves valores inteiros para uma configuração, sendo que cada um deve ser apresentado em uma nova definição de `<value>`.
 * `<debug>` - define onde encontra-se o arquivo de depuração. O caminho até o arquivo é representado em `<path>` e, preferencialmente, iniciar-se com a referência do diretório raiz (/). O usuário pode optar pela forma manual, configurando a tag sem um arquivo de depuração.

# Futuro
 * Integrar **AUTETESE** a serviços de versionamento de software.
 * Mecanismo de envio de e-mail automático dos relatórios.
