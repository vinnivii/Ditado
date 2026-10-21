# Ditado

Ditado em português para Windows, com transcrição local usando o Whisper da OpenAI. Grave a partir de qualquer campo com **Ctrl+Alt+Espaço**, pare com o mesmo atalho e cole o texto com **Ctrl+V**.

O aplicativo fica perto do relógio, inicia junto com o Windows e permite revisar os textos em um painel. O pacote de instalação inclui Python, FFmpeg e os modelos; depois de baixá-lo, a instalação e o uso funcionam sem internet, conta OpenAI ou chave de API.

## Baixar

**[Baixar Ditado-Setup-2.1.0.exe](https://github.com/vinnivii/Ditado/releases/download/v2.1.0/Ditado-Setup-2.1.0.exe)** — instalador offline completo, com assistente em português e desinstalação pelo Windows.

[Todas as versões](https://github.com/vinnivii/Ditado/releases) · [Arquivo SHA-256](https://github.com/vinnivii/Ditado/releases/download/v2.1.0/Ditado-Setup-2.1.0.exe.sha256)

## Requisitos

- Windows 10 ou 11 de **64 bits**. A versão foi validada no Windows 10.
- Microfone conectado e com acesso permitido para aplicativos da área de trabalho.
- Aproximadamente **3 GB livres** para a instalação e seus arquivos temporários.
- A instalação é feita para o usuário atual, sem solicitar administrador.

## Instalação passo a passo

1. Baixe **Ditado-Setup-2.1.0.exe** pelo link acima.
2. Se já estiver usando o Ditado, escolha **Sair** no menu do ícone perto do relógio.
3. Dê dois cliques no instalador e siga o assistente em português.
4. Escolha a pasta e os atalhos desejados. A inicialização com o Windows vem selecionada.
5. Clique em **Instalar** e aguarde. Ao concluir, mantenha **Iniciar o Ditado agora** selecionado e clique em **Concluir**.
6. Aguarde a notificação de que o Whisper está pronto. O ícone de microfone aparece perto do relógio, possivelmente dentro da seta de ícones ocultos.

O instalador registra **Ditado** no Painel de Controle e em Aplicativos Instalados. Também cria os atalhos escolhidos e um item **Desinstalar Ditado** no Menu Iniciar.

### Instalação com um comando

Abra o PowerShell na pasta do arquivo baixado e execute:

```powershell
.\Ditado-Setup-2.1.0.exe
```

O único arquivo `.exe` inclui o ambiente completo. Os arquivos de código deste repositório servem para consultar e desenvolver o projeto.

## Como usar

1. Aguarde o aviso de que o programa está pronto.
2. Clique no campo onde deseja colocar o texto.
3. Pressione **Ctrl+Alt+Espaço**. Após o sinal, comece a falar.
4. Pressione **Ctrl+Alt+Espaço** novamente para parar.
5. Aguarde os dois sinais e o aviso **Texto copiado**. Pressione **Ctrl+V** no campo desejado.

A transcrição acontece depois de encerrar a gravação. Cada ditado coloca **somente o trecho mais recente** na área de transferência, substituindo o conteúdo anterior. Cole o trecho antes de começar o próximo.

Para revisar o texto, trocar o microfone ou alterar o modelo, abra o atalho da Área de Trabalho ou use **Abrir painel** no menu do ícone perto do relógio. O painel reúne os ditados da sessão e permite editar, copiar tudo, salvar `.txt` e abrir arquivos de áudio.

**Fechar o painel mantém o atalho global ativo.** Para encerrar o aplicativo, clique com o botão direito no ícone perto do relógio e escolha **Sair**.

| Ícone | Estado |
| --- | --- |
| Verde | Pronto para gravar |
| Vermelho | Gravando o microfone |
| Amarelo | Preparando o modelo ou transcrevendo |

### Modelos disponíveis

- **Mais rápido — base:** modo inicial para reduzir o tempo de espera.
- **Mais precisão — small:** opção para priorizar o reconhecimento; pode levar mais tempo.

Dite em trechos de aproximadamente 30 a 60 segundos e revise nomes, números, datas, endereços e placas antes de registrar a ocorrência.

## Instalação em vários computadores

Copie o instalador `.exe` para um pendrive ou compartilhamento de rede. Execute **no contexto do usuário que utilizará o aplicativo**.

Exemplo no PowerShell, a partir de um compartilhamento:

```powershell
$instalacao = Start-Process -FilePath '\\servidor\programas\Ditado-Setup-2.1.0.exe' `
  -ArgumentList '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART' -Wait -PassThru
$instalacao.ExitCode
```

Substitua o caminho pelo compartilhamento da sua organização. A instalação silenciosa deixa o programa configurado para o próximo logon, sem abri-lo ao terminar.

| Opção | Efeito |
| --- | --- |
| `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART` | Instala sem janelas e sem reiniciar o Windows |
| `/SEM_INICIAR` | Dispensa a execução ao terminar a instalação interativa |
| `/MERGETASKS="!startup"` | Desativa a inicialização automática |
| `/MERGETASKS="!desktopicon,!menuicon"` | Dispensa atalhos de Área de Trabalho e Menu Iniciar |
| `/DIR="D:\Apps\WhisperDitado"` | Define outra pasta de instalação |
| `/LOG="C:\Temp\ditado-instalacao.log"` | Registra detalhes da instalação |

O caminho padrão é `%LOCALAPPDATA%\Programs\WhisperDitado`. O instalador confere os dados extraídos e verifica as dependências. O código de retorno **0** indica sucesso; outros valores indicam cancelamento ou erro. Consulte o log para detalhes.

Como a instalação é por usuário, executar o comando como `SYSTEM` instala para essa conta. Para ferramentas de gestão e scripts de logon, selecione o contexto do usuário. Consulte [IMPLANTACAO.txt](IMPLANTACAO.txt) para os detalhes.

### Atualizar

Saia pelo menu do ícone perto do relógio e execute o novo instalador `.exe`. Ele reconhece a instalação anterior e preserva as preferências. A versão 2.0.0 também pode ser atualizada na mesma pasta; a entrada no Painel de Controle será criada pela nova instalação.

## Solução de problemas

| Situação | O que fazer |
| --- | --- |
| Atalho sem resposta | Abra o aplicativo pelo atalho da Área de Trabalho e aguarde o modelo ficar pronto |
| Atalho ocupado | Feche o aplicativo em conflito ou use os botões do painel |
| Microfone sem áudio | Escolha outro dispositivo no painel e clique em **Atualizar** |
| Microfone bloqueado | Nas configurações de privacidade do Windows, permita acesso ao microfone para aplicativos da área de trabalho |
| Transcrição demorada | Use **Mais rápido — base** e dite trechos menores |
| Sem aviso sonoro | Acompanhe a notificação e o estado do ícone; confira **Avisos sonoros** no painel |

Preferências: `%LOCALAPPDATA%\WhisperDitado\config.json`.

Registro de erros: `%LOCALAPPDATA%\WhisperDitado\transcritor.log`.

## Processamento e arquivos

A transcrição é executada no computador. O aplicativo mantém o áudio do microfone em memória durante o processamento e não o salva em arquivo. Os textos da sessão ficam no painel; use **Salvar .txt** quando quiser guardá-los. O áudio de cada trecho tem limite de 10 minutos.

## Desinstalar

1. Encerre pelo menu **Sair** do ícone perto do relógio.
2. Abra **Painel de Controle → Programas → Programas e Recursos**.
3. Selecione **Ditado** e clique em **Desinstalar**.
4. Confirme a remoção. O desinstalador remove o aplicativo, os modelos, os atalhos e a inicialização automática.

Também é possível usar **Configurações → Aplicativos → Aplicativos instalados → Ditado → Desinstalar**, ou **Desinstalar Ditado** no Menu Iniciar.

As preferências em `%LOCALAPPDATA%\WhisperDitado` e os textos que você salvou são preservados. Para remover também as preferências, exclua essa pasta depois da desinstalação.

Para remoção silenciosa, execute na pasta de instalação:

```powershell
.\Desinstalar.cmd -Silencioso
```

O desinstalador nativo fica em `unins000.exe` nessa mesma pasta e aceita `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART`.

## Organização do código

- `transcritor.py`: painel, gravação, transcrição, cópia automática e bandeja.
- `integracao_windows.py`: atalho global e controle de instância única.
- `instalador/Ditado.iss`: assistente, registro no Painel de Controle e desinstalador nativo.
- `gerar_instalador.ps1`: compilação do instalador com Inno Setup 7.
- `Instalar.cmd` e `Instalar.ps1`: execução do `.exe` com opções em português.
- `Desinstalar.cmd` e `Desinstalar.ps1`: execução do desinstalador registrado no Windows.
- `diagnostico.py`: verificação das dependências e dos modelos.
- `preparar_modelos.py`: download inicial dos modelos para desenvolvimento.
- `gerar_pacote.py`: montagem do pacote offline em Windows, a partir do ambiente de desenvolvimento preparado.
- `requirements-instalados.txt`: versões das dependências usadas nesta distribuição.

O ambiente de desenvolvimento usa Python 3.11, PyTorch para CPU e FFmpeg. `gerar_pacote.py` prepara o runtime portátil com as dependências e os modelos. Depois, execute `gerar_instalador.ps1` com o Inno Setup 7 instalado, ou informe `-Compilador 'C:\caminho\ISCC.exe'`. O parâmetro `-OrigemAplicativo` permite reutilizar um payload já preparado. Os binários e modelos ficam fora do Git; o instalador completo está em **Releases**.

## Componentes de terceiros

Whisper e os modelos são da [OpenAI](https://github.com/openai/whisper). O aplicativo também utiliza Python, PyTorch, SoundDevice, Pystray, Pillow, FFmpeg e bibliotecas de execução do Visual C++.

Consulte [LICENCAS.txt](LICENCAS.txt) e mantenha os avisos e as licenças que acompanham o pacote ao redistribuí-lo.
